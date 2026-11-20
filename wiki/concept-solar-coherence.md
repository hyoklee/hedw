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

## Time convention (measured)

| Series | Stamp | What the value is |
|---|---|---|
| NSRDB GOES v4 hourly, `utc=true` | `Hour=H, Minute=30` | Value at H:30 UTC (W/m²) |
| HEDW-US `solar_GHI` | row H:00 UTC | The same NSRDB H:30 value; nearest-tie reindex, see [concept-nsrdb.md](concept-nsrdb.md) |
| NASA POWER hourly, `time-standard=UTC` | key `YYYYMMDDHH` = H | Mean over [H:00, H+1:00) UTC. Wh/m² for one hour equals mean W/m² |

NSRDB H:30 is the midpoint of POWER hour H, so the expected best lag is 0 h. The first full run measured a best lag of **0 h in all 745 city-years** ([agent_solar_coherence.md](agent_solar_coherence.md)).

## Implementation

| Piece | File |
|---|---|
| Per-city metrics | `../agent/coherence.py` |
| Cross-city robust z, flags, figures | `../agent/aggregate.py` |
| NSRDB gap-fill flags | `../agent/fillflags.py` |

The metrics are:
- hourly r, daylight-only r and lag scan (−3 to +3 h);
- daily r, bias % (ΣNSRDB/ΣPOWER − 1), and daylight RMSE and MAE;
- night GHI > 5 W/m² at zenith > 96°, negative GHI, and runs of 3 or more identical non-zero daylight values;
- days above 1.1 × POWER clear-sky;
- monthly bias.

An anomalous day is a robust outlier of log((NSRDB+50)/(POWER+50)) in daily totals, |z| > 4 within the city, and the two totals also differ by more than 1,000 Wh/m².

The per-city-year thresholds (r_daily < 0.85, |bias| > 15 %, lag outside {−1, 0, +1}, physics > 0.5 %) were **never triggered** in 2019–2023. The flags come from the cross-city robust z instead (|z| > 3; one-sided for r, RMSE and anomalous-day count).

**Where it is computed:** the agent in `../agent/`; results in [agent_solar_coherence.md](agent_solar_coherence.md).

**Related:** [concept-ghi.md](concept-ghi.md), [concept-nsrdb.md](concept-nsrdb.md), [source-nasa-power.md](source-nasa-power.md)
