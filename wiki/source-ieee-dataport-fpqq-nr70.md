# Source: IEEE DataPort record "Hourly Electricity Demand and Weather Data for Major U.S. Cities (2019–2023)"

- **DOI:** [10.21227/fpqq-nr70](https://doi.org/10.21227/fpqq-nr70)
- **Landing page:** https://ieee-dataport.org/documents/hourly-electricity-demand-and-weather-data-major-us-cities-2019-2023 (DataPort dataset id 14627)
- **Citation:** Mohammed Sleiman, Rui Bo, IEEE DataPort, February 28, 2026.
- **License:** CC BY 4.0 (DataCite `rightsList`).
- **Access:** "Subscription Required". Files need an IEEE DataPort login; IEEE Society members are included. No public mirror was found; see [concept-data-access.md](concept-data-access.md).
- **Metadata record:** [`raw/datacite_10.21227_fpqq-nr70.json`](../raw/datacite_10.21227_fpqq-nr70.json)

## Files (from the landing page, 2026-11-20)

| File | Size |
|---|---|
| `data.zip` | 3.18 GB |
| `results` | 38.76 KB |
| `figures` | 13.2 MB |

The page also links a `README.md` with usage instructions. Not yet downloaded.

## Content *(per descriptor)*

- **Cities:** 141 U.S. metropolitan areas, one file each.
- **Size:** 43,824 hourly records × 22 columns per file. That is 1,826 days × 24 hours, so 2019-01-01 through 2023-12-31 with 2020 as a leap year.
- **Three source streams, synchronised:**
  1. County-level demand in MW from the NREL/OEDI Hourly Electricity Demand dataset (Obika et al., 2025).
  2. Station weather from the NOAA Integrated Surface Database (ISD).
  3. Satellite solar irradiance from the NREL National Solar Radiation Database (NSRDB); see [concept-nsrdb.md](concept-nsrdb.md).
- **Engineered features:**
  - apparent temperature (heat index);
  - 24 h thermal memory;
  - cooling and heating degree days;
  - wind at 100 m hub height (Hellman power law);
  - behind-the-meter rooftop-solar proxy;
  - 3 h solar volatility;
  - cyclical encodings of hour, day of week and month.
- **Quality split:**
  - 101 "pristine" cities: zero missing values, zero imputation.
  - 40 "quarantined" cities with documented data-quality issues, meant as a benchmark for imputation and denoising.
- **ML validation:** trained on all 101 pristine cities, held-out test year 2023.

  | Model | R² | MAE |
  |---|---|---|
  | ARX-LSTM load | 0.993 | 23.66 MW |
  | Weather-only LSTM load | 0.853 | 164.91 MW |
  | Random Forest load | 0.864 | 159.94 MW |
  | LSTM ramp rate | 0.853 | 28.41 MW/h |
  | LSTM solar GHI | 0.881 | 46.56 W/m² |

## Open questions for ingest

The paper and code ([source-paper-hedw-us.md](source-paper-hedw-us.md), [source-upstream-code.md](source-upstream-code.md)) answer most of these:
- **Time base:** UTC master index. The CSVs rebuild time from `solar_Year…solar_Minute`.
- **Irradiance columns:** `solar_GHI`, `solar_DNI`, `solar_DHI` in W/m², from NSRDB GOES aggregated v4 requested at `interval=60`.
- **Coordinates:** city-hall lat/lon in the code's `target_cities.csv`.
- **Rooftop-solar proxy:** `btm_solar_proxy` = GHI × cos(zenith), so it inherits any GHI anomaly.
- **The 22 vs 34 column count:** the DataPort text says 22 columns and the paper says 34; check against the files.
- **Still open, needs `data.zip`:** the actual `solar_Minute` values, which settle the half-hour phase question in [concept-nsrdb.md](concept-nsrdb.md).

## Related

- [source-paper-hedw-us.md](source-paper-hedw-us.md)
- [source-nasa-power.md](source-nasa-power.md): reference for the solar coherence check
- [concept-ghi.md](concept-ghi.md)
