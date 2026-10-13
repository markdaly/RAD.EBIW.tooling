---
event: IHE NA Connectathon 2026
source: tools/mwl_scp.py, tools/ups_rs.py, tools/mllp_receiver.py (checkout as of 2026-10-13 00:00 ET) read against research/rad-130-checklists.md, rad-131-checklists.md, rad-132-checklists.md, gazelle-ebiw-tests.md and from-memory-claims.md
status: verified (code read line by line; nothing executed; findings only, no code)
---
# Tool gaps: what the spec and the Gazelle tests require vs what the stand-ins do

Severity: **blocks a Gazelle step** / **spec deviation** / **cosmetic**. "Required by" cites the section; "tool" states the observed behavior.

## tools/mwl_scp.py (Encounter Manager, RAD-130 MWL; ITI-31 intake)

| # | Required by | Tool does / does not | Severity |
|---|---|---|---|
| M1 | EBIW_10 Part 1(2) and EBIW_20 step 120: two procedures (US and XC) under ONE Admission ID per patient; "MAHAR + Admission ID" must return 2 matches | `encounters()` merges by `admission_id` (`{e["admission_id"]: e ...}`), so a second row with the same Admission ID silently replaces the first. One worklist item per admission, ever. | blocks EBIW_20/30 step 120 and the EBIW_10 data model |
| M2 | Table 4.130.4.1.2.1-1: SPS >Modality (0008,0060) matching SCP = **R**; EBIW_20 step 200 "PEREZ + US, expect 1 match"; EBIW_30 step 200 "PEREZ + XC, expect 1 match" | Modality is echoed from the query (`sps.Modality = sps_q.get("Modality") or "US"`), never a property of the encounter, never filtered. Every encounter matches every modality. | blocks the "1 match" expectations once M1 is fixed; spec deviation on SCP matching |
| M3 | Table 4.130.4.1.2.1-1: SPS >Scheduled Station AE Title (0040,0001) matching SCP = **R**; EBIW_10: EM configures the partner's AET per procedure; EBIW_20 step 110 "Clinical Oncology + own AET, expect 3 matches (PAGE, WAGNER, BERGER)" | AET is echoed, never filtered (comment in `matches()` says so, citing 4.130.4.1.3). 4.130.4.1.3 only says the value "shall be returned" and "may be helpful to tailor the response"; the key table still makes it an SCP matching key. With M1 fixed, step 110 would return 6 rows (3 US + 3 XC) instead of 3 unless AET or Modality filters. | blocks EBIW_20 step 110 count; spec deviation |
| M4 | EBIW_10 Part 1(1): Requested Procedure Description/Code per encounter from the fixed SCT set (3517009, 3787003, 722009, 113091000); EBIW_20 step 220 expects the matching code in (0008,1032) downstream | One global `CONF["procedure"]` ("Perform Imaging", `PERFORM-IMAGING`/`99IHE`) for every encounter. Permitted by 4.130.4.1.3 ("generic code ... such as Perform Imaging"), but EBIW_20/30 evaluation tables name the specific procedure per patient. | blocks EBIW_20/30 step 200/220 value check |
| M5 | Table 4.130.4.1.2.1-1: Issuer of Accession Number Sequence >Universal Entity ID (0040,0032) and >Universal Entity ID Type (0040,0033) return SCP = R+; same for Issuer of Admission ID Sequence; EBIW_10 says the issuer is an OID from Gazelle | Only `LocalNamespaceEntityID` is set in both sequences; (0040,0032)/(0040,0033) absent. An SCU requesting them gets nothing. For an OID issuer the right encoding is Universal Entity ID = OID, Type = `ISO`. | spec deviation (R+ return key missing) |
| M6 | 4.130.4.1.3: "identify Workitems with a matching Patient ID (and Issuer ...) either inside the Other Patient IDs Sequence (0010,1002) or outside" | `OtherPatientIDsSequence` is always empty and matching only looks at the primary ID. Not a defect while the data has no secondary IDs; becomes one if an ADT with repeating PID-3 arrives (`adt_to_encounter` keeps only `split("~")[0]`). | spec deviation (latent) |
| M7 | Table 4.130.4.1.2.1-1: SPS Start Time (0040,0003) matching SCP = R | `matches()` checks SPS Start Date (range) only; a time or time range in the query is ignored (over-matches, never under-matches). | cosmetic |
| M8 | 47.1.1.1: same accession "for the same admission to the same device" | Key is `(admission_id, calling AE title)`. The device identity in the query is Scheduled Station AE Title (0040,0001) [IHE-6]; calling AET is usually the same but a modality can legitimately call with a different AET than it schedules under. UPS-RS side keys on the station parameter, so DIMSE and REST agree only when calling AET == station name. | cosmetic |
| M9 | Table 4.130.4.1.2.1.1-1: Physician(s) of Record Identification Sequence >Person Identification Code Sequence >>Coding Scheme Designator; supplement example (4.131.4.1.2.2.1 note) uses `99NPI` for NPIs | Scheme comes from the JSON (`NPI` in samples). Either is "local"; `99NPI` matches the supplement's own example. | cosmetic |
| M10 | 47.2.1 (POCUS EM): map PV1-3 / dept to Institutional Department Type Code Sequence from CID 7030; EBIW_10 fixes three SCT codes | ITI-31 intake sets `department_type = {value: PV1-3.1, scheme: "99IHE"}` (the point-of-care string as a code). ADT-fed encounters will never carry 225728007/394592004/394914008 unless the sender puts the SCT code literally in PV1-3.1. A small PV1-3 -> code lookup (config) is the gap. | blocks EBIW_POCUS step 60 value check for ADT-fed encounters |
| M11 | RAD TF-2 2.4.4.2 (ACK MSH-5/6 R) and 2.4.4.3; ITI-31 ACK | ADT ACK is well-formed: `ACK^<trigger>^ACK`, MSH-5/6 from inbound MSH-3/4, MSA-2 = inbound MSH-10, MSH-12 echoed. No gap. | none |
| M12 | EBIW_10: Institution Name/Address/Code fixed values; Admitting Date/Time "during Connectathon week" | All from JSON; `research/encounters-from-read-this-first.json` carries them. Current `samples/encounters.json` still has placeholders. | data, not code |

