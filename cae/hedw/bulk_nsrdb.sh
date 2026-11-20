#!/bin/bash
# Bulk selective ingest of every NSRDB point-year in raw/nsrdb/ through the CAE
# csv:: assimilator: one OMNI with one transfer per file, keeping only the time
# fields, GHI/DNI/DHI and solar zenith (9 of 16 columns).
# Headers are stripped beforehand (names with spaces are sanitised), so the
# OMNI needs no run: steps.
# Usage: bulk_nsrdb.sh [max_files]     Env: CLIO_BIN, OUT (as run_hedw.sh)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
RAW=$(cd "$HERE/../../raw/nsrdb" && pwd)
BIN=${CLIO_BIN:-$HOME/clio-core.csv/build/bin}
OUT=${OUT:-${TMPDIR:-/tmp}/hedw_cae_bulk_$USER}
MAX=${1:-100000}
rm -rf "$OUT"; mkdir -p "$OUT/tables"
export LD_LIBRARY_PATH=$BIN:$HOME/miniconda3/envs/iowarp/lib:${LD_LIBRARY_PATH:-}
export CLIO_SERVER_CONF=$HERE/clio_hedw_config.yaml CLIO_BIND_ADDR=127.0.0.1 CLIO_PORT=10700
OMNI=$OUT/nsrdb_bulk_omni.yaml
echo "transfers:" > "$OMNI"
n=0; bytes=0
T0=$(date +%s%N)
for f in "$RAW"/*_20[12][0-9].csv; do
  [ $n -ge "$MAX" ] && break
  b=$(basename "$f" .csv); b=${b// /}
  tail -n +3 "$f" > "$OUT/tables/$b.csv"
  bytes=$((bytes + $(stat -c %s "$OUT/tables/$b.csv")))
  cat >> "$OMNI" <<EOT
  - name: "$b"
    src: csv::$OUT/tables/$b.csv
    dst: iowarp::hedw/nsrdb/$b
    format: csv
    dataset_filter:
      include_patterns: ["/Year", "/Month", "/Day", "/Hour", "/Minute", "/GHI", "/DNI", "/DHI", "/Solar Zenith Angle"]
EOT
  n=$((n+1))
done
T1=$(date +%s%N)
echo "prepared $n files, $bytes bytes in $(( (T1-T0)/1000000 )) ms"
"$BIN/clio_run" stop --force >/dev/null 2>&1
nohup "$BIN/clio_run" start > "$OUT/runtime.out" 2>&1 &
RPID=$!
for i in $(seq 1 60); do
  sleep 1
  "$BIN/clio_run" status >/dev/null 2>&1 && { echo "runtime up after ${i}s"; break; }
  kill -0 $RPID 2>/dev/null || { echo "runtime died"; tail -30 "$OUT/runtime.out"; exit 1; }
done
T0=$(date +%s%N)
"$BIN/clio_cae" "$OMNI" > "$OUT/clio_cae.out" 2>&1
RC=$?
T1=$(date +%s%N)
MS=$(( (T1-T0)/1000000 ))
OK=$(sed 's/\x1b\[[0-9;]*m//g' "$OUT/runtime.out" | grep -c "CsvFileAssimilator: .*9 selected")
FAIL=$(sed 's/\x1b\[[0-9;]*m//g' "$OUT/runtime.out" "$OUT/clio_cae.out" | grep -ci "Assimilator failed\|error")
echo "clio_cae exit=$RC elapsed=$MS ms files=$n selected_ok=$OK error_lines=$FAIL"
sed 's/\x1b\[[0-9;]*m//g' "$OUT/runtime.out" | grep -o "ParseOmni: Successfully.*" | sort -u
python3 -c "print('throughput: %.1f files/s, %.1f MB/s of CSV' % ($n/($MS/1e3), $bytes/1e6/($MS/1e3)))"
"$BIN/clio_run" stop >/dev/null 2>&1
wait $RPID 2>/dev/null
echo "RUN_DONE cae=$RC"
