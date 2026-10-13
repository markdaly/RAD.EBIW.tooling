---
event: IHE North America Connectathon 2026
dates: 2026-10-12 to 2026-10-16
kind: event-doc
expires: 2026-10-16
---
# Get started with TOOL_DDx

TOOL_DDx stands in for the **Encounter Manager** and the **Result Aggregator** in EBIW tests that
have no vendor in those roles. It is approved by the RAD Technical Project Manager and run by the
monitor. It accepts your message, logs every byte, and acknowledges. It does not grade: an **AA
ACK means received and logged, not conformant**. The monitor reads the content.

## 1. Tell the monitor first

On Zulip (ihe-catalyst.zulipchat.com) or at the table, give:

- the Gazelle **test instance** and your **system keyword**
- your **AE title** and modality (US, XC) for worklist tests
- for ITI-31 you receive (POCUS Simple Workflow step 10): your **ADT host:port and MSH-5/6**

The monitor sets you up and confirms. Check the **encounters** page: your AE title should be on
your rows before a worklist run.

## 2. Where to send

Use the **proxy** so Gazelle Message Capture holds your evidence. Direct is the fallback. No TLS.

| Transaction | Proxy | Direct | Put in the message |
|---|---|---|---|
| RAD-130 MWL C-FIND | `proxy.ihe-europe.net:11065` | `10.242.1.99:11112` | Called AE `ENC_MGR` |
| RAD-130 UPS-RS GET | `http://proxy.ihe-europe.net:11066/workitems` | `http://10.242.1.99:8042/workitems` | `ScheduledStationNameCodeSequence.CodeValue=<your AE>` and `ScheduledStationClassCodeSequence.CodeValue=XC` |
| RAD-132 ORU^R01 | `proxy.ihe-europe.net:11067` | `10.242.1.99:2575` | MSH-5/6 `SIMULATOR`/`SIMULATOR`, HL7 v2.5.1 |
| ITI-31 ADT | `proxy.ihe-europe.net:11064` | `10.242.1.99:2576` | MSH-5/6 `SIMULATOR`/`SIMULATOR`; PID-3 and PV1-19 required |

## 3. Patients (EBIW_10_Read_This_First)

The given name carries your partner identifier, e.g. `PEREZ^<id>`; the monitor tells you `<id>`.
Issuer of Patient ID `ENC_MGR`. Each patient has one procedure per modality under one admission.

| Patient | Patient ID | Admission ID | Department |
|---|---|---|---|
| PEREZ | EBIW001 | ADM001 | Emergency |
| PAGE | EBIW002 | ADM002 | Clinical Oncology |
| WAGNER | EBIW003 | ADM003 | Clinical Oncology |
| MAHAR | EBIW004 | ADM004 | Emergency |
| BERGER | EBIW005 | ADM005 | Clinical Oncology (plus one Radiology procedure) |
| UNIDENTIFIED^PATIENT | 0 | VISIT0002 | Emergency (EBIW_50/55; issuer `SITE_A`) |

The same admission and device always get the same Accession Number and Study Instance UID.

## 4. Your test, in one line

- **EBIW_POCUS_Simple_Workflow (13884):** the monitor sends you the step-10 ADT; your Modality
  queries the worklist (step 60, proxy 11065); your POCUS Manager sends the ORU (step 120, proxy 11067).
- **EBIW_20 MWL (13480) / EBIW_30 UPS-RS (13479):** run steps 100, 110, 120 and 200 against our
  Encounter Manager once your AE title is set. Expected: 110 returns PAGE, WAGNER, BERGER;
  120 (MAHAR + ADM004) returns 2; 200 (`PEREZ^<id>` + your modality) returns 1.
- **EBIW_25 (13357) / EBIW_35 (13478):** Modality queries our Encounter Manager, Image Manager
  sends RAD-132 to our Result Aggregator (proxy 11067).
- **EBIW_50 / EBIW_55:** query `UNIDENTIFIED^PATIENT` or Patient ID `0`.

## 5. Watch it arrive and attach the evidence

- **live** (top of every page): everything arriving, merged by time, every 2 seconds. Click a
  line to open the capture.
- **Logs** (front page): actor, then newest session, then your file. HL7 shows field by field.
- **download raw** gives the exact bytes. Attach it, with its ACK or responses, to the Gazelle
  step when the message did not go through the proxy.

## 6. Need a change?

Ask the monitor: AE title, partner identifier, issuer OID, port. Changes are made on the
monitor's machine (this panel is read-only from yours), take effect after a restart, and the
monitor confirms on Zulip. Then re-query.

Full details: [CONNECTIONS.md on GitHub](https://github.com/markdaly/RAD.EBIW.tooling/blob/main/events/2026-na-connectathon/docs/CONNECTIONS.md)
