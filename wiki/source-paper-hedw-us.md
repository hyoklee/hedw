# Source: HEDW-US descriptor paper

- **Title:** Descriptor: Hourly Electricity Demand and Weather for Major U.S. Cities (2019–2023) Dataset (HEDW-US)
- **Authors:**
  - Mohammed Sleiman (ORCID 0000-0002-1677-3150), Dept. of ECE, Missouri University of Science and Technology, Rolla, MO
  - Rui Bo (ORCID 0000-0001-9108-1093), same department
- **Venue:** *IEEE Data Descriptions* vol. 3, pp. 859–867, 2026. IEEE Xplore article 11781587.
- **Timeline:** received 31 Aug 2026, revised 8 Oct, accepted 30 Oct, published 10 Nov, current version 18 Nov 2026.
- **DOI:** [10.1109/IEEEDATA.2026.3752026](https://doi.org/10.1109/IEEEDATA.2026.3752026). License CC BY 4.0. IEEE PES.
- **Files:** [`raw/paper.pdf`](../raw/paper.pdf), added by the user (commit c4c91d5); Crossref record [`raw/crossref_10.1109_IEEEDATA.2026.3752026.json`](../raw/crossref_10.1109_IEEEDATA.2026.3752026.json).
- **Code:** github.com/MohammedSleiman199/Hourly-Electricity-Demand-and-Weather-Data-for-Major-U.S.-Cities-2019-2023- (ref. [13]); see [source-upstream-code.md](source-upstream-code.md).

## Construction (as described in the paper)

| Stream | Source | Matching | Time handling |
|---|---|---|---|
| Load (`load_mw`) | NREL/OEDI county hourly demand, OEDI submission 8562, v1.2, retrieved Jan 2025 | City → primary FIPS county (multi-county metros summed) | UTC, reindexed onto master index |
| Weather (`weather_air_temperature_c`, `weather_wind_speed_ms`) | NOAA ISD global-hourly, TMP and WND fields | Nearest ISD station to city hall (paper: within 50 km; code: cKDTree nearest, no distance cap) | Hourly mean, linear interpolation ≤ 3 h, nearest match within **15 min** |
| Solar (`solar_*`) | NSRDB (GOES-16/17, 4 km, 30 min native), requested at **60 min, UTC** | NSRDB cell containing city-hall coordinates | Nearest match within **40 min** |

- **Master index:** continuous UTC hourly, 2019-01-01 00:00 to 2023-12-31 23:00, which is 43,824 rows.
- **Cities:** candidates were the 150 most populous; 141 were successfully matched (Fig. 2).

## Variables (Table V): 34 columns per city file

| Group | Columns |
|---|---|
| Load | `load_mw` |
| NOAA weather | `weather_air_temperature_c`, `weather_wind_speed_ms` |
| Solar time | `solar_Year`, `solar_Month`, `solar_Day`, `solar_Hour`, `solar_Minute` |
| Irradiance | `solar_GHI`, `solar_DNI`, `solar_DHI` (W/m²) |
| NSRDB meteorology | `solar_Temperature`, `solar_Wind Speed`, `solar_Wind Direction`, `solar_Dew Point`, `solar_Relative Humidity`, `solar_Pressure` |
| Surface and geometry | `solar_Surface Albedo`, `solar_Solar Zenith Angle` |
| Thermal | `CDD`, `HDD` (base 18.3 °C, per hour), `temp_roll_mean_24h`, `apparent_temperature_c` (Steadman) |
| Derived renewable | `solar_volatility_3h` (3 h rolling std of GHI), `btm_solar_proxy` (GHI × cos(zenith), clipped at 0), `wind_speed_100m_ms` (Hellman α = 0.143) |
| Calendar | `hour_sin/cos`, `month_sin/cos`, `day_of_week_sin/cos`, `is_weekend`, `is_holiday` |

**Timestamps:** the CSVs drop the UTC index, so time has to be rebuilt from the `solar_Year…solar_Minute` columns. The Parquet files keep a UTC `DateTime` index.

## Quality audit (Table I)

- All 141 files have 43,824 rows.
- **OK, 101 files:** no fully missing column and every column ≤ 5 % missing.
- **WARN, 36 files:** some column 5–100 % missing.
- **CRITICAL, 4 files:** dead weather columns.
- The 40 non-OK files are "quarantined".
- On the 101 OK files, all of these passed:
  - continuous unique UTC index;
  - GHI within 0–1500 W/m²;
  - temperature within −40 to 55 °C;
  - load ≥ 0;
  - load lag-24 autocorrelation > 0.85 (mean 0.920);
  - FFT dominant period for temperature and GHI of 8764.8 h, with an annual share of spectral power of 61.5 % for temperature and 6.35 % for GHI.
- **No external validation of irradiance was done.** The paper states the benchmarks "should not be interpreted as independent validation of the underlying source products". This is the gap the [solar coherence check](concept-solar-coherence.md) against NASA POWER fills.

## Benchmarks (Table IV; 101 cities, train 2019–2022, test 2023)

| Task | Mean R² (range) | Mean MAE |
|---|---|---|
| ARX-LSTM load | 0.9929 (0.908–0.999) | 23.34 MW |
| Exogenous LSTM load | 0.8555 (0.371–0.968) | 166.85 MW |
| Random Forest load (100 trees, depth 15) | 0.8644 (0.402–0.961) | 159.94 MW |
| Solar GHI LSTM | 0.8819 (0.732–0.958) | 46.56 W/m² |
| Load-ramp LSTM | 0.8528 (0.329–0.959) | 28.41 MW/h |

- **Small differences from the DataPort description:** ARX MAE 23.66 vs 23.34 MW, and exogenous MAE 164.91 vs 166.85 MW. The paper (current version) is taken as authoritative.
- **FGSM robustness (Table II, ramp LSTM):** clean R² 0.8545 / MAE 28.34 MW. At ε = 0.10, FGSM gives R² 0.6230 (+122.31 % MAE) while random noise gives R² 0.8532 (+0.98 %).

## Records and storage

| Directory | Contents |
|---|---|
| `data_parquet/`, `data_csv/`, `data_merged_h5/` | Each with `merged_data/` (101 OK) and `quarantined_data/` (40) |
| `results/` | Benchmark outputs |
| `figures/` | Publication figures |
| `scripts/` | The pipeline code |

- **File names:** `{State}_{City}_FINAL.parquet` / `.csv`.
- **Merged products:** `merged_101_pristine.{csv,h5}` and `merged_141_master.{csv,h5}`. The HDF5 is pandas key `dataset`, compression level 5, with **no city column**: rows are concatenated with `ignore_index=True`, so city provenance relies on file order.
- **Size:** zip about 3.18 GB. Suggested RAM: 16 GB for one city, 32 GB for many.

## Points relevant to this wiki

1. **Possible half-hour phase shift in solar.** NSRDB hourly records are stamped at a minute offset (commonly :30). Matching them to an :00 master index with a 40-min "nearest" tolerance resolves a tie between HH−1:30 and HH:30. pandas breaks ties toward the later label, which would shift irradiance by +30 min. **Hypothesis only;** to be tested from `solar_Minute` and the cross-correlation lag against POWER ([concept-nsrdb.md](concept-nsrdb.md)).
2. **`btm_solar_proxy` = GHI × cos(zenith)** applies the cosine a second time. GHI is already irradiance on a horizontal plane, so the proxy is not a physical PV estimate; the paper itself calls it a modeling proxy only. It inherits any GHI anomaly.
3. **`solar_volatility_3h`** is a trailing 3-row window that is `fillna(0)`'d (code), so it is also sensitive to the phase question.
4. **Quarantined cities** have gaps in "features" that may include solar columns. They are the natural positive controls for the anomaly agent.

## Related

[source-ieee-dataport-fpqq-nr70.md](source-ieee-dataport-fpqq-nr70.md) · [source-upstream-code.md](source-upstream-code.md) · [concept-nsrdb.md](concept-nsrdb.md) · [concept-ghi.md](concept-ghi.md) · [concept-data-access.md](concept-data-access.md)
