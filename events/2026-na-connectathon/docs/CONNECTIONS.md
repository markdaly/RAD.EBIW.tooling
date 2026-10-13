---
event: IHE North America Connectathon 2026
dates: 2026-10-12 to 2026-10-16
kind: event-doc
expires: 2026-10-16
---
# Connecting to TOOL_DDx: EBIW stand-ins at NA 2026

*As of Tue Oct 13, 10:40 ET. All four proxy channels forward; direct connections also work.*

**Short version, one URL:** http://10.242.1.99/ (or http://ddx0.na2026.net/), then **howto**.
The same panel shows your captures live. This page is the full reference.

TOOL_DDx is a monitor-run partner substitute, approved by the RAD Technical Project Manager, for
EBIW tests that have no vendor in one of the roles. It plays the **Result Aggregator** (receives
RAD-132 ORU) and the **Encounter Manager** (worklist over DICOM MWL and UPS-RS, plus an ITI-31
ADT intake). It accepts, logs every byte, and acknowledges. It does not grade, auto-pass, or
change your messages; the monitor reads the captures against the Technical Framework.

Gazelle: organization DDx, system **TOOL_DDx**, host **ddx0** = **10.242.1.99** (static).
Gazelle Proxy: `proxy.ihe-europe.net` = 192.168.2.5. Support: ask the monitor on Zulip
(ihe-catalyst.zulipchat.com) or at the table.

## 1. Where to send

**Use the proxy port.** Gazelle Message Capture then holds the evidence for your test steps.
Direct is the fallback if the proxy misbehaves; attach the panel's raw files in that case.
No TLS on any of these.

| You are | Transaction | Send to (proxy) | Direct fallback | What to put in the message / association |
|---|---|---|---|---|
| Acquisition Modality, POCUS app | RAD-130 MWL C-FIND | `proxy.ihe-europe.net:11065` | `10.242.1.99:11112` | Called AE `ENC_MGR`; calling AE = your registered AE title (tell the monitor) |
| Lightweight Modality | RAD-130 UPS-RS `GET` | `http://proxy.ihe-europe.net:11066/workitems?...` | `http://10.242.1.99:8042/workitems?...` | Also served at `/studies` (as registered). **Send your AE title** as `ScheduledStationNameCodeSequence.CodeValue` or `.CodeMeaning`: through the proxy we cannot see your IP. **Send your modality** as `ScheduledStationClassCodeSequence.CodeValue=XC` to get only your procedures; without it every modality's rows for the patient come back |
| POCUS Manager, Image Manager | RAD-132 ORU^R01 | `proxy.ihe-europe.net:11067` | `10.242.1.99:2575` | MSH-5/6 `SIMULATOR`/`SIMULATOR`; HL7 v2.5.1, original-mode ACK |
| Anyone feeding our Encounter Manager | ITI-31 ADT | `proxy.ihe-europe.net:11064` | `10.242.1.99:2576` | MSH-5/6 `SIMULATOR`/`SIMULATOR`; PID-3 and PV1-19 (Admission ID) required |

**An AA ACK means "received and logged", not "conformant".** The monitor reads the content.

## 2. The panel: see exactly what arrived

Open **http://10.242.1.99/** from any floor device. `http://ddx0.na2026.net/` works where the
floor DNS is used (a tablet or phone may hold a stale cached address); port 8090 works too. The amber **READ-ONLY VIEW** banner is expected: you can browse and download,
but only the monitor's machine can change anything.

- **live** (header): everything arriving, all actors merged by time, refreshed every 2 s.
  Send your message and watch it land; click the line to open the capture.
- **encounters** (header): the worklist rows the Encounter Manager serves, with the AE title
  and procedure per row. Check here that your AE title is set before a worklist run.

To find and attach a capture:

1. Under **Logs**, pick the actor (`result-aggregator` for ORU and ACKs, `encounter-manager` for
   MWL, UPS-RS and ADT) and the newest session folder.
2. Click your file: HL7 shows as a field table with HL7 2.5.1 field names, DICOM queries and
   responses as dumps, UPS-RS as JSON. `related` links the ACK or the responses; `j`/`k` step
   through files.
3. **download raw** gives the exact bytes. Attach that file (plus its ACK or responses) to the
   Gazelle test step when the message did not go through the proxy.

The partner on the other side of a test sees the same files; that is the point.

## 3. Test walkthroughs

### Before any run (every test)
1. Tell the monitor the **Gazelle test instance** and your **system keyword**.
2. Give what the stand-in must know about you: your **AE title** and modality (US, XC) for
   worklist tests; for ITI-31 you receive, your **ADT listener host:port and MSH-5/6**.
