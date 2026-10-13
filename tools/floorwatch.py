#!/usr/bin/env python3
"""floorwatch: one stdout line per thing worth reviewing on the live kit.

Usage: python3 -I -u tools/floorwatch.py [logs]   (stdlib only; macOS lsof for the port check)
Meant as the event source for an assistant's Monitor tool, or just run it in a terminal.

Tails every logs/<actor>/<session>/summary.log (new session folders included, from their first
line), keeps lines about traffic and trouble, and reports listener up/down transitions.
Reads only; never writes to logs/.
"""
import glob, json, os, subprocess, sys, time

ROOT = sys.argv[1] if len(sys.argv) > 1 else "logs"
KEEP = ("CONNECT ", "MSG #", "ITI-31", "C-FIND #", "-> match", "done,", "UPS-RS search", "ASSOC open",
        "NEW CONTEXT", "SEND ", "WARN", "ERROR", "Error", "Traceback", "AR ", "rejected")
PORTS = {"ra": 2575, "adt": 2576, "em": 11112, "ups": 8042, "panel": 8090}

def summaries():
    return glob.glob(os.path.join(ROOT, "*", "*", "summary.log"))

STATE = os.path.join(ROOT, ".floorwatch.pos.json")  # under logs/ (gitignored)
saved = json.load(open(STATE)) if os.path.exists(STATE) else None  # resume across re-arms: no gap
if saved is None:
    pos = {f: os.path.getsize(f) for f in summaries()}  # first arm: only what arrives from now on
else:
    pos = {f: saved.get(f, 0) for f in summaries()}     # files born during the gap read from the top
known = set(pos)
up = {}
last_ports = 0.0
print(f"floorwatch {'resumed' if saved is not None else 'armed'}: {len(pos)} summary logs, ports {sorted(PORTS.values())}", flush=True)
while True:
    for f in summaries():
        if f not in known:
            known.add(f); pos[f] = 0  # a new session folder (service restarted): read it from the top
        try:
            size = os.path.getsize(f)
        except OSError:
            continue
        p = pos.get(f, 0)
        if size < p:
            p = 0
        if size > p:
            with open(f, "rb") as fh:
                fh.seek(p); chunk = fh.read(size - p)
            pos[f] = size
            actor = f.split(os.sep)[-3]
            for line in chunk.decode("utf-8", "replace").splitlines():
                if any(k in line for k in KEEP) and "listening on" not in line:
                    print(f"[{actor}] {line[:400]}", flush=True)
    json.dump(pos, open(STATE + ".tmp", "w")); os.replace(STATE + ".tmp", STATE)
    if time.time() - last_ports > 15:
        last_ports = time.time()
        for name, port in PORTS.items():
            # passive: list listening sockets, never connect (a connect would land in the evidence logs)
            try:  # ss on Linux, lsof on macOS
                ok = subprocess.run(["ss", "-ltnH", f"sport = :{port}"], capture_output=True, text=True).stdout.strip() != ""
            except FileNotFoundError:
                ok = subprocess.run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"], capture_output=True).returncode == 0
            if up.get(name) is not None and up[name] != ok:
                print(f"[ports] {name} port {port} {'BACK UP' if ok else 'DOWN'}", flush=True)
            elif up.get(name) is None and not ok:
                print(f"[ports] {name} port {port} DOWN at arm time", flush=True)
            up[name] = ok
    time.sleep(1)
