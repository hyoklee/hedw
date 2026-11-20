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

None yet.

## Workflow studies

None yet.
