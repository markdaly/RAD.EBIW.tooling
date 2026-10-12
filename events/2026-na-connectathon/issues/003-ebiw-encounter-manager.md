# EBIW: no Encounter Manager on the floor; stand-in needed for RAD-130 (MWL semantics)

- **Source:** floor request via the monitor, Oct 12 afternoon. A VNA vendor's EBIW test scenario needs
  an Encounter Manager partner. No Zulip thread yet.
- **Opened:** 2026-10-12 ~15:30 ET
- **Status:** open (stand-in running on 10.242.1.184:11112 AE `ENC_MGR` since 15:41 ET; waiting for the first query)
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
- Gazelle test name still to be read off the vendor's handwritten note.

## Evidence so far
- Supplement text (rev 3.1) sections quoted above.

## Hypotheses (ranked)
Not a defect ticket. Deliverable is the stand-in: `tools/mwl_scp.py` in Encounter Manager
mode, encounters loaded from `samples/encounters.json`, accession + Study UID generated per
(Admission ID, calling AE) and remembered in a dict (written through to a JSON file so a
restart does not hand out new accessions). Every C-FIND identifier and every response dumped
to `logs/encounter-manager/<session>/`.

## Missing evidence
- [ ] Which Gazelle test instance: name/number and which actor the VNA is registered as.
- [x] Querying system 10.242.1.17 (POCUS Manager box); VNA 10.242.1.11 `SYNVNA` 4000. Calling AE
      title and modality code will show up in the first query dump.
- [ ] `EBIW_10_Read_This_First` code set from Gazelle (department type code, procedure code,
      reason-for-visit codes) to replace the placeholders in `samples/encounters.json`.
- [ ] Whether the VNA will also send RAD-132 to the Encounter Manager (then run
      `ACTOR=encounter-manager tools/mllp_receiver.py` on a second port).
- [ ] TPM approval for this stand-in (the Result Aggregator one was TPM-requested; this one
      came in by a different route).

## Next action
1. Build and loopback-test `tools/mwl_scp.py`. **Done, see Resolution.**
2. Get the Gazelle test name and the code set; edit `samples/encounters.json` to match the
   test's patient/encounter data (Gazelle usually prescribes the patient).
3. Give the modality vendor: AE title `ENC_MGR`, this Mac's floor IP, port 11112.
4. After the first real query: read the dumped identifier against the matching-key table and
   the response against the return-key table; confirm the stored images at the VNA carry the
   accession, Issuer of Accession, Study UID and Admission ID that were returned.

## Resolution
_Open._ Tool built 2026-10-12; waiting on test name, code set, and the modality's AE.
