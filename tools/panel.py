#!/usr/bin/env python3
"""
panel.py: local web panel for the stand-ins. Read the logs, step through messages, export one
raw file, see which servers are up, change ports, start/stop/restart them. Nothing here talks to
a vendor; it only reads logs/ and runs tools/floor.sh.

  GET  /                      status of the four listeners + tmux windows, config form, log index
  GET  /logs/<actor>/<session> files in a session (pairs: message + ACK, query + responses)
  GET  /view?f=<relpath>      one capture, rendered (HL7 field table, DICOM dump, JSON), prev/next, raw link
  GET  /raw?f=<relpath>       the raw bytes as a download (what a vendor attaches in Gazelle)
  GET  /howto                 get-started page for vendors, rendered from events/<event>/docs/HOWTO.md
                              (PANEL_HOWTO overrides the path)
  GET  /tail                  live view: summary lines of every actor merged by time, plus the newest
                              captures, refreshed every 2 s (follows the bottom unless you scroll up)
  POST /config                writes .floor.env (ports, AE title, issuer, encounters file)
  GET  /encounters            the rows the Encounter Manager serves, plus the pre-run setup form:
                              partner identifier (replaces the name suffix on the EBIW_10 rows),
                              one AE title per modality, issuer OID. POST /encounters writes the file.
  POST /service/<start|stop|restart>[/<ra|em|ups>]   runs tools/floor.sh

Config (env): PANEL_HOST default 0.0.0.0 (anyone on the floor can read logs and download raw
captures; set 127.0.0.1 to keep it on this machine). The POST actions (config, service control,
encounter edits) answer only clients on this machine unless PANEL_REMOTE_CONTROL=1. No
authentication either way. PANEL_PORT default 80,8090 (comma list; a port that cannot be bound, e.g.
80 without privileges on Linux, is skipped with a message and the others still serve), LOG_DIR default logs, REPO_URL default from `git remote get-url origin`.
Run: uv run --with fastapi --with uvicorn python tools/panel.py   (or tools/floor.sh panel)
"""
import asyncio, contextvars, html, json, os, re, socket, subprocess, sys
from urllib.parse import parse_qs
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

sys.path.insert(0, str(Path(__file__).parent))
from hl7show import parse as hl7_parse, name_of  # field-name table shared with the console tool

ROOT = Path(__file__).resolve().parent.parent
PY_CMD = (os.environ.get("PYTHON") or "uv run --quiet --python >=3.11 python").split()   # how to run a sibling tool
LOG_DIR = (ROOT / os.environ.get("LOG_DIR", "logs")).resolve()
ENV_FILE = ROOT / ".floor.env"
FLOOR = ROOT / "tools" / "floor.sh"


def howto_path():
    """PANEL_HOWTO, else the newest events/<event>/docs/HOWTO.md (event facts stay under events/)."""
    if os.environ.get("PANEL_HOWTO"):
        return (ROOT / os.environ["PANEL_HOWTO"]).resolve()
    found = sorted(ROOT.glob("events/*/docs/HOWTO.md"))
    return found[-1] if found else None
