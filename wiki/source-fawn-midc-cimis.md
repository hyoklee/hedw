# Source: ground pyranometers near the flagged cities (FAWN, MIDC, CIMIS)

SURFRAD and SOLRAD have no station within 238 km of any flagged city ([source-noaa-surfrad-solrad.md](source-noaa-surfrad-solrad.md)). This page records the regional networks that were checked on 2026-11-20.

## FAWN: Florida Automated Weather Network (UF/IFAS)

- **Access:** open, no key.
  - Hourly data: `https://fawn.ifas.ufl.edu/data/fawnpub/hourly_summaries/BY_STATION/<Name>_<id>/<year>.csv`, one file per station-year.
  - Station coordinates: the first data row of `.../data/fawnpub/DSSAT/<Name>.csv` (Latitude, Longitude, Elevation). `/station/` returns 403.
- **Stations:** 56 in the directory. 53 have coordinates in the DSSAT files (list in `../agent/ground/fawn_stations.csv`). Brooksville, Frostproof and Indian River have no DSSAT file, so no coordinates.
- **Distances to the flagged cities** (`../agent/ground/flagged_city_distances_fawn.txt`):

  | Flagged city | FAWN Fort Lauderdale | Next station |
  |---|---|---|
  | Pembroke Pines | 10 km | Homestead 59 km |
  | Fort Lauderdale | 11 km | Wellington 64 km |
  | Hialeah | 26 km | Homestead 44 km |
  | Miami | 36 km | Homestead 42 km |

  FAWN Fort Lauderdale is at the UF research centre in Davie (26.0853, −80.2405).
- **Format change in 2021:**

  | Years | Columns |
  |---|---|
  | 2019–2020 | `Date`, `Time`, `Solar Radiation (w/m2)` |
  | 2021 onward | `Date Time`, `Solar Radiation (w/m2) Avg` (with min, max and MJ sums) |

  Neither format states a time zone.
- **Time convention, measured:** a lag scan against POWER UTC hours, winter and summer separately. The label is local clock time (America/New_York, with DST) marking the **start** of the averaged hour, in both eras:
  - pre-2021 files: 7 of 9 stations;
  - 2021-onward files: 8 of 9 stations.
- **Jupiter (415):** its files begin 2023-12-19, and the 2023 file has no header row, so it is not used.
- **Quality caveat:**
  - Both NSRDB and POWER read **8–25 % above FAWN** at 9 stations. Against SURFRAD and SOLRAD they read only ~1–2 % above.
  - The offset differs by station (Fort Lauderdale +8.9 %, Citra +21.7 % for NSRDB) and jumps between years (Okeechobee NSRDB +17.2 % in 2022, −4.8 % in 2023).
  - So FAWN's absolute level is not usable as truth: the pyranometers likely read low through calibration, soiling or sensor swaps. FAWN is an agricultural network, not a BSRN-grade one.
  - Day-to-day agreement (daily r) and relative differences between the products are still informative (`../agent/results/ground_local_20261120/fawn_quality.txt`).

## MIDC: NLR Measurement and Instrumentation Data Center

- **Access:** documented public API, `https://midcdmz.nlr.gov/apps/data_api.pl?site=<ID>&begin=YYYYMMDD&end=YYYYMMDD`.
  - Follow redirects (`curl -L`): the archived LMU site is served through `plot.pl`.
  - The old `midcdmz.nrel.gov` host no longer resolves.
- **LMU (Loyola Marymount University, Los Angeles):**
  - Location: 33.966674, −118.4226, about 19 km from LA city hall and about 5 km from the ocean. Instrument: an RSR (rotating shadowband radiometer, roughly ±5 % uncertainty).
  - Data: 1-min, PST (UTC−8, field `PST` = HHMM), from 2010-04-06 to 2016-05-05. **It ended before the HEDW-US period.**
  - The battery was faulty from December 2014 to July 2015, so 2011–2014 was used. The lag scan against POWER gives the best lag at 0 h (r 0.98).
- **NELHA** (Hawaii) is on the Big Island, not Oahu, so it does not cover Honolulu. It was not used.

## CIMIS: California Irrigation Management Information System (DWR)

- **Access (2026-11-20):** API key registered by the user, stored in `~/.config/hedw/cimis.env` (mode 600, outside the repo). The user approved this access.
  - The old API (`et.water.ca.gov/api/...?appKey=`) is gone. Without a key it returns 404; with a key, the firewall answers "Request Rejected".
  - The current API is documented at `cimis.water.ca.gov/web-api/rest-api/latest`:
    - base `https://et.water.ca.gov`;
    - the key goes in header `Ocp-Apim-Subscription-Key`;
    - `GET /StationWeb/GetAllStations` lists stations;
    - `GET /StationWeb/GetDataByStationNumber?stationNbrs=N&startDate&endDate&isHourly=true&unitOfMeasure=M&dataItems=hly-sol-rad` returns hourly data;
    - each request may return at most 1,750 records.
  - The site's JavaScript embeds its own subscription key. **It was not used.**
- **Stations:** 276 in total, 136 active over all of 2019–2023. Every flagged California city has one within 3–21 km (`../agent/ground/flagged_city_distances_cimis.txt`):

  | Flagged city | Station | Distance |
  |---|---|---|
  | San Diego | #184 San Diego II | 3 km |
  | Chula Vista | #184 San Diego II | 11 km |
  | Long Beach | #174 Long Beach | 10 km |
  | Glendale | #223 North Hollywood | 10 km |
  | Los Angeles | #223 North Hollywood | 15 km |
  | Moreno Valley | #44 UC Riverside | 10 km |
  | Fontana | #44 UC Riverside | 17 km |
  | San Bernardino | #251 Highland | 10 km |
  | Ontario | #78 Pomona | 15 km |
  | Rancho Cucamonga | #78 Pomona | 21 km |
  | Oxnard | #152 Camarillo | 17 km |
  | Oakland | #254 Oakland Metro | 12 km |

  #99 Santa Monica was added as a coastal LA reference.
- **Download:** `../agent/ground/fetch_cimis.py` makes 70-day requests 1 s apart. All 9 stations returned 43,824 hourly records with no failed chunk, in 49–76 s per station. Stored in `../raw/ground/cimis/` (git-ignored).
- **Data:**
  - `HlySolRad` in W/m², with a QC code. Records with a blank code (passed) or `Y` (moderate outlier) are kept.
  - Hour labels run 0100–2400. A lag scan against POWER confirms **PST (no DST), with the label marking the end of the hour**, at 9 of 9 stations.
- **Quality caveat:** CIMIS uses agricultural-grade pyranometers. Some stations show a flat offset against both products all year (Highland about +10 % for NSRDB), which looks like the station's own calibration. Monthly *shapes*, and the summer-minus-winter bias, are more robust than absolute levels.

**Results:** [agent_solar_coherence.md](agent_solar_coherence.md#near-the-flagged-cities-fawn-and-midc-lmu) and [the CIMIS section](agent_solar_coherence.md#california-cimis-2019-2023). **Related:** [source-noaa-surfrad-solrad.md](source-noaa-surfrad-solrad.md), [concept-solar-coherence.md](concept-solar-coherence.md)
