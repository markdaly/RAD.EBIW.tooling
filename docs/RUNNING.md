# Running the tools

Every tool is one Python file with its full documentation in the docstring at the top. This page
is the overview: what each one answers, how to configure it, and where its evidence lands.

## All at once: `tools/floor.sh`

```bash
tools/floor.sh start            # tmux session "ihe": windows ra, em, ups, logs
tools/floor.sh status           # window state + which of the four ports listen
tools/floor.sh restart em       # respawn one server in place (ra | em | ups)
tools/floor.sh stop             # kill the session
tmux attach -t ihe              # watch; Ctrl-b d to detach
```

Windows keep their output when a server dies (`remain-on-exit`), so a crash stays readable until
you `restart` it. The `logs` window runs `tools/logwatch.sh result-aggregator`,
`tools/logwatch.sh encounter-manager` (follows new session folders after a restart) and
`tools/newfiles.sh` (newest raw captures with the time each was written, actor, kind and size, sized to the pane, plus state counts).

Set `PYTHON` to use a specific interpreter; otherwise `uv run --python '>=3.11'` provisions one.
Ports and names come from `.floor.env` at the repo root if it exists (gitignored; the panel writes
it): `RA_PORT`, `EM_PORT`, `ADT_PORT`, `UPS_PORT`, `AE_TITLE`, `ACCESSION_ISSUER`,
`ACCESSION_PREFIX`, `ENCOUNTERS`, `ACK_APP`, `ACK_FACILITY`, `PANEL_PORT`.

## The panel: `tools/panel.py`

`tools/floor.sh start` also starts the panel; `tools/floor.sh panel` starts it alone. It listens on
ports 80 and 8090 on all interfaces (`PANEL_PORT`, a comma list; a port that cannot be bound is
skipped; tmux session `ihe-panel`, independent of the servers so "stop all"
does not kill it). Read-only on the logs,
and a thin front end to `floor.sh` for control:

- Service status (tmux windows + which ports listen), start all / stop all / restart one.
- Config form that writes `.floor.env`; takes effect on the next start or restart.
- Encounters page: the rows the Encounter Manager serves, and the pre-run setup form (partner
  identifier for the EBIW_10 names, one AE title per modality, issuer OID) that rewrites the
  encounters file in place. Restart `em` and `ups` afterwards.
- Log index by actor and session; per-session file list with `summary.log`.
- **howto** (header link, `/howto`; the index has a "New here?" callout): vendor get-started page
  rendered from `events/<event>/docs/HOWTO.md` (newest event, or `PANEL_HOWTO=<path>`). Edit that
  Markdown, not the panel; a reload shows the change.
- **live** (header link, `/tail`): every actor's `summary.log` merged by time, newest at the
  bottom, refreshed every 2 s and following the end unless you scroll up; lines that name a
  capture link to it. Below it, the 25 newest captures with the time each was written.
- One capture rendered: HL7 as a field table with HL7 2.5.1 names and components split, DICOM
  query/response dumps and UPS-RS JSON as text. Prev/next (keys `j`/`k` or arrows), the related
  file (ACK for a message, responses for a query), and **download raw**, which is the exact bytes
  for a Gazelle attachment.
- Links to the repo and these docs in the header.

Anyone on the floor can read the log browser and download raw captures, every vendor's, at
http://<floor IP>/ (or :8090). Control actions (config, start/stop/restart, encounter edits) answer only
requests from the panel's own machine; others get 403. `PANEL_REMOTE_CONTROL=1` lifts that,
`PANEL_HOST=127.0.0.1` keeps the whole panel local. No authentication either way. The same HL7 rendering in the console:
`python3 tools/hl7show.py <file.hl7>` (`--raw`, `--next`, `--prev`).

## Result Aggregator: `tools/mllp_receiver.py`

Generic HL7 v2 receiver over MLLP. Accepts any message, writes it and the ACK raw, answers
`ACK^<trigger>^ACK` with `MSA|AA|<MSH-10>`, or `MSA|AR` if MSH will not parse. Nothing else is
validated. Use it as an EBIW Result Aggregator (RAD-132), an Order Filler sink, an ADT consumer.