HOST = os.environ.get("PANEL_HOST", "0.0.0.0")
PORTS = [int(p) for p in os.environ.get("PANEL_PORT", "80,8090").split(",") if p.strip()]  # 80 so a bare IP or hostname works
REMOTE_CONTROL = os.environ.get("PANEL_REMOTE_CONTROL", "") == "1"
LOCAL = {"127.0.0.1", "::1", "localhost"}
TESTER_WRITES = {"/encounters", "/send-adt"}   # POSTs any floor laptop may make
IS_ADMIN = contextvars.ContextVar("is_admin", default=False)  # set per request by the middleware, read by page()
CONFIG_KEYS = [("RA_PORT", "Result Aggregator MLLP port", "2575"), ("EM_PORT", "Encounter Manager DICOM port", "11112"),
               ("ADT_PORT", "Encounter Manager ITI-31 MLLP port", "2576"), ("UPS_PORT", "UPS-RS HTTP port", "8042"),
               ("AE_TITLE", "Encounter Manager AE title", "ENC_MGR"), ("ACCESSION_ISSUER", "Issuer of Accession Number", "ENC_MGR"),
               ("ACCESSION_PREFIX", "Accession prefix", "EM"), ("ENCOUNTERS", "Encounters file", "samples/encounters.json"),
               ("ACK_APP", "ACK MSH-3", "SIMULATOR"), ("ACK_FACILITY", "ACK MSH-4", "SIMULATOR"),
               ("ADT_TARGET_HOST", "ITI-31 send: receiver host (proxy)", "proxy.ihe-europe.net"), ("ADT_TARGET_PORT", "ITI-31 send: receiver port", ""),
               ("ADT_TARGET_APP", "ITI-31 send: receiver MSH-5", "SIMULATOR"), ("ADT_TARGET_FAC", "ITI-31 send: receiver MSH-6", "SIMULATOR")]


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
    css = """:root{--bg:#0f1318;--surface:#161b22;--surface2:#1c232c;--border:#2a323d;--text:#e6e9ef;--muted:#97a3b3;--link:#6cb6ff;
      --accent:#58a6ff;--seg:#1a2b40;--segtext:#cfe3ff;--id:#8ab4f8;--comp:#5f6b7a;--sep:#3fb950;--code:#1f2630;--btn:#2563a8;--btnred:#a33a3a;
      --admin-bg:#12301c;--admin-fg:#9be9a8;--ro-bg:#3b2f0c;--ro-fg:#f2cc60;--callout-bg:#13263d;--callout-bd:#2f5d8f;
      --ra:#6cb6ff;--em:#d2a8ff;--mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,"DejaVu Sans Mono","Liberation Mono",Consolas,monospace;
      --sans:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Ubuntu,Cantarell,"Helvetica Neue",Arial,sans-serif}
    @media (prefers-color-scheme: light){:root{--bg:#f6f8fa;--surface:#ffffff;--surface2:#eef2f6;--border:#d8dee4;--text:#1f2328;--muted:#59636e;
      --link:#0b62c4;--accent:#0969da;--seg:#e3eefb;--segtext:#0b3a6e;--id:#1557b0;--comp:#8c959f;--sep:#1a7f37;--code:#eef1f4;--btn:#0969da;--btnred:#c62f2f;
      --admin-bg:#dff5e3;--admin-fg:#11612b;--ro-bg:#fff4d1;--ro-fg:#7a5300;--callout-bg:#e7f1fd;--callout-bd:#9cc3ef;--ra:#0b62c4;--em:#8250df}}
    body{font:15px/1.5 var(--sans);margin:0;background:var(--bg);color:var(--text);-webkit-font-smoothing:antialiased}
    a{color:var(--link);text-decoration:none}a:hover{text-decoration:underline}
    header{background:var(--surface);padding:8px 16px;border-bottom:1px solid var(--border);display:flex;flex-wrap:wrap;gap:4px 16px;align-items:center}header a,header b,header small,header span{white-space:nowrap}.nw{white-space:nowrap;overflow-wrap:normal}header b a{color:var(--text)}
    h1,h2,h3{font-weight:600;letter-spacing:-.01em}h2 small,h3 small{font-weight:400}
    main{padding:12px 16px;max-width:1400px;overflow-x:auto}table{border-collapse:collapse;width:100%}td,th{padding:3px 8px;border-bottom:1px solid var(--border);vertical-align:top;text-align:left}td{overflow-wrap:anywhere}
    th{color:var(--muted);font-weight:500}tr.seg td{background:var(--seg);font-weight:700;color:var(--segtext);font-family:var(--mono);border-left:3px solid var(--accent)}
    td.n{white-space:nowrap;color:var(--id);width:6em;font-family:var(--mono);font-size:13.5px}td.name{color:var(--muted);width:22em}td.v{font-family:var(--mono);font-size:13.5px;overflow-wrap:anywhere}
    td.v small{color:var(--comp)}
    pre{background:var(--surface);padding:8px;overflow:auto;border:1px solid var(--border);font:13px/1.45 var(--mono);color:var(--text)}
    code{font-family:var(--mono);font-size:.92em}.up{color:var(--sep)}.down{color:var(--btnred)}
    .btn{background:var(--btn);color:#fff;border:0;padding:4px 10px;border-radius:4px;cursor:pointer;font:500 14px var(--sans)}.btn:hover{filter:brightness(1.1)}
    .btn.red{background:var(--btnred)}input{background:var(--surface2);color:var(--text);border:1px solid var(--border);padding:3px 6px;border-radius:3px;font:14px var(--mono)}
    form.inline{display:inline}small{color:var(--muted)}.comp{color:var(--sep);font-weight:700}
    .banner{padding:6px 16px;font-weight:600}.banner.admin{background:var(--admin-bg);color:var(--admin-fg)}.banner.ro{background:var(--ro-bg);color:var(--ro-fg)}
    body.ro form{opacity:.4;pointer-events:none}body.ro form.tester{opacity:1;pointer-events:auto}.callout{background:var(--callout-bg);border:1px solid var(--callout-bd);padding:8px 12px;border-radius:4px;font-size:15px}
    .md{max-width:1000px}.md h1{font-size:24px}.md h2{font-size:18px;margin-top:22px;border-bottom:1px solid var(--border);padding-bottom:2px}
    .md code{background:var(--code);padding:1px 4px;border-radius:3px}.md td code{overflow-wrap:anywhere}.md b{font-weight:600}
    .a-result-aggregator{color:var(--ra)}.a-encounter-manager{color:var(--em)}.a-other{color:var(--muted)}"""
    admin = IS_ADMIN.get()
    banner = (f"<div class='banner admin'>ADMIN: you are on the machine running this panel. Config, start/stop/restart and encounter edits work here only; floor laptops get a read-only view.</div>"
              if admin else
              f"<div class='banner ro'>READ-ONLY VIEW: browse logs and download raw captures. Administration (config, start/stop/restart, encounter edits) is only available on the machine running this panel.</div>")
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark light"><title>{html.escape(title)}</title><style>{css}</style></head>
<body class="{'' if admin else 'ro'}"><header><b><a href="/">kit panel</a></b> <a href="/howto">howto</a> <a href="/tail">live</a> <a href="/encounters">encounters</a> {nav} <span style="margin-left:auto"><a href="{html.escape(repo_url())}" target="_blank">repo</a> · <a href="{html.escape(repo_url())}/blob/main/docs/RUNNING.md" target="_blank">docs</a></span></header>
{banner}<main>{body}</main><script>document.addEventListener('keydown',e=>{{const a=document.querySelector(e.key==='j'||e.key==='ArrowRight'?'#next':e.key==='k'||e.key==='ArrowLeft'?'#prev':null);if(a)location=a.href}})</script></body></html>"""


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
    body = f"""<p class='callout'>New here? <a href='/howto'><b>Get started: how to connect, what to send, how to watch it arrive</b></a></p>
