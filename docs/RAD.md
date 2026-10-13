# IHE Radiology (RAD): Connectathon reference

Event-specific priorities and observations live in `events/<event>/README.md`.

Canonical index: https://profiles.ihe.net/RAD/ (TF Rev 23.0, Vols 1–4 published 2025-08-08)
Change Proposal index (Final Text CPs, which modify the TF): linked from the RAD index page.

## Final Text profiles (in TF volumes)
SWF, SWF.b, PIR, CPI, PGP, ARI, KIN, SINR, CHG, PWF, RWF, ED, PDI, NM, MAMMO, IRWF, TCE,
REM, REM-NM, XDS-I.b, XCA-I, IOCM, DBT, MRRT, BIR, WIA, WIC, PERF, IID.

## Trial Implementation supplements (eligible for testing)
AIRA (2025-06-12), AIR (rev 2025-08-08), AIW-I, CDS-OAT, CAM, XC-WADO (rev 1.2, 2025-09-10),
XDR-I, XRR-WD, EBIW (rev 3.1, 2025-06-19), PDI extensions, FUS, IOCM Extension, IDEP,
IRWF.b, IRA (FHIRcast), IMR, MAP, MADO (v1.0.0, 2026-09-03), DIFF, MIMA, PAWF, POWR,
RRR-WF, RAM (2025-01-23), RD, SOLE.
Public comment: IDR (Imaging Diagnostic Report), Mar–Apr 2026.

## Transaction cheat sheet (most-used)
| # | Name | Notes |
|---|---|---|
| RAD-1 | Patient Registration | ADT |
| RAD-2/3 | Placer / Filler Order Mgmt | SWF.b: OMI^O23 (v2.5.1), not ORM^O01 |
| RAD-4 | Procedure Scheduled | OMI to Image Manager |
| RAD-5 | Query Modality Worklist | MWL C-FIND |
| RAD-6/7 | MPPS In Progress / Completed | N-CREATE / N-SET |
| RAD-8 | Modality Images Stored | C-STORE |
| RAD-10 | Storage Commitment | N-ACTION / N-EVENT-REPORT |
| RAD-12/13 | Patient Update / Procedure Update | PIR |
| RAD-14/16 | Query / Retrieve Images | C-FIND / C-MOVE (C-GET) |
| RAD-43/44/45 | Evidence Docs Stored / Query / Retrieve | ED |
| RAD-47 | Distribute Imaging Info on Media | PDI |
| RAD-49 | Instance Availability Notification | |
| RAD-50 | Store Instances | |
| RAD-55 | WADO Retrieve (URI) | XDS-I.b |
| RAD-66 | Rejection Note Stored | IOCM KOS (113001 quality, 113037 patient safety, 113038 wrong MWL, 113039 retention) |
| RAD-68 | Provide & Register Imaging Document Set (MTOM/XOP) | XDS-I.b manifest |
| RAD-69 | Retrieve Imaging Document Set | XDS-I.b SOAP |
| RAD-75 | Cross Gateway Retrieve Imaging Document Set | XCA-I |
| RAD-106 | Invoke Image Display | IID |
| RAD-107 | WADO-RS Retrieve | WIA et al. |
| RAD-108 | Store Instances over the Web (STOW-RS) | WIC, EBIW Lightweight Modality |
| RAD-129 | QIDO-RS Query | WIA, AIR |
| RAD-130/131/132 | Get Encounter Imaging Context / Store Encounter Images / Notify of Imaging Results | EBIW |
| RAD-136 | Display Analysis Result | AIR |
| RAD-137 | Query Analysis Results | AIR |
| RAD-146..156 | IRA FHIRcast transactions | IRA |
| RAD-160 | Cross-Community WADO-RS Retrieve | XC-WADO |
Verify any number against the TF before quoting it to a vendor.

## HL7 v2.5.1 nudging (SWF.b)
- MSH-12 = `2.5.1`. Orders = OMI^O23 (ack ORI^O24), not ORM^O01.
- IPC segment carries imaging identifiers: IPC-1 Accession, IPC-2 Requested Procedure ID,
  IPC-3 Study Instance UID, IPC-4 Scheduled Procedure Step ID, IPC-5 Modality.
- Codes: Connectathon uses the Gazelle OrderManager value sets. RAD order hierarchy:
  https://gazelle.ihe.net/common/order-manager/orderHierarchy4Radiology.xml
- Common failures: version string mismatch, MRN in the wrong PID field / missing assigning
  authority (PID-3.4), accession not round-tripping into DICOM (0008,0050), Issuer of
  Accession Number missing.

## EBIW: Encounter-Based Imaging Workflow (TI rev 3.1, 2025-06-19)
Supplement: https://www.ihe.net/uploadedFiles/Documents/Radiology/IHE_RAD_Suppl_EBIW.pdf
Imaging with no order (POCUS, derm/wound photos, phone cameras). Follows the SWF.b pattern:
establish context, convey metadata, capture/store, index/archive.
- Actors: Encounter Manager, Acquisition Modality, Lightweight Modality, Image Manager/Archive,
  Result Aggregator (usually the EMR), POCUS Manager, Image Display.
- RAD-130 Get Encounter Imaging Context: MWL semantics (Acquisition Modality) or UPS-RS
  semantics (Lightweight Modality). Encounter Manager must support MWL; MWL **and** UPS-RS
  if it claims the Lightweight Modality Option.
- RAD-131 Store Encounter Images: C-STORE. RAD-108 STOW-RS for Lightweight Modality.
- RAD-132 Notify of Imaging Results: **ORU^R01** (deliberately not R30; R30 requires ORC).
  Sent by the Image Manager (or POCUS Manager) to the Result Aggregator.
