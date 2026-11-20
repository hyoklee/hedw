# Log

## [2026-11-20] bootstrap | Wiki and repo created

- Created the layout (`wiki/`, `raw/`, `cae/`, `agent/`, `bench/`) on the pattern of hyoklee/poro, and the GitHub repo hyoklee/hedw.
- The IEEE Xplore page for article 11781587 refuses automated access (HTTP 202 with an empty body, then HTTP 418). Paper metadata comes from Crossref instead.

## [2026-11-20] ingest | Paper metadata (doi:10.1109/IEEEDATA.2026.3752026)

- Crossref record saved to `raw/crossref_10.1109_IEEEDATA.2026.3752026.json`. CC BY 4.0. Unpaywall: OA at the publisher, no repository copy.
- Page: [source-paper-hedw-us.md](source-paper-hedw-us.md).

## [2026-11-20] ingest | IEEE DataPort record (doi:10.21227/fpqq-nr70)

- DataCite record saved to `raw/datacite_10.21227_fpqq-nr70.json`.
- The landing page lists `data.zip` (3.18 GB), `results` (38.76 KB) and `figures` (13.2 MB). Files need a DataPort subscription or login.
- Page: [source-ieee-dataport-fpqq-nr70.md](source-ieee-dataport-fpqq-nr70.md).

## [2026-11-20] test | NASA POWER hourly API from the Aurora login node

- `temporal/hourly/point`, St. Louis (38.63, −90.20), 2019-07-01, UTC. Four irradiance parameters returned. API v2.10.5, sources SYN1DEG and POWER, fill value −999.0.
- Saved to `raw/power/sample_hourly_stlouis_20190701.json`.
- Page: [source-nasa-power.md](source-nasa-power.md).

## [2026-11-20] query | Which input formats does clio-core CAE accept?

- clio-core `a23b96cbd` (2026-11-11): the OMNI `format` values in the CAE sources are `hdf5`, `hdf5_vol`, `binary` and `sequential`; there is no CSV reader.
- Decision: convert the HEDW-US CSVs to HDF5 with one dataset per column before ingesting through CAE.

## [2026-11-20] query | Can the paper and data be downloaded automatically?

- No. IEEE Xplore returns 202 with an empty body, or 418, for every URL, including the Crossref similarity-checking link. Unpaywall lists no repository copy. DataPort files need a login. GitHub, Hugging Face, Zenodo and web searches found no mirror.
- Spoofing a browser to get past IEEE's bot blocking was refused by the permission system and will not be retried.
- Filed as [concept-data-access.md](concept-data-access.md), with the manual download steps and an NSRDB-API fallback.

## [2026-11-20] ingest | Paper PDF (raw/paper.pdf, added by the user in c4c91d5)

- Read all 9 pages (vol. 3, pp. 859–867). Rewrote [source-paper-hedw-us.md](source-paper-hedw-us.md) with the construction, the 34 columns, the audit (101 OK / 36 WARN / 4 CRITICAL) and the benchmarks.
- The paper says no external validation of irradiance was done.
- Flagged a possible +30 min solar phase shift (nearest-tie alignment with a 40 min tolerance) and the GHI·cos(zenith) proxy.

## [2026-11-20] ingest | Authors' pipeline code (commit e15d054)

- Shallow-cloned to `raw/upstream/hedw-code/` (git-ignored); not executed. MIT license.
- `target_cities.csv` gives 150 city-hall coordinates. The NSRDB request is GOES aggregated v4, interval 60, utc=true.
- Page: [source-upstream-code.md](source-upstream-code.md).

## [2026-11-20] query | Can the NSRDB stream be rebuilt?

- `developer.nrel.gov` no longer resolves (NREL is now NLR); `developer.nlr.gov` works.
- The API key signup is behind reCAPTCHA and needs first and last name, so the user has to create the key. Recorded in [concept-data-access.md](concept-data-access.md).

## [2026-11-20] test | NLR API key and the first NSRDB download

