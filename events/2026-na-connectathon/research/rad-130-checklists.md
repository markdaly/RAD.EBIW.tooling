---
event: IHE NA Connectathon 2026
source: IHE RAD TF Supplement EBIW rev 3.1 (2025-06-19), RAD TF-2 4.130 (Tables 4.130.4.1.2.1-1, 4.130.4.1.2.1.1-1, 4.130.4.1.2.2-1; 4.130.4.1.3; 4.130.4.2); notation from RAD TF-2 rev 23.0 (2025-08-08) Section 2.2
status: transcribed (tables checked against the rendered PDF pages 94-96; notation checked against RAD TF-2 2.2 text)
---
# RAD-130 Get Encounter Imaging Context: monitor checklists

Requester = Acquisition Modality (MWL, SCU) or Lightweight Modality (UPS-RS, user-agent).
Responder = Encounter Manager (MWL SCP; UPS-RS origin-server). Table 4.130.2-1.

## 0. Reading the key tables (RAD TF-2 2.2, rev 23.0 pp. 38-39)

| Code | Matching key, SCU | Matching key, SCP | Return key, SCU | Return key, SCP |
|---|---|---|---|---|
| R | must offer to the user; send if user gave a value, else send zero-length (i.e. as return key) | process as a DICOM-required matching key | must request; must display the value | DICOM type 1/2 processed per DICOM type; type 3 processed as type 2 |
| R+ | same as R; IHE extension of DICOM | same | must request; must display | same |
| R+* | same as R+ | same | must request; display NOT required | same |
| R* | n/a | n/a | must request; display NOT required | n/a |
| O | optional | optional | optional | optional |

Quote, 2.2: "A Query SCU shall include as Return Keys in each C-FIND request all attributes specified as R, R+, R*, or R+*. A Query SCU shall display for the user the returned value of all attributes specified as R or R+ in the normal user interface."

EBIW's own gloss (4.130.4.1.2.1): base RAD-130 "does not place display requirements for specific attributes on the Requester"; the POCUS Option (4.130.4.1.2.1.1) does ("similar to those in Query Modality Worklist [RAD-5]"). In practice: in the base table every SCU-required return key is R+* (request, no display mandate); in the POCUS table the Patient's Name / Patient ID / Birth Date / Department Name / Physician of Record rows are R+ (request AND display).

Monitor shorthand used below: **SCU must** = include in the C-FIND identifier (zero-length unless filtering). **SCP must** = support matching (for matching-key columns) / return a value (for return-key columns). Return-key SCP "R" is DICOM-required (type 1 or 2 in PS3.4 K.6-1), "R+" is IHE-added.

## 1. Table 4.130.4.1.2.1-1: Return and Matching Keys for Encounter Metadata (base, MWL)

Columns: Matching SCU / Matching SCP / Return SCU / Return SCP, verbatim from the table. "Source" = where the Encounter Manager gets the value (4.130.4.1.3, 4.130.4.2.2, RAD TF-2x App. U; marked [U] when the only statement is Table U-1, which is informative).

### Patient Metadata

| Attribute | Tag | Match SCU | Match SCP | Ret SCU | Ret SCP | Source / note |
|---|---|---|---|---|---|---|
| Patient's Name | (0010,0010) | R+* | R | R+* | R | ADT PID-5 [U] |
| Patient ID | (0010,0020) | R+* | R | R+* | R | ADT PID-3 [U]; SCP must also match an ID carried inside Other Patient IDs Sequence (4.130.4.1.3) |
| Issuer of Patient ID | (0010,0021) | O | R+ | R+* | R+ | PID-3.4 [U]; if SCU sends it, SCP must match on it (4.130.4.1.3) |
| Other Patient IDs Sequence | (0010,1002) | | | | | header row |
| >Patient ID | (0010,0020) | O | O | O | R+ | PID-4 [U] |
| >Issuer of Patient ID | (0010,0021) | O | O | O | R+ | |
| >Issuer of Patient ID Qualifiers Sequence | (0010,0024) | O | O | O | R+ | |
| >>Universal Entity ID | (0040,0032) | O | O | O | R+ | |
| >>Universal Entity ID Type | (0040,0033) | O | O | O | R+ | |
| >Type of Patient ID | (0010,0022) | O | O | O | R+ | |
| Patient's Birth Date | (0010,0030) | O | O | R+* | R+ | PID-7 [U] |
| Patient's Sex | (0010,0040) | O | O | R+* | R+ | PID-8 [U] |
| Confidentiality constraint on patient data | (0040,3001) | O | O | O | O | PV1-16 / PD1-12 / PV2-22 [U] |