3. The monitor loads that into the Encounter Manager (section 4) and confirms on Zulip.
4. Patients are the **EBIW_10_Read_This_First** set. Names carry a partner identifier in the given
   name, `PEREZ^<id>`; the monitor tells you the `<id>`. Issuer of Patient ID `ENC_MGR`
   (`SITE_A` for the unidentified patient).

| Patient | Patient ID | Admission ID | Department | Procedures (one per modality) |
|---|---|---|---|---|
| PEREZ^<id> | EBIW001 | ADM001 | Connectathon Emergency Department | US, XC |
| PAGE^<id> | EBIW002 | ADM002 | Connectathon Clinical Oncology Department | US, XC |
| WAGNER^<id> | EBIW003 | ADM003 | Connectathon Clinical Oncology Department | US, XC |
| MAHAR^<id> | EBIW004 | ADM004 | Connectathon Emergency Department | US, XC |
| BERGER^<id> | EBIW005 | ADM005 | Clinical Oncology (US, XC); Radiology (other modality) | US, XC, CR |
| UNIDENTIFIED^PATIENT | 0 | VISIT0002 | Connectathon Emergency Department | any (EBIW_50/55) |

The same admission and device always get the **same Accession Number and Study Instance UID**,
over MWL and UPS-RS alike, across restarts (RAD TF-1 47.1.1.1).

### EBIW_POCUS_Simple_Workflow (Gazelle 13884)
Roles: RESULT_AGGREGATOR = TOOL_DDx; POCUS_MGR, MOD, IM = vendors. If your POCUS Manager does
not serve the worklist itself, TOOL_DDx's Encounter Manager answers step 60 on its behalf.

1. **Step 10, ITI-31 (TOOL_DDx starts it).** Agree a patient with the monitor and give your
   ADT listener host:port and MSH-5/6. The monitor sends ADT^A04 to your POCUS Manager and,
   when our Encounter Manager serves the worklist, to it as well. Confirm it arrived; your ACK
   goes back to us.
2. **Steps 20-50** are not transactions: screenshots or log lines in the instance.
3. **Step 60, MWL.** The Modality queries the worklist: proxy 11065, called AE `ENC_MGR` (or your
   own POCUS Manager if it serves MWL). Query by the agreed patient.
4. **Steps 70-110** happen on your side: acquire, store to your POCUS Manager (step 80, not to
   us), worksheet, sign.
5. **Step 120, RAD-132.** The POCUS Manager sends the ORU to proxy 11067. The monitor reads it
   against RAD TF-2 4.132.4.1.2-1 through 4.132.4.1.2.3.4.
6. **Step 130** goes to your Image Manager. **Steps 150-160** are the monitor's, noted in the
   instance.

### EBIW_20 MWL (13480) and EBIW_30 UPS-RS (13479): your Modality, our Encounter Manager
1. Before the run, the monitor sets your partner identifier and AE title. The match counts
   below hold only after that: until your AE title is set, rows match any device.
2. Run the Gazelle queries. Expected matches per Gazelle:
   step 100 Patient ID + Issuer; step 110 Clinical Oncology + your AE title (PAGE, WAGNER,
   BERGER); step 120 MAHAR + ADM004 (2: US and XC); step 200 `PEREZ^<id>` + modality
   (US for MWL, XC for UPS-RS: 1).
3. Steps 210-220: acquire and store to the Image Manager (a vendor, not us).

### EBIW_25 DIMSE (13357) and EBIW_35 RESTful (13478) full workflow
The Modality queries our Encounter Manager (MWL 11065, or UPS-RS 11066 for EBIW_35), stores to
the Image Manager, and the Image Manager sends RAD-132 to our Result Aggregator (proxy 11067).

### EBIW_50 / EBIW_55, unidentified patient
TOOL_DDx serves one pre-registered unidentified encounter: `UNIDENTIFIED^PATIENT`, Patient ID
`0`, Admission ID `VISIT0002`. Query by name or Patient ID. The monitor posts the Encounter
Manager's step-20 description in the test instance chat.

## 4. Changing the configuration (monitor only, on ddx0)

Configuration changes are made **on the monitor's Mac** (green **ADMIN** banner in the panel).
From any other machine the panel refuses changes (HTTP 403), so vendors ask the monitor.

1. Vendor asks on Zulip or at the table: new AE title, partner identifier, issuer OID, port.
2. Monitor opens http://127.0.0.1/ on ddx0:
   - **Encounters** page: partner identifier, AE title per modality, issuer OID. Save.
   - **Config** form on the index page: ports, AE title, ACK MSH-3/4. Save.
3. **Restart what reads it**, from the index page. A change does nothing until that restart.

   | Changed | Restart |
   |---|---|
   | Encounters page (partner identifier, AE titles, issuer OID) | `em` and `ups` |
   | Result Aggregator port, ACK MSH-3/4 | `ra` |
   | Encounter Manager DICOM or ITI-31 port, its AE title | `em` |
   | UPS-RS port | `ups` |
   | Issuer of Accession Number, accession prefix, encounters file | `em` and `ups` |
