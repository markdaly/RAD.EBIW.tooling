---
event: IHE NA Connectathon 2026
source: IHE RAD TF Supplement EBIW rev 3.1 (2025-06-19), RAD TF-2 4.132 (Table 4.132.4.1.2-1; 4.132.4.1.2.1 Tables 4.132.4.1.2.1-1/-2; 4.132.4.1.2.2; 4.132.4.1.2.3.1-.4 Tables 4.132.4.1.2.3.2-1, 4.132.4.1.2.3.4-1; 4.132.4.1.3; 4.132.4.2); IHE RAD TF Supplement Results Distribution (RD) rev 1.2 (2019-08-09) 4.128.4.1.2.2-.5, 4.128.4.1.2.8-.9, 4.128.4.2 (the segment sections EBIW points to but does not reprint); RAD TF-2 rev 23.0 (2025-08-08) 2.3.1, 2.4.1.2, 2.4.4.1-.3 (HL7 conventions, MSH, ACK)
status: transcribed (EBIW from the extracted PDF text; RD and RAD TF-2 text pulled from the published PDFs via pdf.js, page numbers given; Gazelle EBIW_90 expectations cross-referenced)
---
# RAD-132 Notify of Imaging Results: monitor checklists

Sender = Image Manager/Image Archive or POCUS Manager. Receiver = Result Aggregator (required receiver) or Encounter Manager (optional, 47.1.1.3). Table 4.132.2-1.
Message: HL7 v2.5.1 ORU^R01 over MLLP (RAD TF-2 2.4.1.1), Original Mode ACK (2.4.1.2). Message spec "is based on the Send Imaging Result Message in [RAD-128] with minor changes" (4.132.4.1.2).

Usage codes (RAD TF-2 2.3.1, rev 23.0 pp. 40-42): **R** sender shall populate non-empty; **R2/RE** shall send if the sender has the data; **O** undefined; **C/CE** by predicate; **X** shall not be sent. Receivers "may ignore" required elements but "may raise an error due to the absence of a required element".

POCUS Option optionality flips, collected (4.132.4.1.2.3.x): PV1-19 R2->R; OBR-4 "R2->R" (base table already says R, see note); OBR-16 O->R; OBR-32 R2->R; Finding OBX becomes "shall be sent for POCUS reports"; ORC stays optional but if sent ORC-1 R (=RE) and ORC-12 R2.

## 1. Table 4.132.4.1.2-1: message structure

| Segment | Content | HL7 ch. | Spec section | Usage |
|---|---|---|---|---|
| MSH | Message Header | 2 | RD 4.128.4.1.2.2 | R |
| PID | Patient Identification | 3 | RD 4.128.4.1.2.3 | R |
| PV1 | Patient Visit | 3 | RD 4.128.4.1.2.4 (+ EBIW 4.132.4.1.2.3.1 under POCUS) | R |
| [ORC] | Order Common | 4 | RD 4.128.4.1.2.5 (+ EBIW 4.132.4.1.2.3.2 under POCUS) | optional |
| OBR | Order Detail | 4 | EBIW 4.132.4.1.2.1 (+ 4.132.4.1.2.3.3 under POCUS) | R; may repeat under POCUS for multi-procedure sessions (4.132.4.1.2.3.3) |
| TQ1 | Timing/Quantity | 4 | EBIW 4.132.4.1.2.2 | R (may be empty) |
| OBX | DICOM Study Instance UID | 7 | RD 4.128.4.1.2.8 | R (unbracketed in the EBIW table; RD says "shall be included if the Study Instance UID is known") |
| [{OBX}] | Findings | 7 | EBIW 4.132.4.1.2.3.4 | optional in base; "shall be sent for POCUS reports" |

Note 1 of the table: POCUS Senders see 4.132.4.1.2.3. Z-segments: prohibited unless defined for the transaction (RAD TF-2 2.4.1.5); none is defined for RAD-132.

