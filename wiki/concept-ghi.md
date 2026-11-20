# Concept: Global Horizontal Irradiance (GHI)

**Definition.** GHI is the total shortwave solar irradiance received on a horizontal surface: GHI = DNI · cos(θz) + DHI, where θz is the solar zenith angle, DNI the direct normal irradiance and DHI the diffuse horizontal irradiance. Units are W/m² instantaneous, or Wh/m² accumulated over an interval.

**Where it appears**
- **HEDW-US:** NSRDB-derived irradiance columns; the solar-GHI LSTM benchmark reports MAE 46.56 W/m² *(per descriptor)*; [source-ieee-dataport-fpqq-nr70.md](source-ieee-dataport-fpqq-nr70.md).
- **NASA POWER:** `ALLSKY_SFC_SW_DWN` (all-sky), with `CLRSKY_SFC_SW_DWN` as the clear-sky reference; [source-nasa-power.md](source-nasa-power.md).

**Physical consistency checks**
- GHI ≥ 0, and GHI = 0 when the sun is below the horizon (allowing for twilight and hour-averaging at sunrise and sunset).
- GHI ≤ roughly 1.1 × clear-sky GHI. Brief cloud-enhancement events can exceed clear-sky values; sustained exceedance is an error.
- Closure: GHI ≈ DNI · cos θz + DHI, when all three components are present.

**Related:** [concept-nsrdb.md](concept-nsrdb.md), [concept-solar-coherence.md](concept-solar-coherence.md)
