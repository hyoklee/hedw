# Overview

**HEDW-US** is an analysis-ready hourly dataset for 141 U.S. metro areas covering 2019–2023. Each city file joins three streams: county electricity demand (NREL/OEDI), station weather (NOAA ISD) and satellite solar irradiance (NSRDB). It adds physics-informed features and separates the cities into 101 pristine and 40 quarantined *(per descriptor)*. See [source-ieee-dataport-fpqq-nr70.md](source-ieee-dataport-fpqq-nr70.md) and [source-paper-hedw-us.md](source-paper-hedw-us.md).

## Goals of this wiki

1. **Document the dataset:** structure, provenance, units, time base and quality issues.
2. **Solar coherence:** check every city's NSRDB irradiance against NASA POWER for the full 2019–2023 period, and flag cities and years where they disagree ([concept-solar-coherence.md](concept-solar-coherence.md), [source-nasa-power.md](source-nasa-power.md)). This matters downstream: the rooftop-solar proxy, solar volatility and the GHI forecasting benchmark all inherit any irradiance error.
3. **Selective ingest with CAE:** ingest only the columns an analysis needs (for example timestamp and GHI) through OMNI files. CAE reads `hdf5` and `binary`, so the CSVs are first converted to one HDF5 dataset per column (`../cae/`).
4. **CLIO agent:** an anomaly agent built with clio-agent (tools and plugin) and clio-coder (code and interpretation), on the pattern proven in [hyoklee/poro](https://github.com/hyoklee/poro).
5. **Aurora workflow:** find the layout of nodes, ranks, queue and LLM calls that gives the most CLIO-agent work per node-hour of the `IOWarp` allocation.

## Status (2026-11-20)

- Done:
  - paper and dataset metadata ingested;
  - NASA POWER hourly API verified from Aurora;
  - coherence method drafted.
- Paper ingested ([source-paper-hedw-us.md](source-paper-hedw-us.md)); authors' code inspected ([source-upstream-code.md](source-upstream-code.md)).
- Blocked: `data.zip` needs a DataPort login; the NLR API key needs a browser signup (reCAPTCHA). See [concept-data-access.md](concept-data-access.md).