- Encounter Manager generates Study UID + Accession; Issuer of Accession configurable; must
  avoid accession collisions; **must not return different accession numbers for the same
  admission to the same device** unless it knows a new encounter occurred; must handle
  John Doe patients.
- POCUS Option: PV1-19 Visit Number → Admission ID (0038,0010); PV1-7 Attending →
  Physician(s) of Record; training flag in Reason for Performed Procedure Code Seq
  (0040,1012); Operator Identification Sequence (0008,1072) may be multi-valued.
- Photos: Modality XC, VL Photographic Image IOD; Secondary Capture only as last resort.
- Header signature vs SWF.b: Accession = value, Request Attribute Sequence = empty,
  Admission ID present, no RAD-4, MPPS probably not.
- Required grouping: EBIW Image Manager **with SWF.b Image Manager** (open issue whether too
  strict, so expect arguments). Other actors grouped with ITI CT.
- Gazelle: `EBIW_10_Read_This_First` defines the code set; Encounter Manager must preload it.

## XDS-I.b / XCA-I
- Imaging Document Source publishes a KOS manifest via RAD-68; consumers fetch images via
  RAD-55 (WADO-URI), RAD-69 (SOAP), or RAD-16. RAD-16 retrieve tests were removed from NIST
  conformance tests in 2018.
- Preloaded test studies: C3L-00277 (DX), C3N-00953 (CT), TCGA-G4-6304 (CT), IHEBLUE-199 (CT).
- Graded in "XDS-I.b_Manifest_and_Metadata": DICOM manifest content + XDS metadata against
  Connectathon affinity-domain codes (codes.xml). Validate the KOS in Gazelle EVS.
- NIST conformance wiki: https://github.com/usnistgov/iheos-toolkit2/wiki

## IOCM
KOS rejection notes (RAD-66). Image Manager hides rejected instances from Q/R unless the
client uses the "expose rejected" AE/endpoint. Classic failure: vendor rejects locally but
never propagates downstream.

## PDI
Creator brings 2 copies of media (CD required; USB/DVD optional), labeled with Gazelle system
name, table, contact. PDI+XDM on same media supported (test `PDI_with_XDM_Create`).

## REM
CT dose SR: TID 10011. XR/XA/RF/MG/CR/DX: TID 10001. Preparatory text file
`CompanyName_SystemName_REM.txt`.

## IID / BIR
- IID Image Display must host ≥3 studies for one patient (same PID, different accession/date),
  ≥1 other patient's study, and a study with a KOS key image.
- BIR is functional: the monitor runs the BIR test plan at the vendor's workstation (test data
  BIRTestData_2015 in the IHE Google Drive test_data folder).

## WIA / WIC
WIA = QIDO-RS (RAD-129) + WADO-RS (RAD-107), backend-neutral, optional XDS-I backend proxy.
WIC = STOW-RS (RAD-108) from capture devices; the Image Manager fills Image Pixel Macro fields
the capturer leaves empty.

## AI profiles
- **AIR**: AI results as DICOM SR TID 1500, SEG, Parametric Map, KOS. Monitor evaluation via
  no-peer AIR_Content_* tests; Image Display evaluated hands-on against RAD-136.
  Test data: https://github.com/IHE/connectathon-events/2026-na-connectathon/artifacts/tree/main/profile_test_data/RAD/AIR
- **AIRA**: Quality Note Creator records per-result accepted / modified / rejected / added /
  unassessed / unable-to-assess (AIRA_111..116) in an Assessment Status SR
  (TID IHE_RADAIRA1), writes replacement Output AI Result Objects, rejects originals via KOS
  (113001 + modifier AIRA_26). Defines PCR/PIR alarm metrics for post-market surveillance.
- **AIW-I**: UPS-based AI task orchestration (pull, triggered pull, push).
- **IRA**: FHIRcast reporting sessions; Hub returns 409 for update/select/close on an unopened
  context; select implicitly unselects.
- **IMR**: interactive multimedia report (RAD-141/142/143).

## XC-WADO (TI rev 1.2)
RAD-160 Cross-Community WADO-RS Retrieve. URL:
`https://<gw>/<path>/homeCommunityId/<hcid>/RetrieveLocationUID/<uid>/studies/...`,
RetrieveURL as query param. Gateways only swap the endpoint and must preserve Accept/MediaType.
Imaging Document Consumer grouped with XDS.b or MHD Document Consumer.

## Spec errata worth knowing
- XC-WADO Table 4.160.2-1 lists Imaging Document Source as RAD-160 Requester (should be
  Imaging Document Consumer). The doc is inconsistent on location-as-path vs query param, and
  one example uses `RetrieveLocationUID=`. Vendors may implement either shape.
- AIRA says Image Manager supports RAD-66 "as a C-STORE SCU" (should be SCP), and cites
  "QIDO-RS Query [RAD-107]" (should be RAD-129).

## Links
- RAD TF index: https://profiles.ihe.net/RAD/
- RAD 'Do This First' tests: https://gazelle.ihe-europe.net/book/export/html/1022
- Connectathon artifacts: https://github.com/IHE/connectathon-artifacts
- EBIW: https://www.ihe.net/uploadedFiles/Documents/Radiology/IHE_RAD_Suppl_EBIW.pdf
- AIRA: https://www.ihe.net/uploadedFiles/Documents/Radiology/IHE_RAD_Suppl_AIRA.pdf
- XC-WADO: https://www.ihe.net/uploadedFiles/Documents/Radiology/IHE_RAD-Suppl_XC-WADO.pdf
- IRA: https://profiles.ihe.net/RAD/IRA/volume-1.html
- MADO: https://profiles.ihe.net/RAD/MADO/