Data-model consequence of M1-M4: the encounter record needs `modality`, `scheduled_station_ae_title` and `procedure` per row, and the list must be keyed by (admission_id, modality or AET), not admission_id. `research/encounters-from-read-this-first.json` already carries those three fields so the fix is a read-side change.

## tools/ups_rs.py (Encounter Manager, RAD-130 UPS-RS)

| # | Required by | Tool does / does not | Severity |
|---|---|---|---|
| U1 | same as M1-M4 (shares `em.encounters()` and `em.worklist_item()`) | inherits the one-item-per-admission, global-procedure, echo-only Modality/AET behavior. EBIW_30 steps 110/120/200 counts (3 / 2 / 1) cannot all be satisfied. | blocks EBIW_30 |
| U2 | Table 4.130.4.1.2.2-1: AET in Scheduled Station Name Code Sequence (0040,4025) **Code Meaning**, local scheme; EBIW_30 reads "value of Code Meaning" | Returns `code(station, "99IHE", station)`: Code Value and Code Meaning both = AET. Satisfies the table. Station identity is taken from `ScheduledStationNameCodeSequence.CodeValue` first, then `.CodeMeaning`; a client that only sends `.CodeMeaning=<AET>` works. No gap. | none |
| U3 | Table 4.130.4.1.2.2-1: Modality -> Scheduled Station Class Code Sequence (0040,4026), CID 29 (scheme DCM) | `code(modality, "DCM", CID29.get(...))`. Correct. Matching is echo-only (see M2). | spec deviation via M2 |
| U4 | Table 4.130.4.1.2.2-1: Accession, Issuer, Requested Procedure Description/Code, Requesting Service, Referring Physician's Name inside Referenced Request Sequence (0040,A370); Study UID top level | Accession, issuer seq, RP ID/Description/Code, Study UID placed inside (0040,A370); Study UID also top level. Referring Physician's Name / Requesting Service not produced (O). Correct. | none |
| U5 | M5 | inherits: issuer sequences carry Local Namespace Entity ID only | spec deviation |
| U6 | 4.130.4.2.2.2: `application/dicom+json`; PS3.18 11.9: 204 on no match | both done. | none |
| U7 | PS3.18 search: `includefield`, `offset`, `limit` | accepted; full workitem always returned; offset/limit applied after matching. Acceptable. | none |
| U8 | 4.130.5: HTTPS permitted | `TLS_CERT`/`TLS_KEY` supported. | none |
| U9 | `match()` treats any key containing `-` with only digits/dots as a range | a Patient ID like `123-45` would be parsed as a range. Edge case; Gazelle IDs are EM-generated. | cosmetic |

## tools/mllp_receiver.py (Result Aggregator, RAD-132 receiver)

