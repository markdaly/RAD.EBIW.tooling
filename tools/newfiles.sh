#!/bin/bash
# newfiles.sh: every 5 s, list the 25 most recent raw captures under logs/ (messages, ACKs, queries, responses)
while true; do
  clear; echo "newest raw captures under ${LOG_DIR:-logs}/  ($(date +%H:%M:%S))"; echo
  find "${LOG_DIR:-logs}" -type f ! -name summary.log ! -name '*.json' -print0 2>/dev/null \
    | xargs -0 ls -lt 2>/dev/null | head -25 | awk '{printf "%s %s  %6s  %s\n", $6, $7, $5, $9}'
  echo; echo "state: $(python3 -c "import json;print(len(json.load(open('${LOG_DIR:-logs}/encounter-manager/state.json'))))" 2>/dev/null || echo 0) accession contexts, $(python3 -c "import json;print(len(json.load(open('${LOG_DIR:-logs}/encounter-manager/encounters-from-adt.json'))))" 2>/dev/null || echo 0) ADT encounters"
  sleep 5
done
