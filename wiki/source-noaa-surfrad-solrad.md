# Source: NOAA GML SURFRAD and SOLRAD ground radiation networks

- **Provider:** NOAA Global Monitoring Laboratory (GML), Boulder.
  - Data: `https://gml.noaa.gov/aftp/data/radiation/surfrad/<Station_Dir>/<year>/<code><yy><jjj>.dat` and `.../solrad/<code>/<year>/<code><yy><jjj>.dat`, one file per station-day.
  - Format: `README_SURFRAD` and `README_SOLRAD.txt` in the same tree.
- **Access:** open, no key.
  - About 0.35 MB per daily file of 1-minute data, about 0.2 s per file from the Aurora login node.
  - **Throttling:** after about 12,000 files in about 13 minutes at 8 parallel connections (2026-11-20 15:17–15:30), `gml.noaa.gov` started refusing TLS connections from this node (curl exit 35, HTTP 000) while `www.noaa.gov` still answered. The fetcher now uses 3 workers and resumes by filling only missing days.
- **Measurements:** 1-min UTC. Each value is followed by a QC flag (0 = good, BSRN philosophy); −9999.9 means missing.
  - SURFRAD columns: global, upwelling, direct-normal, diffuse, ...
  - SOLRAD columns: global, direct-normal, diffuse, ...
  - The READMEs recommend the component sum (direct·cos z + diffuse) over the global pyranometer when both components are good. `fetch_ground.py` follows this.

## Stations with 2019–2023 data

Coordinates are read from the file headers (`../agent/ground/stations.csv`).

| Network | Code | Station | Lat | Lon | Elev (m) |
|---|---|---|---|---|---|
| SURFRAD | bon | Bondville IL | 40.05 | −88.37 | 213 |
| SURFRAD | tbl | Table Mountain (Boulder) CO | 40.125 | −105.237 | 1689 |
| SURFRAD | dra | Desert Rock NV | 36.624 | −116.019 | 1007 |
| SURFRAD | fpk | Fort Peck MT | 48.31 | −105.10 | 634 |
| SURFRAD | gwn | Goodwin Creek MS | 34.25 | −89.87 | 98 |
| SURFRAD | psu | Penn State PA | 40.72 | −77.93 | 376 |
| SURFRAD | sxf | Sioux Falls SD | 43.73 | −96.62 | 473 |
| SOLRAD | abq | Albuquerque NM | 35.038 | −106.622 | 1617 |
| SOLRAD | bis | Bismarck ND | 46.772 | −100.760 | 503 |
| SOLRAD | hnx | Hanford CA | 36.31 | −119.63 | 73 |
| SOLRAD | msn | Madison WI | 43.073 | −89.411 | 271 |
| SOLRAD | sea | Seattle WA | 47.687 | −122.257 | 20 |
| SOLRAD | slc | Salt Lake City UT | 40.772 | −111.955 | 1288 |
| SOLRAD | ste | Sterling VA | 38.972 | −77.487 | 85 |

Not usable for 2019–2023:
- SURFRAD Alamosa CO (2014–16), Red Lake AZ (2017), Rutland VT (2014–15) and Wasco OR (2016–17) are short campaigns.
- SOLRAD Oak Ridge (`ort`) and Tallahassee (`tlh`) have no yearly directories.

## Coverage of the HEDW-US flagged cities

`../agent/ground/flagged_city_distances.txt` lists the distance from each flagged city to its nearest station:

| Flagged group | Nearest station | Distance |
|---|---|---|
| Coastal Southern California, Inland Empire, Oakland | Hanford CA (Central Valley) or Desert Rock NV (Mojave) | 238–454 km |
| South Florida | Goodwin Creek MS | ~1,300 km |
| Honolulu | Hanford CA | 4,047 km |

**No station can verify any flagged city directly,** and none sits in a coastal marine-layer or South Florida climate. Other networks that do have pyranometers there are recorded as options, not yet used:
- CIMIS (California irrigation network; free API key);
- FAWN (Florida Automated Weather Network);
- University of Hawaii / HNEI sites.

## Processing

- **`../agent/ground/fetch_ground.py`:** streams the daily files and keeps only hourly means over [H:00, H+1:00) UTC, with at least 45 valid minutes per hour, in `../raw/ground/<station>_hourly.csv` (git-ignored). The 1-min files are not stored.
- **`../agent/ground/validate.py`:** compares the ground data with NSRDB and POWER, fetched for the station coordinates by `fetch_all.py --cities agent/ground/stations.csv`. Results are in [agent_solar_coherence.md](agent_solar_coherence.md#ground-truth-surfrad-and-solrad).

**Related:** [source-nasa-power.md](source-nasa-power.md), [concept-nsrdb.md](concept-nsrdb.md), [concept-solar-coherence.md](concept-solar-coherence.md)
