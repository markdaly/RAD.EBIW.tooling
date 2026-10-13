#!/bin/bash
# newfiles.sh: every 5 s, list the 25 most recent raw captures under logs/ (messages, ACKs, queries,
# responses, outbound sends) with the time each was written, actor, kind and size, newest first.
# Shows as many as fit the pane (up to the terminal height).
LOGS="${LOG_DIR:-logs}"
while true; do
  rows=$(stty size < /dev/tty 2>/dev/null | cut -d' ' -f1); [ -z "$rows" ] && rows=31
  n=$(( rows - 6 )); [ "$n" -lt 5 ] && n=5   # fit the pane: title, header and state lines
  out=$(python3 - "$LOGS" "$n" <<'PY'
import json, os, sys, time
root, limit = sys.argv[1], int(sys.argv[2])
rows = []
for dirpath, _, files in os.walk(root):
    for f in files:
        if f == "summary.log" or len(os.path.relpath(os.path.join(dirpath, f), root).split(os.sep)) != 3:
            continue  # captures live in <actor>/<session>/; state and lock files sit one level up
        p = os.path.join(dirpath, f)
        try:
            st = os.stat(p)
        except OSError:
            continue
        rows.append((st.st_mtime, st.st_size, os.path.relpath(p, root)))
rows.sort(reverse=True)
kinds = [(".in.hl7", "in"), (".out.hl7", "out"), (".ack.hl7", "ack"), (".query.txt", "query"),
         (".request.txt", "request"), (".response.json", "response"), (".response.txt", "response")]
print(f"{'time':8}  {'actor':18} {'kind':8} {'bytes':>7}  file")
today = time.strftime("%Y%m%d")
for m, size, rel in rows[:limit]:
    parts = rel.split(os.sep)
    actor, name = parts[0], parts[-1]
    kind = next((k for suf, k in kinds if name.endswith(suf)), "resp" if ".resp" in name else "")
    stamp = time.strftime("%H:%M:%S", time.localtime(m))
    if time.strftime("%Y%m%d", time.localtime(m)) != today:
        stamp = time.strftime("%m-%d %H:%M", time.localtime(m))
    print(f"{stamp:8}  {actor:18} {kind:8} {size:7}  {name}")
def count(p):
    try:
        return len(json.load(open(os.path.join(root, p))))
    except Exception:
        return 0
print(f"\nstate: {count('encounter-manager/state.json')} accession contexts, "
      f"{count('encounter-manager/encounters-from-adt.json')} ADT encounters")
PY
)
  clear; echo "newest raw captures under $LOGS/  (now $(date +%H:%M:%S))"; echo; echo "$out"
  sleep 5
done
