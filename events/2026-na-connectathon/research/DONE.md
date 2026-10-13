---
event: IHE NA Connectathon 2026
source: overnight research thread, 2026-10-13 00:00-00:25 ET
status: complete
---
# DONE: overnight research, status

All six deliverables are written. Nothing in Gazelle was changed (read and navigate only); no git commands were run; no tool was edited.

## Complete
| File | Status | Notes |
|---|---|---|
| `rad-130-checklists.md` | transcribed, tables checked against rendered PDF pp. 94-96 | base + POCUS key tables, UPS-RS mapping, Expected Actions as a checklist, RAD TF-2 2.2 notation legend quoted |
| `rad-131-checklists.md` | transcribed | Table 4.131.4.1.2-1, POCUS modality attributes, POCUS Manager coercion, A.6-1, A.7-1 with coercion-diff guidance, App. O codes |
| `rad-132-checklists.md` | transcribed | full segment-by-segment incl. the RD 4.128 sections EBIW points to (MSH, PID, PV1, ORC, Study UID OBX) and the ACK; POCUS optionality flips collected at the top; 8 spec inconsistencies listed at the bottom |
| `from-memory-claims.md` | verified | (a) confirmed, text lives in RD supplement 4.128.4.2 not TF-2 Final Text; (b) confirmed, OBX-2 ST / OBX-11 O; (c) requirement real, section is RAD TF-2 2.4.4.2 not 2.3.1; (d) confirmed, Apple 103769; 398-day rule is public roots only |
| `gazelle-ebiw-tests.md` | transcribed from the signed-in Chrome session | all 10 EBIW tests: ids, roles, step tables, evaluation text; EBIW_10 code set and patient table; EBIW_90 field list; the two POCUS tests |
| `encounters-from-read-this-first.json` | transcribed | 11 encounters (5 patients x US+XC, plus BERGER radiology row), EBIW_10 institution/department/procedure/modality codes; placeholders for [Modality], AE titles, Gazelle OID |
| `tool-gaps.md` | verified by reading the code | 12 findings on mwl_scp.py, 9 on ups_rs.py, 9 on mllp_receiver.py, 4 cross-cutting. Headline: encounters are keyed by Admission ID so EBIW_10's two-procedures-per-admission model collapses (M1); Modality/AET are echoed not matched (M2/M3); one global procedure (M4) |

## Partial / could not reach
- Gazelle "OIDs for current session" page listed nothing, so the assigning-authority OID for the EM/POCUS Manager issuer fields is `[GAZELLE_OID]` in the JSON. EBIW_20 says any value is fine for POCUS.
- RAD TF-2 ITI TF-2x C.2.3 (MSA field list RD points to) not fetched; immaterial.
- Apple 103769: the fetch did not quote back the "SHA-1 / RSA<2048 rejected regardless of date" sentence verbatim; marked unverified in the file.
- Gazelle test instances (actual runs, chat windows, proxy captures) were not opened; only test definitions.

## Where the sources are
- `IHE_RAD_Suppl_EBIW.pdf` and `IHE_RAD_Suppl_EBIW.txt` (pdftotext -layout) sit in the repo root; both should stay out of git (IHE copyright; README already says the documents are not redistributed).
- RAD TF-2 rev 23.0 and the RD supplement rev 1.2 were read through pdf.js in the browser (ihe.net blocks the shells' egress); page numbers in the files are PDF page numbers of those documents.

## Suggested morning order
1. `tool-gaps.md` M1-M4 (data model) before any vendor MWL query; the JSON already has the needed fields.
2. Drop `encounters-from-read-this-first.json` over `samples/encounters.json` after filling the placeholders.
3. Fix issue 002 citations per `from-memory-claims.md` (c) and `tool-gaps.md` X2.
4. Build an EBIW_10-shaped ITI-31 sample for the POCUS tests where the RA is the sender (X1).