<h2>Services</h2><pre>{status}</pre>
<form class='inline' method='post' action='/service/start'><button class='btn'>start all</button></form>
<form class='inline' method='post' action='/service/stop'><button class='btn red'>stop all</button></form>
{' '.join(f"<form class='inline' method='post' action='/service/restart/{w}'><button class='btn'>restart {w}</button></form>" for w in ('ra','em','ups'))}
<small> &nbsp; actions run <code>tools/floor.sh</code>; a restart reads the config below.</small>
<h2>Config <small>(.floor.env, applied on next start/restart)</small></h2>
<form method='post' action='/config'><table>{rows}</table><button class='btn'>save</button></form>
<h2>Encounters</h2><p><a href='/encounters'>rows served by the Encounter Manager, pre-run setup (partner identifier, AE titles, OID)</a></p>
<h2>Logs <small>{html.escape(str(LOG_DIR))}</small></h2>{actors or '<small>no logs yet</small>'}"""
    return page("kit panel", body)


@app.middleware("http")
async def local_only_writes(request: Request, call_next):
    """Floor laptops may read, edit the encounter set and send the step-10 ADT; only this machine
    (or PANEL_REMOTE_CONTROL=1) may change ports or start/stop servers."""
    admin = REMOTE_CONTROL or (request.client.host if request.client else "") in LOCAL
    IS_ADMIN.set(admin)
    if request.method != "GET" and not admin and request.url.path not in TESTER_WRITES:
        return Response("read-only from other machines: ports and start/stop are local to the panel host; "
                        "encounter setup and the ITI-31 send are open to everyone\n", status_code=403)
    return await call_next(request)


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
    form = f"""<form class='tester' method='post' action='/encounters'><table>
