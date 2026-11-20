# HEDW-US Wiki: Schema

This wiki documents the HEDW-US dataset: hourly electricity demand and weather for 141 U.S. metro areas, 2019–2023 (paper doi:10.1109/IEEEDATA.2026.3752026; data doi:10.21227/fpqq-nr70). It covers three things:
- the dataset itself;
- a check of its solar irradiance against NASA POWER;
- how IOWarp's Context Assimilation Engine (clio-core CAE) and CLIO agents process it on Aurora.

The LLM maintains every file under `wiki/`. Raw sources are never modified:
- the paper;
- the IEEE DataPort files (`data.zip`, `results`, `figures`);
- the NASA POWER API responses;
- the metadata records in `../raw/`.

The dataset zip and the extracted CSVs live in `../raw/` and are not committed (see `../.gitignore`).

## Directory layout

```
wiki/
  CLAUDE.md          ← this file (schema)
  index.md           ← catalog of all wiki pages
  log.md             ← append-only event log
  overview.md        ← high-level synthesis
  source-*.md        ← one page per raw source (paper, DataPort record, POWER API, city file)
  concept-*.md       ← reusable concept / entity pages
  cae_*.md           ← CAE / OMNI ingestion experiments and their results
  agent_*.md         ← agent runs (code in ../agent/, results in ../agent/results/run_*/)
  workflow_*.md      ← Aurora workflow and allocation studies (code in ../bench/)
```

## Page conventions

- Use GitHub-flavored markdown. Link between pages with `[text](file.md)`.
- Every `source-*.md` page lists:
  - provenance (DOI or URL), license and access conditions;
  - for data files: columns or datasets with units, time base (UTC or local) and record count;
  - known quality issues.
- Every `concept-*.md` page lists: definition, where it appears (which sources), related concepts.
- Every `cae_*.md` page lists:
  - platform and compiler, clio-core commit, OMNI file used;
  - what was verified and how;
  - timings in milliseconds;
  - any bugs found.
- Every `agent_*.md` page lists:
  - the question;
  - agent design: data, detector, PBS job, model, LLM steps;
  - the run directory and PBS job id;
  - results with figures;
  - limitations, and how reliable the LLM steps were.
- Every `workflow_*.md` page lists: nodes, ranks, queue, wall time, node-hours charged, throughput, and the bottleneck.
- Numbers come from the source or from a run recorded in `log.md`, never from memory.
- Mark claims taken from the dataset description or the paper, rather than measured here, with *(per descriptor)*.

## Workflows

### Ingest a source
1. Save the immutable source (or its metadata record) under `../raw/`.
2. Write or update `source-<name>.md`. Update the `concept-*.md` pages it touches.
3. Update `index.md` and append to `log.md`.

### Run a CAE ingestion test
1. Convert the city CSVs to HDF5, one dataset per column (`cae/hedw/csv_to_h5.py`), because CAE reads `hdf5` and `binary` only.
2. Write or reuse an OMNI file with a `dataset_filter` that selects only the columns the analysis needs, for example the GHI and timestamp columns.
3. Run it through `clio_cae` and the verifier. Check byte-for-byte.
4. File the result as `cae_<topic>.md` and log it.

### Run the solar-coherence agent
1. Fetch the matching NASA POWER hourly series (`ALLSKY_SFC_SW_DWN`, UTC) for each city's coordinates. Cache them under `../raw/power/`.
2. Align both series to UTC. NSRDB values are instantaneous or period-centred W/m²; POWER hourly values are Wh/m² for the hour. Record the convention used.
3. Compute the coherence metrics per city and year, flag anomalies, and write `summary.json`.
4. Use clio-coder to interpret the run. Check every number it quotes against `summary.json`.
5. File the result as `agent_<topic>.md` and log it with kind `test`.

### Answer a query
1. Read `index.md`, then the relevant pages.
2. Write the answer with page citations. If it is worth keeping, file it as a page and log the query.

### Lint
Check for:
- orphan pages;
- stale claims;
- contradictions between pages;
- concepts that are mentioned but have no page.

## Log entry format

`## [YYYY-MM-DD] <kind> | <title>`, where kind is one of `bootstrap`, `ingest`, `query`, `test`, `lint`.
