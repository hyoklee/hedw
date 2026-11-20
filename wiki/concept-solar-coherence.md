# Concept: Solar irradiance coherence (HEDW-US vs NASA POWER)

**Definition.** For each city, "coherence" here means agreement between the HEDW-US (NSRDB) GHI series and the NASA POWER `ALLSKY_SFC_SW_DWN` series at the same coordinates over 2019-01-01 to 2023-12-31 UTC. Agreement is measured on four axes.

| Axis | Metric | What a failure suggests |
|---|---|---|
| Phase | Lag maximising the hourly cross-correlation (expected 0 h; ±1 h tolerated for hour labelling) | Time-zone, DST or hour-ending vs hour-starting error |
| Amplitude | Daily-total bias and ratio (HEDW / POWER) | Unit error (W/m² vs kW/m², or MJ), scaling, wrong site |
| Shape | Hourly and daily Pearson r, RMSE and MAE, by season | Wrong city coordinates, gaps, repeated or interpolated blocks |
| Physics | Night-time GHI > 0; GHI > 1.1 × POWER clear-sky for long runs; flat-lines | Imputation artefacts, sensor or processing faults |

**Anomaly definition (initial; tune after the first run).** A city-year is anomalous if any of these holds:
- best lag ≠ 0 and ≠ ±1 h;
- daily r < 0.85;
- |daily bias| > 15 %;
- physics violations in more than 0.5 % of hours.

Each city is also given a robust z-score of every metric across all 141 cities, and |z| > 3 is flagged. The 40 quarantined cities *(per descriptor)* act as a sanity check: the detector should flag more of them than of the 101 pristine ones.

**Where it is computed:** the agent in `../agent/` (see [agent_solar_coherence.md](agent_solar_coherence.md) once a run exists).

**Related:** [concept-ghi.md](concept-ghi.md), [concept-nsrdb.md](concept-nsrdb.md), [source-nasa-power.md](source-nasa-power.md)
