---
event: IHE NA Connectathon 2026
source: IHE RAD TF Supplement EBIW rev 3.1 (2025-06-19), RAD TF-2 4.131 (Table 4.131.4.1.2-1, 4.131.4.1.2.1, 4.131.4.1.2.2.1 Table 4.131.4.1.2.2.1-1, 4.131.4.1.2.2.2, 4.131.4.1.3); RAD TF-2x A.6 (Table A.6-1), A.7 (Table A.7-1), Appendix O (Table O-1); type notation RAD TF-2 rev 23.0 Section 2.2
status: transcribed
---
# RAD-131 Store Encounter Images: monitor checklists

Sender = Acquisition Modality (SCU). Receiver = Image Manager / Image Archive (SCP). Table 4.131.2-1.
Under the POCUS Option the modality stores to the **POCUS Manager** instead (47.2.1), and the POCUS Manager is in turn the Sender toward the Image Manager (4.131.4.1.2.2.2). Lightweight Modalities use RAD-108 STOW-RS, not this transaction.

Type codes (RAD TF-2 2.2): **R** DICOM type 1 already, IHE adds constraints; **R+** IHE makes it type 1 ("shall be present with a value in images created by the Acquisition Modality"); **RC+** type 1C when the condition holds; **O** DICOM type 2/3, no IHE addition.

Two global rules in 4.131.4.1.2:
- "The Sender shall omit the Request Attributes Sequence (0040,0275)." Presence = order-based or imported, not encounter-based (also 4.132.4.1.1).
- Images may be sent in one or several associations, as they become available or collectively.

## 1. Table 4.131.4.1.2-1: Required Attributes (all Senders)

"Source" column: where the value comes from per Table A.6-1 (MWL = copied from the RAD-130 response; Modality = originated on the device) and Table U-1 for the ADT origin, so a monitor can trace a wrong value back one hop.

### Patient / institution / visit (all copied from MWL per A.6-1)

| Attribute | Tag | Type | Sender must | Source |
|---|---|---|---|---|
| Patient's Name | (0010,0010) | R+ | value present | MWL copy |
| Patient ID | (0010,0020) | R+ | value present | MWL copy |
| Issuer of Patient ID | (0010,0021) | R+ | value present | MWL copy |
| Issuer of Patient ID Qualifiers Sequence | (0010,0024) | O | | |
| Other Patient IDs Sequence | (0010,1002) | O | | MWL copy if present |
| Patient's Birth Date | (0010,0030) | R+ | value present (zero-length allowed only if the EM truly had none, RAD TF-2 2.2) | MWL copy |
| Patient's Sex | (0010,0040) | R+ | value present | MWL copy |
| Ethnic Group / Weight / Size / Patient State / Pregnancy Status / Medical Alerts / Contrast Allergies | (0010,2160) (0010,1030) (0010,1020) (0038,0500) (0010,21C0) (0010,2000) (0010,2110) | O | | |
| Institution Name | (0008,0080) | R+ | value present | MWL copy |
| Institution Address | (0008,0081) | R+ | value present | MWL copy |
| Institution Code Sequence | (0008,0082) | R+ | item present | MWL copy |
| Institutional Department Name | (0008,1040) | R+ | value present | MWL copy |
| Institutional Department Type Code Sequence | (0008,1041) | R+ | item present | MWL copy |
| Admission ID | (0038,0010) | R+ | value present | MWL copy |
| Issuer of Admission ID Sequence | (0038,0014) | R+ | item present | MWL copy |
| Consulting Physician's Name / Identification Seq | (0008,009C) (0008,009D) | O | | |
| Referring Physician's Name / Address / Telephone / Identification Seq | (0008,0090) (0008,0092) (0008,0094) (0008,0096) | O | | |
| Admitting Diagnoses Description / Code Seq | (0008,1080) (0008,1084) | O | | |
| Reason for Visit / Code Seq | (0032,1066) (0032,1067) | O | | MWL copy if present (A.6-1) |
| Route of Admissions | (0038,0016) | O | | |

### Study

