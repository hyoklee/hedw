#!/bin/bash
# Write the city manifest and submit hedw_coherence to Aurora's debug queue.
# Usage: agent/pbs/submit.sh [nodes] [ppn]
set -eu
NODES=${1:-1}; PPN=${2:-50}
AGENT_DIR=$(cd "$(dirname "$0")/.." && pwd)
RUN_DIR=$AGENT_DIR/results/run_$(date -u +%Y%m%dT%H%M%SZ)_n${NODES}p${PPN}
mkdir -p "$RUN_DIR/shards"
tail -n +2 "$AGENT_DIR/../raw/upstream/hedw-code/target_cities.csv" | cut -d, -f1 > "$RUN_DIR/manifest.txt"
V="AGENT_DIR=$AGENT_DIR,RUN_DIR=$RUN_DIR,MANIFEST=$RUN_DIR/manifest.txt,PPN=$PPN"
J=$(qsub -l select="$NODES" -v "$V" -o "$RUN_DIR/job.log" "$AGENT_DIR/pbs/coherence.pbs")
echo "$J $(date -u +%FT%TZ) submitted" | tee "$RUN_DIR/jobs.txt"
echo "run dir: $RUN_DIR"