### Encounter Metadata, Visit Identification

| Attribute | Tag | Match SCU | Match SCP | Ret SCU | Ret SCP | Source / note |
|---|---|---|---|---|---|---|
| Institution Name | (0008,0080) | O | R+ | R+* | R+ | PV1-3 [U]; EBIW_10 fixes the value for this event |
| Institution Code Sequence | (0008,0082) | | | | | header |
| >Code Value | (0008,0100) | O | O | R+* | R+ | CID 5002 [U]; EBIW_10 value |
| >Coding Scheme Version | (0008,0103) | O | O | O | O | |
| >Coding Scheme Designator | (0008,0102) | O | O | R+* | R+ | |
| >Code Meaning | (0008,0104) | O | O | R+* | R+ | |
| Institution Address | (0008,0081) | O | O | R+* | R+ | PV1-3 [U] |
| Institutional Department Name | (0008,1040) | R+* | R+ | R+* | R+ | PV1-3 [U] |
| Institutional Department Type Code Sequence | (0008,1041) | | | | | header |
| >Code Value | (0008,0100) | R+* | R+ | R+* | R+ | CID 7030 [U]; EBIW_10 values (SCT) |
| >Coding Scheme Version | (0008,0103) | O | O | O | O | |
| >Coding Scheme Designator | (0008,0102) | R+* | R+ | R+* | R+ | |
| >Code Meaning | (0008,0104) | O | O | R+* | R+ | |
| Admission ID | (0038,0010) | R+* | R+ | R+* | R+ | PV1-19 [U]; POCUS Option requires EM to map PV1-19 to this (47.2.1) |
| Issuer of Admission ID Sequence | (0038,0014) | | | | | header |
| >Local Namespace Entity ID | (0040,0031) | O | O | O | R+ | PV1-19.4 [U] |
| >Universal Entity ID | (0040,0032) | O | O | O | R+ | |
| >Universal Entity ID Type | (0040,0033) | O | O | O | R+ | |

### Encounter Metadata, Visit Admission / Visit Status

| Attribute | Tag | Match SCU | Match SCP | Ret SCU | Ret SCP | Source / note |
|---|---|---|---|---|---|---|
| Admitting Date | (0038,0020) | O | O | O | R+ | PV1-44 [U] |
| Admitting Time | (0038,0021) | O | O | O | R+ | PV1-44 [U] |
| Admitting Diagnoses Description | (0008,1080) | O | O | O | O | DG1-4 [U] |
| Admitting Diagnoses Code Sequence | (0008,1084) | O | O | O | O | DG1-3 [U] |
| Reason for Visit | (0032,1066) | O | O | O | R+ | DG1-4 / PV2-12 [U] |
| Reason for Visit Code Sequence | (0032,1067) | | | | | header |
| >Code Value | (0008,0100) | O | O | O | R+ | DG1-3 / PV2-3 [U] |
| >Coding Scheme Version | (0008,0103) | O | O | O | O | |
| >Coding Scheme Designator | (0008,0102) | O | O | O | R+ | |
| >Code Meaning | (0008,0104) | O | O | O | R+ | |
| Referring Physician's Name | (0008,0090) | O | O | O | O | PV1-8 [U] |
| Referring Physician Identification Sequence | (0008,0096) | O | O | O | O | |
| Referring Physician's Telephone Numbers | (0008,0094) | O | O | O | O | |
| Current Patient Location | (0038,0300) | O | O | O | O | PV1-3 [U] |

### Procedure Metadata

