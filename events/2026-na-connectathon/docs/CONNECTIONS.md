---
event: IHE North America Connectathon 2026
dates: 2026-10-12 to 2026-10-16
kind: event-doc
expires: 2026-10-16
---
# Floor connections (NA 2026, EBIW), as of Oct 12 16:20 ET

The monitor's Mac = **10.242.1.184**, Gazelle hostname **ddx0** (`ddx0.na2026.net`), organization DDx, system
**TOOL_DDx** (Encounter Manager + Result Aggregator). Gazelle configurations approved and proxy
ports assigned 16:40 ET (Gazelle TM → Configurations, org DDx).
Tests: 13478 EBIW_35_Full_Workflow-RESTful (ticket 003), 13884 EBIW_POCUS_Simple_Workflow (ticket 004).
Proxy: `proxy.ihe-europe.net` = 192.168.2.5. **Vendors target the proxy port below, not the Mac.**

## Gazelle configurations for TOOL_DDx (what vendors see) and proxy ports

| Gazelle type | Actor | Host / IP | Real port | **Proxy port** | Details (as registered) |
|---|---|---|---|---|---|
| HL7 V2 Responder | ENCOUNTER_MGR | ddx0 / 10.242.1.184 | 2576 | **11064** | receiving app/facility `SIMULATOR / SIMULATOR` (ITI-31 in) |
| Dicom SCP | ENCOUNTER_MGR | ddx0 / 10.242.1.184 | 11112 | **11065** | AE `ENC_MGR`, MWL |
| Webservice | ENCOUNTER_MGR | ddx0 / 10.242.1.184 | 8042 | **11066** | RAD-130 (UPS-RS), URL `http://ddx0:8042/studies`, HTTP rewrite disabled |
| HL7 V2 Responder | RESULT_AGGREGATOR | ddx0 / 10.242.1.184 | 2575 | **11067** | receiving app/facility `SIMULATOR / SIMULATOR` (RAD-132 in) |

**Status 16:50 ET: the proxy accepts TCP on all four ports but closes immediately and forwards nothing (ticket 005). Until fixed, vendors hit the Mac directly and attach captures.** All four approved, none secured (plain MLLP / DICOM / HTTP). Vendor-side targets once the proxy works:
- RAD-132 ORU → `proxy.ihe-europe.net:11067`, MSH-5/6 = `SIMULATOR`/`SIMULATOR`
- ITI-31 ADT → `proxy.ihe-europe.net:11064` (our own step-10 send goes there too, so it is captured)
- RAD-130 MWL → `proxy.ihe-europe.net:11065`, called AE `ENC_MGR`
- RAD-130 UPS-RS → `http://proxy.ihe-europe.net:11066/studies?...`
Our ACKs and the ITI-31 sample carry MSH-3/4 = `SIMULATOR`/`SIMULATOR` to match the registration.

## Listeners on the Mac (stand-ins)

| Port | Proto | Transaction | Role here | Who connects | Tool / tab | Status |
|---|---|---|---|---|---|---|
| 2575 | HL7 v2 MLLP | RAD-132 ORU^R01 in, ACK out | Result Aggregator | POCUS Manager 10.242.1.9 (test 13884 step 120); Image Manager (13478 step 50) | `tools/mllp_receiver.py`, the monitor's shell | up since 14:56; 1 ORU received 15:07 (connectivity only) |
| 2576 | HL7 v2 MLLP | ITI-31 ADT in, ACK out | Encounter Manager (grouped in POCUS_MGR, 13884 step 10) | the monitor's own `mllp_send.py`; vendor ADT feeds if any | `tools/mwl_scp.py` (ADT thread), tab "MWL 11112 + ADT 2576" | up since 16:15 |
| 11112 | DICOM MWL C-FIND, AE `ENC_MGR` | RAD-130 MWL semantics (POCUS Option keys) | Encounter Manager | POCUS Manager box 10.242.1.17 (13884 step 60); any Acquisition Modality | `tools/mwl_scp.py`, same tab | up since 16:15; no queries yet |
| 8042 | HTTP, `GET /workitems` | RAD-130 UPS-RS semantics, dicom+json | Encounter Manager | Lightweight Modality = VNA 10.242.1.11 (13478 step 20), once their UPS-RS client exists | `tools/ups_rs.py`, tab "UPS-RS 8042" | up since 16:07; no queries yet |

## Outbound from the Mac

| Target | Proto | Transaction | Test step | Command |
|---|---|---|---|---|
| Encounter Manager stand-in via proxy `proxy.ihe-europe.net:11064` (and the vendor POCUS Manager if it accepts ADT) | MLLP | ITI-31 ADT^A04 | 13884 step 10 | `uv run python tools/mllp_send.py samples/ADT_A04_ITI-31.hl7 proxy.ihe-europe.net 11064` |
| Any vendor Encounter Manager | DICOM C-FIND | RAD-130 check | ad hoc | `uv run --with pynetdicom --with pydicom python tools/mwl_find.py <host> <port> <AE> [PatientID] [AdmissionID]` |

## Vendor endpoints (one VNA vendor, two systems)

| System | IP | AE / port | Gazelle roles | Transactions with the Mac |
|---|---|---|---|---|
| POCUS Manager box ("sync") | 10.242.1.17 | not yet given | POCUS_MGR-EBIW, IM-EBIW | RAD-130 → 11112 (step 60); RAD-132 → 2575 (step 120); maybe ITI-31 ← 2576 sender |
| VNA | 10.242.1.11 | `SYNVNA` : 4000 | Lightweight Modality (MOD-EBIW in 13478), IM-EBIW | RAD-130 UPS-RS → 8042 (13478 step 20); RAD-132 → 2575 (13478 step 50). C-ECHO from `ENC_MGR` rejected (calling AE not whitelisted), which is fine |
| Other POCUS Manager (ORU at 15:07) | 10.242.1.9 | n/a | POCUS_MGR-EBIW, ENCOUNTER_MGR (declines to act as EM) | RAD-132 → 2575 only |

## Through the proxy
The Mac sees connections from 192.168.2.5, so the UPS-RS station identity must come from the
query parameter (it does) and the MLLP peer in `summary.log` will be the proxy. Evidence lives in
Message Capture (https://connectathon.ihe-catalyst.net/gazelle/message-capture/messages); local
`logs/` is the backup copy.

## Not reachable from here (off-floor paths checked Oct 12)
GSS syslog collector 3102/3202 timed out from this Mac; GSS TLS simulators at 151.80.220.161 are reachable.

## Watching it all
`tools/floor.sh start` runs the three servers and a `logs` window (Result Aggregator summary,
Encounter Manager summary, newest raw captures) in tmux session `ihe`; `tmux attach -t ihe`.
`tools/floor.sh status` lists windows and which of 2575/2576/8042/11112 are listening;
`tools/floor.sh restart <ra|em|ups>` respawns one. Details: `docs/RUNNING.md` at the repo root.
