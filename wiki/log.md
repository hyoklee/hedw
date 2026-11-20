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