| # | Required by | Tool does / does not | Severity |
|---|---|---|---|
| R1 | RD 4.128.4.2.2 / RAD TF-2 2.4.1.2: Original Mode ACK; 2.4.4.3: MSA-1 AA/AE/AR, MSA-2 = MSH-10; 2.4.4.2: MSH-9 three components; EBIW_25/35 step 55 | Normal path: `ACK^<trigger>^ACK`, MSA-1 `AA`, MSA-2 = inbound MSH-10, MSH-5/6 = inbound MSH-3/4, MSH-12 = inbound MSH-12. Matches claim (a). | none |
| R2 | RAD TF-2 2.4.4.3 Table 2.4-7: MSA-3 is **X** (not supported); errors belong in ERR (2.4.4.4); 2.4.4.2: MSH-9 all three components, MSH-5/6 R | Unparseable-MSH path sends `MSH|...||ACK|...` (single-component MSH-9, empty MSH-5/6) and `MSA|AR||Cannot parse MSH` (MSA-3 valued). Only reachable with a non-HL7 frame. | cosmetic / spec deviation on the error path only |
| R3 | RD 4.128.4.2.3: "If the HL7 ORU was invalid, the Receiver shall send an error message" | Tool ACKs AA for anything with a parseable MSH, by design (CLAUDE.md neutrality rule; the monitor grades, not the tool). This is a deliberate, documented divergence, not a bug. Worth one sentence in the tool docstring and RUNNING.md so nobody reads AA as "conformant": the stand-in catches the message; the monitor and TPM judge it. | document, do not change |
| R4 | 2.4.4.2 MSH-12 of the ACK "2.5.1 or higher" | ACK echoes the inbound MSH-12; an inbound `2.4` yields an ACK claiming `2.4`. Harmless on the floor; fixed `2.5.1` would be the strictly conformant ACK. | cosmetic |
| R5 | 4.132.4.1.3: accept multiple messages for the same Study UID | Stateless, logs in order. | none |
| R6 | 4.132.4.1.2.3.3: OBR may repeat under POCUS (eFAST) | Summary line reads only the first OBR/OBX (`segs` keeps the first of each segment type). Evidence files are raw, so nothing is lost; the console line under-reports. | cosmetic |
| R7 | Monitor needs (rad-132-checklists.md): the fields most often wrong on day 1 were MSH-9 structure, MSH-12, PID-3 vs PID-2, OBR-16/32, OBX-2/3/11 of the Study UID OBX, TQ1 presence | Summary line shows MSH-9/10/12, PID-3/5, PV1-19, OBR-4/18/19/25, first OBX-5. Not shown: PID-2 (should be empty), OBR-16, OBR-32, OBR-44, OBX-2/3/11, TQ1-9, count of OBR/OBX segments. Adding them is read-only reporting, within the "no grading" rule. | cosmetic, high value |
| R8 | Table 4.132.4.1.2-1 segment order MSH PID PV1 [ORC] OBR TQ1 OBX [{OBX}] | not checked by the tool (by design). | none |
| R9 | MLLP framing, several frames per connection, unframed trailing bytes saved | done. | none |

## Cross-cutting

| # | Required by | Finding |
|---|---|---|
| X1 | EBIW_POCUS_Simple_Workflow step 10 and EBIW_POCUS_Non-privileged_Flow step 10: the **Result Aggregator sends ITI-31 to the POCUS Manager** | The kit covers the receiving side (mwl_scp.py port 2576) for when the stand-in is the EM/POCUS Manager. When the stand-in is the RA (its registered role), the sender is `tools/mllp_send.py samples/ADT_A04_ITI-31.hl7 <vendor host> <port>`; the sample must carry the EBIW_10 patient (name with [Modality], DOB, sex), PV1-3 with a department the vendor maps to the SCT dept code, PV1-7 attending (-> (0008,1049)), PV1-19 with assigning authority, PV1-44. Nothing in `samples/` is EBIW_10-shaped yet. |
| X2 | issue 002 finding #2 cites "RAD TF-2 2.3.1 conventions" for three-component MSH-9 | the citation should be RAD TF-2 2.4.4.2 and RD 4.128.4.1.2.2 (from-memory-claims.md (c)). Finding #5 (`OBX|n|ST|113014^DICOM Study^DCM||<UID>`) should add OBX-11 = `O`. Finding #6 is right that OBR-16/OBR-32 are R under POCUS (4.132.4.1.2.3.3). |
| X3 | docs/TLS-CERTS.md / issue 001 cite the Apple 825-day rule | confirmed (Apple 103769); the 398-day rule (102028) applies only to Apple-preinstalled roots, so it does not hit the GSS CA. |
| X4 | docs/RUNNING.md says mwl_scp.py "generic 'Perform Imaging' procedure (4.130.4.1.3)" | true to the TF, false to EBIW_10/20/30 expectations (M4). |
