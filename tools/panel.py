#!/usr/bin/env python3
"""
panel.py: local web panel for the stand-ins. Read the logs, step through messages, export one
raw file, see which servers are up, change ports, start/stop/restart them. Nothing here talks to
a vendor; it only reads logs/ and runs tools/floor.sh.

  GET  /                      status of the four listeners + tmux windows, config form, log index
  GET  /logs/<actor>/<session> files in a session (pairs: message + ACK, query + responses)
  GET  /view?f=<relpath>      one capture, rendered (HL7 field table, DICOM dump, JSON), prev/next, raw link
  GET  /raw?f=<relpath>       the raw bytes as a download (what a vendor attaches in Gazelle)
  POST /config                writes .floor.env (ports, AE title, issuer, encounters file)
  GET  /encounters            the rows the Encounter Manager serves, plus the pre-run setup form:
                              partner identifier (replaces the name suffix on the EBIW_10 rows),
                              one AE title per modality, issuer OID. POST /encounters writes the file.
  POST /service/<start|stop|restart>[/<ra|em|ups>]   runs tools/floor.sh

Config (env): PANEL_HOST default 127.0.0.1 (set 0.0.0.0 to let others on the floor read it),
PANEL_PORT default 8090, LOG_DIR default logs, REPO_URL default from `git remote get-url origin`.
Run: uv run --with fastapi --with uvicorn python tools/panel.py   (or tools/floor.sh panel)
"""
import html, json, os, re, subprocess, sys
from urllib.parse import parse_qs
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

sys.path.insert(0, str(Path(__file__).parent))
from hl7show import parse as hl7_parse, name_of  # field-name table shared with the console tool

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = (ROOT / os.environ.get("LOG_DIR", "logs")).resolve()
ENV_FILE = ROOT / ".floor.env"
FLOOR = ROOT / "tools" / "floor.sh"
HOST, PORT = os.environ.get("PANEL_HOST", "127.0.0.1"), int(os.environ.get("PANEL_PORT", "8090"))
CONFIG_KEYS = [("RA_PORT", "Result Aggregator MLLP port", "2575"), ("EM_PORT", "Encounter Manager DICOM port", "11112"),
               ("ADT_PORT", "Encounter Manager ITI-31 MLLP port", "2576"), ("UPS_PORT", "UPS-RS HTTP port", "8042"),
               ("AE_TITLE", "Encounter Manager AE title", "ENC_MGR"), ("ACCESSION_ISSUER", "Issuer of Accession Number", "ENC_MGR"),
               ("ACCESSION_PREFIX", "Accession prefix", "EM"), ("ENCOUNTERS", "Encounters file", "samples/encounters.json"),
               ("ACK_APP", "ACK MSH-3", "SIMULATOR"), ("ACK_FACILITY", "ACK MSH-4", "SIMULATOR")]


def repo_url():
    if os.environ.get("REPO_URL"):
        return os.environ["REPO_URL"]
    try:
        u = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"], capture_output=True, text=True, timeout=5).stdout.strip()
        u = re.sub(r"^git@github\.com:", "https://github.com/", u)
        return re.sub(r"\.git$", "", u)
    except Exception:
        return ""


def read_env():
    cfg = {k: d for k, _, d in CONFIG_KEYS}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1); cfg[k.strip()] = v.strip().strip('"')
    return cfg


def floor(*args):
    try:
        r = subprocess.run(["bash", str(FLOOR), *args], capture_output=True, text=True, timeout=60, cwd=ROOT)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"floor.sh failed: {e}"


def safe(rel: str) -> Path:
    p = (LOG_DIR / rel).resolve()
    if LOG_DIR not in p.parents or not p.is_file():
        raise FileNotFoundError(rel)
    return p


def session_files(folder: Path):
    return sorted(p for p in folder.iterdir() if p.is_file() and p.name != "summary.log")


