---
event: IHE North America Connectathon 2026
dates: 2026-10-12 to 2026-10-16
kind: issue
opened: 2026-10-13 13:15 ET
status: answered
expires: 2026-10-16
---
# A modality vendor's "nominal EBIW MWL response": what it requests, what TOOL_DDx returns

- **Source:** a POCUS modality vendor's engineer sent a sample MWL response on Zulip (direct
  message, 11:36 ET) "in case you decode to stand up a simulator"; asked for feedback. Not a
  test run. File kept locally, not committed (it carries vendor-private code values).
- **Domain / profile / actor / transaction:** RAD EBIW POCUS Option / Acquisition Modality (SCU)
  and Encounter Manager (SCP) / RAD-130 MWL; downstream RAD-131

## What the file is
A bare C-FIND response identifier (no Part 10 header), implicit VR little endian, undefined-length
sequences. Values are placeholders (`IHENominalForEBIW^First Name`, `Institution Name`, ...).
A C-FIND response carries only the keys the SCU asked for, so the file is the modality's query
footprint: 16 top-level keys plus SPS (Modality `US`, Scheduled Station AE Title `myTestAE`,
SPS Start Date/Time).

## Read against the tables
1. **RAD-130 base, SCU return keys (Table 4.130.4.1.2.1-1, R+*):** all requested. Patient's Name,
   Patient ID, Issuer of Patient ID, Birth Date, Sex, Institution Name / Address / Code Sequence,
   Department Name / Type Code Sequence, Admission ID, Accession Number, Issuer of Accession
   Number Sequence, Study Instance UID, SPS with own AE title and modality (IHE-6, IHE-7).
2. **POCUS Option (Table 4.130.4.1.2.1.1-1):** Physician(s) of Record Identification Sequence
   (0008,1049) requested, with the full Person Identification macro inside. Meets the table.
3. **Not requested, and needed downstream:**
   - **Issuer of Admission ID Sequence (0038,0014).** Optional for the SCU in RAD-130, but RAD-131
     Table 4.131.4.1.2-1 lists it R+ in the images with the MWL as the source (Table A.6-1). If the
     query does not ask for it, the images cannot carry it, and the RAD-132 PV1-19 issuer link has
     nothing to copy.
   - **Requested Procedure Code Sequence (0032,1064) / Description (0032,1060).** Optional in
     RAD-130, but the Gazelle EBIW_20/30 evaluation expects Procedure Code Sequence (0008,1032) in
     the images, mapped from them; the Image Manager maps it into OBR-4.
   - Copy rows in Table A.6-1 also not requested: Admitting Date/Time (0038,0020/0021), Reason for
     Visit (0032,1066/1067), Other Patient IDs Sequence (0010,1002). Optional; mention only.

## TOOL_DDx answering that exact query
Replayed on an isolated Encounter Manager (scratch ports and logs): every requested key returned,
calling AE `myTestAE` echoed in Scheduled Station AE Title, 7 US matches for the universal query
(the five EBIW_10 US rows plus the two generic rows). One gap on our side:

- **Issuer of Accession Number Sequence: Universal Entity ID and Type come back empty** because
  `issuer_oid` is not set. Table 4.130.4.1.2.1-1 has both R+ for the SCP. Set the issuer OID on
  the panel's Encounters page before the first graded run (the monitor picks the OID).

## Resolution
Feedback relayed to the vendor by the monitor: query footprint is complete for RAD-130 base and
POCUS; add (0038,0014) and (0032,1064)/(0032,1060) so RAD-131 can carry them. TOOL_DDx action:
set the issuer OID.