| Env | Default | Meaning |
|---|---|---|
| `LISTEN_HOST` / `LISTEN_PORT` | `0.0.0.0` / `2575` | bind |
| `ACTOR` | `result-aggregator` | log folder name under `logs/` |
| `LOG_DIR` | `logs` | root of the log tree |
| `ACK_APP` / `ACK_FACILITY` | `SIMULATOR` / `SIMULATOR` | MSH-3/4 of the ACK; match what you registered in Gazelle |
| `TLS_CERT` + `TLS_KEY` | unset | both set: MLLPS (TLS 1.2+) |
| `TLS_CA` | unset | set: client certificate required (ATNA mutual TLS) |

Console line per message: MSH-9/12/10, segment counts, PID-3 (and PID-2 if someone still
uses it), PID-5, PV1-19, OBR-4/16/18/19/25/32/44, TQ1-9, first OBX-2/3/5/11, and the file name:
the fields the EBIW_90 scrutiny test reads. **AA means received and logged, never
"conformant"**; the monitor grades from the raw capture. Files: `<ts>-<n>-<MSH-9>.in.hl7` and `.ack.hl7`, plus `summary.log`.
Edge cases, as tested with the adversarial corpus (`samples/adversarial/`, driver
`tools/adversarial/adversarial_mllp.py`; isolated instances only): MSH-9 with no trigger gets
`ACK^^ACK` (always three components); empty MSH-10 gets `MSA|AA|` with MSA-2 empty; an
unparseable MSH gets `MSA|AR|` + ERR. Bytes outside an MLLP frame (no VT, no FS/CR) get no ACK,
are saved as-is when the connection closes and show as `WARN ... unframed bytes` in the summary.
10 MiB messages, two messages per connection, LF or CRLF segment ends, NUL bytes and 8
concurrent senders are all ACKed; captures are byte-exact, undeclared Latin-1 included.
ITI-31 intake: A01/A04/A08 add or update the encounter; A03 is ACKed and stored like the others
(the stand-in does not remove discharged encounters); no PV1-19 gets AR.

## Encounter Manager, DIMSE side: `tools/mwl_scp.py`

DICOM Modality Worklist C-FIND SCP implementing RAD-130 MWL semantics with the POCUS Option
return keys (RAD TF-2 Tables 4.130.4.1.2.1-1 and 4.130.4.1.2.1.1-1). Serves the encounters in a
JSON file, one row per procedure and device type (the Gazelle EBIW_10 model: a patient with a
US and an XC procedure under one admission is two rows, each with its own `modality`,
`scheduled_station_ae_title` and `procedure`; rows without them match any device and get the
generic "Perform Imaging" procedure allowed by 4.130.4.1.3). Modality and Scheduled Station AE
Title are matching keys when the row names them, echoed otherwise. One Accession Number and
Study Instance UID per (Admission ID, modality, station), kept across restarts (RAD TF-1
47.1.1.1). SPS start = now. Issuer sequences carry an OID as Universal Entity ID when
`issuer_oid` (file) or `ACCESSION_ISSUER_OID` (env) is set. Also takes ITI-31 ADT over MLLP and
adds the encounter (RAD TF-2x Appendix U mapping; PV1-3 point of care → department type code via
`department_codes` in the file). `samples/encounters.json` ships the EBIW_10 patient set; fill
the partner AE titles and the Gazelle OID before a graded run.

| Env | Default | Meaning |
|---|---|---|
| `AE_TITLE` / `LISTEN_PORT` | `ENC_MGR` / `11112` | DICOM SCP |
| `ADT_PORT` | `2576` | ITI-31 intake (MLLP); `0` disables |
| `ENCOUNTERS` | `samples/encounters.json` | encounter list; edit for the event's test patients |
| `ACCESSION_ISSUER` | `ENC_MGR` | Issuer of Accession Number (Local Namespace Entity ID) |
| `ACCESSION_PREFIX` | `EM` | prefix to avoid collisions with other issuers |
| `UID_ROOT` | pydicom root + suffix | Study UID root |
| `LOG_DIR` | `logs` | log tree; also where `state.json` and `encounters-from-adt.json` live |

