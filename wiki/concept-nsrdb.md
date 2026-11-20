# Concept: National Solar Radiation Database (NSRDB)

**Definition.** The NSRDB is a satellite-derived solar-radiation dataset (GHI, DNI, DHI plus meteorology) from NREL, now the **National Laboratory of the Rockies (NLR)**. It is on a grid of about 4 km and comes from GOES-16/17 imagery. The native time step is 30 min. HEDW-US used the **GOES aggregated v4.0.0** product, requested at 60 min with UTC timestamps.

**Where it appears**
- HEDW-US `solar_*` columns: [source-paper-hedw-us.md](source-paper-hedw-us.md), [source-upstream-code.md](source-upstream-code.md).
- The series checked against NASA POWER (CERES SYN1deg, 1°): [source-nasa-power.md](source-nasa-power.md).

**API**
- **Endpoint:**
  - was `https://developer.nrel.gov/api/nsrdb/v2/solar/nsrdb-GOES-aggregated-v4-0-0-download.csv`;
  - now on `developer.nlr.gov`, because the `nrel.gov` hosts no longer resolve (2026-11-20).
- **Each request needs:**
  - an API key from api.data.gov (signup behind reCAPTCHA);
  - `email`, `full_name`, `affiliation` and `reason`.
- **One request covers one point-year** (`names=<year>`). 141 cities × 5 years is 705 requests.

**Timing pitfall (to verify).** Hourly NSRDB records carry a `Minute` field, which is often 30: the value represents the hour centred on HH:30. HEDW-US aligned them to an HH:00 index with `method='nearest', tolerance=40min`. HH:00 is equidistant (30 min) from HH−1:30 and HH:30, and pandas breaks the tie toward the later timestamp. If the minute is 30, HEDW-US row HH therefore holds the NSRDB value for HH:30, which is irradiance averaged over roughly HH:00–HH+1:00.

POWER's own hour-labelling convention (hour-starting or hour-ending) is not yet confirmed, so whether the two line up has to be **checked empirically** using:
- the `solar_Minute` column in the HEDW CSVs;
- the lag that maximises the cross-correlation with POWER;
- the sunrise and sunset edges of `solar_GHI` against `solar_Solar Zenith Angle`.

**Related:** [concept-ghi.md](concept-ghi.md), [concept-solar-coherence.md](concept-solar-coherence.md), [concept-data-access.md](concept-data-access.md)
