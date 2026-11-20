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

- **Status:** not used.
  - The documented API (`et.water.ca.gov/api/...`) returns 404 without a key and needs a registered app key.
  - The website is now a JavaScript app. Calling its internal `ApiWeb` endpoints, found in the app's bundle, was **refused by the permission system**: they are not a documented public interface.
- **To use CIMIS:** the user registers for a CIMIS app key and stores it outside the repo. CIMIS has pyranometers across the Inland Empire, the LA basin and the Bay Area, so it would cover the 12 flagged California cities and Oakland.

**Results:** [agent_solar_coherence.md](agent_solar_coherence.md#near-the-flagged-cities-fawn-and-midc-lmu). **Related:** [source-noaa-surfrad-solrad.md](source-noaa-surfrad-solrad.md), [concept-solar-coherence.md](concept-solar-coherence.md)
