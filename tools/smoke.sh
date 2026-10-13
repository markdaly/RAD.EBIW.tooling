#!/bin/bash
# smoke.sh: start the whole kit with tools/floor.sh in its own tmux session, on its own ports and
# log folder, and exercise every listener once over loopback. Safe next to a live kit: it never
# touches the "ihe" session, the default ports, logs/ or .floor.env. Exit 0 = every check passed.
# Used by .github/workflows/ubuntu-smoke.yml; run it by hand on a new machine before the floor.
# Needs: bash, tmux, uv (first run downloads Python and the packages), python3 for the checks.
set -u
R="$(cd "$(dirname "$0")/.." && pwd)"; cd "$R"
export FLOOR_SESSION="smoke$$" FLOOR_ENV=/dev/null
export LOG_DIR="${SMOKE_LOG_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/kit-smoke.XXXXXX")}"
export RA_PORT=12575 ADT_PORT=12576 UPS_PORT=18042 EM_PORT=21112 PANEL_PORT="80,18090"
PY="uv run -q --python >=3.11 --with pynetdicom --with pydicom --with fastapi --with uvicorn python"
fails=0; pass() { echo "PASS  $*"; }; fail() { echo "FAIL  $*"; fails=$((fails + 1)); }
cleanup() {
  tmux kill-session -t "$FLOOR_SESSION" 2>/dev/null; tmux kill-session -t "$FLOOR_SESSION-panel" 2>/dev/null
}
trap cleanup EXIT

