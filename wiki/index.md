# Index

- [overview.md](overview.md): goals, status, synthesis
- [log.md](log.md): chronological record of ingests, queries and tests
- [CLAUDE.md](CLAUDE.md): schema and workflows

## Sources

| Page | Summary |
|---|---|
| [source-paper-hedw-us.md](source-paper-hedw-us.md) | Sleiman & Bo, *IEEE Data Descriptions* 3:859–867 (2026). Construction, 34 columns, quality audit, benchmarks, solar timing caveats |
| [source-upstream-code.md](source-upstream-code.md) | Authors' MIT pipeline (commit e15d054): city coordinates, exact NSRDB request; NREL host now dead |
| [source-ieee-dataport-fpqq-nr70.md](source-ieee-dataport-fpqq-nr70.md) | DataPort record: 141 cities × 43,824 h × 22 columns, `data.zip` 3.18 GB, CC BY 4.0, login required |
| [source-noaa-surfrad-solrad.md](source-noaa-surfrad-solrad.md) | NOAA GML SURFRAD (7) and SOLRAD (7) ground pyranometers, 2019–2023; none within 238 km of a flagged city; GML throttles bulk downloads |
| [source-fawn-midc-cimis.md](source-fawn-midc-cimis.md) | Ground data near the flagged cities: FAWN Fort Lauderdale 10–36 km from 4 flagged cities (reads 8–25 % low, local start-of-hour labels), MIDC LMU on the LA coast (2010–2016), CIMIS blocked without a key |
| [source-nasa-power.md](source-nasa-power.md) | POWER Hourly API v2.10.5: `ALLSKY_SFC_SW_DWN` in Wh/m², UTC, CERES SYN1deg |

## Concepts

| Page | Summary |
|---|---|
| [concept-data-access.md](concept-data-access.md) | Download issues: IEEE Xplore returns 418, DataPort needs a login, no mirrors. Manual steps and a fallback |
| [concept-ghi.md](concept-ghi.md) | Global horizontal irradiance and its physical consistency checks |
| [concept-nsrdb.md](concept-nsrdb.md) | NREL NSRDB, the HEDW-US irradiance source; resampling and time-zone pitfalls |
| [concept-solar-coherence.md](concept-solar-coherence.md) | Coherence metrics (phase, amplitude, shape, physics) and anomaly thresholds |

## CAE experiments

| Page | Summary |
|---|---|
| [cae_csv_assimilator.md](cae_csv_assimilator.md) | New clio-core `csv::` assimilator: column-wise ingest with `dataset_filter`; 47/47 CAE tests pass; NSRDB real-data run, 116 ms |

## Agent runs

| Page | Summary |
|---|---|
| [agent_solar_coherence.md](agent_solar_coherence.md) | NSRDB (HEDW-US solar) vs NASA POWER, 149 cities, 2019–2023: lag 0 h in all 745 city-years, median daily r 0.977; 17 coastal or mountain-edge cities flagged; NSRDB gap-filled the whole eastern domain (109 cities) on 6 days, passed into HEDW-US unflagged; clio-agent 10/10, clio-coder prose errors; at 14 SURFRAD and SOLRAD sites NSRDB beats POWER (daily RMSE 9.0 % vs 12.0 %) but is badly wrong on the filled days (25.8 % vs 10.8 %) |

## Workflow studies

| Page | Summary |
|---|---|
| [workflow_aurora_clio.md](workflow_aurora_clio.md) | Stage timings on Aurora: downloads ~25 min on the login node, detector 2.6 s (P=16) vs debug job 7 s plus ~3 min queue, CAE bulk ingest 95 files/s; clio-core ctest kills clio-agent's runtime |