## 2. MSH (RD 4.128.4.1.2.2 -> ITI TF-2b 3.30.5.1; RAD TF-2 2.4.4.2 Table 2.4-6)

| Field | Usage | Sender must | Note |
|---|---|---|---|
| MSH-1, MSH-2 | R | `|` and `^~\&` recommended; any ASCII permitted | 2.4.4.2 |
| MSH-3, MSH-4 | R | Sending Application / Facility valued | match the Gazelle system registration for the proxy |
| MSH-5, MSH-6 | R | Receiving Application / Facility valued | |
| MSH-7 | R | Date/Time of Message | |
| MSH-8 | X | not sent | |
| MSH-9 | R | `ORU^R01^ORU_R01`, all three components | RD 4.128.4.1.2.2 (verbatim: "shall have three components ... ORU ... R01 ... ORU_R01"); RAD TF-2 2.4.4.2 MSH-9: "All three components are required." |
| MSH-10 | R | unique Message Control ID; echoed in MSA-2 | |
| MSH-11 | R | Processing ID | |
| MSH-12 | R | first component `2.5.1` or higher | 2.4.4.2; 2.4.1.3 permits higher. `2.4` fails. |
| MSH-14, MSH-20 | X | not sent | |
| MSH-15, MSH-16 | O [0..0] | | |
| MSH-17 | RE | country code ISO 3166 alpha-3 if available | |
| MSH-18 | C | only if a non-ASCII character set; one value only | 2.4.4.2 |
| MSH-19 | RE | ISO 639 if available | |
| MSH-21 | RE | profile id if one is registered | |

## 3. PID (RD 4.128.4.1.2.3, Table 4.128.4.1.2.3-1, RD p. 30-31)

| SEQ | Field | DT | Usage | Sender must | POCUS source (A.7-1) |
|---|---|---|---|---|---|
| 2 | Patient ID | CX | X | not sent (an ID in PID-2 only = defect) | |
| 3 | Patient Identifier List | CX | R | PID-3.1 ID and PID-3.4 Assigning Authority "shall be present"; PID-3.5 type code if known (PI typical) | (0010,0020) + (0010,0021) |
| 4 | Alternate Patient Identifier List | CX | X | not sent | A.7-1 maps (0010,1002) Other Patient IDs to PID-4: conflict; treat extra IDs as repeats of PID-3 |
| 5 | Patient Name | XPN | R | valued | (0010,0010) |
| 7 | Date/Time of Birth | TS | R2 | if known | (0010,0030) |
| 8 | Administrative Sex | IS | R2 | if known | (0010,0040) |
| 9 | Patient Alias | XPN | X | | |
| 11 | Patient Address | XAD | R2 | | |
| 12 | Country Code | IS | X | | |
| 13, 14 | Phone Home / Business | XTN | R2 | | |
| 18 | Patient Account Number | CX | R2 | | |
| 19, 20 | SSN, Driver's License | | X | not sent | |
| 27 | Veterans Military Status | CE | R2 | | |
| 28 | Nationality | CE | X | | |

Gazelle EBIW_90 checks PID-3 (.1 and .4), PID-5, PID-7, PID-8 as "value required".

## 4. PV1 (RD 4.128.4.1.2.4, Table 4.128.4.1.2.4-1, RD p. 32-33; EBIW 4.132.4.1.2.3.1)

