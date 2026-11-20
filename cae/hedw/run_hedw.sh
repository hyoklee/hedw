#!/bin/bash
# Ingest a CSV through the CAE csv:: assimilator on a fresh single-node runtime.
#
# Usage: run_hedw.sh [nsrdb.csv]
# Env:   CLIO_BIN  clio-core build bin dir with CSV support
#                  (default ~/clio-core.csv/build/bin, branch feat/cae-csv-assimilator)
#        OUT       scratch dir for the rendered OMNI, run_out files, logs
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
CSV=$(realpath "${1:-$HERE/../../raw/nsrdb/test_NewYork_2019.csv}")
BIN=${CLIO_BIN:-$HOME/clio-core.csv/build/bin}
OUT=${OUT:-${TMPDIR:-/tmp}/hedw_cae_$USER}
mkdir -p "$OUT"
export LD_LIBRARY_PATH=$BIN:$HOME/miniconda3/envs/iowarp/lib:${LD_LIBRARY_PATH:-}
export CLIO_SERVER_CONF=$HERE/clio_hedw_config.yaml
export CLIO_BIND_ADDR=127.0.0.1
export CLIO_PORT=10700
OMNI=$OUT/nsrdb_solar_omni.yaml
sed -e "s|@NSRDB_CSV@|$CSV|g" -e "s|@OUT@|$OUT|g" "$HERE/nsrdb_solar_omni.yaml.in" > "$OMNI"
cp "$HERE/strip_nsrdb_header.sh" "$OUT/"   # run: paths resolve against the OMNI dir
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
echo "clio_cae exit=$RC elapsed=$(( (T1-T0)/1000000 )) ms"
grep -h 'CsvFileAssimilator\|ParseOmni: Successfully\|Assimilator failed' "$OUT/runtime.out" /tmp/clio_hedw.log 2>/dev/null \
  | sed 's/\x1b\[[0-9;]*m//g; s|^.*CsvFileAssimilator|CsvFileAssimilator|; s|^.*ParseOmni|ParseOmni|' | sort -u
"$BIN/clio_run" stop >/dev/null 2>&1
wait $RPID 2>/dev/null
echo "RUN_DONE cae=$RC"
exit $RC