for c in tmux uv python3; do command -v $c >/dev/null || { echo "missing prerequisite: $c (see docs/INSTALL.md)"; exit 2; }; done
os=$( (. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME") || sw_vers -productName 2>/dev/null)
cu=$(ls --version 2>/dev/null | head -1 | grep -o "(.*)" || echo "BSD userland")
echo "smoke: $os, $(uname -srm), coreutils $cu, tmux $(tmux -V | cut -d' ' -f2), uv $(uv --version | cut -d' ' -f2), user $(id -un)"
echo "smoke: logs in $LOG_DIR"

tools/floor.sh start
up() { python3 -c "import socket,sys; socket.create_connection(('127.0.0.1', int(sys.argv[1])), 1).close()" "$1" 2>/dev/null; }
for i in $(seq 1 180); do  # the first run on a machine downloads Python and the wheels
  up $RA_PORT && up $ADT_PORT && up $EM_PORT && up $UPS_PORT && up 18090 && break; sleep 1
done
for p in $RA_PORT $ADT_PORT $EM_PORT $UPS_PORT 18090; do up $p && pass "port $p listening" || fail "port $p not listening after 180 s"; done
tools/floor.sh status | grep -q "port $UPS_PORT  listening\|port $UPS_PORT listening" && pass "floor.sh status sees the listeners" || fail "floor.sh status: $(tools/floor.sh status | tr '\n' ' ')"
grep -q "port(s) 80," <(tmux capture-pane -p -t "$FLOOR_SESSION-panel" 2>/dev/null) && echo "INFO  this panel bound port 80 too" \
  || echo "INFO  this panel did not bind port 80 (Linux without privileges, or 80 already in use); 18090 serves"

out=$($PY tools/mllp_send.py samples/ORU_R01_RAD-132_POCUS.hl7 127.0.0.1 $RA_PORT 2>&1)
echo "$out" | grep -q "^MSA|AA|" && pass "RAD-132 ORU -> AA" || fail "RAD-132: $out"
out=$($PY tools/mllp_send.py samples/ADT_A04_ITI-31_EBIW10.hl7 127.0.0.1 $ADT_PORT 2>&1)
echo "$out" | grep -q "^MSA|AA|" && pass "ITI-31 ADT -> AA" || fail "ITI-31: $out"
ls "$LOG_DIR"/result-aggregator/send-*/*.out.hl7 >/dev/null 2>&1 && pass "sender logged its outbound messages" || fail "no .out.hl7 under $LOG_DIR/result-aggregator/send-*"

out=$($PY tools/mwl_find.py 127.0.0.1 $EM_PORT ENC_MGR EBIW001 2>&1)
echo "$out" | grep -q "^[1-9][0-9]* worklist item" && pass "MWL C-FIND PEREZ: $(echo "$out" | grep 'worklist item')" || fail "MWL: $(echo "$out" | tail -3)"

http() { python3 - "$@" <<'PY'
import json, sys, urllib.request
url = sys.argv[1]
try:
    with urllib.request.urlopen(url, timeout=10) as r:
        body = r.read(); print(r.status, len(json.loads(body)) if body and sys.argv[2:] == ["json"] else len(body))
except Exception as e:
    print("ERR", e)
PY
}
q="PatientName=PEREZ%5ETEST&ScheduledStationNameCodeSequence.CodeValue=SMOKE_LWM&ScheduledStationClassCodeSequence.CodeValue=XC"
a=$(http "http://127.0.0.1:$UPS_PORT/workitems?$q" json); [ "$a" = "200 1" ] && pass "UPS-RS PEREZ + XC -> 1 workitem" || fail "UPS-RS: $a"
acc() { python3 -c "import json,sys,urllib.request;d=json.load(urllib.request.urlopen(sys.argv[1]));print(d[0]['0040A370']['Value'][0]['00080050']['Value'][0])" "$1" 2>/dev/null; }
a1=$(acc "http://127.0.0.1:$UPS_PORT/workitems?$q"); a2=$(acc "http://127.0.0.1:$UPS_PORT/workitems?$q")
[ -n "$a1" ] && [ "$a1" = "$a2" ] && pass "accession stable across queries ($a1)" || fail "accession: '$a1' vs '$a2'"
python3 -c "import json,sys;json.load(open(sys.argv[1]))" "$LOG_DIR/encounter-manager/state.json" && pass "state.json parses" || fail "state.json unreadable"

for u in / /howto /tail /tail.json /encounters; do
  a=$(http "http://127.0.0.1:18090$u"); case "$a" in "200 "*) pass "panel $u";; *) fail "panel $u: $a";; esac
done
a=$(python3 -c "import json,urllib.request;print(len(json.load(urllib.request.urlopen('http://127.0.0.1:18090/tail.json'))['lines']))" 2>&1)
[ "${a:-0}" -gt 0 ] 2>/dev/null && pass "panel live feed has $a lines" || fail "panel live feed: $a"

n=$(ls samples/adversarial/oru_*.hl7 | wc -l | tr -d ' ')
r=$($PY -I tools/adversarial/adversarial_mllp.py --port $RA_PORT 2>&1 | grep -c "RESPONDED")
[ "$r" = "$n" ] && pass "adversarial corpus: $r/$n ORU cases answered" || fail "adversarial corpus: $r/$n answered"

nfout="$LOG_DIR/newfiles.out"; bash tools/newfiles.sh > "$nfout" 2>/dev/null & nfpid=$!; sleep 4; kill $nfpid 2>/dev/null; wait $nfpid 2>/dev/null
nf=$(grep -c "^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]  " "$nfout")
[ "${nf:-0}" -gt 0 ] && pass "newfiles.sh lists captures with times ($nf rows)" || fail "newfiles.sh printed no timed rows"

if [ $fails -gt 0 ]; then
  echo; echo "---- summary logs"; tail -n 20 "$LOG_DIR"/*/*/summary.log 2>/dev/null
  for w in ra em ups; do echo "---- window $w"; tmux capture-pane -p -t "$FLOOR_SESSION:$w" 2>/dev/null | tail -15; done
  echo "---- panel"; tmux capture-pane -p -t "$FLOOR_SESSION-panel" 2>/dev/null | tail -15
fi
echo; echo "smoke: $fails failure(s)"; exit $((fails > 0))
