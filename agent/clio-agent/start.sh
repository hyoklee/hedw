#!/bin/bash
# Start clio-agent 0.9.7.x with the HEDW-US solar-coherence agent
# (hedw/solar-coherence, plugin marketplace in ./marketplace) on Mistral Large 4
# served by the ALCF inference gateway. Adapted from ~/poro/agent/clio-agent/start-0971.sh:
# same venv, home and port 8100 (starting it stops the poro server), server runs
# from an empty folder (clio-agent #2375), output cap 8192 (#2371).
# One-time login: ~/.local/share/clio/clio-agent-097/.venv/bin/python -m clio_agent.providers.argonne_auth authenticate
# Usage: agent/clio-agent/start.sh [minerva|tara]
set -eu
CLUSTER=${1:-minerva}
HERE=$(cd "$(dirname "$0")" && pwd)
VENV=${CLIO097_VENV:-$HOME/.local/share/clio/clio-agent-097/.venv}/bin
export CLIO_AGENT_HOME=${CLIO097_HOME:-$HOME/.local/share/clio/clio-agent-097/home}
export CLIO_RUNTIME_STATE_DIR=${CLIO097_RUNTIME:-$HOME/.local/share/clio/clio-agent-097/runtime-state}
WORKDIR=${CLIO097_CWD:-$HOME/.local/share/clio/clio-agent-097/cwd}
PORT=${CLIO097_PORT:-8100}
AGENT=hedw/solar-coherence

case "$CLUSTER" in
  minerva) MODEL=mistral-large-4-nvfp4 ;;
  tara)    MODEL=mistral-large-4 ;;
  *) echo "cluster must be minerva or tara"; exit 2 ;;
esac
[ -x "$VENV/clio-agent" ] || { echo "no clio-agent 0.9.7.x in $VENV (see the setup lines in this script)"; exit 1; }
"$VENV/python" -m clio_agent.providers.argonne_auth status >/dev/null 2>&1 || {
  echo "no valid ALCF Globus token; run: $VENV/python -m clio_agent.providers.argonne_auth authenticate"; exit 1; }

mkdir -p "$CLIO_AGENT_HOME" "$CLIO_RUNTIME_STATE_DIR" "$WORKDIR"
[ -e "$WORKDIR/.clio" ] && { echo "$WORKDIR/.clio exists; 0.9.7.1 would adopt it (clio-agent #2375)"; exit 1; }
cd "$WORKDIR"

export CLIO_LM_PROVIDER=argonne_metis
export CLIO_LM_API_BASE=https://inference-api.alcf.anl.gov/resource_server/$CLUSTER/api/v1
export CLIO_LM_MODEL=${CLIO_LM_MODEL:-$MODEL}
# No default output cap upstream (clio-agent #2371). Normal steps use < 2k tokens;
# this bounds a runaway reasoning stream to about 23 s at ~360 tokens/s.
export CLIO_LM_MAX_TOKENS=${CLIO_LM_MAX_TOKENS:-8192}
export CLIO_ALLOWED_ROOTS=${CLIO_ALLOWED_ROOTS:-$HOME/hedw:/tmp}
export HEDW_ROOT=${HEDW_ROOT:-$HOME/hedw}

# Install (first time) or refresh (later) the marketplace, then trust it. An
# update whose Python parts changed (agents/, the porotomo_report tool) is held
# until it is trusted again, so trust after every update: it is this repo's code.
"$VENV/clio-agent" plugin check "$HERE/marketplace" >/dev/null
if "$VENV/clio-agent" plugin list 2>/dev/null | grep -q "^hedw "; then
  "$VENV/clio-agent" plugin update hedw
else
  "$VENV/clio-agent" plugin install "$HERE/marketplace" --name hedw
fi
"$VENV/clio-agent" plugin trust hedw

# Stop any clio-agent server (0.9.4 or 0.9.7) and clio-core runtime left on this port.
pkill -u "$USER" -f "clio-agent(-gact| serve) --host 127.0.0.1 --port $PORT" 2>/dev/null && sleep 3 || true
pkill -u "$USER" -f "iowarp_core/bin/clio_run start" 2>/dev/null || true
# Wait for the old runtime to exit: a new server that attaches while it still
# holds port 9413 fails with clio_core_post_attach_probe_timeout and answers 503.
for _ in $(seq 1 30); do
  pgrep -u "$USER" -f "iowarp_core/bin/clio_run start" >/dev/null || break
  sleep 1
done

"$VENV/clio-agent" serve --host 127.0.0.1 --port "$PORT" &
SERVER=$!
trap 'kill $SERVER 2>/dev/null' INT TERM
# New sessions run the PoroTomo agent unless they name another one. /v1/health
# answers before the task runtime is up, so retry until the server accepts it
# (503 task_runtime_starting until then).
ok=
for _ in $(seq 1 90); do
  if curl -sf -m 5 -X PATCH "http://127.0.0.1:$PORT/v1/session-defaults" \
       -H 'content-type: application/json' -d "{\"agent_ref\": \"$AGENT\"}" >/dev/null; then
    ok=1; break
  fi
  kill -0 $SERVER 2>/dev/null || { echo "server exited"; exit 1; }
  sleep 2
done
[ -n "$ok" ] && echo "clio-agent 0.9.7.x on port $PORT, default agent $AGENT" \
  || echo "warning: could not set the default agent; pass metadata.agent_ref=$AGENT per session"
wait $SERVER