- The user-provided key is saved in `~/.config/hedw/nlr.env` (mode 600, outside the repo).
- `developer.nlr.gov/.../nsrdb-GOES-aggregated-v4-0-0-download.csv` returns a 302 to S3 (`nsrdb-data.stratus.nlr.gov`). `full_name` is not required.
- New York 2019: 8,760 rows, all `Minute = 30`. pandas 2.3.3 nearest-tie goes to the later record, so HEDW-US row HH:00 holds NSRDB HH:30. Recorded in [concept-nsrdb.md](concept-nsrdb.md); script `agent/checks/nearest_tie.py`.

## [2026-11-20] test | CSV assimilator added to clio-core CAE

- The user asked for CSV support in CAE. This supersedes the earlier "convert CSV to HDF5" decision.
- clio-core branch `feat/cae-csv-assimilator`, commit `7d45a1cdd` (local, base `dev` 1ad647318): `csv::` source, `format: csv`, columns filtered as `/<header>`, the same tag and blob layout as HDF5.
- `ctest -R '^cae_'` passes 47/47. The new tests are `cae_csv_table` and `cae_csv_assim` (200k rows, byte-for-byte; −9 and −5 paths).
- NSRDB NYC 2019 run through `cae/hedw/run_hedw.sh`: `clio_cae` exit 0 in 116 ms; 16 columns × 8,760 rows; 9 selected per transfer.
- Page: [cae_csv_assimilator.md](cae_csv_assimilator.md).

## [2026-11-20] test | CSV assimilator PR opened

