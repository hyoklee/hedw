#!/bin/bash
# Run the detector on the current host (login node) with P parallel processes.
# Usage: agent/run_local.sh [P]
set -eu
P=${1:-16}
AGENT_DIR=$(cd "$(dirname "$0")" && pwd)
PY=${CLIO_AGENT_PY:-$HOME/.local/share/clio/clio-agent-097/.venv/bin/python}
RUN_DIR=$AGENT_DIR/results/run_$(date -u +%Y%m%dT%H%M%SZ)_local_p$P
mkdir -p "$RUN_DIR/shards"
tail -n +2 "$AGENT_DIR/../raw/upstream/hedw-code/target_cities.csv" | cut -d, -f1 > "$RUN_DIR/manifest.txt"
T0=$(date +%s.%N)
seq 0 $((P-1)) | xargs -P "$P" -I{} env PALS_RANKID={} PALS_SIZE="$P" \
  "$AGENT_DIR/pbs/worker.sh" "$RUN_DIR/manifest.txt" "$RUN_DIR/shards" > "$RUN_DIR/workers.log"
T1=$(date +%s.%N)
OMP_NUM_THREADS=1 "$PY" -I "$AGENT_DIR/aggregate.py" "$RUN_DIR"
T2=$(date +%s.%N)
python3 -c "print('timing detect_s=%.2f aggregate_s=%.2f' % ($T1-$T0, $T2-$T1))" | tee "$RUN_DIR/timing.txt"
echo "$RUN_DIR"