<tr><td>Partner identifier (name suffix on the {len(ebiw)} EBIW_10 rows, e.g. PEREZ^&lt;this&gt;)</td><td><input name='suffix' value='{html.escape(suffix)}'></td></tr>
{''.join(f"<tr><td>AE title for modality {html.escape(m)} rows</td><td><input name='aet_{m}' value='{html.escape(aet_now[m])}'> <small>blank = any device</small></td></tr>" for m in mods)}
<tr><td>Issuer OID (Universal Entity ID on issuer sequences)</td><td><input name='issuer_oid' value='{html.escape(d.get("issuer_oid", ""))}' size='40'> <small>blank = Local Namespace only</small></td></tr>
<tr><td>Issuer (Local Namespace) on EBIW rows</td><td><input name='issuer_local' value='{html.escape(ebiw[0].get("issuer_of_patient_id", "") if ebiw else "")}'></td></tr>
</table><button class='btn'>save to {html.escape(path.name)}</button> <small>then restart em and ups from the index page</small></form>"""
    table = "".join(f"<tr><td>{html.escape(r.get('patient_name',''))}</td><td>{html.escape(r.get('patient_id',''))}</td><td>{html.escape(r.get('admission_id',''))}</td>"
                    f"<td>{html.escape(r.get('modality','') or 'any')}</td><td>{html.escape(r.get('scheduled_station_ae_title','') or 'any')}</td>"
                    f"<td>{html.escape(((r.get('procedure') or {}).get('code') or {}).get('value', '') or 'generic')}</td><td>{html.escape(r.get('department_name',''))}</td></tr>" for r in rows)
    cfg = read_env()
    adms = []
    for r in rows:
        if r.get("admission_id") and r["admission_id"] not in [a for a, _ in adms]:
            adms.append((r["admission_id"], f"{r['admission_id']}: {r.get('patient_name','')} ({r.get('patient_id','')})"))
    opts = "".join(f"<option value='{html.escape(a)}'>{html.escape(l)}</option>" for a, l in adms)
    send = f"""<h3>Send ITI-31 ADT^A04 for an encounter (EBIW_POCUS step 10, the Result Aggregator starts it)</h3>
