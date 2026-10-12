#!/bin/bash
# logwatch.sh <actor>: tail every logs/<actor>/*/summary.log, picking up new session folders
# (each restart of a stand-in opens a new timestamped folder). Usage: tools/logwatch.sh result-aggregator
dir="${LOG_DIR:-logs}/$1"
while true; do
  files=$(ls -t "$dir"/*/summary.log 2>/dev/null)
  if [ -z "$files" ]; then echo "[logwatch] waiting for $dir/*/summary.log"; sleep 3; continue; fi
  echo "[logwatch] $(date +%H:%M:%S) following: $(echo "$files" | tr '\n' ' ')"
  tail -n 12 -F $files &
  pid=$!
  while [ "$(ls -t "$dir"/*/summary.log 2>/dev/null)" = "$files" ]; do sleep 3; done
  kill $pid 2>/dev/null; wait $pid 2>/dev/null
done
