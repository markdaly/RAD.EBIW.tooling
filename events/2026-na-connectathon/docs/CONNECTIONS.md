# Floor connections (NA 2026, EBIW), as of Oct 12 16:20 ET

the monitor's Mac = **10.242.1.184** (Gazelle SUT "DDX": Encounter Manager + Result Aggregator).
Tests: 13478 EBIW_35_Full_Workflow-RESTful (ticket 003), 13884 EBIW_POCUS_Simple_Workflow (ticket 004).
Proxy: `proxy.ihe-europe.net` = 192.168.2.5; proxy ports assigned per configuration in Gazelle TM
(not yet created). Until then vendors hit the Mac directly.

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
| Encounter Manager stand-in 10.242.1.184:2576 (and the vendor POCUS Manager if it accepts ADT) | MLLP | ITI-31 ADT^A04 | 13884 step 10 | `uv run python tools/mllp_send.py samples/ADT_A04_ITI-31.hl7 10.242.1.184 2576` |
| Any vendor Encounter Manager | DICOM C-FIND | RAD-130 check | ad hoc | `uv run --with pynetdicom --with pydicom python tools/mwl_find.py <host> <port> <AE> [PatientID] [AdmissionID]` |

## Vendor endpoints (one VNA vendor, two systems)

| System | IP | AE / port | Gazelle roles | Transactions with the Mac |
|---|---|---|---|---|
| POCUS Manager box ("sync") | 10.242.1.17 | not yet given | POCUS_MGR-EBIW, IM-EBIW | RAD-130 → 11112 (step 60); RAD-132 → 2575 (step 120); maybe ITI-31 ← 2576 sender |
| VNA | 10.242.1.11 | `SYNVNA` : 4000 | Lightweight Modality (MOD-EBIW in 13478), IM-EBIW | RAD-130 UPS-RS → 8042 (13478 step 20); RAD-132 → 2575 (13478 step 50). C-ECHO from `ENC_MGR` rejected (calling AE not whitelisted), which is fine |
| Other POCUS Manager (ORU at 15:07) | 10.242.1.9 | n/a | POCUS_MGR-EBIW, ENCOUNTER_MGR (declines to act as EM) | RAD-132 → 2575 only |

## Proxy channels to create in Gazelle TM (system configurations → proxy)

| Config type | Host | Port | For |
|---|---|---|---|
| HL7 v2 responder | 10.242.1.184 | 2575 | RAD-132 to Result Aggregator |
| HL7 v2 responder | 10.242.1.184 | 2576 | ITI-31 to Encounter Manager |
| HTTP / DICOMweb responder | 10.242.1.184 | 8042 | RAD-130 UPS-RS |
| DICOM SCP, AE `ENC_MGR` | 10.242.1.184 | 11112 | RAD-130 MWL |

Once channels exist: vendors target `proxy host:assigned port`; the Mac then sees connections
from 192.168.2.5, and Message Capture (https://connectathon.ihe-catalyst.net/gazelle/message-capture/messages)
holds the evidence. Local `logs/` stays the backup.

## Not reachable from here (off-floor paths checked Oct 12)
GSS syslog collector 3102/3202 timed out from this Mac; GSS TLS simulators at 151.80.220.161 are reachable.