<p class='callout'><b>For testers.</b> In EBIW_POCUS_Simple_Workflow the <b>Result Aggregator sends</b> the admit (step 10)
to the POCUS / Encounter Manager, which then serves the worklist for step 60. Pick the encounter you agreed with the monitor,
enter <b>your</b> ADT listener's proxy host and port and the MSH-5/6 you registered in Gazelle, and send. Your ACK comes back
here and both sides land in the send log. <b>Leave "Also to our Encounter Manager" off</b> when your system (or another
vendor's) is the Encounter Manager; tick it only when this kit's Encounter Manager serves the worklist for your run.
Anyone on the floor network can do this from their own laptop; no need for the panel host.</p>
<form class='tester' method='post' action='/send-adt'><table>
<tr><td>Encounter</td><td><select name='admission_id'>{opts}</select></td></tr>
<tr><td>Receiver host</td><td><input name='host' value='{html.escape(cfg.get("ADT_TARGET_HOST",""))}' size='30'> <small>the POCUS Manager's proxy host, or its IP</small></td></tr>
<tr><td>Receiver port</td><td><input name='port' value='{html.escape(cfg.get("ADT_TARGET_PORT",""))}' size='8'> <small>their proxy port for the ADT listener</small></td></tr>
<tr><td>Receiver MSH-5 / MSH-6</td><td><input name='app' value='{html.escape(cfg.get("ADT_TARGET_APP",""))}' size='16'> / <input name='fac' value='{html.escape(cfg.get("ADT_TARGET_FAC",""))}' size='16'> <small>what they registered in Gazelle</small></td></tr>
<tr><td>Also to our Encounter Manager</td><td><input type='checkbox' name='also_em' value='1'> <small>only when our Encounter Manager serves step 60's worklist; leave off when a vendor is the Encounter Manager (127.0.0.1:{html.escape(cfg.get("ADT_PORT","2576"))})</small></td></tr>
</table><button class='btn'>send ADT</button> <small>message and ACK are logged under logs/result-aggregator/send-&lt;date&gt;/</small></form>"""
    body = f"<h2>Encounters <small>{html.escape(str(path))}</small></h2>{('<p class=up>' + html.escape(msg) + '</p>') if msg else ''}<h3>Pre-run setup</h3> <p class='callout'><b>For testers.</b> These rows are the worklist this kit's Encounter Manager serves (the Gazelle EBIW_10 patient set). Before an EBIW_20 / EBIW_30 run, put your partner identifier on the names, your modality's AE title on its rows, and the OID if you use one, then save. The panel host restarts <code>em</code> (ask the monitor, or use the index page from that machine). If a vendor is the Encounter Manager for your run, nothing here matters except the ITI-31 send below.</p>{form}{send}<h3>Rows served</h3><table><tr><th>name</th><th>patient id</th><th>admission</th><th>modality</th><th>AE title</th><th>procedure</th><th>department</th></tr>{table}</table>"
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


def adt_from_encounter(d, enc, app, fac):
    """ADT^A04^ADT_A01 (ITI-31 admit) from an encounter row: PID-3/5/7/8/18, PV1-2/3/7/19/44, DG1.
    Same mapping as the Encounter Manager's intake (RAD TF-2x Appendix U), run backwards."""
    def seg(name, fields):
        n = max(fields); out = [name] + [""] * n
        for k, v in fields.items(): out[k] = v
        return "|".join(out)
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    iss = enc.get("issuer_of_patient_id", "") or "ENC_MGR"
    adm_iss = enc.get("issuer_of_admission_id", "") or iss
    dept = enc.get("department_name", "")
    poc = next((k for k, v in d.get("department_codes", {}).items() if v.get("value") == (enc.get("department_type") or {}).get("value")), dept)
    por = enc.get("physician_of_record") or {}
    phys = f"{por.get('id','')}^{por.get('name','')}^^^^^^NPI&2.16.840.1.113883.4.6&ISO^L^^^NPI" if por.get("id") else (por.get("name", "") and f"^{por['name']}")
    lines = [
        f"MSH|^~\\&|SIMULATOR|SIMULATOR|{app}|{fac}|{now}||ADT^A04^ADT_A01|ADT{now[-8:]}|P|2.5|||AL|NE",
        seg("EVN", {1: "A04", 2: now}),
        seg("PID", {1: "1", 3: f"{enc.get('patient_id','')}^^^{iss}^MR", 5: enc.get("patient_name", ""), 7: enc.get("birth_date", ""),
                    8: enc.get("sex", ""), 18: f"{enc['admission_id']}^^^{adm_iss}^AN"}),
        seg("PV1", {1: "1", 2: "E" if "mergency" in dept else "O", 3: f"{poc}^^^{d.get('institution', {}).get('name','')}^^^^^{dept}",
                    7: phys, 19: f"{enc['admission_id']}^^^{adm_iss}^VN", 44: (enc.get("admitting_date", "") + enc.get("admitting_time", ""))}),
    ]
    if enc.get("reason_for_visit"):
        lines.append(seg("DG1", {1: "1", 4: enc["reason_for_visit"], 6: "A"}))
    return "\r".join(lines) + "\r"


@app.post("/send-adt")
async def send_adt(request: Request):
    form = {k: v[0].strip() for k, v in parse_qs((await request.body()).decode("utf-8", "replace")).items()}
    d = json.loads(enc_path().read_text())
    enc = next((r for r in d.get("encounters", []) if r.get("admission_id") == form.get("admission_id")), None)
    if not enc:
        return page("send", "<p>unknown encounter</p><a href='/encounters'>back</a>")
    cfg = read_env()
    for k, f in (("ADT_TARGET_HOST", "host"), ("ADT_TARGET_PORT", "port"), ("ADT_TARGET_APP", "app"), ("ADT_TARGET_FAC", "fac")):
        cfg[k] = form.get(f, cfg.get(k, ""))
    ENV_FILE.write_text("# written by tools/panel.py; read by tools/floor.sh\n" + "".join(f"{k}={cfg.get(k, dflt)}\n" for k, _, dflt in CONFIG_KEYS))
    msg = adt_from_encounter(d, enc, form.get("app", ""), form.get("fac", ""))
    folder = LOG_DIR / "result-aggregator" / f"send-{datetime.now():%Y%m%d}"; folder.mkdir(parents=True, exist_ok=True)
    src = folder / f"{datetime.now():%Y%m%d-%H%M%S}-panel-{enc['admission_id']}-ADT_A04.hl7"
    src.write_bytes(msg.encode("latin-1"))
    targets = []
    if form.get("host") and form.get("port"):
        targets.append((form["host"], form["port"], "the receiver"))
    if form.get("also_em"):
        targets.append(("127.0.0.1", cfg.get("ADT_PORT", "2576"), "our Encounter Manager"))
    out = []
    for host, port, who in targets:
        r = subprocess.run([*PY_CMD, str(ROOT / "tools" / "mllp_send.py"), str(src), host, str(port)],
                           capture_output=True, text=True, timeout=40, cwd=ROOT, env={**os.environ, "LOG_DIR": str(LOG_DIR), "SEND_ACTOR": "result-aggregator"})
        out.append(f"<h3>{html.escape(who)}: {html.escape(host)}:{html.escape(str(port))}</h3><pre>{html.escape((r.stdout + r.stderr).strip() or 'no output')}</pre>")
    if not targets:
        out.append("<p>nothing sent: no receiver host/port and the Encounter Manager box was unchecked</p>")
    body = f"<h2>ITI-31 sent for {html.escape(enc['admission_id'])} ({html.escape(enc.get('patient_name',''))})</h2>{''.join(out)}" \
           f"<h3>message</h3><pre>{html.escape(msg.replace(chr(13), chr(10)))}</pre><p><a href='/encounters'>back to encounters</a> · <a href='/logs/result-aggregator/{folder.name}'>send log</a></p>"
    return page("ITI-31 sent", body, "<a href='/encounters'>encounters</a>")


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
                rows.append(f"<tr><td class='n'>{seg}-{n}</td><td class='name'>{html.escape(name_of(seg, n))}</td><td class='v'>{shown}</td></tr>")
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
    stem = re.sub(r"\.(in|out|ack)\.hl7$|\.query\.txt$|\.resp\d+\.txt$|\.request\.txt$|\.response\.(json|txt)$", "", p.name)
    pair = [q for q in files if q.name.startswith(stem) and q != p]
    pairs = " ".join(f"<a href='/view?f={rel(q)}'>{html.escape(q.name[len(stem):])}</a>" for q in pair)
    text = p.read_bytes().decode("utf-8", "replace")
    nav = f"<a href='/logs/{p.parent.parent.name}/{p.parent.name}'>{html.escape(p.parent.parent.name)}/{html.escape(p.parent.name)}</a> {prev_} {next_} <small>{i+1}/{len(files)}</small>"
    body = f"<h2>{html.escape(p.name)} <small><a href='/raw?f={f}'>download raw</a></small></h2><p>related: {pairs or '<small>none</small>'} &nbsp; <small>keys: j/k or arrows</small></p>{render(p, text)}"
    return page(p.name, body, nav)


TS_FILE = re.compile(r"(\d{8})-(\d{6})")  # session folders and capture names carry YYYYMMDD-HHMMSS


def tail_data(n=300):
    """Last n summary lines across actors, merged by date+time; newest 25 captures with mtime."""
    lines, caps = [], []
    if LOG_DIR.exists():
        for actor in (a for a in LOG_DIR.iterdir() if a.is_dir()):
            sessions = sorted((d for d in actor.iterdir() if d.is_dir()), key=lambda d: d.stat().st_mtime)[-4:]
            for d in sessions:
                m = re.search(r"(\d{8})", d.name)
                day = m.group(1) if m else datetime.fromtimestamp(d.stat().st_mtime).strftime("%Y%m%d")
                summ = d / "summary.log"
                if summ.exists():
                    for i, line in enumerate(summ.read_text("utf-8", "replace").splitlines()[-n:]):
                        f = re.search(r"file=(\S+)", line)
                        link = f"{actor.name}/{d.name}/{f.group(1)}" if f and (d / f.group(1)).exists() else ""
                        lines.append((day, line[:8], i, actor.name, line, link))
                for c in d.iterdir():
                    if c.is_file() and c.name != "summary.log":
                        caps.append((c.stat().st_mtime, actor.name, d.name, c))
    lines.sort()
    caps = sorted(caps, reverse=True)[:25]
    return lines[-n:], caps


def md_inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    return re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r"<a href='\2' target='_blank'>\1</a>", t)


