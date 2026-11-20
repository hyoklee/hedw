#!/bin/bash
# Detector strong scaling on the current host: run agent/run_local.sh with
# P = 1, 2, 4, 8, 16, 32, 64 processes and collect detect/aggregate seconds.
# Usage: bench/local_scaling.sh [P list]   -> bench/results/local_scaling_<host>_<stamp>.csv
set -eu
H=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$H/bench/results"
OUT=$H/bench/results/local_scaling_$(hostname -s)_$(date -u +%Y%m%dT%H%M%SZ).csv
echo "host,P,detect_s,aggregate_s,cities_ok,run_dir" > "$OUT"
for P in ${@:-1 2 4 8 16 32 64}; do
  RUN=$("$H/agent/run_local.sh" "$P" | tail -1)
  read -r D A < <(sed -E 's/timing detect_s=([0-9.]+) aggregate_s=([0-9.]+)/\1 \2/' "$RUN/timing.txt")
  N=$(python3 -c "import json;print(json.load(open('$RUN/summary.json'))['cities_analysed'])")
  echo "$(hostname -s),$P,$D,$A,$N,$(basename "$RUN")" | tee -a "$OUT"
  [ "$P" != "${KEEP_P:-16}" ] && rm -rf "$RUN"
done
echo "$OUT"
