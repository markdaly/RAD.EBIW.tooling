#!/bin/bash
# floor.sh: run every stand-in in one tmux session ("ihe") so servers and logs are managed in one
# place. Windows: ra (Result Aggregator 2575), em (Encounter Manager MWL 11112 + ADT 2576),
# ups (UPS-RS 8042), logs (three panes). remain-on-exit is on, so a crashed server leaves its
# output on screen; restart one with `tools/floor.sh restart <ra|em|ups>`.
# Usage: tools/floor.sh start | restart <win> | status | stop
R="$(cd "$(dirname "$0")/.." && pwd)"; cd "$R"
PY="${PYTHON:-uv run --python '>=3.11' --with pynetdicom --with pydicom --with fastapi --with uvicorn python}"
cmd() {  # macOS ships bash 3.2: no associative arrays
  case "$1" in
    ra)  echo "LISTEN_PORT=2575 $PY tools/mllp_receiver.py";;
    em)  echo "$PY tools/mwl_scp.py";;
    ups) echo "$PY tools/ups_rs.py";;
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
    tmux list-windows -t ihe -F '#{window_name}: #{?pane_dead,DEAD (exit #{pane_dead_status}),running} #{pane_current_command}'
    for p in 2575 2576 8042 11112; do printf 'port %-5s ' $p; lsof -nP -iTCP:$p -sTCP:LISTEN >/dev/null 2>&1 && echo listening || echo "NOT listening"; done;;
  stop) tmux kill-session -t ihe && echo "stopped";;
  *) echo "usage: tools/floor.sh start | restart <ra|em|ups> | status | stop";;
esac