- Pushed `feat/cae-csv-assimilator` (7d45a1cdd) to the fork hyoklee/core. Opened [iowarp/clio-core#1393](https://github.com/iowarp/clio-core/pull/1393) against `dev`.

## [2026-11-20] test | PR #1393 patch coverage fixed
- **Problem:** Codecov reported patch coverage of 97.63 %, with 5 uncovered lines (4 in `csv_table.cc`, 1 in `csv_file_assimilator.cc`).
- **Fix:**
  - Two of the lines were untested error paths. Added tests for a blank first line and for a bad last record with no trailing newline.
  - Three were closing braces of functions that return a named local. GCC 13 marks these as exception-only blocks (`=====`) and lcov 2 counts them as misses. `EncodeCsvColumn` and `SelectColumns` now fill out-parameters instead.
- **Verification:** GCC 13.4 with gcov shows `csv_table.cc` fully covered; `ctest -R '^cae_'` passes 47/47; lint is clean.
- **Pushed:** commit `9ed157887`, waiting for CI. Details in [cae_csv_assimilator.md](cae_csv_assimilator.md#patch-coverage-codecov).

## [2026-11-20] ingest | NSRDB and NASA POWER for all target cities
- **POWER:** 150/150 cities, 2019–2023 hourly, with all-sky, clear-sky, DNI and diffuse. 594 MB in `raw/power/`.
- **NSRDB:** 745/750 city-years, using the authors' request. Anchorage gets HTTP 400 "No data available": GOES v4 does not cover Alaska. 601 MB in `raw/nsrdb/`. The run took 1,419 s; burst HTTP 429s were all retried successfully.
- **Script and logs:** `agent/fetch/fetch_all.py`; logs are in `agent/results/fetch/`, with the email redacted.
- **Pages updated:** [concept-data-access.md](concept-data-access.md), [source-nasa-power.md](source-nasa-power.md).

## [2026-11-20] test | Solar-coherence agent, first full run
- **Runs:**
  - `run_20261120T143434Z_local_p16` (reference, login node).
  - PBS 9107657 (1 node × 50 ranks) and 9107666 (1 × 16) in `debug`. Their outputs are identical.
- **Agreement:**
  - The best lag is 0 h in all 745 city-years.
  - Median hourly r is 0.9785 and median daily r 0.9768.
  - Median bias is +1.11 %.
  - No physics violations.
- **Flagged:** 17 cities, all coastal Southern California, the Inland Empire, South Florida, Oakland or Honolulu. Monthly bias patterns suggest the cause is mixed ocean, mountain or land within POWER's 1° cells.
- **NSRDB artefact:** 2020-02-14 was gap-filled across 31 eastern cities. In Birmingham, every daylight hour has Fill Flag 100 and the GHI is flat at 25–51 W/m² on a clear day. HEDW-US inherits these values unflagged.
- **clio-agent `hedw/solar-coherence`:** benchmark 10/10 (median 2.2 s, 1 tool call per question). On the open Dallas 2021-02-17 question, all its numbers were verified.
- **clio-coder interpretation:** all 71 of its numbers are supported, but its prose has 4 errors (see the reviewer note).
- **Scaling:** see [workflow_aurora_clio.md](workflow_aurora_clio.md).
- **CAE:** bulk `csv::` ingest of 746 NSRDB files in 7.86 s.
- **Hazard:** clio-core's ctest cleanup killed the clio-agent runtime.
- **Pages:** [agent_solar_coherence.md](agent_solar_coherence.md), [workflow_aurora_clio.md](workflow_aurora_clio.md).

## [2026-11-20] test | PR #1393 merged with dev (path policy)
- **Why:** #1392 (the CAE local path policy) landed on `dev`, so the PR conflicted and GitHub skipped CI on the coverage commit.
- **What:** merge commit `9b44e0f3e` keeps both sides and applies `PathPolicy` to `csv::` sources. It adds a refusal test (a CSV under `.ssh` gives ParseOmni −2).
- **Result:** `ctest -R '^cae_'` passes 46/46 and the PR is mergeable again.
- **Side effect:** the ctest run killed the clio-agent runtime again, so the server was restarted ([workflow_aurora_clio.md](workflow_aurora_clio.md)).

## [2026-11-20] test | NSRDB gap-fill audit (fill_flag, 745 city-years)
- **Download:** `fetch_all.py --only flags` fetched 745/750 in 1,010 s (Anchorage has no data). Analysis: `agent/fillflags.py`. Results: `fillflags.json`, `fillflag_days.csv` and `fill_episodes.txt` in `run_20261120T143434Z_local_p16`.
- **Routine filling:** a median of 1.34 % of daylight hours (clear-sky GHI > 200) have fill ≥ 50.
- **Episodes:** 2019-11-17 to 20 and 2020-02-13 to 14 were filled in the same 109 cities, all east of about −113°. None of the 40 western cities is affected.
- **Enrichment:** filled days are 4.28 % of the listed anomalous days against a 0.615 % base rate. Flagged cities have a median of 3.73 % filled hours against 1.31 % for the rest.
- **Agent:** clio-agent plugin 0.2.0: `hedw_day` now shows the fill flag and cloud type. On Atlanta 2019-11-18 it correctly said the values were gap-filled, all numbers verified, with one interpretive error ("mostly cloudy" on a clear day).

## [2026-11-20] test | SURFRAD ground truth for the coherence check
- **Question:** check SURFRAD stations for the 17 flagged cities.
- **Answer:** none is close. The nearest stations are Hanford CA and Desert Rock NV at 238–454 km for California, Goodwin Creek at ~1,300 km for South Florida, and ~4,000 km for Honolulu. None is in a comparable coastal climate.
- **Alternative test:** NSRDB and POWER against the ground at the 7 SURFRAD stations, 2019–2023. The 1-min data was reduced to hourly while streaming (`agent/ground/fetch_ground.py`); NSRDB, flags and POWER were fetched at the station coordinates; `agent/ground/validate.py` did the comparison. Results: `agent/results/ground_20261120_surfrad/`.
  - NSRDB is closer than POWER at all 7: median daily RMSE 9.1 % against 11.8 %, hourly 62.1 against 78.7 W/m².
  - Routine filled hours are fine (36.6 against 41.2 W/m²).
  - The episode fill days are wrong in NSRDB: median absolute daily error 28.2 % against 10.2 % for POWER, hourly RMSE 107.5 against 63.1 W/m².
- **Operations:**
  - GML refused TLS from this node after about 12,000 files at 8 workers. The SOLRAD fetch now waits for GML and resumes with 3 workers.
  - NSRDB returned 3 transient HTTP 400s for station-years; they succeeded on retry.
- **Pages:** [source-noaa-surfrad-solrad.md](source-noaa-surfrad-solrad.md), [agent_solar_coherence.md](agent_solar_coherence.md#ground-truth-surfrad-and-solrad).