4. Monitor confirms on Zulip; vendor re-queries.

Restarts keep accessions already handed out: the per-admission state lives in a file. Proxy
channels and Gazelle configurations do not change unless a port changes; a port change also
needs the Gazelle configuration updated and the proxy channel re-checked.

## Listeners on the Mac (stand-ins)

| Port | Proto | Transaction | Role here | Who connects | Tool / tab | Status |
|---|---|---|---|---|---|---|
| 2575 | HL7 v2 MLLP | RAD-132 ORU^R01 in, ACK out | Result Aggregator | POCUS Manager 10.242.1.9 (test 13884 step 120); Image Manager (13478 step 50) | `tools/mllp_receiver.py`, tmux window `ra` | live; direct ORU 10:10 Tue (connectivity), proxy ORU 10:25 Tue |
| 2576 | HL7 v2 MLLP | ITI-31 ADT in, ACK out | Encounter Manager (grouped in POCUS_MGR, 13884 step 10) | the monitor's own `mllp_send.py`; vendor ADT feeds if any | `tools/mwl_scp.py` (ADT thread), tmux window `em` | live |
| 11112 | DICOM MWL C-FIND, AE `ENC_MGR` | RAD-130 MWL semantics (POCUS Option keys) | Encounter Manager | POCUS Manager box 10.242.1.17 (13884 step 60); any Acquisition Modality | `tools/mwl_scp.py`, tmux window `em` | live; proxy C-ECHO 10:36 Tue |
| 8042 | HTTP, `GET /workitems` | RAD-130 UPS-RS semantics, dicom+json | Encounter Manager | Lightweight Modality = VNA 10.242.1.11 (13478 step 20), once their UPS-RS client exists | `tools/ups_rs.py`, tmux window `ups` | live; proxy probe 10:36 Tue |

## Outbound from the Mac

| Target | Proto | Transaction | Test step | Command |
|---|---|---|---|---|
| The vendor's POCUS Manager (their ADT listener); also our own Encounter Manager (proxy 11064) when it serves the MWL | MLLP | ITI-31 ADT^A04 | 13884 step 10 | copy `samples/ADT_A04_ITI-31_EBIW10.hl7`, set MSH-5/6 to the receiver's values, then `uv run python tools/mllp_send.py <copy> <their host> <their port>`; logged under `logs/result-aggregator/send-<date>/` |
| Any vendor Encounter Manager | DICOM C-FIND | RAD-130 check | ad hoc | `uv run --with pynetdicom --with pydicom python tools/mwl_find.py <host> <port> <AE> [PatientID] [AdmissionID]` |

## Vendor endpoints (one VNA vendor, two systems)

| System | IP | AE / port | Gazelle roles | Transactions with the Mac |
|---|---|---|---|---|
| POCUS Manager box | 10.242.1.17 | not yet given | POCUS_MGR-EBIW, IM-EBIW | RAD-130 → 11112 (step 60); RAD-132 → 2575 (step 120); maybe ITI-31 ← 2576 sender |
| VNA | 10.242.1.11 | `SYNVNA` : 4000 | Lightweight Modality (MOD-EBIW in 13478), IM-EBIW | RAD-130 UPS-RS → 8042 (13478 step 20); RAD-132 → 2575 (13478 step 50). C-ECHO from `ENC_MGR` rejected (calling AE not whitelisted), which is fine |
| Other POCUS Manager (ORU at 15:07) | 10.242.1.9 | n/a | POCUS_MGR-EBIW, ENCOUNTER_MGR (declines to act as EM) | RAD-132 → 2575 only |

## Through the proxy (working since Tue 10:25 ET)
The Mac sees connections from 192.168.2.5, so the UPS-RS station identity must come from the
query parameter (it does) and the MLLP peer in `summary.log` will be the proxy. Evidence lives in
Message Capture (https://connectathon.ihe-catalyst.net/gazelle/message-capture/messages); local
`logs/` is the backup copy.

## Not reachable from here (off-floor paths checked Oct 12)
GSS syslog collector 3102/3202 timed out from this Mac; GSS TLS simulators at 151.80.220.161 are reachable.

## Watching it all
`tools/floor.sh start` runs the three servers, the panel and a `logs` window (Result Aggregator summary,
Encounter Manager summary, newest raw captures) in tmux session `ihe`; `tmux attach -t ihe`.
`tools/floor.sh status` lists windows and which of 2575/2576/8042/11112 are listening;
`tools/floor.sh restart <ra|em|ups>` respawns one. Details: `docs/RUNNING.md` at the repo root.