| Attribute | Tag | Type | Sender must | Source |
|---|---|---|---|---|
| Study Instance UID | (0020,000D) | R | use the EM-generated UID from MWL; modality-generated only in the no-context exception (4.131.4.1.2.1) | MWL copy |
| Accession Number | (0008,0050) | R+ | value present, = MWL accession | MWL copy |
| Issuer of Accession Number Sequence | (0008,0051) | R+ | item present; "can also be an indicator to differentiate encounter-based imaging from unscheduled radiology" | MWL copy |
| Study Date | (0008,0020) | R+ | value present | Modality |
| Study Time | (0008,0030) | R+ | value present | Modality |
| Study Description | (0008,1030) | R+ | value present; "many hanging protocols and data browsing interfaces use this prominently" | Modality |
| Study ID | (0020,0010) | O | | |
| Procedure Code Sequence | (0008,1032) | O | optional in the TF; Gazelle EBIW_20/30 expect it, mapped from (0032,1064) else (0032,1060), because the Image Manager maps it into OBR-4 | Modality from MWL |
| Reason for Performed Procedure Code Sequence | (0040,1012) | O | "strongly recommended"; codes in RAD TF-2x App. O. POCUS Option makes it RC+ (training), see Section 2 | Modality |
| Name of Physician(s) Reading Study / Identification Seq | (0008,1060) (0008,1062) | O | | |
| Physician(s) of Record | (0008,1048) | O | "May contain Admitting Physician" | |
| Physician(s) of Record Identification Sequence | (0008,1049) | O | POCUS Option makes it RC+, see Section 2 | MWL copy |

### Series / equipment / anatomy

| Attribute | Tag | Type | Sender must | Source |
|---|---|---|---|---|
| Series Date | (0008,0021) | R+ | value present | Modality |
| Series Time | (0008,0031) | R+ | value present | Modality |
| Series Description | (0008,103E) | R+ | value present | Modality |
| Series Description Code Sequence | (0008,103F) | O | | |
| Modality | (0008,0060) | R | value present (DICOM type 1); US for POCUS, XC for photography (47.1.1.2) | Modality |
| Performing Physician's Name / Identification Seq | (0008,1050) (0008,1052) | O | | |
| Operators' Name | (0008,1070) | R+ | value present; "attributing the images to a specific person for quality purposes" | Modality |
| Operator Identification Sequence | (0008,1072) | R+ | item(s) present; one item per operator under POCUS (4.131.4.1.2.2.1) | Modality |
| Body Part Examined | (0018,0015) | R+ | value present | Modality |
| Laterality | (0020,0060) | O | | |
| Anatomic Region Sequence | (0008,2218) | O | "strongly recommended", CID 4 | |
| Anatomic Region Modifier Sequence | (0008,2220) | O | | |
| Primary Anatomic Structure Sequence | (0008,2228) | O | CID 4 | |
| Primary Anatomic Structure Modifier Sequence | (0008,2230) | O | | |

### Series rules (4.131.4.1.2.1)
- Images added after a procedure step completes -> new Series.
- Different equipment -> new Series (single Frame of Reference per series).
- Different patient positioning (different FoR) -> new Series, unless FoR absent.
- Same as RAD TF-2 4.8.4.1.1.1 for SWF.

## 2. POCUS Option: Required Modality Attributes (4.131.4.1.2.2.1, Table 4.131.4.1.2.2.1-1)

"In addition to" Table 4.131.4.1.2-1.

| Attribute | Tag | Type | Condition / Sender must | Source |
|---|---|---|---|---|
| Physician(s) of Record Identification Sequence | (0008,1049) | RC+ | "Required if provided in the MWL response"; "shall copy ... from the MWL response, if present" | MWL copy |
| Reason for Performed Procedure Code Sequence | (0040,1012) | RC+ | "Required if the study is a training study"; training identified with **(129012, DCM, "Educational Intent")**; other App. O codes typically alongside | Modality |

Text requirements in the same section:
- Attribute consistency per RAD TF-2x A.6 before sending to the POCUS Manager.
- Operator Identification Sequence (0008,1072): multiple items when multiple operators participated; the same operator may appear twice with different IDs (local employee ID + NPI, note at line 2059).
- 47.2.1 (Vol 1) adds: operator and patient identification by barcode/RFID/QR; imaging of unregistered patients must still be possible, with metadata indicating missing patient identification; operators identified before capture; training studies identified at acquisition time via (0040,1012).