def page(title, body, nav=""):
    css = """body{font:14px/1.4 -apple-system,Helvetica,Arial,sans-serif;margin:0;background:#111;color:#ddd}
    a{color:#7cc4ff;text-decoration:none}a:hover{text-decoration:underline}header{background:#1c1c1c;padding:8px 16px;border-bottom:1px solid #333;display:flex;gap:16px;align-items:center}
    main{padding:12px 16px;max-width:1400px}table{border-collapse:collapse;width:100%}td,th{padding:3px 8px;border-bottom:1px solid #2a2a2a;vertical-align:top;text-align:left}
    th{color:#999;font-weight:normal}tr.seg td{background:#1f2a36;font-weight:bold;color:#fff}td.n{white-space:nowrap;color:#9cf;width:6em}td.name{color:#aaa;width:22em}
    pre{background:#0b0b0b;padding:8px;overflow:auto;border:1px solid #333}.up{color:#6f6}.down{color:#f66}.btn{background:#2b4a6b;color:#fff;border:0;padding:4px 10px;border-radius:3px;cursor:pointer}
    .btn.red{background:#6b2b2b}input{background:#222;color:#eee;border:1px solid #444;padding:3px 6px}form.inline{display:inline}small{color:#888}.comp{color:#8d8}"""
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title><style>{css}</style></head>
<body><header><b><a href="/">kit panel</a></b> {nav} <span style="margin-left:auto"><a href="{html.escape(repo_url())}" target="_blank">repo</a> · <a href="{html.escape(repo_url())}/blob/main/docs/RUNNING.md" target="_blank">docs</a></span></header>
<main>{body}</main><script>document.addEventListener('keydown',e=>{{const a=document.querySelector(e.key==='j'||e.key==='ArrowRight'?'#next':e.key==='k'||e.key==='ArrowLeft'?'#prev':null);if(a)location=a.href}})</script></body></html>"""


app = FastAPI(title="kit panel")


@app.get("/", response_class=HTMLResponse)
def index():
    cfg = read_env()
    status = html.escape(floor("status"))
    rows = "".join(f"<tr><td><label>{html.escape(lbl)}</label></td><td><input name='{k}' value='{html.escape(cfg.get(k, d))}' size='30'></td></tr>" for k, lbl, d in CONFIG_KEYS)
    actors = ""
    if LOG_DIR.exists():
        for actor in sorted(p for p in LOG_DIR.iterdir() if p.is_dir()):
            sessions = sorted((s for s in actor.iterdir() if s.is_dir()), reverse=True)
            items = "".join(f"<li><a href='/logs/{actor.name}/{s.name}'>{s.name}</a> <small>{len(session_files(s))} files</small></li>" for s in sessions[:12])
            actors += f"<h3>{html.escape(actor.name)}</h3><ul>{items or '<li><small>no sessions</small></li>'}</ul>"
    body = f"""<h2>Services</h2><pre>{status}</pre>
<form class='inline' method='post' action='/service/start'><button class='btn'>start all</button></form>
<form class='inline' method='post' action='/service/stop'><button class='btn red'>stop all</button></form>
{' '.join(f"<form class='inline' method='post' action='/service/restart/{w}'><button class='btn'>restart {w}</button></form>" for w in ('ra','em','ups'))}
<small> &nbsp; actions run <code>tools/floor.sh</code>; a restart reads the config below.</small>
<h2>Config <small>(.floor.env, applied on next start/restart)</small></h2>
<form method='post' action='/config'><table>{rows}</table><button class='btn'>save</button></form>
<h2>Encounters</h2><p><a href='/encounters'>rows served by the Encounter Manager, pre-run setup (partner identifier, AE titles, OID)</a></p>
<h2>Logs <small>{html.escape(str(LOG_DIR))}</small></h2>{actors or '<small>no logs yet</small>'}"""
    return page("kit panel", body)


@app.post("/config")
async def save_config(request: Request):
    form = {k: v[0] for k, v in parse_qs((await request.body()).decode("utf-8", "replace")).items()}  # stdlib; no python-multipart needed
    lines = ["# written by tools/panel.py; read by tools/floor.sh"] + [f"{k}={str(form.get(k, d)).strip()}" for k, _, d in CONFIG_KEYS]
    ENV_FILE.write_text("\n".join(lines) + "\n")
    return RedirectResponse("/", status_code=303)


@app.post("/service/{action}")
@app.post("/service/{action}/{win}")
def service(action: str, win: str = ""):
    if action not in ("start", "stop", "restart"):
        return Response("bad action", status_code=400)
    out = floor(action, *([win] if win else []))
    return page("service", f"<pre>{html.escape(out)}</pre><a href='/'>back</a>")


def enc_path():
    return (ROOT / read_env().get("ENCOUNTERS", "samples/encounters.json")).resolve()


@app.get("/encounters", response_class=HTMLResponse)
def encounters_page(msg: str = ""):
    path = enc_path()
    try:
        d = json.loads(path.read_text())
    except Exception as e:
        return page("encounters", f"<p>cannot read {html.escape(str(path))}: {html.escape(str(e))}</p>")
    rows = d.get("encounters", [])
    mods = sorted({r.get("modality", "") for r in rows if r.get("modality")})
    ebiw = [r for r in rows if "^" in r.get("patient_name", "") and str(r.get("patient_id", "")).startswith("EBIW")]
    suffix = ebiw[0]["patient_name"].split("^", 1)[1] if ebiw else ""
    aet_now = {m: next((r.get("scheduled_station_ae_title", "") for r in rows if r.get("modality") == m), "") for m in mods}
    form = f"""<form method='post' action='/encounters'><table>
