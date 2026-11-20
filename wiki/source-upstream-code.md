# Source: HEDW-US pipeline code (authors' GitHub)

- **Repo:** https://github.com/MohammedSleiman199/Hourly-Electricity-Demand-and-Weather-Data-for-Major-U.S.-Cities-2019-2023- (paper ref. [13])
- **Commit inspected:** `e15d054da1b172c3f8a9881f50b16ac4a3eae90c` (2026-08-06). Shallow-cloned to `raw/upstream/hedw-code/`, which is git-ignored; re-clone at this commit. **Read only, never executed.**
- **License:** MIT (`LICENSE_CODE.txt`), © 2026 Mohammed Sleiman and Rui Bo.
- **Python stack (`requirements.txt`):** pandas 2.3.3, numpy 1.26.4, h5py 3.15.1, tables 3.10.1, scikit-learn 1.7.2, tensorflow 2.20.0, torch 2.10.0.

## Scripts

| Script | Role |
|---|---|
| `01_map_cities.py` | Top 150 cities by population from plotly's `us-cities-top-1k.csv`; nearest ISD station (cKDTree on lat/lon degrees, no distance cap, station active 2019-01-01..2023-12-31); nearest of 30 hard-coded BA hubs. Writes `target_cities.csv` |
| `02_build_dataset.py` | Downloads load (OEDI HDF5), NOAA ISD and NSRDB; aligns everything to the UTC master index; feature engineering |
| `03_audit_dataset.py`, `04_quarantine.py` | Missingness audit (OK / WARN > 5 % / CRITICAL dead or no-load); move the non-OK files |
| `05`–`06` | Inspect, merge, export (CSV and HDF5) |
| `07`–`11` | The five benchmarks |
| `12`–`13` | Aggregation and figures |

## `target_cities.csv`

- 150 rows. Columns `name,lat,lon,ba,station`, e.g. `Missouri_KansasCity` style names, city-hall lat/lon, BA label, 11-digit ISD id.
- The final release has 141 cities, so 9 were dropped downstream.
- BA counts: CISO 31, PJM 21, ERCO 16, SWPP 11, SOCO 9, …
- **This is the coordinate list for the NASA POWER and NSRDB requests.**

## NSRDB request in `02_build_dataset.py`

```
NSRDB_URL = https://developer.nrel.gov/api/nsrdb/v2/solar/nsrdb-GOES-aggregated-v4-0-0-download.csv
params: names=<year>, interval=60, utc=true, leap_day=true,
        attributes=ghi,dni,dhi,air_temperature,wind_speed,wind_direction,dew_point,
                   relative_humidity,surface_pressure,surface_albedo,solar_zenith_angle,
        wkt=POINT(<lon> <lat>), api_key, full_name, email, affiliation, reason
```

- The response skips 2 metadata lines.
- `timestamp_utc` is built from Year/Month/Day/Hour/Minute.
- The result is aligned with `reindex(master_idx, method='nearest', tolerance='40min')`.

## Findings

- **Dead host:** `developer.nrel.gov` no longer resolves (2026-11-20); NREL was renamed the National Laboratory of the Rockies. The live API host is `developer.nlr.gov`, so the script cannot reproduce the data as written. See [concept-data-access.md](concept-data-access.md).
- **Distance cap:** the paper says the station is "within 50 km"; `01_map_cities.py` applies no distance cap.
- **Solar features:** `btm_solar_proxy = GHI·cos(zenith)` clipped at 0, and `solar_volatility_3h = GHI.rolling(3).std().fillna(0)`; see [source-paper-hedw-us.md](source-paper-hedw-us.md).

## Related

[source-paper-hedw-us.md](source-paper-hedw-us.md) · [concept-nsrdb.md](concept-nsrdb.md) · [source-nasa-power.md](source-nasa-power.md)
