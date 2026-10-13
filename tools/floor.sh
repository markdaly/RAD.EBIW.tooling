#!/bin/bash
# floor.sh: run every stand-in in one tmux session ("ihe") so servers and logs are managed in one
# place. Windows: ra (Result Aggregator 2575), em (Encounter Manager MWL 11112 + ADT 2576),
# ups (UPS-RS 8042), logs (three panes). remain-on-exit is on, so a crashed server leaves its
# output on screen; restart one with `tools/floor.sh restart <ra|em|ups>`.
# Ports and names come from .floor.env at the repo root if present (tools/panel.py writes it).
# Usage: tools/floor.sh start | restart <win> | status | stop | panel | panel-stop
R="$(cd "$(dirname "$0")/.." && pwd)"; cd "$R"
[ -f .floor.env ] && . ./.floor.env
RA_PORT="${RA_PORT:-2575}"; EM_PORT="${EM_PORT:-11112}"; ADT_PORT="${ADT_PORT:-2576}"; UPS_PORT="${UPS_PORT:-8042}"
AE_TITLE="${AE_TITLE:-ENC_MGR}"; ACCESSION_ISSUER="${ACCESSION_ISSUER:-ENC_MGR}"; ACCESSION_PREFIX="${ACCESSION_PREFIX:-EM}"
ENCOUNTERS="${ENCOUNTERS:-samples/encounters.json}"; ACK_APP="${ACK_APP:-SIMULATOR}"; ACK_FACILITY="${ACK_FACILITY:-SIMULATOR}"
PANEL_PORT="${PANEL_PORT:-8090}"
PY="${PYTHON:-uv run --python '>=3.11' --with pynetdicom --with pydicom --with fastapi --with uvicorn python}"
cmd() {  # macOS ships bash 3.2: no associative arrays
  case "$1" in
    ra)  echo "LISTEN_PORT=$RA_PORT ACK_APP=$ACK_APP ACK_FACILITY=$ACK_FACILITY $PY tools/mllp_receiver.py";;
    em)  echo "LISTEN_PORT=$EM_PORT ADT_PORT=$ADT_PORT AE_TITLE=$AE_TITLE ACCESSION_ISSUER=$ACCESSION_ISSUER ACCESSION_PREFIX=$ACCESSION_PREFIX ENCOUNTERS=$ENCOUNTERS $PY tools/mwl_scp.py";;
    ups) echo "LISTEN_PORT=$UPS_PORT ENCOUNTERS=$ENCOUNTERS ACCESSION_ISSUER=$ACCESSION_ISSUER ACCESSION_PREFIX=$ACCESSION_PREFIX $PY tools/ups_rs.py";;
  esac
}
case "$1" in
  start)
    tmux has-session -t ihe 2>/dev/null && { echo "session 'ihe' exists; use restart/status"; exit 1; }
    tmux new-session -d -s ihe -n ra -c "$R" "$(cmd ra)"
    tmux set-option -t ihe remain-on-exit on
    tmux new-window -t ihe -n em -c "$R" "$(cmd em)"
    tmux new-window -t ihe -n ups -c "$R" "$(cmd ups)"
    tmux new-window -t ihe -n logs -c "$R" "tools/logwatch.sh result-aggregator"
    tmux split-window -t ihe:logs -c "$R" "tools/logwatch.sh encounter-manager"
    tmux split-window -t ihe:logs -c "$R" "tools/newfiles.sh"
    tmux select-layout -t ihe:logs tiled
    tmux set-option -t ihe pane-border-status top 2>/dev/null
    tmux select-window -t ihe:logs
    echo "started; attach with: tmux attach -t ihe";;
  restart)
    w="$2"; [ -n "$(cmd "$w")" ] || { echo "restart <ra|em|ups>"; exit 1; }
    tmux respawn-window -k -t "ihe:$w" -c "$R" "$(cmd "$w")" && echo "restarted $w";;
  status)
    tmux list-windows -t ihe -F '#{window_name}: #{?pane_dead,DEAD (exit #{pane_dead_status}),running} #{pane_current_command}' 2>/dev/null || echo "session ihe not running"
    for p in "ra $RA_PORT" "adt $ADT_PORT" "ups $UPS_PORT" "em $EM_PORT" "panel $PANEL_PORT"; do set -- $p; printf '%-5s port %-5s ' $1 $2; lsof -nP -iTCP:$2 -sTCP:LISTEN >/dev/null 2>&1 && echo listening || echo "NOT listening"; done;;
  stop) tmux kill-session -t ihe && echo "stopped";;
  panel)
    tmux has-session -t ihe-panel 2>/dev/null && { echo "panel already running on http://127.0.0.1:$PANEL_PORT/"; exit 0; }
    tmux new-session -d -s ihe-panel -n panel -c "$R" "PANEL_PORT=$PANEL_PORT $PY tools/panel.py"
    tmux set-option -t ihe-panel remain-on-exit on; echo "panel on http://127.0.0.1:$PANEL_PORT/ (tmux session ihe-panel)";;
  panel-stop) tmux kill-session -t ihe-panel && echo "panel stopped";;
  *) echo "usage: tools/floor.sh start | restart <ra|em|ups> | status | stop | panel | panel-stop";;
esac