Monitor check for a training study: (0040,1012) contains 129012/DCM AND no RAD-132 was sent to the Result Aggregator for it (4.132.4.1.1.1).

## 3. POCUS Manager Coercion (4.131.4.1.2.2.2)

The POCUS Manager is the Receiver from the modality and the Sender to the Image Manager. Shall:

| # | Requirement | Check |
|---|---|---|
| 1 | Ensure attribute consistency per RAD TF-2x A.7 before transmitting to the Image Manager | compare modality-sent vs PM-sent headers against Table A.7-1 below |
| 2 | Be able to split one acquired study into multiple studies: new Accession Number, Study Description and Study Instance UID per new study; update attributes per A.7; worksheet may supply values; whether the original UID/accession is reused for one of the split studies is implementation choice | only testable if a split is demonstrated (EBIW_POCUS_Non-privileged_Flow step 120 "hard split") |
| 3 | (47.1.1.5) Generate Study UIDs and accessions; Issuer of Accession Number configurable; collision avoidance configurable | ask operator; check (0008,0051) on PM-sent images |
| 4 | (47.1.1.5) Separate clinical and training studies | training study must not reach RA via RAD-132; may or may not reach IM (test 13934 says IM store is "clinical study only") |
| 5 | (47.2.1) Image Manager shall be configurable to NOT send RAD-132 for instances received from the POCUS Manager | ask IM operator; otherwise RA gets duplicate notifications |

Receiver Expected Actions (4.131.4.1.3): store so that RAD-16 retrieval works; DICOM Level 2 Storage SCP (PS3.4 B.4.1).

## 4. Table A.6-1: Required Mapping for the POCUS Modality (RAD TF-2x A.6)

Columns: MWL (return attribute values) / Original Image or Standalone IOD / Append Image or Standalone IOD. "Source" = originates here, "Copy" = copied from the Source column, "n.a." = not applicable. IHE-A.6.1: for MWL-sourced rows the append image may copy from the original image. IHE-A.6.2: the append case creates new series with their own Series Date/Time/Description.

| Attribute | Tag | MWL | Original image | Append image |
|---|---|---|---|---|
| Patient's Name | (0010,0010) | Source | Copy | Copy |
| Patient ID | (0010,0020) | Source | Copy | Copy |
| Issuer of Patient ID | (0010,0021) | Source | Copy | Copy |
| Other Patient IDs Sequence | (0010,1002) | Source | Copy | Copy |
| Patient's Birth Date | (0010,0030) | Source | Copy | Copy |
| Patient's Sex | (0010,0040) | Source | Copy | Copy |
| Institution Name | (0008,0080) | Source | Copy | Copy |
| Institution Code Sequence | (0008,0082) | Source | Copy | Copy |
| Institution Address | (0008,0081) | Source | Copy | Copy |
| Institutional Department Name | (0008,1040) | Source | Copy | Copy |
| Institutional Department Type Code Sequence | (0008,1041) | Source | Copy | Copy |
| Admission ID | (0038,0010) | Source | Copy | Copy |
| Issuer of Admission ID Sequence | (0038,0014) | Source | Copy | Copy |
| Admitting Date | (0038,0020) | Source | Copy | Copy |
| Admitting Time | (0038,0021) | Source | Copy | Copy |
| Reason for Visit | (0032,1066) | Source | Copy | Copy |
| Reason for Visit Code Sequence | (0032,1067) | Source | Copy | Copy |
| Physician(s) of Record Identification Sequence | (0008,1049) | Source | Copy | Copy |
| Accession Number | (0008,0050) | Source | Copy | Copy |
| Issuer of Accession Number Sequence | (0008,0051) | Source | Copy | Copy |
| Requested Procedure Description | (0032,1060) | Source | n.a. | n.a. |
| Requested Procedure Code Sequence | (0032,1064) | Source | n.a. | n.a. |
| Scheduled Procedure Step Sequence | (0040,0100) | Source | n.a. | n.a. |
| >Scheduled Station AE Title | (0040,0001) | Source | n.a. | n.a. |
| >SPS Start Date | (0040,0002) | Source | n.a. | n.a. |
| >SPS Start Time | (0040,0003) | Source | n.a. | n.a. |
| >Modality | (0008,0060) | Source | n.a. | n.a. |
| >SPS Description | (0040,0007) | Source | n.a. | n.a. |
| Study Instance UID | (0020,000D) | Source | Copy | Copy |
| Operators' Name | (0008,1070) | n.a. | Source | Copy |
| Operator Identification Sequence | (0008,1072) | n.a. | Source | Copy |
| Study Date | (0008,0020) | n.a. | Source | Copy |
| Study Time | (0008,0030) | n.a. | Source | Copy |
| Study Description | (0008,1030) | n.a. | Source | Copy |
| Reason for Performed Procedure Code Sequence | (0040,1012) | n.a. | Source | Copy |
| Body Part Examined | (0018,0015) | n.a. | Source | Copy |
| Series Date | (0008,0021) | n.a. | Source | Copy, see IHE-A.6.2 |
| Series Time | (0008,0031) | n.a. | Source | Copy, see IHE-A.6.2 |
| Series Description | (0008,103E) | n.a. | Source | Copy, see IHE-A.6.2 |

