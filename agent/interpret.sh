#!/bin/bash
# LLM interpretation of one solar-coherence run with clio-coder (headless).
# Writes <run>/interpretation.md, then checks every number in it against the
# run's files (agent/check_numbers.py -> <run>/interpretation_check.json).
# Usage: agent/interpret.sh <run_dir>
set -eu
RUN=$(cd "$1" && pwd)
cd "$(dirname "$0")/.."
clio-coder run --turn-mode answer --no-delegate --allow-tools read,ls,grep,find \
"Read $RUN/summary.json, the first 40 lines of $RUN/cities.csv sorted as given, and the first 40 lines of \
$RUN/anomalous_days.csv. Do not modify any files. Write a markdown report for a solar-resource analyst with sections: \
(1) What was compared: NSRDB GHI (HEDW-US solar source, value at HH:30 UTC) vs NASA POWER ALLSKY_SFC_SW_DWN (UTC hourly means, 1-degree cells), period and number of cities. \
(2) Timing: the best-lag counts (best_lag_city_years) and what a lag of 0 h means for the HEDW-US time stamps. \
(3) Agreement: r_hourly, r_daily and bias_pct distributions (median, p05, p95, min). \
(4) Anomalies: each anomalous city with its flags, and the pattern they share (geography, coast, terrain, season). Use correlation_bias_vs_lat. \
(5) Notable anomalous days from anomalous_days.csv and plausible physical causes (snow, fog, smoke, cloud edges) - mark causes as hypotheses. \
(6) Limitations. Quote numbers exactly as they appear in the files; never invent numbers." \
  | sed '1{/^clio-coder run: session/d}' > "$RUN/interpretation.md"
echo "wrote $RUN/interpretation.md ($(wc -l < "$RUN/interpretation.md") lines)"
python3 agent/check_numbers.py "$RUN"
