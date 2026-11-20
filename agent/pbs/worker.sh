#!/bin/bash
# One rank of the coherence job: rank r of N takes city lines r, r+N, ...
# of the manifest and appends one JSON line per city to its own shard.
set -u
MANIFEST=$1; OUTDIR=$2
RANK=${PALS_RANKID:-${PMI_RANK:-0}}
SIZE=${PALS_SIZE:-${PMI_SIZE:-1}}
[ "$SIZE" = 1 ] && [ -n "${NRANKS:-}" ] && SIZE=$NRANKS
AGENT_DIR=$(cd "$(dirname "$0")/.." && pwd)
PY=${CLIO_AGENT_PY:-$HOME/.local/share/clio/clio-agent-097/.venv/bin/python}
mkdir -p "$OUTDIR"
mapfile -t C < <(awk -v r="$RANK" -v s="$SIZE" 'NF && (NR-1)%s==r' "$MANIFEST")
[ ${#C[@]} -gt 0 ] && OMP_NUM_THREADS=1 "$PY" -I "$AGENT_DIR/coherence.py" "${C[@]}" \
  --out "$OUTDIR/rank$(printf %04d "$RANK").jsonl"
echo "rank $RANK/$SIZE on $(hostname): ${#C[@]} cities"