| Attribute | Tag | Match SCU | Match SCP | Ret SCU | Ret SCP | Source / note |
|---|---|---|---|---|---|---|
| Accession Number | (0008,0050) | O [IHE-4] | O [IHE-4] | R+* | R+ [IHE-3] | Generated by EM (47.1.1.1); IHE-3: value shall be non-empty; IHE-4: SCP matching is single-value only |
| Issuer of Accession Number Sequence | (0008,0051) | | | | | header |
| >Local Namespace Entity ID | (0040,0031) | O | O | R+* | R+ | EM-configurable issuer (47.1.1.1) |
| >Universal Entity ID | (0040,0032) | O | O | R+* | R+ | |
| >Universal Entity ID Type | (0040,0033) | O | O | R+* | R+ | |
| Requesting Service | (0032,1033) | O | O | O | O | PV1-10 / PV2-23 [U] |
| Requesting Service Code Sequence | (0032,1034) | O | O | O | O | |
| Requested Procedure Description | (0032,1060) | O | O | O | R [IHE-5] | IHE-5: SCP shall support (0032,1060) or (0032,1064) or both; generic "Perform Imaging" permitted (4.130.4.1.3) |
| Requested Procedure Code Sequence | (0032,1064) | O | O | O | R [IHE-5] | same; EBIW_10 fixes three SCT codes for this event |
| Reason for the Requested Procedure | (0040,1002) | O | O | O | O | PV2-12 [U] |
| Reason for Requested Procedure Code Sequence | (0040,100A) | O | O | O | O | PV2-3 [U] |
| Study Instance UID | (0020,000D) | O | O | R+* | R | Generated by EM (47.1.1.1, 4.131.4.1.2.1) |
| Scheduled Procedure Step Sequence | (0040,0100) | | | [IHE-1] | [IHE-2] | IHE-1: SCU requests SPS attributes by universal match inside the sequence; IHE-2: SCP shall support that |
| >Scheduled Station AE Title | (0040,0001) | R+* [IHE-6] | R | R+* | R | IHE-6: SCU populates with its OWN AE title; SCP shall return the same value (4.130.4.1.3) |
| >Scheduled Procedure Step Start Date | (0040,0002) | O | R | O | R | If nothing is scheduled, SCP returns current date (4.130.4.1.3) |
| >Scheduled Procedure Step Start Time | (0040,0003) | O | R | O | R | same, current time |
| >Scheduled Procedure Step Location | (0040,0011) | O | O | O | O | PV1-3 [U] |
| >Modality | (0008,0060) | R+* [IHE-7] | R | R+* | R | IHE-7: SCU populates with its OWN modality; SCP shall return the same value (4.130.4.1.3) |
| >Scheduled Performing Physician's Name | (0040,0006) | O | R | O | O | PV1-7 [U] |
| >Scheduled Protocol Code Sequence | (0040,0008) | O | O | O | O | |
| >Scheduled Procedure Step Description | (0040,0007) | O | O | O | R | generic description permitted (4.130.4.1.3) |

Footnotes IHE-1..IHE-7 are paraphrased in the notes column; full text at 4.130.4.1.2.1 lines 1825-1841.

### Minimum C-FIND identifier an SCU must send (base table, SCU column R+*)
Patient's Name, Patient ID, Issuer of Patient ID, Patient's Birth Date, Patient's Sex, Institution Name, Institution Code Sequence (>Code Value, >Coding Scheme Designator, >Code Meaning), Institution Address, Institutional Department Name, Institutional Department Type Code Sequence (>Code Value, >Coding Scheme Designator, >Code Meaning), Admission ID, Accession Number, Issuer of Accession Number Sequence (>three items), Study Instance UID, SPS Sequence with >Scheduled Station AE Title (valued = own AET), >Modality (valued = own modality). Everything else may be absent. A query missing any of these is non-conformant on the SCU side even if the SCP answers happily.

### Minimum the SCP must be able to return (base table, SCP column R or R+)
Everything above plus: Other Patient IDs Sequence items, Issuer of Admission ID Sequence items, Admitting Date/Time, Reason for Visit (+ code seq), Requested Procedure Description and/or Code Sequence, SPS Start Date/Time, SPS Description. Accession Number must be non-empty (IHE-3).

## 2. Table 4.130.4.1.2.1.1-1: POCUS Option additions (4.130.4.1.2.1.1)

Applies to Acquisition Modality + Encounter Manager with the POCUS Option, "in addition to" Table 4.130.4.1.2.1-1. Rows below REPLACE the base row's requirement level where they differ. Note the R+ (not R+*): display required.

