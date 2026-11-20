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

**Timing: confirmed half-hour offset in HEDW-US alignment (2026-11-20)**

- **NSRDB side, measured:** a test download (New York, 2019, the authors' exact parameters, `raw/nsrdb/test_NewYork_2019.csv`, 8,760 rows) has `Minute = 30` on **every** row. The NSRDB location id is 1243965 at 40.73, −74.02; Time Zone 0, since `utc=true`; version 4.0.0.
- **pandas side, measured:** with pandas 2.3.3, the authors' pinned version, `reindex(method='nearest', tolerance='40min')` resolves the equidistant tie toward the **later** record ([`agent/checks/nearest_tie.py`](../agent/checks/nearest_tie.py)).
- **Consequence:** the HEDW-US row labelled HH:00 UTC holds the NSRDB record stamped **HH:30**. The `solar_Minute` column (30) keeps this visible in the CSVs. Anyone who treats the row's UTC label as the irradiance time is 30 min early. For example, `btm_solar_proxy` pairs GHI with the zenith angle from the same NSRDB row, so it is self-consistent; but joining GHI with `load_mw` at HH:00 mixes times 30 min apart.
- **Still to confirm against data:** whether the released files show this, and how big it looks against NASA POWER. That requires `data.zip` and POWER's hour-labelling convention.

**Related:** [concept-ghi.md](concept-ghi.md), [concept-solar-coherence.md](concept-solar-coherence.md), [concept-data-access.md](concept-data-access.md)


## Gap filling (`fill_flag`), measured 2026-11-20

- **What the flag looks like:**
  - The hourly GOES aggregated v4 product returns `Fill Flag` values from 0 to 100 in steps of about 7. We read it as the percentage of the hour's sub-hourly samples that NSRDB gap-filled; this is an inference.
  - The file header lists the 30-min codes: 1 Missing Image, 2 Low Irradiance, 3 Exceeds Clearsky, 4 Missing Cloud Properties, 5 Rayleigh Violation.
- **Routine filling:** across 149 target cities in 2019–2023, a median of 1.34 % of daylight hours (clear-sky GHI > 200 W/m²) are at least half filled. The highest is North Las Vegas at 8.04 %.
- **Domain-wide fills:** on 2019-11-17 to 20 and 2020-02-13 to 14, every target city east of about −113° (109 cities) is filled for most of the day, and no western city is.
  - On clear days the filled GHI is far too low. Birmingham on 2020-02-14 has a flat 25–51 W/m² against a POWER clear sky of up to 763.
- **Effect on HEDW-US:** HEDW-US does not carry `Fill Flag`, so these values look like observations. Details are in [agent_solar_coherence.md](agent_solar_coherence.md#gap-filling-across-all-cities-fillflagsjson-fill_episodestxt).