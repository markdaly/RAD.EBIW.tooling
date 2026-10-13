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
`tools/newfiles.sh` (newest raw captures plus state counts).

Set `PYTHON` to use a specific interpreter; otherwise `uv run --python '>=3.11'` provisions one.

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

Console line per message: MSH-9/10/12, PID-3, PID-5, PV1-19, OBR-4/18/19/25, first OBX-5, and the
file name. Files: `<ts>-<n>-<MSH-9>.in.hl7` and `.ack.hl7`, plus `summary.log`.

## Encounter Manager, DIMSE side: `tools/mwl_scp.py`

DICOM Modality Worklist C-FIND SCP implementing RAD-130 MWL semantics with the POCUS Option
return keys (RAD TF-2 Tables 4.130.4.1.2.1-1 and 4.130.4.1.2.1.1-1). Serves the encounters in a
JSON file; generates one Accession Number and Study Instance UID per (Admission ID, calling AE
title) and keeps returning the same pair (RAD TF-1 47.1.1.1); echoes Scheduled Station AE Title
and Modality; SPS start = now; generic "Perform Imaging" procedure (4.130.4.1.3). Also takes
ITI-31 ADT over MLLP and adds the encounter (RAD TF-2x Appendix U mapping).

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

- `tools/mllp_send.py <file.hl7> <host> <port>`: send one message, print the ACK, save it next to
  the input as `<file>.ack.hl7`. Env `TLS_CA`, `TLS_CERT`/`TLS_KEY`, `TLS_SERVERNAME`,
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