| Attribute | Tag | Match SCU | Match SCP | Ret SCU | Ret SCP | Delta vs base / note |
|---|---|---|---|---|---|---|
| Patient's Name | (0010,0010) | R+ | R | R+ | R | display now required on the modality |
| Patient ID | (0010,0020) | R+ | R | R+ | R | display now required |
| Patient's Birth Date | (0010,0030) | O | O | R+ | R+ | display now required |
| Institutional Department Name | (0008,1040) | R+ | R+ | R+ | R+ | display now required |
| Admission ID | (0038,0010) | R+* | R+ | R+* [IHE-1] | R+ | IHE-1: if multiple Admission IDs come back, modality shall display ALL of them to the operator |
| Physician(s) of Record Identification Sequence | (0008,1049) | | | | | header; NEW attribute. 47.2.1 says the EM maps PV1-7 Attending Doctor to (0008,009D) [sic]; Table U-1 maps PV1-7 to (0008,1048)/(0008,009D). The return key actually required here is (0008,1049). Treat (0008,1049) as the one to check. |
| > Person Identification Code Sequence | (0040,1101) | | | | | header |
| >>Code Value | (0008,0100) | O | O | R+* | R+ | physician identifier (NPI in the US per 4.132.4.1.2.3.2/.3) |
| >>Coding Scheme Version | (0008,0103) | O | O | O | O | |
| >>Coding Scheme Designator | (0008,0102) | O | O | R+* | R+ | |
| >>Code Meaning | (0008,0104) | O | O | R+* | R+ | |

Downstream: the modality shall copy (0008,1049) from the MWL response into the images when present (4.131.4.1.2.2.1, RC+), the POCUS Manager may coerce it if absent (A.7-1 IHE-A.7.2), and it feeds ORC-12 / OBR-16 / OBR-32 Physician of Record in RAD-132.

## 3. Table 4.130.4.1.2.2-1: MWL to UPS-RS mapping (4.130.4.1.2.2)

Rules: "The Requester and the Responder shall meet the requirements in Section 4.130.4.1.2.1 (MWL) using the corresponding RESTful mechanisms as described in DICOM PS3.18 Section 11.9" with these attribute mappings. SCU/SCP columns of Table 4.130.4.1.2.1-1 apply to user-agent/origin-server respectively. No workitem management is presumed (no claim/subscribe). Both sides shall support `application/dicom+json` (4.130.4.2.2.2). HTTPS permitted (4.130.5).

| MWL attribute | Tag | UPS placement |
|---|---|---|
| Patient's Name, Patient ID, Issuer of Patient ID, Other Patient IDs Sequence, Patient's Birth Date, Patient's Sex, Confidentiality constraint | (0010,0010) (0010,0020) (0010,0021) (0010,1002) (0010,0030) (0010,0040) (0040,3001) | Same (top level) |
| Institution Name, Institution Code Sequence, Institution Address, Institutional Department Name, Institutional Department Type Code Sequence, Admission ID, Issuer of Admission ID Sequence | (0008,0080) (0008,0082) (0008,0081) (0008,1040) (0008,1041) (0038,0010) (0038,0014) | Same (top level) |
| Admitting Date/Time, Admitting Diagnoses Description/Code Seq, Reason for Visit (+ Code Seq) | (0038,0020) (0038,0021) (0008,1080) (0008,1084) (0032,1066) (0032,1067) | Same (top level) |
| Referring Physician's Name | (0008,0090) | Same, **inside Referenced Request Sequence (0040,A370)** |
| Referring Physician Identification Sequence, Referring Physician's Telephone Numbers | (0008,0096) (0008,0094) | Same (top level) |
| Current Patient Location | (0038,0300) | Same |
| Accession Number | (0008,0050) | Same, inside (0040,A370) |
| Issuer of Accession Number Sequence | (0008,0051) | Same, inside (0040,A370) |
| Requesting Service (+ Code Seq) | (0032,1033) (0032,1034) | Same, inside (0040,A370) |
| Requested Procedure Description | (0032,1060) | Same, inside (0040,A370) |
| Requested Procedure Code Sequence | (0032,1064) | Same, inside (0040,A370) |
| Reason for the Requested Procedure (+ Code Seq) | (0040,1002) (0040,100A) | Same, inside (0040,A370) |
| Study Instance UID | (0020,000D) | Same (top level; the UPS IOD also carries it inside (0040,A370)) |
| Scheduled Procedure Step Sequence | (0040,0100) | not nested in UPS; items map individually: |
| >Scheduled Station AE Title | (0040,0001) | Scheduled Station Name Code Sequence (0040,4025): AE title in **Code Meaning**, local coding scheme |
| >SPS Start Date + Start Time | (0040,0002) (0040,0003) | Scheduled Procedure Step Start DateTime (0040,4005) |
| >SPS Location | (0040,0011) | Scheduled Station Geographic Location Code Sequence (0040,4027) |
| >Modality | (0008,0060) | Scheduled Station Class Code Sequence (0040,4026), codes from PS3.16 CID 29 |
| >Scheduled Performing Physician's Name | (0040,0006) | Human Performer's Name (0040,4037) in Scheduled Human Performers Sequence (0040,4034) |
| >Scheduled Protocol Code Sequence | (0040,0008) | Scheduled Workitem Code Sequence (0040,4018) |
| >SPS Description | (0040,0007) | Procedure Step Label (0074,1204) |