Query keys supported: Patient's Name, Patient ID, Issuer of Patient ID, Institution Name,
Institutional Department Name and Type Code, Admission ID, Accession Number (single value),
SPS Start Date (range), Scheduled Performing Physician's Name. `*`/`?` wildcards, empty = all.
Files per query: `<ts>-<n>-<AE>.query.txt` and one `.respN.txt` per match.

Test it: `uv run --with pynetdicom --with pydicom python tools/mwl_find.py <host> <port> <AE> [PatientID] [AdmissionID]`
sends the EBIW required SCU keys as modality `US`, AE `MOD_TEST`, and prints every response.

## Encounter Manager, REST side: `tools/ups_rs.py`

The same encounters as a UPS-RS Search origin server (RAD-130 UPS-RS semantics, mapping Table
4.130.4.1.2.2-1) for Lightweight Modalities. `GET /workitems?...` and, for clients configured
with a DICOMweb root, the same at `/studies`. Response `application/dicom+json`, one UPS
instance per encounter; `204` when nothing matches. Accession, Issuer and Requested Procedure sit
inside Referenced Request Sequence (0040,A370); Study Instance UID there and at top level.

Shares `ENCOUNTERS`, `LOG_DIR`, `state.json` and `encounters-from-adt.json` with `mwl_scp.py`,
so a station gets the same accession over DIMSE and REST.

| Env | Default | Meaning |
|---|---|---|
| `LISTEN_PORT` | `8042` | HTTP |
| `BASE_PATH` | empty | prefix for every route |
| `ROUTES` | `/workitems,/studies` | paths that serve the search |
| `TLS_CERT` + `TLS_KEY` | unset | HTTPS |

Query keys: any DICOM keyword or 8-hex tag, dotted for sequences, e.g.
`ScheduledStationNameCodeSequence.CodeValue=<station>` (this is the station identity used for the
accession), `ScheduledStationClassCodeSequence.CodeValue=XC`, `AdmissionID=...`,
`ReferencedRequestSequence.AccessionNumber=...`, `ScheduledProcedureStepStartDateTime=a-b`.
Files per request: `<ts>-upsN-<station>.request.txt` and `.response.json` (or `.response.txt` for 204).

## Senders and probes

- `tools/smoke.sh`: starts the whole kit through `floor.sh` in its own tmux session, on spare ports
  and a temp log folder, and checks every listener and panel page once (22 checks). Safe beside a
  live kit. Run it on any new machine before the floor; CI runs it on Ubuntu 22.04 and 24.04.

- `tools/mllp_send.py <file.hl7> <host> <port>`: send one message, print the ACK. The bytes sent
  and the ACK are logged as `logs/result-aggregator/send-<date>/<ts>-out-<host>_<port>-<MSH-9>.out.hl7`
  and `.ack.hl7` with a `summary.log` line, failures included (`SEND_ACTOR`, `LOG_DIR` override).
  That pair is the sender-side evidence, e.g. EBIW_POCUS_Simple_Workflow step 10. Env `TLS_CA`, `TLS_CERT`/`TLS_KEY`, `TLS_SERVERNAME`,
  `TLS_INSECURE=1` for MLLPS.
- `tools/mwl_find.py`: see above.
- `samples/`: `ORU_R01_RAD-132_POCUS.hl7` (RAD-132 with the POCUS Option fields),
  `ADT_A04_ITI-31.hl7` (ITI-31 admit for the sample patient), `encounters.json`.
  All synthetic. The department and procedure codes are placeholders until the event's code set
  is loaded.

## Through a Gazelle proxy

Register one configuration per listener in Gazelle Test Management (HL7 v2 responder for 2575
and 2576, DICOM SCP for 11112, webservice for 8042). Gazelle assigns a proxy port per
configuration; vendors target the proxy host and that port. Connections then arrive from the
proxy's IP, which is why the UPS-RS station identity comes from the query parameter and not from
the peer address. The proxy's Message Capture holds the evidence; `logs/` is the backup copy.

## Reading the evidence

`summary.log` in each session folder is the timeline. For a vendor's Gazelle attachment, hand
over the raw `.in.hl7` with its `.ack.hl7`, or the `.query.txt` with its `.respN.txt`, or the
`.request.txt` with its `.response.json`. Never edit them.
