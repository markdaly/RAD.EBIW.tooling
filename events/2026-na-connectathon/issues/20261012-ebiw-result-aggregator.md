# EBIW POCUS: no Result Aggregator on the floor; stand-in needed for RAD-132

- **Source:** floor request via the monitor (RAD TPM / POCUS Manager vendor). No Zulip thread yet.
- **Opened:** 2026-10-12 ~13:30 ET
- **Status:** open (tool built, not yet pointed at a vendor)
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
- Reply: Acknowledge Imaging Result "as described in 4.128.4.2" (RAD TF-2, RD profile).
  From memory of 4.128.4.2: HL7 v2.5.1 Chapter 2 original-mode ACK, `MSH-9 = ACK^R01^ACK`,
  `MSA-1 = AA|AE|AR`, `MSA-2 = MSH-10` of the ORU. Verify against RAD TF-2 if a vendor argues.
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

## Scope
One POCUS Manager vendor now; any EBIW Image Manager or POCUS Manager that needs a RAD-132
partner this week.

## Evidence so far
- Supplement text extracted from https://www.ihe.net/uploadedFiles/Documents/Radiology/IHE_RAD_Suppl_EBIW.pdf
  (rev 3.1, 132 pages), sections quoted above.

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
- [ ] TPM approval for the stand-in (CLAUDE.md: tools are partner stand-ins approved by the TPM).
- [ ] Vendor's target: hostname/IP + port the monitor will listen on; TLS or plain MLLP.
- [ ] RAD TF-2 4.128.4.2 text, to confirm the ACK shape above.

## Next action
1. Build `tools/mllp_receiver.py` (Result Aggregator mode), `tools/mllp_send.py`, and a sample
   `samples/ORU_R01_RAD-132_POCUS.hl7`; test loopback. **Done, see Resolution.**
2. Ask the RAD TPM to approve the stand-in and point the vendor at `<this Mac's IP>:2575`.
3. When the first real message lands, read it against the checklist above and paste the
   file path + findings into the Gazelle test instance.

## Resolution
_Open._ Tool built 2026-10-12; waiting on TPM approval and a vendor endpoint.