Reading note: A.6-1 does not say the modality must carry Requested Procedure Code/Description into the image (n.a.); the Gazelle tests nevertheless ask for Procedure Code Sequence (0008,1032) mapped from them. Treat (0008,1032) as a test-defined expectation, not an A.6-1 one.

## 5. Table A.7-1: POCUS Manager Integration, Critical Attributes (RAD TF-2x A.7)

Columns: Objects from Modality / Worksheet / Original images sent to IM / Append images sent to IM / HL7 v2.5.1 ORU report sent to the Result Aggregator. All values in a row shall be consistent except where noted. Worksheet is not transferred but drives mapping (Note 1). "Equal" = the actor already holds the value (IHE-A.7.9).

| Attribute | Tag | From modality | Worksheet | Original to IM | Append to IM | ORU field |
|---|---|---|---|---|---|---|
| Patient's Name | (0010,0010) | Source | Copy (A.7.9) | Copy | Copy | Copy PID-5 |
| Patient ID | (0010,0020) | Source | Copy (A.7.9) | Copy | Copy | Copy PID-3 |
| Issuer of Patient ID | (0010,0021) | Source | Copy (A.7.9) | Copy | Copy | Copy PID-3 (.4) |
| Other Patient IDs Sequence | (0010,1002) | Source | Copy (A.7.9) | Copy | Copy | Copy PID-4 (note: RAD-128 PID table marks PID-4 as X, see rad-132-checklists) |
| Patient's Birth Date | (0010,0030) | Source | Copy (A.7.9) | Copy | Copy | Copy PID-7 |
| Patient's Sex | (0010,0040) | Source | Copy (A.7.9) | Copy | Copy | Copy PID-8 |
| Institution Name | (0008,0080) | Source | Copy (A.7.9) | Copy | Copy | Copy PV1-39 |
| Institution Code Sequence | (0008,0082) | Source | Copy (A.7.9) | Copy | Copy | n.a. |
| Institution Address | (0008,0081) | Source | Copy (A.7.9) | Copy | Copy | Copy PV1-3 (A.7.1) |
| Institutional Department Name | (0008,1040) | Source | Copy (A.7.9) | Copy | Copy | Copy PV1-3 |
| Institutional Department Type Code Sequence | (0008,1041) | Source | Copy (A.7.9) | Copy | Copy | Copy PV1-3 (and drives OBR-24, 4.132.4.1.2.1) |
| Admission ID | (0038,0010) | Source | Copy (A.7.9) | Copy | Copy | Copy PV1-19 |
| Issuer of Admission ID Sequence | (0038,0014) | Source | Copy (A.7.9) | Copy | Copy | Copy PV1-19 (.4) |
| Admitting Date | (0038,0020) | Source | Copy (A.7.9) | Copy | Copy | Copy PV1-44 |
| Admitting Time | (0038,0021) | Source | Copy (A.7.9) | Copy | Copy | Copy PV1-44 |
| Reason for Visit | (0032,1066) | Source | Copy (A.7.9) | Copy | Copy | n.a. |
| Reason for Visit Code Sequence | (0032,1067) | Source | Copy (A.7.9) | Copy | Copy | n.a. |
| Physician(s) of Record Identification Sequence | (0008,1049) | Source | Copy (A.7.2: PM may coerce in the worksheet if absent from MWL) | Copy | Copy | Copy ORC-12 |
| Accession Number | (0008,0050) | Source | Copy (A.7.3: split -> new accession) | Copy | Copy | Copy OBR-18 (A.7.4: OBR-3 may also carry it) |
| Issuer of Accession Number Sequence | (0008,0051) | Source | Copy (A.7.5: if PM coerces the accession, issuer = PM's assigning authority) | Copy | Copy | Copy OBR-18 (A.7.4) [sic: OBR-19 per 4.132.4.1.2.1; see rad-132-checklists] |
| Study Instance UID | (0020,000D) | Source | Copy (A.7.3) | Copy | Copy | Copy OBX-5 |
| Operators' Name | (0008,1070) | Source | Copy (A.7.8) | Copy | Copy | Copy "ORC-1 and OBR-32 or OBR-33" (A.7.8) [sic: ORC-1 is Order Control; read as ORC-12] |
| Operator Identification Sequence | (0008,1072) | Source | Copy (A.7.8) | Copy | Copy | Equal "ORC-1 and OBR-32 or OBR-33" (A.7.8) [same sic] |
| Study Date | (0008,0020) | Source | Copy | Copy | Copy | Copy OBR-7 |
| Study Time | (0008,0030) | Source | Copy | Copy | Copy | Copy OBR-7 |
| Study Description | (0008,1030) | Source | Copy (A.7.3) | Copy | Copy | Copy OBR-4 |
| Reason for Performed Procedure Code Sequence | (0040,1012) | Source | Copy (A.7.7) | Source | Source | Copy OBR-31 |
| Body Part Examined | (0018,0015) | Source | Copy (A.7.6) | Copy | Copy | n.a. |
| Series Date | (0008,0021) | Source | n.a. | Copy | Source (A.7.10) | n.a. |
| Series Time | (0008,0031) | Source | n.a. | Copy | Source (A.7.10) | n.a. |
| Series Description | (0008,103E) | Source | n.a. | Copy | Source (A.7.10) | n.a. |
| Modality | (0008,0060) | Source | Copy | Copy | Copy | n.a. |

Notes (A.7.1-A.7.10), paraphrased:
- A.7.1 PV1-3 Assigned Patient Location is the hierarchical PL (point of care, room, bed, facility, ...).
- A.7.2 (0008,1049) may be coerced by the PM in the worksheet if the MWL lacked it.
- A.7.3 Multiple worksheets -> PM shall split into multiple studies with new Accession, Study Description, Study UID (4.131.4.1.2.2.2).
- A.7.4 OBR-3 Filler Order Number may also contain the Accession Number.
- A.7.5 Coerced accession -> (0008,0051) = PM's assigning authority.
- A.7.6 Body Part may be coerced if the worksheet changed it; per split study.
- A.7.7 (0040,1012) populated by the modality for training studies; PM may reassign/coerce on split.
- A.7.8 With multiple operators the worksheet distinguishes the Physician of Record from POCUS learners (-> OBR-32 vs OBR-33).
- A.7.9 PM grouped with EM may coerce; then "Equal".
- A.7.10 Append creates new series with own Series Date/Time/Description.

### A.7-1 as a coercion diff for the monitor
Compare the modality-to-PM header against the PM-to-IM header for the same study:
- Must be identical unless a note permits coercion: everything in the patient/visit block (A.7.9 only applies when PM is grouped with EM), Study UID and Accession unless a split happened (A.7.3), Body Part unless worksheet changed it (A.7.6), Reason for Performed Procedure (A.7.7).
- Legitimately different on append: Series Date/Time/Description (A.7.10).
- (0008,1049) may appear on PM output but not on modality output (A.7.2).
- If the accession changed, (0008,0051) must now name the PM (A.7.5).

## 6. Appendix O, Table O-1 (informative): Reason for Performed Procedure codes seen in POCUS

DCM 129012 Educational Intent (the training marker, normative via 4.131.4.1.2.2.1); LN 69280-6, 39415-5, 80871-7, 80877-4, 39527-7, 87162-4, 38032-9, 25059-7, 30643-1, 87144-2, 87019-6, 87017-0; SCT 401186003, 710241003, 431805002, 61593002, 439864002 (FAST). Full meanings on supplement pp. 125-126. Gazelle tests call Appendix O/U adherence "highly recommended", not required.
