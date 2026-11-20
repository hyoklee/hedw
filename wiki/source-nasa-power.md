# Source: NASA POWER (ASDC) hourly API

- **Service:** NASA Prediction Of Worldwide Energy Resources (POWER), NASA Langley Atmospheric Science Data Center. https://power.larc.nasa.gov/
- **Endpoint used:** `https://power.larc.nasa.gov/api/temporal/hourly/point`
  - Parameters: `parameters`, `community=RE`, `longitude`, `latitude`, `start`, `end` (YYYYMMDD), `format=JSON`, `time-standard=UTC`
- **Access:** open, with no key. Reachable directly from Aurora login nodes (tested 2026-11-20). Compute nodes need the ALCF proxy (`http_proxy=http://proxy.alcf.anl.gov:3128`).
- **Sample response:** [`raw/power/sample_hourly_stlouis_20190701.json`](../raw/power/sample_hourly_stlouis_20190701.json) (St. Louis, 38.63 N, −90.20 E, 2019-07-01)

## What the sample response shows

| Field | Value |
|---|---|
| API | POWER Hourly API v2.10.5 |
| Title | "NASA/POWER Source Native Resolution Hourly Data" |
| Sources | `SYN1DEG`, `POWER` (the irradiance comes from CERES SYN1deg, 1° grid) |
| Fill value | −999.0 |
| Time standard | UTC, keys `YYYYMMDDHH` |

| Parameter | Long name | Units |
|---|---|---|
| `ALLSKY_SFC_SW_DWN` | All Sky Surface Shortwave Downward Irradiance (GHI) | Wh/m² |
| `CLRSKY_SFC_SW_DWN` | Clear Sky Surface Shortwave Downward Irradiance | Wh/m² |
| `ALLSKY_SFC_SW_DNI` | All Sky Surface Shortwave Downward Direct Normal Irradiance | Wh/m² |
| `ALLSKY_SFC_SW_DIFF` | All Sky Surface Shortwave Diffuse Irradiance | Wh/m² |

In the sample, St. Louis on 2019-07-01 has GHI = 0 from 02 to 10 UTC and a peak of 792.0 Wh/m² at 17 UTC (local solar noon is about 18 UTC).

## Caveats for the comparison with HEDW-US

- **Resolution:** POWER irradiance is on a 1° CERES grid; NSRDB is about 4 km. Cloud-scale differences show up as hourly scatter even when both are correct, so coherence should be judged at the daily level as well as the hourly level.
- **Units:** an hourly Wh/m² total equals the mean W/m² over that hour, so the values compare directly. The hour labelling, however (the hour starting at HH or ending at HH), has to be checked against the HEDW-US timestamp convention.
- **Clear-sky reference:** `CLRSKY_SFC_SW_DWN` gives a physical ceiling for flagging impossible GHI values, such as all-sky above clear-sky or night-time irradiance.

## Related

- [concept-ghi.md](concept-ghi.md), [concept-nsrdb.md](concept-nsrdb.md), [concept-solar-coherence.md](concept-solar-coherence.md)
