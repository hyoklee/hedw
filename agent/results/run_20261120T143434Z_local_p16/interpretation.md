> **Reviewer note (2026-11-20):** raw clio-coder output (alcf-metis, gpt-oss-120b), kept for the record. check_numbers.py: 71/71 numbers supported. Four errors: (1) `correlation_bias_vs_lat` *is* in summary.json (-0.216); (2) the flagged cities are among the most southerly, not "higher latitude"; (3) only the first 10 flagged cities are listed, missing South Florida and Honolulu; (4) physics reversed: snow raises surface/cloud reflection (NSRDB reads high), and positive bias means NSRDB > POWER. See wiki/agent_solar_coherence.md.

**Task Board**

| ID | Action | Note |
|----|--------|------|
| 1 | plan | Declare the report structure and required data extraction steps. |
| 2 | start | Read `summary.json`, `cities.csv`, and `anomalous_days.csv`. |
| 3 | done | Evidence collected from the three files (citations). |
| 4 | start | Summarize comparison details, timing interpretation, agreement statistics, anomalous city flags, and anomalous days with hypotheses. |
| 5 | done | Report written in markdown, quoting exact numbers from the files. |
| 6 | drop | No further actions required. |

**Report for Solar‑Resource Analyst**

---

### 1. What was compared
- **Datasets**:  
  - **NSRDB GHI** – HEDW‑US solar source, hourly values taken at **HH:30 UTC**.  
  - **NASA POWER** – `ALLSKY_SFC_SW_DWN`, hourly means over **HH:00‑HH+1:00 UTC**, 1‑degree cells.  
- **Period**: `2019‑01‑01T00` to `2023‑12‑31T23` (UTC).  
- **Number of cities analysed**: **149** (see `summary.json` line 5).  

### 2. Timing
- **Best‑lag counts**: `best_lag_city_years` shows **745** city‑years with a lag of **0 h** (summary.json line 70‑71).  
- **Interpretation of lag 0 h**: The HEDW‑US timestamps (HH:30) align exactly with the midpoint of the NASA POWER hourly window (HH:00‑HH+1:00), so no temporal offset is applied.

### 3. Agreement (distribution of statistics across all cities)
| Statistic | Median | p05 | p95 | Min |
|-----------|--------|-----|-----|-----|
| **r_hourly** | 0.9785 (summary.json line 36) | 0.967 (line 35) | 0.993 (line 37) | 0.9604 (line 34) |
| **r_daily** | 0.9768 (line 43) | 0.9321 (line 42) | 0.9894 (line 44) | 0.8987 (line 41) |
| **bias_pct** | 1.1083 % (line 50) | –2.0919 % (line 49) | 4.7637 % (line 51) | –4.1699 % (line 48) |

### 4. Anomalous cities
Rows in `cities.csv` where the **anomalous** column equals 1 are flagged as anomalous. Selected examples (first 10 shown):

| City | Flags (from `cities.csv`) |
|------|---------------------------|
| California_ChulaVista | `z(r_daily)=-7.2; z(bias_pct)=+5.1; z(anomalous_days)=+5.1` |
| California_Fontana | `z(r_daily)=-4.2; z(anomalous_days)=+9.0` |
| California_LongBeach | `z(r_daily)=-5.8; z(anomalous_days)=+5.9` |
| California_LosAngeles | `z(r_daily)=-3.3; z(anomalous_days)=+6.5` |
| California_MorenoValley | `z(anomalous_days)=+4.7` |
| California_Oakland | `z(bias_pct)=+3.3` |
| California_Ontario | `z(r_daily)=-5.3; z(anomalous_days)=+9.1` |
| California_Oxnard | `z(r_daily)=-4.3; z(anomalous_days)=+3.4` |
| California_RanchoCucamonga | `z(r_daily)=-3.9; z(anomalous_days)=+8.0` |
| California_SanDiego | `z(r_daily)=-6.5; z(bias_pct)=+3.9; z(anomalous_days)=+4.0` |

**Shared pattern** (from `correlation_bias_vs_lat` – not present in the provided files, so the pattern cannot be confirmed here). The anomalous cities are predominantly **coastal California locations** with higher latitudes, suggesting systematic biases related to **coastal fog, marine layer, or terrain‑induced cloud edges**.

### 5. Notable anomalous days
From `anomalous_days.csv` (selected extreme‑z rows):

| City | Date | NSRDB Wh m⁻² | POWER Wh m⁻² | Z‑score |
|------|------|--------------|---------------|---------|
| Alabama_Birmingham | 2020‑02‑14 | 390 | 4768 | –35.06 |
| Alabama_Birmingham | 2023‑04‑03 | 4116 | 1493 | +14.28 |
| California_ChulaVista | (not listed, but flagged in `cities.csv`) – likely days with large negative r_daily and positive bias. |
| … (many rows omitted for brevity) |

**Plausible physical causes (hypotheses)**:
- **Snow cover** (high albedo, low GHI) – could explain large negative z‑scores.
- **Fog or low‑level stratus** (coastal California) – reduces GHI while POWER’s clear‑sky model remains high, yielding positive bias.
- **Smoke / aerosol events** – attenuate solar radiation, affecting NSRDB more than the satellite‑derived POWER product.
- **Rapid cloud edge passage** – timing mismatch between the 30‑min NSRDB sample and the hourly POWER mean can produce spikes.

### 6. Limitations
- The **correlation_bias_vs_lat** analysis referenced in the task is not present in the supplied result files; therefore any geographic pattern inference is based solely on the city flags in `cities.csv`.
- The report uses only the first 40 lines of each CSV as requested; additional anomalous cities or days beyond those lines are not considered.
- No external validation (e.g., weather observations) is performed; the physical explanations remain hypotheses.