| SEQ | Field | DT | Usage (RD) | POCUS | Sender must | Source |
|---|---|---|---|---|---|---|
| 2 | Patient Class | IS | R | R | valued (EBIW_90 uses O) | |
| 3 | Assigned Patient Location | PL | R2 | | if known; A.7-1 puts Institution Address, Dept Name, Dept Type here | (0008,0081)/(0008,1040)/(0008,1041) |
| 6 | Prior Patient Location | PL | R2 | | | |
| 7 | Attending Doctor | XCN | R2 | | if known; family+given names required when sent; ID and assigning authority strongly recommended | |
| 8 | Referring Doctor | XCN | R2 | | same rule | |
| 9 | Consulting Doctor | XCN | X | | | |
| 10 | Hospital Service | IS | C | | | |
| 17 | Admitting Doctor | XCN | R2 | | same rule as PV1-7 | |
| 19 | Visit Number | CX | R2 | **R** | "shall be valued with the Admission ID (0038,0010) from the images" (4.132.4.1.2.3.1); RD: use Admission ID when images have it. Assigning authority in PV1-19.4 is what the Gazelle test expects (marked OK-if-missing there) | (0038,0010) + (0038,0014) |
| 39 | Servicing Facility | | not in RD table | | A.7-1 maps Institution Name here | (0008,0080) |
| 40 | Bed Status | IS | X | | | |
| 44 | Admit Date/Time | | not in RD table | | A.7-1 maps Admitting Date/Time here | (0038,0020)/(0038,0021) |
| 51 | Visit Indicator | IS | C | | `V` whenever PV1-19 is valued (RD) | |
| 52 | Other Healthcare Provider | XCN | R2 | | RD: for encounter-based results, operators (0008,1070)/(0008,1072) and performing physician (0008,1050)/(0008,1052) may go here | |

Receiver action under POCUS (4.132.4.1.3.1): "link the report conveyed in the OBX segment to the Encounter identified in PV1-19 Admission ID".

## 5. ORC (RD 4.128.4.1.2.5; EBIW 4.132.4.1.2.3.2, Table 4.132.4.1.2.3.2-1)

RD: recommended NOT to send; if sent, must be identical to analogous OBR fields. EBIW POCUS: may be included so the Result Aggregator can create/manage an order; all fields optional except:

| SEQ | Field | DT | Usage | Sender must |
|---|---|---|---|---|
| 1 | Order Control | ID | R | `RE` |
| 12 | Ordering Provider | XCN | R2 | Physician of Record, NPI in the US; "ORC-12 duplicates OBR-16", send the same value in both |

## 6. OBR (EBIW 4.132.4.1.2.1, Table 4.132.4.1.2.1-1; POCUS 4.132.4.1.2.3.3)

Base = EBIW table (which already differs from RD Table 4.128.4.1.2.6-1; differences noted). POCUS column shows the flip.