<tr><td>Partner identifier (name suffix on the {len(ebiw)} EBIW_10 rows, e.g. PEREZ^&lt;this&gt;)</td><td><input name='suffix' value='{html.escape(suffix)}'></td></tr>
{''.join(f"<tr><td>AE title for modality {html.escape(m)} rows</td><td><input name='aet_{m}' value='{html.escape(aet_now[m])}'> <small>blank = any device</small></td></tr>" for m in mods)}
<tr><td>Issuer OID (Universal Entity ID on issuer sequences)</td><td><input name='issuer_oid' value='{html.escape(d.get("issuer_oid", ""))}' size='40'> <small>blank = Local Namespace only</small></td></tr>
<tr><td>Issuer (Local Namespace) on EBIW rows</td><td><input name='issuer_local' value='{html.escape(ebiw[0].get("issuer_of_patient_id", "") if ebiw else "")}'></td></tr>
</table><button class='btn'>save to {html.escape(path.name)}</button> <small>then restart em and ups from the index page</small></form>"""
    table = "".join(f"<tr><td>{html.escape(r.get('patient_name',''))}</td><td>{html.escape(r.get('patient_id',''))}</td><td>{html.escape(r.get('admission_id',''))}</td>"
                    f"<td>{html.escape(r.get('modality','') or 'any')}</td><td>{html.escape(r.get('scheduled_station_ae_title','') or 'any')}</td>"
                    f"<td>{html.escape(((r.get('procedure') or {}).get('code') or {}).get('value', '') or 'generic')}</td><td>{html.escape(r.get('department_name',''))}</td></tr>" for r in rows)
    body = f"<h2>Encounters <small>{html.escape(str(path))}</small></h2>{('<p class=up>' + html.escape(msg) + '</p>') if msg else ''}<h3>Pre-run setup</h3>{form}<h3>Rows served</h3><table><tr><th>name</th><th>patient id</th><th>admission</th><th>modality</th><th>AE title</th><th>procedure</th><th>department</th></tr>{table}</table>"
    return page("encounters", body, "<a href='/'>index</a>")


@app.post("/encounters")
async def encounters_save(request: Request):
    form = {k: v[0].strip() for k, v in parse_qs((await request.body()).decode("utf-8", "replace")).items()}
    path = enc_path()
    d = json.loads(path.read_text())
    changed = 0
    for r in d.get("encounters", []):
        if str(r.get("patient_id", "")).startswith("EBIW") and "^" in r.get("patient_name", "") and form.get("suffix"):
            new = r["patient_name"].split("^", 1)[0] + "^" + form["suffix"]
            changed += new != r["patient_name"]; r["patient_name"] = new
            if form.get("issuer_local"):
                r["issuer_of_patient_id"] = r["issuer_of_admission_id"] = form["issuer_local"]
        m = r.get("modality")
        if m and f"aet_{m}" in form:
            changed += form[f"aet_{m}"] != r.get("scheduled_station_ae_title", ""); r["scheduled_station_ae_title"] = form[f"aet_{m}"]
    if "issuer_oid" in form:
        changed += form["issuer_oid"] != d.get("issuer_oid", ""); d["issuer_oid"] = form["issuer_oid"]
    path.write_text(json.dumps(d, indent=2) + "\n")
    return RedirectResponse(f"/encounters?msg=saved+({changed}+field+changes)", status_code=303)


@app.get("/logs/{actor}/{session}", response_class=HTMLResponse)
def session(actor: str, session: str):
    folder = (LOG_DIR / actor / session).resolve()
    if LOG_DIR not in folder.parents or not folder.is_dir():
        return Response("not found", status_code=404)
    files = session_files(folder)
    rows = "".join(f"<tr><td><a href='/view?f={actor}/{session}/{f.name}'>{html.escape(f.name)}</a></td><td>{f.stat().st_size} B</td>"
                   f"<td><a href='/raw?f={actor}/{session}/{f.name}'>raw</a></td></tr>" for f in reversed(files))
    summary = (folder / "summary.log").read_text(errors="replace") if (folder / "summary.log").exists() else ""
    body = f"<h2>{html.escape(actor)} / {html.escape(session)}</h2><table><tr><th>file</th><th>size</th><th></th></tr>{rows}</table><h3>summary.log</h3><pre>{html.escape(summary)}</pre>"
    return page(f"{actor}/{session}", body, f"<a href='/'>index</a>")


def render(p: Path, text: str) -> str:
    if p.suffix == ".hl7":
        rows = []
        for seg, fields in hl7_parse(text):
            rows.append(f"<tr class='seg'><td colspan='3'>{html.escape(seg)}</td></tr>")
            for n, v in fields:
                comps = [v] if seg == "MSH" and n <= 2 else v.split("^")
                shown = html.escape(v) if len(comps) == 1 else " <span class='comp'>^</span> ".join(f"<small>{i+1}:</small>{html.escape(c)}" for i, c in enumerate(comps))
                rows.append(f"<tr><td class='n'>{seg}-{n}</td><td class='name'>{html.escape(name_of(seg, n))}</td><td>{shown}</td></tr>")
        return f"<table>{''.join(rows)}</table><h3>raw</h3><pre>{html.escape(text.replace(chr(13), chr(10)))}</pre>"
    if p.suffix == ".json":
        try:
            return f"<pre>{html.escape(json.dumps(json.loads(text), indent=1))}</pre>"
        except ValueError:
            pass
    return f"<pre>{html.escape(text)}</pre>"


@app.get("/view", response_class=HTMLResponse)
def view(f: str):
    try:
        p = safe(f)
    except FileNotFoundError:
        return Response("not found", status_code=404)
    files = session_files(p.parent)
    i = files.index(p)
    rel = lambda q: f"{q.parent.parent.name}/{q.parent.name}/{q.name}"
    prev_ = f"<a id='prev' href='/view?f={rel(files[i-1])}'>&larr; prev</a>" if i > 0 else "<span style='color:#555'>&larr; prev</span>"
    next_ = f"<a id='next' href='/view?f={rel(files[i+1])}'>next &rarr;</a>" if i + 1 < len(files) else "<span style='color:#555'>next &rarr;</span>"
    stem = re.sub(r"\.(in|ack)\.hl7$|\.query\.txt$|\.resp\d+\.txt$|\.request\.txt$|\.response\.(json|txt)$", "", p.name)
    pair = [q for q in files if q.name.startswith(stem) and q != p]
    pairs = " ".join(f"<a href='/view?f={rel(q)}'>{html.escape(q.name[len(stem):])}</a>" for q in pair)
    text = p.read_bytes().decode("utf-8", "replace")
    nav = f"<a href='/logs/{p.parent.parent.name}/{p.parent.name}'>{html.escape(p.parent.parent.name)}/{html.escape(p.parent.name)}</a> {prev_} {next_} <small>{i+1}/{len(files)}</small>"
    body = f"<h2>{html.escape(p.name)} <small><a href='/raw?f={f}'>download raw</a></small></h2><p>related: {pairs or '<small>none</small>'} &nbsp; <small>keys: j/k or arrows</small></p>{render(p, text)}"
    return page(p.name, body, nav)


@app.get("/raw")
def raw(f: str):
    try:
        p = safe(f)
    except FileNotFoundError:
        return Response("not found", status_code=404)
    return Response(p.read_bytes(), media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="{p.name}"'})


if __name__ == "__main__":
    print(f"{datetime.now():%H:%M:%S} panel on http://{HOST}:{PORT}/  logs={LOG_DIR}  repo={repo_url()}", flush=True)
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
