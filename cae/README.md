# cae/: clio-core CAE experiments on HEDW-US

HEDW-US city files are CSV. CAE gained a `csv::` assimilator for this work, on clio-core branch `feat/cae-csv-assimilator`, commit `7d45a1cdd`; see [wiki/cae_csv_assimilator.md](../wiki/cae_csv_assimilator.md). OMNI `dataset_filter`s select CSV columns by `/<header>`, so there is no CSV-to-HDF5 conversion step.

## Files: `hedw/`

| File | Purpose |
|---|---|
| `clio_hedw_config.yaml` | Single-node runtime: CTE (2 GB RAM tier) + CAE, port 10700 |
| `nsrdb_solar_omni.yaml.in` | OMNI template with two csv transfers over one NSRDB point-year (include list / exclude list) |
| `strip_nsrdb_header.sh` | `run:` step that drops NSRDB's two metadata lines |
| `run_hedw.sh` | Driver: render the OMNI, start `clio_run`, run `clio_cae`, show the assimilator lines, stop |

## Build clio-core with CSV support

```bash
cd ~/clio-core.dev && git worktree add -b feat/cae-csv-assimilator ~/clio-core.csv origin/dev   # done once
cd ~/clio-core.csv && CC=icx CXX=icpx cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH="$HOME/miniconda3/envs/iowarp;$HOME/miniconda3" \
  -DHDF5_DIR=$HOME/miniconda3/envs/iowarp/cmake \
  -DCLIO_CORE_ENABLE_HDF5=ON -DCLIO_CAE_ENABLE_HDF5=ON -DCLIO_CORE_ENABLE_CAE=ON \
  -DCLIO_CORE_ENABLE_CTE=ON -DCLIO_CORE_ENABLE_TESTS=ON -DBUILD_TESTING=ON \
  -DCLIO_CORE_ENABLE_CEE=OFF -DCAE_ENABLE_S3=OFF
# build the CTE/bdev/admin chimods too, or ParseOmni hangs
make -C build -j 64 clio_run clio_cae clio_cae_core_runtime clio_cte_core_runtime \
  clio_bdev_runtime clio_admin_runtime cae_csv_table cae_csv_assim
(cd build && ctest -R cae_csv)
```

## Run

```bash
cae/hedw/run_hedw.sh                          # default: raw/nsrdb/test_NewYork_2019.csv
cae/hedw/run_hedw.sh raw/data/.../Missouri_KansasCity_FINAL.csv   # once data.zip is in (needs its own OMNI)
```

The HEDW-US city OMNI (`/solar_*`, `/load_mw`) will be added once `raw/data.zip` is available.
