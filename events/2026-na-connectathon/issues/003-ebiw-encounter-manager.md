---
event: IHE North America Connectathon 2026
dates: 2026-10-12 to 2026-10-16
kind: issue
opened: 2026-10-12
status: open
expires: 2026-10-16
---
# EBIW: no Encounter Manager on the floor; stand-in needed for RAD-130 (MWL semantics)

- **Source:** floor request via the monitor, Oct 12 afternoon. A VNA vendor's EBIW test scenario needs
  an Encounter Manager partner. No Zulip thread yet.
- **Opened:** 2026-10-12 ~15:30 ET
- **Status:** open (MWL on 10.242.1.184:11112 `ENC_MGR` since 15:41 ET; UPS-RS on http://10.242.1.184:8042/workitems since 16:05 ET; waiting for the first query)
- **Domain / profile / actor / transaction:** RAD EBIW (TI rev 3.1, 2025-06-19) / Encounter
  Manager, POCUS Option / RAD-130 Get Encounter Imaging Context (MWL semantics); RAD-132
  Notify of Imaging Results as optional Responder

## Symptom
- The vendor is an Image Manager/Image Archive. Nothing in EBIW flows from the Encounter
  Manager to the Image Manager directly (Table 47.1-1): the Encounter Manager answers
  RAD-130 for the modality, and the modality stores to the Image Manager with the
  accession / Study UID / Admission ID the Encounter Manager handed out. So the scenario
  needs an Encounter Manager for whichever modality feeds the VNA, so that stored images carry
  the EBIW header signature (Accession valued, Request Attributes Sequence absent, Admission ID
  present; RAD.md notes).
- Optionally the Image Manager sends RAD-132 to the Encounter Manager (Responder O for EM).

## What an Encounter Manager is (RAD TF-1: 47.1.1.1, RAD TF-2: 4.130)
- "Manages and provides encounter metadata and marshaled patient demographics."
- Shall implement **MWL semantics** of RAD-130 (C-FIND SCP, Modality Worklist SOP Class);
  UPS-RS too only with the Lightweight Modality Option. Shall support at least one option
  (Table 47.2-1 note 1); POCUS Option is the one in play.
- Shall **generate Study Instance UIDs and accession numbers**; Issuer of Accession Number
  configurable; accession collisions avoided (prefix/suffix allowed).
- **State the spec forces:** "shall not return different accession numbers for the same
  admission to the same device unless it can determine that there has been an additional
  encounter" (47.1.1.1). So one (Admission ID, calling AE) → one accession + Study UID.
- Shall handle "John Doe" patients (how the query triggers it is up to the EM).
- RAD-130 Expected Actions (4.130.4.1.3): match on Patient ID (+ Issuer if given); echo back
  Scheduled Station AE Title and Modality from the query as return keys; if nothing was
  actually scheduled, SPS Start Date/Time = **now**; a generic "Perform Imaging" description
  or code is allowed for SPS Description / Requested Procedure Description / Code Sequence.
- Return keys the SCP must be able to return (Table 4.130.4.1.2.1-1, R/R+ for SCP):
  Patient's Name, Patient ID, Issuer of Patient ID, Other Patient IDs Sequence, Birth Date,
  Sex, Institution Name, Institution Code Sequence, Institution Address, Institutional
  Department Name, Institutional Department Type Code Sequence, Admission ID, Issuer of
  Admission ID Sequence, Admitting Date/Time, Reason for Visit (+ code seq), **Accession
  Number (non-empty, IHE-3)**, Issuer of Accession Number Sequence, Requested Procedure
  Description and/or Code Sequence (IHE-5), Study Instance UID, SPS Sequence with Scheduled
  Station AE Title, SPS Start Date/Time, Modality, SPS Description.
- Matching keys the SCP must support: Patient's Name, Patient ID, Issuer of Patient ID (R+),
  Institution Name (R+), Institutional Department Name (R+), Dept Type Code Seq (R+),
  Admission ID (R+), Accession Number (single value, IHE-4), SPS: Scheduled Station AE Title,
  SPS Start Date/Time, Modality, Scheduled Performing Physician's Name.
- POCUS Option additions (Table 4.130.4.1.2.1.1-1): Institutional Department Name and
  Admission ID are R+ matching keys both sides; Physician(s) of Record Identification
  Sequence → Person Identification Code Sequence (Code Value / Scheme / Meaning) is an R+
  return key. Multiple Admission IDs returned must all be shown to the operator (IHE-1).
- Gazelle: `EBIW_10_Read_This_First` defines the code set; the Encounter Manager must
  preload it (RAD.md). **Not fetched yet; the stand-in's codes are placeholders until it is.**

## Scope
One VNA vendor's scenario now; any EBIW Acquisition Modality that needs a RAD-130 responder.

### Floor facts (the monitor, 15:35 ET)
- Gazelle EBIW registrations: Encounter Manager has two SUTs, both unavailable this week
  (one declines, one not on site). Result Aggregator: none. The VNA vendor has two systems:
  the VNA (Image Manager/Image Archive + Lightweight Modality; options MPEG4, JPEG, DICOM
  Instance Storage, POCUS) and a sync/POCUS-manager box (POCUS Manager + Image Manager).
- **Querying system:** the vendor's POCUS Manager box, 10.242.1.17. It will C-FIND the
  stand-in at **10.242.1.184:11112, AE `ENC_MGR`**.
- **VNA:** 10.242.1.11, AE `SYNVNA`, port 4000. Reachable from this Mac (TCP open); a C-ECHO
  with calling AE `ENC_MGR` was rejected at association, which is normal for a VNA that only
  accepts known calling AEs. Not needed for the Encounter Manager role.
- **Gazelle test:** EBIW_35_Full_Workflow-RESTful, id 13478, peer-to-peer, version EU2020
  (https://connectathon.ihe-catalyst.net/tm/test.seam?id=13478). Roles:
  ENCOUNTER_MGR-EBIW, IM-EBIW, MOD-EBIW, RESULT_AGGREGATOR-EBIW, one each. **The monitor's Gazelle
  system (DDX) is registered as Encounter Manager and Result Aggregator**; the VNA vendor is
  MOD-EBIW (Lightweight Modality) and IM-EBIW. Steps: 20 RAD-130 UPS-RS GET workitems →
  EM; 40 RAD-131 STOW-RS → IM; 50 RAD-132 ORU^R01 → Result Aggregator; 55 ACK (original
  mode, MSA-1 AA, MSA-2 = MSH-10); 60/65 optional ORU → EM + ACK. All partners must go
  through the Gazelle Proxy or attach captures. EM prerequisite: EBIW_10_Read_This_First
  (patients and encounters). IM prerequisite: EBIW_90_RAD-132-Scrutiny.
  **Monitor checklist (from the test):** watch the modality query and store (nothing to
  verify), then at the Result Aggregator confirm the ORU carries, from the worklist: Patient
  ID + assigning authority (PID-3), Patient Name (PID-5), Accession + assigning authority
  (OBR-18/19), Study Instance UID (OBX-5), Procedure Code (OBR-4); and that the Aggregator
  "does something more than ACK" (our stand-in writes the raw ORU and a key-field summary
  line to `logs/`). Step 20 says the EM "should tell the Modality what query parameters will
  result in a match": see the query line in Next action. The vendor's VNA is registered as **Lightweight
  Modality**, which means RAD-130 **UPS-RS semantics**, not MWL (47.1.1.2). They do not have
  UPS-RS yet and are coding it. Supplement open issue Q1 (p.7): committee published UPS-RS for
  the RESTful path, FHIR still being worked; POCUS community prefers MWL. So the stand-in now
  serves both: `tools/mwl_scp.py` (DIMSE) for whatever they can test today, `tools/ups_rs.py`
  (REST) for when their client exists.
- UPS-RS endpoint for the vendor: `GET http://10.242.1.184:8042/workitems?<keys>`; station
  identity via `ScheduledStationNameCodeSequence.CodeValue=<their id>`, modality via
  `ScheduledStationClassCodeSequence.CodeValue=XC|US`; response is a JSON array of UPS
  instances with Accession / Issuer / Requested Procedure inside Referenced Request Sequence
  (0040,A370) and Study Instance UID both there and at top level.

## Evidence so far
- Supplement text (rev 3.1) sections quoted above.

## Hypotheses (ranked)
Not a defect ticket. Deliverable is the stand-in: `tools/mwl_scp.py` in Encounter Manager
mode, encounters loaded from `samples/encounters.json`, accession + Study UID generated per
(Admission ID, calling AE) and remembered in a dict (written through to a JSON file so a
restart does not hand out new accessions). Every C-FIND identifier and every response dumped
to `logs/encounter-manager/<session>/`.

## Missing evidence
- [x] Gazelle test id 13478; VNA registered as Lightweight Modality (+ Image Manager). Test text
      still to capture (the monitor logs into Gazelle in the browser pane, or pastes it).
- [x] Querying system 10.242.1.17 (POCUS Manager box); VNA 10.242.1.11 `SYNVNA` 4000. Calling AE
      title and modality code will show up in the first query dump.
- [ ] `EBIW_10_Read_This_First` code set from Gazelle (department type code, procedure code,
      reason-for-visit codes) to replace the placeholders in `samples/encounters.json`.
- [ ] Whether the VNA will also send RAD-132 to the Encounter Manager (then run
      `ACTOR=encounter-manager tools/mllp_receiver.py` on a second port).
- [ ] TPM approval for this stand-in (the Result Aggregator one was TPM-requested; this one
      came in by a different route).

## Next action
1. Build and loopback-test `tools/mwl_scp.py`. **Done.** Add UPS-RS (`tools/ups_rs.py`),
   loopback-tested incl. shared accession with the MWL side. **Done.**
2. Export EBIW_10_Read_This_First from Gazelle (same "print test as pdf" route) and load its
   patients/encounters/codes into `samples/encounters.json`.
2b. Query line to hand the modality vendor (matches DOE^JANE / VISIT0001 today):
    `GET http://10.242.1.184:8042/workitems?PatientID=MRN12345&ScheduledStationNameCodeSequence.CodeValue=<their station id>&ScheduledStationClassCodeSequence.CodeValue=XC`
    or by wristband: `AdmissionID=VISIT0001`. Through the proxy, replace host:port with the
    proxy channel Gazelle assigns.
3. Give the modality vendor: AE title `ENC_MGR`, this Mac's floor IP, port 11112.
4. After the first real query: read the dumped identifier against the matching-key table and
   the response against the return-key table; confirm the stored images at the VNA carry the
   accession, Issuer of Accession, Study UID and Admission ID that were returned.

## Resolution
_Open._ MWL and UPS-RS stand-ins running since 2026-10-12 afternoon; waiting on the vendor's first query (DIMSE now, REST once their client exists), the test text, and the code set.