def md_to_html(text):
    """Just enough Markdown for HOWTO.md: front matter, #/## headings, paragraphs, - and 1. lists,
    pipe tables, `code`, **bold**, [links](https://...). No dependency."""
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    out, para, items, kind, rows = [], [], [], "", []
    def flush():
        nonlocal para, items, kind, rows
        if para: out.append("<p>" + md_inline(" ".join(para)) + "</p>")
        if items: out.append(f"<{kind}>" + "".join(f"<li>{md_inline(i)}</li>" for i in items) + f"</{kind}>")
        if rows:
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows if not re.match(r"^\|[\s:|-]+\|?$", r.strip())]
            if cells:
                out.append("<table><tr>" + "".join(f"<th>{md_inline(c)}</th>" for c in cells[0]) + "</tr>" +
                           "".join("<tr>" + "".join(f"<td>{md_inline(c)}</td>" for c in r) + "</tr>" for r in cells[1:]) + "</table>")
        para, items, kind, rows = [], [], "", []
    for line in text.splitlines():
        st = line.strip()
        m = re.match(r"^(#{1,3}) (.*)", st)
        if not st:
            flush()
        elif m:
            flush(); n = len(m.group(1)); out.append(f"<h{n}>{md_inline(m.group(2))}</h{n}>")
        elif st.startswith("|"):
            if para or items: flush()
            rows.append(st)
        elif re.match(r"^(- |\d+\. )", st):
            k = "ul" if st.startswith("- ") else "ol"
            if para or rows or (items and k != kind): flush()
            kind = k; items.append(re.sub(r"^(- |\d+\. )", "", st))
        elif items and line.startswith("  "):
            items[-1] += " " + st          # continuation of a list item
        else:
            if items or rows: flush()
            para.append(st)
    flush()
    return "\n".join(out)