Monitor consequences for a UPS-RS search (GET .../workitems?...):
- Required user-agent query parameters mirror the SCU R+* list above, expressed as UPS attributes: e.g. `00400001` has no top-level home; the station identity travels as `ScheduledStationNameCodeSequence.CodeMeaning` (the table puts the AET in Code Meaning, not Code Value). Gazelle EBIW_30 reads it the same way ("value of Code Meaning").
- Modality filter is `ScheduledStationClassCodeSequence.CodeValue=US|XC` with scheme DCM (CID 29).
- Accession / issuer / requested procedure live under `ReferencedRequestSequence.*` in the response; a response with them at top level only is a mapping error.
- The Encounter Manager must still return the same AET and modality it was given (4.130.4.1.3 applies via 4.130.4.1.2.2).

## 4. Expected Actions, Responder (4.130.4.1.3) as a checklist

| # | Requirement (shall) | How to check |
|---|---|---|
| 1 | Accept and process the request; parse matching keys; compose worklist entries with the requested return keys | any response at all; compare identifier vs response keys |
| 2 | Match Patient ID (and Issuer, if provided) whether it sits in the primary ID or inside Other Patient IDs Sequence (0010,1002) | query with an ID that only exists in Other Patient IDs; expect a match |
| 3 | Still include "scheduled" details (SPS Sequence item / UPS scheduled info) even though nothing was scheduled | SPS item present in every response |
| 4 | Return the Scheduled Station AE Title (0040,0001) received as matching key, unchanged, as return key | response SPS AET == identifier SPS AET |
| 5 | Return the Modality (0008,0060) received as matching key, unchanged | response SPS Modality == identifier Modality |
| 6 | If the entry has no specifically scheduled datetime, populate SPS Start Date/Time (0040,0002)/(0040,0003) with the current date and time | date/time of the query, local to the EM |
| 7 | When returning SPS Description (0040,0007), Requested Procedure Description (0032,1060) and/or Code Sequence (0032,1064), a generic "Perform Imaging" style value is permitted | not a defect if generic |
| 8 | (47.1.1.1, Vol 1) Same accession for the same admission to the same device, unless an additional encounter is determined | repeat the same query twice from the same AET; accession and Study UID stable |
| 9 | (47.1.1.1) Issuer of Accession Number configurable; accession collision avoidance configurable (prefix/suffix) | ask the operator; look at (0008,0051) |
| 10 | (47.1.1.1) Can populate required fields for "John Doe" patients | EBIW_50/55 |
| 11 | (47.2.1 POCUS) EM maps PV1-19 to Admission ID and PV1-7 to Physician(s) of Record (text says (0008,009D); return key is (0008,1049)) | compare ADT in vs MWL out |

Not required of the Responder: knowing which encounters are complete; filtering by AET/Modality (the values "may be helpful ... to tailor the response", nothing more).

Expected Actions, Requester (4.130.4.2.3): shall accept the responses; no other wire-visible obligation. Base RAD-130 leaves display to product design; the POCUS Option's R+ rows (Section 2 above) must be displayed.

## 5. Example query patterns (4.130.4.1.2.3, informative)
Wristband (Patient ID or Admission ID, with issuer); by department (0008,1040)/(0008,1041) with an SPS start date range; by operator (0040,0006); by room (0040,0011). Note: SCUs recommended to append `*` to each component of a structured Patient's Name; date/time single-value matching is "by meaning", range matching recommended when in doubt.
