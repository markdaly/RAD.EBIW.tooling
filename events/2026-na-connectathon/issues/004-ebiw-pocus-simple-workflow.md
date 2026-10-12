# EBIW_POCUS_Simple_Workflow (Gazelle test 13884): Encounter Manager grouped into POCUS Manager; Result Aggregator sends ITI-31

- **Source:** the monitor, from Gazelle test definition (PDF in `docs/tests/EBIW_POCUS_Simple_Workflow.pdf`),
  Oct 12 ~16:40 ET. Permanent link https://connectathon.ihe-catalyst.net/tm/test.seam?id=13884
- **Opened:** 2026-10-12 16:45 ET
- **Status:** open (stand-ins extended; who plays POCUS_MGR-EBIW still to confirm)
- **Domain / profile / actor / transaction:** RAD EBIW POCUS Option / Result Aggregator (ITI-31
  initiator, RAD-132 responder), Encounter Manager function of the POCUS Manager (RAD-130 MWL)

## Symptom
Test roles: RESULT_AGGREGATOR-EBIW, POCUS_MGR-EBIW, MOD-EBIW, IM-EBIW, one each. There is **no
separate Encounter Manager role**: step 60 RAD-130 (DICOM MWL, POCUS Option table
4.130.4.1.2.1.1-1) goes from MOD-EBIW to POCUS_MGR-EBIW. The vendor's POCUS Manager does
not serve MWL itself, so the Encounter Manager stand-in answers step 60 on behalf of the
grouped POCUS/Encounter Manager. Step 10 has the **Result Aggregator initiating ITI-31**
(Patient Encounter Management, "Scheduled Encounter & Demographics") to the POCUS/Encounter
Manager, so the monitor's Result Aggregator must also *send* an ADT, and the Encounter Manager
should build its worklist from it (RAD TF-1 47.4.1.4–47.4.1.5; profile use-case diagrams show
"RA->EM: ITI-31"; mapping in RAD TF-2x Appendix U).

## Test steps (from the PDF)
| Step | From → To | Transaction | Stand-in involvement |
|---|---|---|---|
| 10 | RESULT_AGGREGATOR → POCUS_MGR | ITI-31 HL7 v2 ADT | `tools/mllp_send.py samples/ADT_A04_ITI-31.hl7 <EM host> 2576` (and to the vendor's POCUS Manager if it accepts ADT) |
| 20–30 | RA internal | patient arrives, HCP begins encounter | screenshot/log evidence |
| 40–50 | MOD internal | identify HCP, identify patient | vendor evidence |
| 60 | MOD → POCUS_MGR | RAD-130 DICOM MWL (POCUS Option table) | `tools/mwl_scp.py`, AE `ENC_MGR` 11112 |
| 70 | MOD internal | acquire | |
| 80 | MOD → POCUS_MGR | RAD-131 C-STORE (4.131.4.1.2.2.1 required modality attributes, Table A.6-1) | vendor's POCUS Manager |
| 90–110 | POCUS_MGR internal | worksheet, privileges/QC, HCP signs | vendor evidence |
| 120 | POCUS_MGR → RESULT_AGGREGATOR | RAD-132 ORU^R01 (Table 4.132.4.1.2-1 through 4.132.4.1.2.3.4) | `tools/mllp_receiver.py` 2575; checklist in ticket 002 |
| 130 | POCUS_MGR → IM | RAD-131 C-STORE (Table 4.131.4.1.2-1, Table A.7-1) | vendor VNA |
| 140 | POCUS_MGR internal | QA sampling | optional |
| 150–160 | RA internal | integrate observation, billing | our log line + raw file; say so in the instance |

Monitor evaluation (from the PDF): proxy logs for transactional steps; non-tangible steps by
screenshot/log; RAD-130 against the **POCUS Option** key table; RAD-132 against 4.132.4.1.2-1
and the segment sections through 4.132.4.1.2.3.4. Appendices O and U recommended, not required.

## Scope
The POCUS Manager vendor(s) that cannot serve MWL themselves; the monitor as Result Aggregator in
every instance of this test.

## Evidence so far
- Test PDF; supplement sections 47.4.1.4, 47.4.1.5, 47.4.2.1, Appendix U Table U-1.

## Hypotheses (ranked)
Not a defect ticket. Deliverables:
1. `tools/mwl_scp.py` gains ITI-31 intake (MLLP 2576, env `ADT_PORT`): ADT^A01/A04/A05/A08 →
   encounter per Table U-1 (PID-3/5/7/8, PV1-3/7/19/44, DG1-4), ACK AA, persisted to
   `logs/encounter-manager/encounters-from-adt.json`, visible to both MWL and UPS-RS.
2. `samples/ADT_A04_ITI-31.hl7`: the step-10 message, same patient/visit as `encounters.json`.

## Missing evidence
- [ ] Which system is POCUS_MGR-EBIW in the instance the monitor is monitoring, and whether it accepts
      ITI-31 (if yes, send the ADT to both it and the Encounter Manager stand-in).
- [ ] Confirm with the RAD TPM that a monitor-run Encounter Manager inside the POCUS_MGR role
      is acceptable for grading step 60.
- [ ] Vendor modality AE title and modality code for step 60.
- [ ] `EBIW_10_Read_This_First` data (same as ticket 003).

## Next action
1. Extend `mwl_scp.py` with ITI-31 intake; sample ADT; loopback: ADT in → MWL and UPS-RS
   return the new encounter with the same accession. **Done, see Resolution.**
2. the monitor: confirm the POCUS_MGR system and TPM acceptance; restart the Encounter Manager tab
   so the ADT listener is up (`ADT_PORT=2576`).
3. Step 10 on the floor: `uv run python tools/mllp_send.py samples/ADT_A04_ITI-31.hl7 10.242.1.184 2576`
   (through the proxy once the channel exists), attach the ACK.

## Resolution
_Open._ ITI-31 intake built and loopback-tested 16:15 ET: ADT^A04 for a new visit → AA, MWL
and UPS-RS both return it with one shared accession; ADT^A08 for the same visit replaces the
record; garbage → AR. Waiting on the POCUS_MGR system identity and TPM acceptance.
