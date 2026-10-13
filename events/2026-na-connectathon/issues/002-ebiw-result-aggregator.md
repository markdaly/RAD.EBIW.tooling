---
event: IHE North America Connectathon 2026
dates: 2026-10-12 to 2026-10-16
kind: issue
opened: 2026-10-12
status: needs-evidence
expires: 2026-10-16
---
# EBIW POCUS: no Result Aggregator on the floor; stand-in needed for RAD-132

- **Source:** RAD TPM asked the monitor to build the Result Aggregator stand-in (floor, Oct 12). No Zulip thread yet.
- **Opened:** 2026-10-12 ~13:30 ET
- **Status:** needs-evidence (first message received 15:07 ET; 8 blocking findings sent back)
- **Domain / profile / actor / transaction:** RAD EBIW (TI rev 3.1, 2025-06-19) / Result
  Aggregator, POCUS Option / RAD-132 Notify of Imaging Results

## Symptom
- A POCUS Manager wants to test EBIW with the POCUS Option. RAD-132 requires a Result
  Aggregator as the receiver, and no participant is registered for that actor this week.
- The vendor offered to stand up Mirth as the receiver. That would make them their own test
  partner, and Mirth counts as one of the two allowed intermediates.

## What a Result Aggregator is (RAD TF-1: 47.1.1.4, RAD TF-2: 4.132)
- "Receives notifications about newly acquired and stored images and reports from
  encounter-based procedures. Typically a component of, or a proxy for, an EMR." (47.1.1.4)
- Receiver role of RAD-132, an HL7 v2.5.1 **ORU^R01** over MLLP (4.132.4.1.2). Segments:
  MSH, PID, PV1, [ORC], OBR, TQ1, OBX (Study Instance UID), [{OBX}] findings.
- Expected actions (4.132.4.1.3): "accept and process the message"; must accept multiple
  messages for the same Study Instance UID. POCUS Option (4.132.4.1.3.1): link the OBX
  report to the encounter in PV1-19. Nothing else is testable on the wire.
- Reply: Acknowledge Imaging Result "as described in 4.128.4.2", which lives in the RD
  supplement rev 1.2 (RAD TF-2 only holds a placeholder): HL7 v2.5.1 original-mode ACK
  (RAD TF-2 2.4.1.2), `MSH-9 = ACK^R01^ACK` (three components, 2.4.4.2), `MSA-1 = AA|AE|AR`,
  `MSA-2 = MSH-10` of the ORU (2.4.4.3). Verified overnight: `research/from-memory-claims.md` (a).
- What the Sender must put in the ORU under the POCUS Option (4.132.4.1.2.3), the parts a
  monitor reads off the captured message:
  - PV1-19 Visit Number **R**, = Admission ID (0038,0010) from the images.
  - ORC optional; if present ORC-1 = `RE`, ORC-12 Physician of Record (NPI in the US).
  - OBR-4 **R**, procedure code from the worksheet, first three components valued
    (LOINC RadLex Playbook recommended); CPT may ride in OBR-4.4–4.6. OBR may repeat for
    eFAST-style multi-procedure sessions, each with a distinct OBR-4.
  - OBR-7 observation date/time R; OBR-16 Ordering Provider **R** (Physician of Record);
    OBR-18 = Accession Number (0008,0050) R; OBR-19 = Issuer of Accession Number R2;
    OBR-24 Diagnostic Serv Sect ID R; OBR-25 Result Status R (`R`, `F`, `C`, never `P`);
    OBR-27.6 = TQ1-9.1; OBR-32 Principal Result Interpreter **R** (Physician of Record);
    OBR-33 may name a POCUS Learner; OBR-44 = OBR-4.
  - TQ1 may be empty; `R^Routine^HL70078` typical.
  - Finding OBX **shall** be sent for POCUS reports; OBX-2 = `CE` or `TX`; one finding per
    OBX; OBX-11 = `R|F|C`.
  - No RAD-132 for training studies (4.132.4.1.1.1). One notification per study when the
    completeness criteria are met; addenda may trigger another.

## Gazelle test context (added 16:20 ET)
EBIW_35_Full_Workflow-RESTful (id 13478, Gazelle) step 50/55: IM-EBIW → RESULT_AGGREGATOR-EBIW
ORU^R01, ACK AA with MSA-2 = MSH-10. Monitor checks at the Aggregator: PID-3 with assigning
authority, PID-5, OBR-18 with assigning authority, OBX-5 Study UID, OBR-4, all matching the
worklist the EM served. The monitor's Gazelle system (DDX) is the registered Result Aggregator, so
the proxy channel for port 2575 comes from that system's configuration.

## Scope
One POCUS Manager vendor now; any EBIW Image Manager or POCUS Manager that needs a RAD-132
partner this week.

## Evidence so far
- Supplement text extracted from https://www.ihe.net/uploadedFiles/Documents/Radiology/IHE_RAD_Suppl_EBIW.pdf
  (rev 3.1, 132 pages), sections quoted above.

### First live message, 2026-10-12 15:07:57 ET (file `logs/result-aggregator/20261012-145646/20261012-150757-0001-ORU_R01.in.hl7`, ACKed AA)
A connectivity probe at 15:05:52 (connect/close, no bytes) preceded it. The ORU parsed and was
ACKed, so transport is done. Content read against RAD TF-2 4.132 (POCUS Option), monitor view:

**Blocking (the message is not a RAD-132 as sent)**
1. **MSH-12 = `2.4`.** Must be `2.5.1` (4.132.3, 4.132.4.1.2). Floor-wide nudge, same as everyone.
2. **MSH-9 = `ORU^R01`**, no message-structure component. Must be `ORU^R01^ORU_R01`:
   RAD TF-2 2.4.4.2 ("all three components are required") and RD 4.128.4.1.2.2 (verified
   overnight, `research/from-memory-claims.md` (c)).
3. **Patient ID in PID-2 (retired), PID-3 empty.** RAD-128 PID requires PID-3 CX with an
   assigning authority (PID-3.4). Nothing downstream can match the patient.
4. **OBR-18 Accession Number empty** (R). Without it the Result Aggregator cannot tie the
   report to the stored images. OBR-19 Issuer empty too (R2, fill if the images carry 0008,0051).
5. **No Study Instance UID OBX** (`OBX|n|ST|113014^DICOM Study^DCM||<UID>||||||O`, OBX-2 ST,
   OBX-11 O per RD 4.128.4.1.2.8, verified), which the message table requires unbracketed.
   Needed for the RAD-106 link in 4.132.4.1.3.1.
6. **OBR-16 Ordering Provider and OBR-32 Principal Result Interpreter empty.** Both are R
   under the POCUS Option (Physician of Record, NPI in the US). ORC is absent, which is fine,
   but then OBR-16 has to carry it.
7. **OBX-11 Observation Result Status empty** on all three OBX (R: `R`, `F`, `C`).
8. **OBX-5 says `Exam category: educational`.** 4.132.4.1.1.1: the POCUS Manager shall not
   send RAD-132 for training studies. Ask what "educational" means in their model. If it is
   the training flag, this message should not exist; if it is a worksheet category, fine.

**Should fix**
9. OBR-4 coding: `POCUS^POCUS^Point of Care Ultrasound` puts a description in 4.3 where the
   coding system belongs. Local codes are allowed but 4.3 should name the scheme (e.g.
   `99GEVP` or `L`); LOINC RadLex Playbook recommended. The eFAST code that the worksheet
   actually used sits only in a Z-segment (ZED-1) and in OBX-3; per 4.132.4.1.2.3.3 it belongs
   in OBR-4.
10. Procedure code repeated in **OBR-47** (Filler Supplemental Service Info) instead of
    **OBR-44** Procedure Code, which "shall match OBR-4". Off by three fields.
11. **OBR-24 Diagnostic Serv Sect ID empty** (R; `US` or whatever 0008,1041 maps to).
12. **TQ1 segment absent** and OBR-27 empty. TQ1 is required in the table (may be empty);
    OBR-27.6 must match TQ1-9.1 if valued.
13. Second OBR group (Quality Assurance) has **OBR-1 = 1** again; Set ID should be 2. Also
    QA is not an imaging procedure; repeating OBR is for multiple procedures in one session
    (eFAST example in the text), each with a distinct OBR-4. Ask whether QA belongs in RAD-132.
14. **OBX-2 = `ST`** with `\.br\` formatting and >199 chars. Table 4.132.4.1.2.3.4-1 allows
    `CE` or `TX`; ST is capped at 199 in v2.5.1. Use TX (or FT if they insist on escapes).
15. Several findings bundled in one OBX (eFAST indication, views, findings). Text says one
    finding per OBX is recommended, not required. Mention, don't fail.

**Fine as sent:** PV1-19 valued (`V0005`); OBR-7 observation time; OBR-25 = `F`; MSH-18
`UNICODE UTF-8`; Z-segment is permitted. Verify PV1-19 equals Admission ID (0038,0010) in the
stored images when the Image Manager side is checked.

Suggested validator: paste the capture into Gazelle EVSClient HL7v2 validation if a RAD-132
profile exists there; otherwise this list is the review.

## Hypotheses (ranked)
Not a defect ticket. The question is who plays the Result Aggregator:
1. **Monitor-run stand-in** (`tools/mllp_receiver.py`): neutral, logs every message raw with
   the ACK, one file. Vendor attaches the capture to the Gazelle test instance, monitor
   validates the ORU content against 4.132 by reading it (or via the Gazelle HL7 validator).
2. **Vendor-run Mirth**: works technically, but the sender and receiver are the same party and
   the Mirth channel config is not something a monitor can read in five minutes. Acceptable
   only if the TPM says so and the raw inbound message is exported unmodified.

## Missing evidence
- [ ] Gazelle test definition(s) for EBIW Result Aggregator / POCUS Manager RAD-132: what the
      test instance wants attached (message capture, validator link, screenshots).
- [x] TPM approval for the stand-in: the RAD TPM requested it.
- [ ] Vendor's target: hostname/IP + port the monitor will listen on; TLS or plain MLLP.
- [ ] RAD TF-2 4.128.4.2 text, to confirm the ACK shape above.

## Next action
1. Build `tools/mllp_receiver.py` (Result Aggregator mode), `tools/mllp_send.py`, and a sample
   `samples/ORU_R01_RAD-132_POCUS.hl7`; test loopback. **Done, see Resolution.**
2. Give the vendor this Mac's floor IP and port 2575 (plain MLLP unless they want MLLPS; then
   `TLS_CERT/TLS_KEY` = a GSS-issued "Client and Server" cert for this Mac, `TLS_CA` = `events/2026-na-connectathon/artifacts/gss-ca-2656-ihe-europe-ca-gazelle.pem`).
3. When the first real message lands, read it against the checklist above and paste the
   file path + findings into the Gazelle test instance.

## Resolution
_Open._ Tool built 2026-10-12 at the RAD TPM's request. First message 15:07 ET: transport works, content is v2.4 and missing PID-3, accession, Study UID OBX, physician of record, OBX-11. Waiting on a corrected send.