@app.get("/howto", response_class=HTMLResponse)
def howto():
    p = howto_path()
    if not p or not p.is_file():
        return page("howto", "<p>No HOWTO.md found under events/*/docs/ (set PANEL_HOWTO).</p>")
    return page("get started", f"<div class='md'>{md_to_html(p.read_text('utf-8', 'replace'))}</div>")


@app.get("/tail.json")
def tail_json():
    lines, caps = tail_data()
    return {"lines": [{"day": d, "actor": a, "text": t, "link": l} for d, _, _, a, t, l in lines],
            "captures": [{"time": datetime.fromtimestamp(m).strftime("%H:%M:%S"), "actor": a, "session": s, "name": c.name,
                          "size": c.stat().st_size, "link": f"{a}/{s}/{c.name}"} for m, a, s, c in caps]}


@app.get("/tail", response_class=HTMLResponse)
def tail_page():
    body = """<h2>Live <small>summary lines of every actor, merged by time; refreshes every 2 s</small></h2>
<p><label><input type='checkbox' id='follow' checked> follow the newest line</label> <small id='stamp'></small></p>
<pre id='lines' style='height:55vh;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere'></pre>
<h3>Newest captures</h3><table id='caps'><tr><th>time</th><th>actor</th><th>size</th><th>file</th></tr></table>
<script>
const esc=s=>s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const cls=a=>a==='result-aggregator'||a==='encounter-manager'?'a-'+a:'a-other';
async function tick(){
  try{
    const r=await fetch('/tail.json',{cache:'no-store'}); const d=await r.json();
    const box=document.getElementById('lines'); const atBottom=box.scrollTop+box.clientHeight>=box.scrollHeight-20;
    box.innerHTML=d.lines.map(l=>{const t=esc(l.text);const tag=`<span class='${cls(l.actor)}'>${l.actor.padEnd(18)}</span>`;
      return tag+' '+(l.link?`<a href='/view?f=${encodeURIComponent(l.link)}'>${t}</a>`:t)}).join('\\n');
    if(document.getElementById('follow').checked&&atBottom||box.dataset.first!=='done'){box.scrollTop=box.scrollHeight;box.dataset.first='done'}
    document.getElementById('caps').innerHTML='<tr><th>time</th><th>actor</th><th>size</th><th>file</th></tr>'+d.captures.map(c=>
      `<tr><td class='nw'>${c.time}</td><td class='nw ${cls(c.actor)}'>${esc(c.actor)}</td><td class='nw'>${c.size} B</td><td><a href='/view?f=${encodeURIComponent(c.link)}'>${esc(c.name)}</a> <small><a href='/raw?f=${encodeURIComponent(c.link)}'>raw</a></small></td></tr>`).join('');
    document.getElementById('stamp').textContent='updated '+new Date().toLocaleTimeString();
  }catch(e){document.getElementById('stamp').textContent='panel unreachable, retrying'}
}
tick(); setInterval(tick,2000);
</script>"""
    return page("live", body)


@app.get("/raw")
def raw(f: str):
    try:
        p = safe(f)
    except FileNotFoundError:
        return Response("not found", status_code=404)
    return Response(p.read_bytes(), media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="{p.name}"'})


def bind(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, port))
    sock.listen(128)
    sock.setblocking(False)
    return sock


if __name__ == "__main__":
    socks = []
    for port in PORTS:
        try:
            socks.append(bind(port))
        except OSError as e:
            print(f"{datetime.now():%H:%M:%S} panel: cannot listen on port {port} ({e}); skipping it", flush=True)
    if not socks:
        sys.exit("panel: no port could be bound")
    bound = [s.getsockname()[1] for s in socks]
    print(f"{datetime.now():%H:%M:%S} panel on {HOST} port(s) {', '.join(map(str, bound))}  logs={LOG_DIR}  repo={repo_url()}", flush=True)
    asyncio.run(uvicorn.Server(uvicorn.Config(app, log_level="warning")).serve(sockets=socks))
