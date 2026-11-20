# Concept: NREL National Solar Radiation Database (NSRDB)

**Definition.** The NSRDB is NREL's satellite-derived solar-radiation dataset for the Americas: GHI, DNI, DHI and meteorological fields on a grid of about 4 km. Its Physical Solar Model takes inputs from GOES imagery. The native time step is 30 min (5 to 15 min in newer releases).

**Where it appears**
- HEDW-US takes its satellite solar irradiance from the NSRDB *(per descriptor)*: [source-ieee-dataport-fpqq-nr70.md](source-ieee-dataport-fpqq-nr70.md).
- It is the dataset being checked against NASA POWER (CERES SYN1deg): [source-nasa-power.md](source-nasa-power.md).

**Points to verify once the data is downloaded**
- Which NSRDB release and spatial resolution HEDW-US used.
- How 30-min values were brought to hourly: by subsampling or by averaging. Subsampling shifts the effective hour by up to 30 min, which would show up against POWER as a diurnal phase offset.
- The time zone. NSRDB downloads can be in UTC or local standard time, and a time-zone or DST mistake would appear as a whole-hour lag.

**Related:** [concept-ghi.md](concept-ghi.md), [concept-solar-coherence.md](concept-solar-coherence.md)
