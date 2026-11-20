# Overview

**HEDW-US** is an analysis-ready hourly dataset for 141 U.S. metro areas covering 2019–2023. Each city file joins three streams: county electricity demand (NREL/OEDI), station weather (NOAA ISD) and satellite solar irradiance (NSRDB). It adds physics-informed features and separates the cities into 101 pristine and 40 quarantined *(per descriptor)*. See [source-ieee-dataport-fpqq-nr70.md](source-ieee-dataport-fpqq-nr70.md) and [source-paper-hedw-us.md](source-paper-hedw-us.md).

## Goals of this wiki

1. **Document the dataset:** structure, provenance, units, time base and quality issues.
2. **Solar coherence:** check every city's NSRDB irradiance against NASA POWER for the full 2019–2023 period, and flag cities and years where they disagree ([concept-solar-coherence.md](concept-solar-coherence.md), [source-nasa-power.md](source-nasa-power.md)). This matters downstream: the rooftop-solar proxy, solar volatility and the GHI forecasting benchmark all inherit any irradiance error.
3. **Selective ingest with CAE:** ingest only the columns an analysis needs (for example timestamp and GHI) through OMNI files. CAE now reads CSV column by column through a new `csv::` assimilator ([cae_csv_assimilator.md](cae_csv_assimilator.md)).
4. **CLIO agent:** an anomaly agent built with clio-agent (tools and plugin) and clio-coder (code and interpretation), on the pattern proven in [hyoklee/poro](https://github.com/hyoklee/poro).
5. **Aurora workflow:** find the layout of nodes, ranks, queue and LLM calls that gives the most CLIO-agent work per node-hour of the `IOWarp` allocation.

## Status (2026-11-20)

- **Done:**
  - Paper, metadata and the authors' code ingested ([source-paper-hedw-us.md](source-paper-hedw-us.md), [source-upstream-code.md](source-upstream-code.md)).
  - NSRDB (745 city-years) and NASA POWER (150 cities) downloaded.
  - CAE `csv::` assimilator built ([cae_csv_assimilator.md](cae_csv_assimilator.md), PR iowarp/clio-core#1393).
  - Solar-coherence agent run on 149 cities ([agent_solar_coherence.md](agent_solar_coherence.md)).
  - Aurora workflow measured ([workflow_aurora_clio.md](workflow_aurora_clio.md)).
- **Headline:**
  - HEDW-US's solar stream is coherent with POWER: lag 0 h everywhere, median daily r 0.977, median bias +1.1 %.
  - Disagreement concentrates where POWER's 1° cells mix ocean, mountains and land (17 cities).
    - **South Florida:** FAWN ground data blames POWER for the low correlation.
    - **Coastal Los Angeles:** MIDC LMU (2011–2014) and CIMIS (2019–2023) both show NSRDB/HEDW-US about 5–15 % too high in summer.
    - **Inland Empire, Oakland, San Diego:** CIMIS ground data puts the error on POWER.
  - NSRDB gap-filled every city east of about −113° (109 cities) on 6 days (2019-11-17 to 20, 2020-02-13 to 14), plus a median of 1.3 % of daylight hours elsewhere. HEDW-US carries these values without a flag.
- **Open:**
  - `data.zip` needs a DataPort login, to check the released files and the quarantined cities ([concept-data-access.md](concept-data-access.md)).
  - Ground truth for Honolulu: no public Oahu series. Every other flagged city now has a ground check (FAWN, CIMIS, MIDC LMU). At all 14 SURFRAD and SOLRAD sites NSRDB beats POWER, and the filled days are confirmed wrong ([source-noaa-surfrad-solrad.md](source-noaa-surfrad-solrad.md)).
