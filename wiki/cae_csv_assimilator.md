# CAE: CSV assimilator (csv:: sources)

HEDW-US ships each city as CSV (and Parquet). clio-core CAE could read only `hdf5` and `binary`. We added a CSV assimilator to clio-core so the OMNI `dataset_filter` can select CSV **columns** directly, with no conversion to HDF5 first.

## Change

| Item | Value |
|---|---|
| Repo / branch | `iowarp/clio-core`, local branch `feat/cae-csv-assimilator` in `~/clio-core.csv` (worktree of `~/clio-core.dev`) |
| Base | upstream `dev` at `1ad647318` (2026-11-20) |
| Commits | `7d45a1cdd` "CAE: add a CSV assimilator (csv:: sources, format csv)"; `9ed157887` "CAE csv: cover the remaining patch lines"; `9b44e0f3e`, a merge of upstream `dev` that applies the path policy to `csv::` (2026-11-20). Fork `hyoklee/core`, branch `feat/cae-csv-assimilator` |
| PR | [iowarp/clio-core#1393](https://github.com/iowarp/clio-core/pull/1393), base `dev`, opened 2026-11-20 |
| Size | 15 files, about 1,430 lines new (7 files) plus about 80 changed. The shared glob matcher moved out of `hdf5_file_assimilator.cc`, which drops 119 lines there |

### Semantics

- `src: csv::<path>`, `format: csv`. The factory dispatches the `csv` protocol to `CsvFileAssimilator`, which has no optional dependencies.
- Each column is filtered as the dataset name `/<header>`. It uses the same matcher as HDF5: fnmatch with flags 0 on POSIX, a portable copy on Windows, now shared in `glob_match.h`.
- Each selected column becomes tag `<dst>/<header>`, holding a `description` blob and `chunk_0..N` blobs of at most 1.5 MB each. This is identical to the HDF5 dataset layout, so existing readers work.
- Types:

  | Column contents | Stored as |
  |---|---|
  | All fields int64 | `tensor<int64, N>` |
  | Otherwise all non-empty fields numeric (empty → NaN) | `tensor<float64, N>` |
  | Otherwise | `tensor<char, N, W>`, NUL-padded to W bytes |

- Parsing is RFC 4180: quotes, `""`, embedded commas and newlines, LF or CRLF, BOM, trailing blank lines.
- Errors:
  - **-5:** syntax error, field-count mismatch or duplicate header.
  - **-9:** the include list matched no column.
  - **-6:** a column failed to store.
- A `run:` step's output is ingested as `csv::` when `format: csv`.
- Limitation: the whole file is read into memory on the node running the transfer. That is fine for HEDW-US: one city is 43,824 rows × 34 columns.

## Verification

- **Platform:** Aurora login node `aurora-uan-0012`, icpx 2026.1.0, Release, HDF5 2.1.0 (conda `iowarp` env).
- **Unit tests:** the full `ctest -R '^cae_'` suite ran 47/47 green, including the new tests:
  - `cae_csv_table`: parser and encoder, no runtime.
  - `cae_csv_assim`, 1.2 s: a 200,000-row file run through `ParseOmni` with three filters (none; `/solar_*` minus `/solar_Minute`; `/id` + `/c?ty`). Every selected column was read back from CTE and compared **byte for byte**:

    | Column | Description | Chunks | Bytes |
    |---|---|---|---|
    | `id` | `tensor<int64, 200000>` | 2 | 1,600,000 |
    | `solar_GHI` (empty fields as NaN) | `tensor<float64, 200000>` | 2 | 1,600,000 |
    | `city` (quoted, with commas and quotes) | `tensor<char, 200000, 15>` | 2 | 3,000,000 |

    Rejected columns had no blobs. An include list matching nothing returned −9; a malformed file returned −5.
  - Existing tests that touch the edited code, still green: `cae_hdf5_dataset_filter`, `cae_omni_loader`, `cae_cloud_factory_guard`.
- **Lint:** the new files pass cpplint and are formatted with clang-format 19.1.7 using the repo's `.clang-format`.

### Real-data run (NSRDB)

`cae/hedw/run_hedw.sh` runs the New York 2019 NSRDB file from `raw/nsrdb/` on a fresh single-node runtime (port 10700, 2 GB RAM tier). It uses OMNI `cae/hedw/nsrdb_solar_omni.yaml.in`, whose `run:` step `strip_nsrdb_header.sh` drops NSRDB's two metadata lines.

```
clio_cae exit=0 elapsed=116 ms
CsvFileAssimilator: '.../nsrdb_table.csv': 16 column(s) x 8760 row(s), 9 selected
CsvFileAssimilator: '.../nsrdb_table2.csv': 16 column(s) x 8760 row(s), 9 selected
ParseOmni: Successfully scheduled 2 assimilations
```

- Transfer 1 used an include list of the 5 time fields plus GHI, DNI, DHI and Solar Zenith Angle.
- Transfer 2 excluded the 7 meteorology columns.
- Both kept 9 of the 16 columns, as intended.
- This run checks the column selection only, not the stored bytes; that byte-for-byte check is done by `cae_csv_assim`. A Python-side verifier like poro's `verify_porotomo.py` would need clio-core built with `CLIO_CORE_ENABLE_PYTHON=ON`.

## Patch coverage (Codecov)

The first CI run passed every check, but Codecov reported patch coverage of 97.63 %, with 5 lines uncovered. The line list came from the public Codecov API (`api.codecov.io/api/v2/github/iowarp/repos/clio-core/compare/file/<path>?pullid=1393`).

| Line | Cause | Fix |
|---|---|---|
| `csv_table.cc:74-75` | No test for a blank first line (the "empty header" error) | New test |
| `csv_table.cc:202` | No test for a malformed last record without a trailing newline | New test |
| `csv_table.cc:287`, `csv_file_assimilator.cc:75` | Closing braces of `EncodeCsvColumn` and `SelectColumns` | Both now fill an out-parameter |

**Why the closing braces counted as missed.** Both functions return a named local (NRVO). GCC 13 puts the exception cleanup of that object on the closing brace. That is an exception-only block that never runs (`=====` in gcov), and lcov 2 counts it as a missed line. CI collects coverage with GCC 13.3 and lcov 2.x.

A 30-line experiment under GCC 13.4 reproduced this. Returning a local struct or vector left a `=====` brace; filling a caller-owned out-parameter did not.

**Verification:**
- GCC 13.4 with gcov shows no unexecuted lines in `csv_table.cc`.
- `ctest -R '^cae_'` passes 47/47.
- clang-format 19.1.7 and cpplint are clean.

## Bugs and notes found on the way

- **Missing CTE chimod gives a hang, not an error.** The first test run hung for 300 s because only the CAE targets had been built. The runtime log said `ChiMod 'clio_cte_core' not found`, but `ParseOmni` then waited forever (`[stuck-wait] no completion after 60s`) instead of failing. Build `clio_cte_core_runtime`, `clio_bdev_runtime` and `clio_admin_runtime` before running CAE tests. Fail-fast behaviour here would help; this is not filed upstream.
- **Upstream:** opened as [iowarp/clio-core#1393](https://github.com/iowarp/clio-core/pull/1393).
  - **Conflict:** #1392 (the CAE local path policy) merged into `dev` on 2026-11-20. The PR then showed as CONFLICTING, and GitHub ran no CI on the coverage commit.
  - **Resolution:** a merge, not a rebase, so no force-push was needed. It keeps both sides in `core/CMakeLists.txt` and `assimilator_factory.cc`.
  - **csv:: now checked:** `AssimilatorFactory::Get` applies `PathPolicy` to `csv::` sources as well as `file::` and `hdf5::`.
  - **New test case:** in `test_csv_assim`, a valid CSV under `<tmp>/cae_csv_policy/.ssh/` is refused and ParseOmni returns −2.
  - **Results:** `ctest -R '^cae_'` passes 46/46, including `cae_path_policy`. The PR is MERGEABLE again.

## Related

[cae/README.md](../cae/README.md) · [source-paper-hedw-us.md](source-paper-hedw-us.md) (Records and storage) · [concept-nsrdb.md](concept-nsrdb.md)
