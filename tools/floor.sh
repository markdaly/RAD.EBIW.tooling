#!/bin/bash
# floor.sh: run every stand-in in one tmux session ("ihe") so servers and logs are managed in one
# place. Windows: ra (Result Aggregator 2575), em (Encounter Manager MWL 11112 + ADT 2576),
# ups (UPS-RS 8042), logs (three panes). remain-on-exit is on, so a crashed server leaves its
# output on screen; restart one with `tools/floor.sh restart <ra|em|ups>`.
# Ports and names come from .floor.env at the repo root if present (tools/panel.py writes it).
# `start` also brings up the panel (tools/panel.py, PANEL_HOST default 0.0.0.0, writes local-only).
# Usage: tools/floor.sh start | restart <win> | status | stop | panel | panel-stop
R="$(cd "$(dirname "$0")/.." && pwd)"; cd "$R"
CONF="${FLOOR_ENV:-.floor.env}"; [ -f "$CONF" ] && . "$CONF"   # FLOOR_ENV=/dev/null ignores the saved config
SS="${FLOOR_SESSION:-ihe}"; SP="$SS-panel"                       # tmux session names (tools/smoke.sh uses its own)
RA_PORT="${RA_PORT:-2575}"; EM_PORT="${EM_PORT:-11112}"; ADT_PORT="${ADT_PORT:-2576}"; UPS_PORT="${UPS_PORT:-8042}"
AE_TITLE="${AE_TITLE:-ENC_MGR}"; ACCESSION_ISSUER="${ACCESSION_ISSUER:-ENC_MGR}"; ACCESSION_PREFIX="${ACCESSION_PREFIX:-EM}"
ENCOUNTERS="${ENCOUNTERS:-samples/encounters.json}"; ACK_APP="${ACK_APP:-SIMULATOR}"; ACK_FACILITY="${ACK_FACILITY:-SIMULATOR}"
PANEL_PORT="${PANEL_PORT:-80,8090}"; PANEL_HOST="${PANEL_HOST:-0.0.0.0}"
E="${LOG_DIR:+LOG_DIR=$LOG_DIR }"   # pass an explicit LOG_DIR into every window (tmux may hold an older env)
PY="${PYTHON:-uv run --python '>=3.11' --with pynetdicom --with pydicom --with fastapi --with uvicorn python}"
cmd() {  # macOS ships bash 3.2: no associative arrays
  case "$1" in
    ra)  echo "${E}LISTEN_PORT=$RA_PORT ACK_APP=$ACK_APP ACK_FACILITY=$ACK_FACILITY $PY tools/mllp_receiver.py";;
    em)  echo "${E}LISTEN_PORT=$EM_PORT ADT_PORT=$ADT_PORT AE_TITLE=$AE_TITLE ACCESSION_ISSUER=$ACCESSION_ISSUER ACCESSION_PREFIX=$ACCESSION_PREFIX ENCOUNTERS=$ENCOUNTERS $PY tools/mwl_scp.py";;
    ups) echo "${E}LISTEN_PORT=$UPS_PORT ENCOUNTERS=$ENCOUNTERS ACCESSION_ISSUER=$ACCESSION_ISSUER ACCESSION_PREFIX=$ACCESSION_PREFIX $PY tools/ups_rs.py";;
  esac
}
panel_start() {  # own tmux session so "stop" (servers) leaves the panel up
  tmux has-session -t "$SP" 2>/dev/null && { echo "panel already running on port $PANEL_PORT"; return 0; }
  tmux new-session -d -s "$SP" -n panel -c "$R" "${E}PANEL_HOST=$PANEL_HOST PANEL_PORT=$PANEL_PORT $PY tools/panel.py"
  tmux set-option -t "$SP" remain-on-exit on
  ip=$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}')
  urls=""; for p in ${PANEL_PORT//,/ }; do [ "$p" = 80 ] && urls="$urls http://${ip:-127.0.0.1}/" || urls="$urls http://${ip:-127.0.0.1}:$p/"; done
  echo "panel starting on$urls (read-only from other machines; admin at http://127.0.0.1:${PANEL_PORT##*,}/)"
  echo "  a port it cannot bind is skipped (Linux: 80 needs the sysctl in docs/INSTALL.md); check: tools/floor.sh status"
}
case "$1" in
  start)
    tmux has-session -t "$SS" 2>/dev/null && { echo "session '$SS' exists; use restart/status"; exit 1; }
    tmux new-session -d -s "$SS" -n ra -c "$R" "$(cmd ra)"
    tmux set-option -t "$SS" remain-on-exit on
    tmux new-window -t "$SS" -n em -c "$R" "$(cmd em)"
    tmux new-window -t "$SS" -n ups -c "$R" "$(cmd ups)"
    tmux new-window -t "$SS" -n logs -c "$R" "${E}tools/logwatch.sh result-aggregator"
    tmux split-window -t "$SS":logs -c "$R" "${E}tools/logwatch.sh encounter-manager"
    tmux split-window -t "$SS":logs -c "$R" "${E}tools/newfiles.sh"
    tmux select-layout -t "$SS":logs tiled
    tmux set-option -t "$SS" pane-border-status top 2>/dev/null
    tmux select-window -t "$SS":logs
    echo "started; attach with: tmux attach -t $SS"
    panel_start;;
  restart)
    w="$2"; [ -n "$(cmd "$w")" ] || { echo "restart <ra|em|ups>"; exit 1; }
    tmux respawn-window -k -t "$SS:$w" -c "$R" "$(cmd "$w")" && echo "restarted $w";;
  status)
    tmux list-windows -t "$SS" -F '#{window_name}: #{?pane_dead,DEAD (exit #{pane_dead_status}),running} #{pane_current_command}' 2>/dev/null || echo "session $SS not running"
    listening() {  # ss on Linux (always there), lsof on macOS
      if command -v ss >/dev/null 2>&1; then ss -ltnH "sport = :$1" 2>/dev/null | grep -q .; else lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; fi; }
    check() { printf '%-5s port %-5s ' "$1" "$2"; listening "$2" && echo listening || echo "NOT listening"; }
    check ra "$RA_PORT"; check adt "$ADT_PORT"; check ups "$UPS_PORT"; check em "$EM_PORT"
    for pp in ${PANEL_PORT//,/ }; do check panel "$pp"; done;;
  stop) tmux kill-session -t "$SS" && echo "stopped";;
  panel) panel_start;;
  panel-stop) tmux kill-session -t "$SP" && echo "panel stopped";;
  *) echo "usage: tools/floor.sh start | restart <ra|em|ups> | status | stop | panel | panel-stop";;
esac