| SEQ | Field | DT | Base | POCUS | Sender must | Source |
|---|---|---|---|---|---|---|
| 1 | Set ID | SI | (HL7 R) | | sequential per OBR; 1, 2, ... when OBR repeats | |
| 2 | Placer Order Number | EI | R2 | | typically empty (unordered) | |
| 3 | Filler Order Number | EI | R2 | | typically empty; may carry the accession (A.7.4) | |
| 4 | Universal Service ID | CE | R | R (text says "modified from R2 to R": inconsistent with the base table, which already says R; either way it is R) | first three components valued: 4.1 code, 4.2 meaning, 4.3 coding system; LOINC RadLex Playbook recommended; source order: (0008,1032), else (0032,1064), else generic. POCUS: code derived from the worksheet; 4.4-4.6 may carry CPT; each repeating OBR must have a distinct OBR-4 | (0008,1030)/(0008,1032) |
| 5 | Priority (retired) | ID | X | | not sent | |
| 6 | Requested Date/time | TS | X | | not sent | |
| 7 | Observation Date/Time | TS | R (RD: R2) | | date/time of the imaging; from Study Date/Time or Series Date/Time | (0008,0020)+(0008,0030) |
| 12 | Danger Code | CE | X (RD: R2) | | not sent (4.132.4.1.2.3.3 lists it among omit-able "R2" fields, contradicting the X in the table; don't fail either way) | |
| 16 | Ordering Provider | XCN | O (RD: R2) | **R** | Physician of Record incl. NPI (US) | (0008,1049) |
| 18 | Placer Field 1 | ST | R | | Accession Number (0008,0050) | |
| 19 | Placer Field 2 | ST | R2 | | Assigning Authority corresponding to (0008,0051); OBR-18 may carry a prefix/suffix hint | |
| 22 | Results Rpt/Status Chng Date/Time | TS | (absent from EBIW table; RD: R) | | unverified whether required in RAD-132; HL7 base makes it conditional. Do not fail on absence | |
| 24 | Diagnostic Serv Sect ID | ID | R (RD: R2) | | derived from Institutional Department Type Code Sequence (0008,1041), possibly via a mapping table to HL7 Table 0074 (e.g. `US`, `RAD`) | |
| 25 | Result Status | ID | R | | `R` (stored, not verified), `F` (final), `C` (correction). **Never `P`** (Table 4.132.4.1.2.1-2 note) | |
| 27 | Quantity/Timing | TQ | R | | backwards compatibility only: OBR-27.6 Priority = TQ1-9.1; all other components empty | |
| 28 | Result Copies To | XCN | O | | typically empty | |
| 31 | Reason for Study | CE | R2 | | if known; from (0040,1012), (0040,1002)/(0040,100A), (0032,1066)/(0032,1067), (0008,1080)/(0008,1084) | (0040,1012) per A.7-1 |
| 32 | Principal Result Interpreter | NDL | R2 (RD: R) | **R** | Physician of Record who signs; base text says usually empty for encounter images | (0008,1070)/(0008,1072) per A.7.8 |
| 33 | Assistant Result Interpreter | NDL | R2 | | POCUS Learner, if any | A.7.8 |
| 34 | Technician | NDL | R2 | | person who acquired, from (0008,1070)/(0008,1072) or (0008,1050)/(0008,1052) | |
| 44 | Procedure Code | CE | R | | "shall match OBR-4" | |
| 46 | Placer Supplemental Service Info | CE | R2 | | laterality in the site-modifier component when relevant and not in OBR-4; otherwise omit | |

Multi-procedure POCUS session (eFAST): OBR may repeat, each with distinct OBR-4 (4.132.4.1.2.3.3). RD 4.128 says a single OBR; EBIW POCUS overrides.

## 7. TQ1 (EBIW 4.132.4.1.2.2)

"The TQ1 Segment may be sent empty." If populated, TQ1-9 Priority `R^Routine^HL70078` appropriate; must agree with OBR-27.6. Segment presence is required by Table 4.132.4.1.2-1 (no brackets). Gazelle EBIW_90 expects `R^Routine^HL70078`.

## 8. OBX, DICOM Study Instance UID (RD 4.128.4.1.2.8, Table 4.128.4.1.2.8-1, RD p. 40-41)

| SEQ | Field | DT | Usage | Sender must |
|---|---|---|---|---|
| 1 | Set ID | SI | R | |
| 2 | Value Type | ID | R | `ST` |
| 3 | Observation Identifier | CE | R | `113014^DICOM Study^DCM` (first three components) |
| 4 | Observation Sub-ID | ST | C | sequential integer when several Study UID OBX are present |
| 5 | Observation Value | HD (sic, table) | R | the Study Instance UID; one UID per OBX |
| 11 | Observation Result Status | ID | R | `O` ("Order detail description - no result") |
| 23, 24, 25 | Performing Organization Name / Address / Medical Director | XON/XAD/XCN | C | "should" be the acquiring organization |

Example from RD p. 41: `OBX|7|ST|113014^DICOM Study^DCM|1|1.2.840.113532.7.7345.3453445346802.34534||||||O|...`
EBIW: one notification per study at minimum; multiple series may each produce a notification with the same UID (4.132.4.1.1, 4.132.4.1.3). POCUS: one per study when completeness criteria are met; addendum may trigger another; none for training studies (4.132.4.1.1.1).

## 9. OBX, Finding (EBIW 4.132.4.1.2.3.4, Table 4.132.4.1.2.3.4-1; field semantics RD 4.128.4.1.2.9)

Optionality: "shall be sent for POCUS reports". One finding per OBX; repeat per finding; text findings one per OBX recommended (not required).

| SEQ | Field | DT | Usage | Sender must |
|---|---|---|---|---|
| 1 | Set ID | SI | R | continues the OBX numbering after the Study UID OBX |
| 2 | Value Type | ID | R | `CE` or `TX` (not ST, not FT) |
| 3 | Observation Identifier | CE | R | coded finding (e.g. SNOMED) or, for TX, `59776-5^Procedure Findings^LN` (RD 4.128.4.1.2.9) |
| 4 | Observation Sub-ID | ST | C | |
| 5 | Observation Value | CE or TX | R | the finding; LEN 483 (CE) or 99999 (TX) |
| 11 | Observation Result Status | ID | R | `R`, `F` or `C` |

Not carried over from RD Table 4.128.4.1.2.9-1 into the EBIW table: OBX-8 Abnormal Flag and OBX-15 Producer's Reference (both R in RD). EBIW's table is the constraint for RAD-132; absence of OBX-8/15 is not a RAD-132 defect.

## 10. Expected Actions and ACK

Receiver (4.132.4.1.3): accept and process; support multiple messages for the same Study Instance UID. POCUS (4.132.4.1.3.1): link the OBX report to the encounter in PV1-19; if grouped with Image Display Invoker, build a RAD-106 link from the OBX Study UID.

ACK (4.132.4.2 -> RD 4.128.4.2.2, RD p. 52; RAD TF-2 2.4.4.1-.3, rev 23.0 pp. 46-50):
- "HL7 2.5.1 MSA-1 Original Mode Acknowledgement message" (RD 4.128.4.2.2); Original Mode is also the RAD-wide default (RAD TF-2 2.4.1.2).
- Structure (Table 2.4-5): MSH R, MSA R, ERR C [0..*].
- MSH per Table 2.4-6: MSH-9 all three components required (2.4.4.2) -> `ACK^R01^ACK`; MSH-12 `2.5.1`.
- MSA-1: `AA`, `AE` or `AR` (Table 2.4-7 text); MSA-2 = MSH-10 of the ORU; MSA-3 and MSA-6 X (not supported), errors go in ERR (2.4.4.4).
- RD 4.128.4.2.3: invalid ORU -> error acknowledgement; otherwise valid acknowledgement. "The Receiver is not required to send any attributes within the MSA segment beyond what is specified in the HL7 standard."
- Gazelle EBIW_25/35 step 55: MSA-1 AA, MSA-2 = MSH-10 ("the monitor does not have to check that these values match").

## 11. Spec inconsistencies worth knowing before arguing with a vendor
1. OBR-4: 4.132.4.1.2.3.3 says "modified from R2 to R" but Table 4.132.4.1.2.1-1 already lists R. Harmless.
2. OBR-12: table says X, 4.132.4.1.2.3.3 calls it an R2 field implementers "may omit". Don't fail on presence or absence.
3. OBR-16: EBIW base O vs RD R2; POCUS makes it R. OBR-32: EBIW base R2 vs RD R; POCUS makes it R. OBR-7, OBR-24: EBIW R vs RD R2. The EBIW table governs RAD-132.
4. OBR-22 (R in RD) is absent from the EBIW table. Unverified whether EBIW intends to drop it.
5. A.7-1 maps Issuer of Accession Number to OBR-18; 4.132.4.1.2.1 puts it in OBR-19. Follow 4.132.4.1.2.1.
6. A.7-1 says "ORC-1 and OBR-32 or OBR-33" for operators; ORC-1 is Order Control (`RE`). Read as ORC-12.
7. A.7-1 maps Other Patient IDs to PID-4; RD Table 4.128.4.1.2.3-1 marks PID-4 X. Repeating PID-3 is the HL7 v2.5.1 way.
8. Gazelle EBIW_90 cites "RAD TF-3" for 4.132 sections and "4.132.3.1.2.1"; both are typos for RAD TF-2 4.132.4.1.2.1.
