---
event: IHE North America Connectathon 2026
dates: 2026-10-12 to 2026-10-16
kind: research
source: adversarial review, 2026-10-13 (web-only reviewer, no clone; see its section 8)
expires: 2026-10-16
---
> **Applied 2026-10-13** (details in `../docs/LOG.md`): state-file race fixed (issue 008); corpus
> run against isolated instances, one defect fixed (ACK MSH-9 always three components); edge-case
> behaviour documented in `docs/RUNNING.md`; errata A-B added to `rad-132-checklists.md` OFI
> 12-13 (C was already `rad-130-checklists.md` OFI 2). Not applied: its branch workflow, the
> DIMSE and shell drivers (untested by the reviewer, not committed), and its panel bind
> recommendation (decision recorded in the LOG). Corpus: `samples/adversarial/`, driver:
> `tools/adversarial/adversarial_mllp.py`.

# Adversarial review, 2026-10-13 (partial: no repo clone, no DIMSE runtime)

Reviewer environment: web chat, no network egress from the sandbox, no pynetdicom/pydicom/FastAPI,
no clone. GitHub's HTML was readable for the repo root only; the search index has nothing for a
repo created this week, so individual files were unreachable. The EBIW rev 3.1 PDF truncates at
~p.48 in the fetch tool (transactions start p.91). RD rev 1.2 came through to the OBX payload table.
Everything below is tagged **[verified]** (read in the PDF or exercised in the sandbox),
**[inferred]** (from README text), or **[unverified]** (needs the clone or the EBIW transaction pages).

## 1. Verdict

1. Fit for purpose this week: **cannot say from here.** The rules in README are the right rules for a
   partner substitute; whether the code keeps them is unverified.
2. Merge first, before Wednesday: `review/adversarial-corpus`. It changes no tool, adds 26 messages and
   three drivers under `samples/adversarial/` and `tools/adversarial/`, and every later finding keys off it.
3. The surface the brief undercounts: `tools/panel.py` (FastAPI, start/stop/restart, port editing, log
   browser, raw export) and `tools/hl7show.py`. The panel is the only thing in the kit that *renders*
   vendor messages field by field. Rendering is where silent normalisation hides (unescaping, charset
   guessing, segment splitting on LF). The "byte-exact raw download for Gazelle" claim is the single most
   important property to prove; it is the evidence path. **[inferred]**
4. Two spec errata in the public PDFs matter to this kit and should go on the clarification list as
   "both readings exist on the wire": OBR-27.6 priority encoding, and TQ1-9 code system. See §4.
5. One tag/name mismatch inside EBIW rev 3.1 itself (47.2.1, Physician(s) of Record Identification
   Sequence printed as (0008,009D)) will produce two incompatible Encounter Manager implementations
   if anyone codes from that line. See §4, item C. **[verified in Vol 1 text; 4.130 table unverified]**

## 2. Branches this review produced / proposes

| Branch | Prefix | State | One line |
|---|---|---|---|
| `review/adversarial-corpus` | `[evidence]` | ready to apply | 26 hostile HL7 messages (ORU + ADT), stdlib MLLP driver with 14 framing modes, concurrency and 10 MiB cases; pynetdicom C-FIND cases; UPS-RS + state.json race script. Senders smoke-tested against a stub; receivers not. |
| `review/summary` | `[docs]` | this file | |
| `review/clarifications-rd-errata` | `[spec]` | proposed, needs `events/<event>/research/*.md` | Add §4 items A–F to the "could be clarified" list with the wire examples given here; cite RD pp.29, 36, 39 and EBIW p.43 line 515. |
| `review/msh10-empty-and-unframed` | `[blocks-test]`? | proposed, pending run | If `mllp_receiver.py` crashes or stays silent on `oru_msh10_empty.hl7`, `--frame no-start`, `--frame two-in-frame`, or `--frame lf-terms`, the fix is: always answer *something* inside a frame and log the raw bytes with a `.unframed` suffix. Silence is the one behaviour a stand-in cannot have; the vendor will blame their sender. |
| `review/state-json-atomic-write` | `[blocks-test]`? | proposed, pending run | If `adversarial_concurrency.sh` leaves `state.json` unparseable: write to temp + `os.replace`, and a `fcntl.flock` around read-modify-write shared by `mwl_scp.py` and `ups_rs.py`. Still a JSON file, still no database. |
| `review/panel-raw-export-byte-exact` | `[evidence]`? | proposed, pending run | Send `oru_ed_pdf_payload.hl7`, `oru_latin1_no_msh18.hl7`, `oru_lf_inside_obx5.hl7`; `sha256sum` the raw download against the bytes the driver sent. Any difference is a PR. |
| `review/running-md-cold-start` | `[docs]` | proposed, pending clone | README quick start says "needs uv" but the one-liner is `tools/floor.sh start`; whether `floor.sh` runs `uv sync`, needs tmux installed, and what happens on a Mac without tmux is the Wednesday-monitor question. |

## 3. What the author got right; do not "improve" these

- **Raw bytes to a timestamped file before anything else.** Any proposal to log structured JSON,
  normalise CR/LF, or store decoded strings destroys the evidence property. Keep the raw file primary;
  derived views are disposable.
- **No HL7 parsing library.** `hl7apy`/`python-hl7` will reject or "repair" exactly the messages a
  monitor needs to see unmodified (one-component MSH-9, raw LF in OBX-5, undeclared Latin-1). The
  hand-rolled split-on-`|` for MSH-10 is correct for a mitt.
- **ACK AA regardless of content.** The temptation is `AE` on "invalid" messages. That is grading.
  The only legitimate non-AA is when the receiver physically cannot build an ACK (no MSH-10).
- **A dict in a JSON file for the accession-per-admission rule** (EBIW 47.1.1.1 lines 363–366).
  The spec forces exactly that much state and no more. SQLite is not an improvement here.
- **`events/<event>/` with front-matter and "nothing in there outlives the event".** The next-event
  reuse story depends on this partition staying clean.
- **"Status and honesty" in README.** A TPM approving a partner substitute needs that paragraph more
  than any feature.
- **No vendor names anywhere, including logs.** Roles and Gazelle system keywords only. Keep it.

## 4. Spec facts and clarification candidates (checklist cross-check)

Verified against RD rev 1.2 (2019-08-09). EBIW rev 3.1 4.130/4.132 tables not reached; items that
depend on them are marked. For each clarification item both readings are shown on the wire. The
stand-in must accept both; the checklist should name both.

### 4.1 RD 4.128 facts the Result Aggregator checklist must match [verified]

- Message: `ORU^R01^ORU_R01`, HL7 2.5.1. MSH per ITI TF-2b 3.30.5.1. **MSH-9 shall have three
  components** (4.128.4.1.2.2, p.30). Q30 in EBIW: R01, not R30.
- Segment set: MSH, PID, PV1, [ORC], OBR, TQ1, [{OBX}] (Table 4.128.4.1.2-1, p.27).
- **Exactly one OBR and one TQ1 per ORU** (4.128.4.1.2.1, p.29 line 585). OBR-27.6 and TQ1-9.1
  carry the most severe priority in the message.
- ORC: "recommended that the ORC segment is not sent"; if sent, must mirror OBR (4.128.4.1.2.5, p.33).
- PID: PID-3 R with 3.1 and 3.4 present, 3.5 if known; PID-5 R; PID-18 R2 (Table 4.128.4.1.2.3-1, p.30).
- PV1: PV1-2 R; PV1-19 R2 but "shall be valued if known" and shall equal Admission ID (0038,0010) of
  the DICOM instances; **PV1-51 = V when PV1-19 is valued** (p.33 lines 661–667). PV1-52 is where
  EBIW operators/performing physicians go (lines 668–675).
- OBR: OBR-4 R (performed procedure code, else requested); OBR-7 R2 = procedure date/time;
  **OBR-18 R = Accession Number** (p.36 line 740); OBR-22 R = signed/amended time; OBR-24 should be
  RAD/CUS/VUS/CTH; OBR-25 R ∈ {R, F, C} and **shall equal OBX-11 of the payload OBX**; OBR-27 R with
  only component 6 valued; OBR-32 R (NDL, family and given name required); OBR-44 R = OBR-4
  (Table 4.128.4.1.2.6-1, pp.34–35).
- TQ1: TQ1-9 R, CWE, values from Table 0485, shall match OBR-27.6 (p.39).
- Study UID OBX: OBX-2 `ST`, OBX-3 `113014^DICOM Study^DCM`, OBX-4 sub-ID when repeated, OBX-11 `O`
  (Table 4.128.4.1.2.8-1, p.40). One UID per OBX.
- Payload OBX: OBX-2 `TX` or `ED`, OBX-3 `18748-4^Diagnostic Imaging Report^LN` (first of a list the
  fetch truncated), OBX-8 R, OBX-11 R ∈ {R, F, C}, OBX-15 R (Table 4.128.4.1.2.13-1, p.49). Amended
  result = whole report, status `C`. An ORU with no payload OBX is legal (procedure not completed).
- Abnormal/priority mapping: OBX-8 ∈ {N, A, AA}; OBX-15 RadLex RID13173 / RID50261 / RID49482 /
  RID49481 / RID49480; priority ∈ {R, A, S} (Table 4.128.4.1.2.1-1, p.29).
- ACK: 4.128.4.2 not reached. **[unverified]** Expect `ACK^R01^ACK`, MSA-1 AA/AE/AR, MSA-2 = inbound
  MSH-10, original mode per RAD TF-2 2.3.1. Confirm in the PDF before the checklist asserts it.

### 4.2 EBIW facts reached in Vol 1 [verified], Vol 2 [unverified]

- Encounter Manager shall implement MWL semantics of RAD-130; UPS-RS only with the Lightweight
  Modality Option (47.1.1.1, 47.2.1, 47.2.2). Floor reality matches: MWL first, UPS-RS a sidebar.
- Encounter Manager shall generate Study Instance UIDs and accession numbers, configurable Issuer of
  Accession Number, collision-avoiding prefix/suffix, **and shall not return different accession
  numbers for the same admission to the same device** unless it can tell there is a new encounter
  (47.1.1.1 lines 355–366). This is the only state the spec forces; `adversarial_dimse.py --case
  determinism` and `--concurrent` exercise it.
- Encounter Manager shall populate required RAD-130 fields for unidentified patients; trigger
  (e.g. first name "Unidentified", Patient ID 0) is implementation-defined (lines 367–372).
- POCUS Option, Encounter Manager: map **PV1-19 → Admission ID (0038,0010)** and **PV1-7 →
  Physician(s) of Record Identification Sequence**, printed as **(0008,009D)** at line 515 (p.43).
- POCUS Option, Result Aggregator: receive RAD-132 **including the additional segments in
  4.132.4.1.2.3** (PV1, ORC, OBR, OBX subsections per the TOC, pp.115–117). Note the TOC lists an
  **ORC** subsection for the POCUS Option. **[unverified: content]**
- Closed issue Q30 (p.20): committee did not want ORC and considered prohibiting it.
- Closed issue Q26 (p.17): no normative way to filter completed encounters; EM "can likely omit
  discharged patients" from ADT. `adt_a03_discharge.hl7` asks what this kit does.
- Closed issue Q27 (p.17): "auto-matching" keys (Modality, Scheduled Station AE Title = calling AE)
  are intended. `adversarial_dimse.py` sets SSAET to the calling AE in every baseline query.
- Appendix U (p.128): HL7 ADT → DICOM MWL mapping for POCUS, informative. **[unverified: content]**
  This is the table the ITI-31 intake in `mwl_scp.py` should be checked against, line by line.

### 4.3 Clarification candidates, with both readings on the wire

**A. OBR-27.6 priority encoding** [verified erratum, RD Table 4.128.4.1.2.1-1 p.29 vs HL7 2.5.1 TQ datatype]
The table prints OBR-27.6 as `R^Routine^HL70078`. TQ component 6 is `ST`; a `^` inside it is a
component separator, so the literal spills into TQ-7 and TQ-8.
```
OBR|1|...|^^^^^R|...                              (reading 1: TQ.6 = "R", as the datatype allows)
OBR|1|...|^^^^^R^Routine^HL70485|...              (reading 2: as the table literally shows; TQ.7="Routine", TQ.8="HL70485")
```
Sample: `oru_obr27_priority_ce_spill.hl7`. A field view that renders TQ components will show the
spill; the monitor should know it is the spec's doing, not the vendor's.

**B. Priority code system** [verified erratum, RD p.29]
Text says Table 0485; the table column prints `HL70078` (which is Abnormal Flags) on every row.
```
TQ1|1||||||||R^Routine^HL70485    (reading 1: the text)
TQ1|1||||||||R^Routine^HL70078    (reading 2: the table)
```
Sample: `oru_tq1_priority_hl70078.hl7`.

**C. Physician(s) of Record Identification Sequence tag** [verified mismatch, EBIW p.43 line 515; 4.130 table unverified]
47.2.1 says PV1-7 maps to "Physician(s) of Record Identification Sequence (0008,009D)". In PS3.6,
(0008,1049) is Physician(s) of Record Identification Sequence and (0008,009D) is Consulting Physician
Identification Sequence; (0008,1048) is Physician(s) of Record (PN). Q58/Q59 (p.30) use (0008,1049).
```
(0008,1049) SQ  >(0008,0080)... >(0040,1101) Person Identification Code Sequence   (reading 1: the name)
(0008,009D) SQ  ...                                                                   (reading 2: the printed tag)
```
If `mwl_scp.py` returns one and `mwl_find.py` requests the other, the kit tests against itself and
passes. Check Table 4.130.4.1.2.1-1 before filing; then file against the supplement.

**D. ORC in RAD-132** [RD verified; EBIW 4.132.4.1.2.3.2 unverified]
RD: recommended absent, must mirror OBR if present. EBIW Q30: "we do NOT want to include ORC". EBIW
4.132 TOC: a POCUS-Option ORC subsection exists. Three positions in two documents.
```
MSH|...^ORU^R01^ORU_R01...\rPID|...\rPV1|...\rOBR|...                     (reading 1: no ORC)
MSH|...^ORU^R01^ORU_R01...\rPID|...\rPV1|...\rORC|RE||||CM\rOBR|...        (reading 2: ORC present, mirrors OBR)
```
Sample: `oru_orc_present.hl7`. The stand-in logs both; the checklist must not fail a POCUS Manager
for either until 4.132.4.1.2.3.2 is read.

**E. MSH-9 with fewer than three components** [verified requirement RD p.30; ACK behaviour unverified]
```
MSH|^~\&|...||ORU^R01^ORU_R01|MSG1|P|2.5.1       (required)
MSH|^~\&|...||ORU^R01|MSG2|P|2.5.1               (common; what goes in the ACK's MSH-9: ACK^R01^ACK or ACK^R01?)
MSH|^~\&|...||ORU|MSG3|P|2.5.1                   (ACK^?)
```
Samples: `oru_msh9_two_components.hl7`, `oru_msh9_one_component.hl7`. Whatever the receiver does,
RUNNING.md should state it, because the vendor will ask.

**F. Empty MSH-10** [HL7 2.5.1 ch.2; ACK design decision]
MSA-2 is R and must echo MSH-10. With MSH-10 empty the receiver can send `MSA|AA|` (empty MSA-2),
`MSA|AR||...` (reject), or nothing. Nothing is wrong for a stand-in; the other two are defensible.
Sample: `oru_msh10_empty.hl7`. Document the choice.

**G. Escaped delimiters in identifiers that cross HL7 → DICOM** [HL7 escaping; EBIW mapping unverified]
PV1-19 `VN\F\100\S\234` is the visit number `VN|100^234`. When the Encounter Manager copies it to
Admission ID (0038,0010), does `\F\` get unescaped (DICOM has no `|` problem) or copied literally?
```
PV1|...|VN\F\100\S\234^^^HOSP_VISIT&...&ISO^VN|...   →  (0038,0010) LO "VN|100^234"      (reading 1: unescape)
                                                      →  (0038,0010) LO "VN\F\100\S\234"  (reading 2: literal)
```
Samples: `adt_a01_escaped_delims_in_pv1_19.hl7`, then `adversarial_dimse.py --case admission-id-delims`.
Round-trip through RAD-132 (PV1-19 from the DICOM Admission ID) makes this visible to the Result
Aggregator too.

**H. Charset with no MSH-18** [HL7 2.5.1 says default is ASCII; floor reality is Latin-1 or UTF-8]
Samples: `oru_utf8_no_msh18.hl7`, `oru_latin1_no_msh18.hl7`. The raw log is correct by construction;
the field view must either show bytes or say which decoding it guessed. A field view that throws
on 0xC9 is a Wednesday outage.

## 5. Prior art, per stand-in

Rule context: IHE lists Gazelle Order Manager as the MWL SCP participants may use "especially at
Connectathon" and says Connectathon tests do not call for monitors to use Patient Manager
(gazelle.ihe-europe.net NA tool pages). Gazelle Proxy is a non-TLS capture proxy, the sanctioned
intermediary for evidence. The event's exact intermediary rule text was not available to me
**[unverified]**; verdicts below assume "no intermediary that is not a Gazelle tool, and no tool that
judges".

| Stand-in | Public alternative | Verdict |
|---|---|---|
| `mllp_receiver.py` (Result Aggregator) | dcm4che `hl7rcv` (raw MLLP receiver, writes each message to a file, ACKs); HAPI TestPanel (GUI); Mirth channel | `hl7rcv` is the honest competitor: one JAR, logs raw, ACKs AA, no judgement. It loses on two points: no Gazelle-ready raw export with the paired ACK in one place, and Java on a monitor's laptop at 7am. Mirth is an interface engine, i.e. an intermediary by construction, and it rewrites; out. **Kit wins narrowly, on evidence packaging.** |
| `mwl_scp.py` (Encounter Manager, MWL + ITI-31 intake) | Gazelle Order Manager MWL SCP; DCMTK `wlmscpfs` (worklist from .wl files); Orthanc + ModalityWorklists plugin; dcm4chee-arc-light | Order Manager is the sanctioned one but models SWF.b orders, not encounters: no Admission-ID-keyed accession persistence (47.1.1.1), no ADT-fed PV1-19/PV1-7 → (0038,0010)/(0008,1049) mapping, and it runs off-floor. `wlmscpfs`/Orthanc serve static items and cannot satisfy "same accession for same admission and device" without a script in front of them, which is this kit. **Kit wins; this is the stand-in the profile actually needed.** |
| `ups_rs.py` (Encounter Manager, UPS-RS) | dcm4chee-arc-light (full UPS-RS); Orthanc has no UPS-RS | Only matters for a registered Lightweight Modality. dcm4chee-arc is a heavy intermediary-shaped thing and needs an ADT feed configured. **Kit wins by default; if no Lightweight Modality is on the floor, nothing wins and this file is dormant.** |
| `mllp_send.py`, `mwl_find.py` (test clients) | dcm4che `hl7snd`; DCMTK `findscu`; HAPI TestPanel | Equivalent. Keep the kit's for one reason: identical logging path and env vars as the servers. Loopback tests in RUNNING.md should also show the `findscu` incantation so a monitor without the kit's venv can still probe a vendor SCP. |
| `panel.py`, `hl7show.py` | Gazelle HL7 message viewer (in Proxy); `hl7show`-type CLIs | The panel's raw export with paired ACK is unique and is the kit's evidence advantage. Its process-control half (start/stop/restart/ports) has no prior art because nobody else ships it; see §6 TPM and §8. |

## 6. Perspectives

**Modality vendor engineer.** I need three things from a partner substitute: the called AE title,
host and port on one page; a worklist that answers my C-FIND with the keys my product actually asks
for; and the raw capture of what I sent when the monitor says something is missing. The kit's one
page is README's table. The risk is the third: if the panel's field view shows me a prettified
message and the monitor reads the same view, we argue about the view, not the bytes. Give me the
`.raw` download link on the same screen as the rendering.

**Second monitor, Wednesday, no author.** `tools/floor.sh start` presumes tmux, uv, and that ports
2575/11112/2576/8042/8090 are free. The first failure I will hit is a port already bound by a
vendor's own listener on the shared laptop, and the message I get will be Python's, not the kit's.
TROUBLESHOOTING.md's "when nothing arrives" is the right section title; it needs the two commands
I will actually type: `ss -ltnp | grep -E '2575|11112|2576|8042'` and `tools/floor.sh status`.

**Technical Project Manager approving a partner substitute.** Approval hinges on neutrality and
non-interference. README's "never grades, auto-passes or rewrites" plus "Status and honesty" is the
paragraph I need. The panel's start/stop/port-edit controls do not change that, but I would want a
line saying the panel binds to 127.0.0.1 only and has no vendor-facing surface. The second thing I
want is that the logs the vendor attaches came from the kit unmodified: a per-capture SHA-256 in the
file name or a sidecar is cheap and ends arguments.

**IHE committee member reading the clarification list.** Items A–C above are errata in public
documents and belong in CP form with the page and line cited; D is a committee question (ORC yes or
no in 4.132 POCUS); E–H are implementation-guidance gaps that a one-sentence note in 4.132.4.2
and Appendix U would close. Wire examples make these actionable; prose complaints do not.

**Same author, next Connectathon, different profile.** The reusable core is: MLLP receiver with raw
logging and paired ACK, MWL SCP driven by a JSON item file, env-var config, `events/<event>/`
partition, panel. The EBIW-specific parts are the POCUS return keys in `mwl_scp.py` and the
ADT → MWL mapping. If those two are not already isolated at the top of the file as a dict, do that
before the repo is next opened; it is the difference between an afternoon and a day.

## 7. Blue sky, not implemented

1. **Tamper-evident capture manifest.** Append `sha256 timestamp filename` to `logs/MANIFEST` on
   every write; optionally sign the manifest with a key generated on first run. *For:* a vendor cannot
   later claim the monitor edited the capture; TPM approval gets easier. *Against:* Gazelle verifies
   nothing; monitors will not check hashes at 4pm on Wednesday; the ceremony invites "why is the hash
   wrong" when a log is re-exported with normalised line endings, which is itself the normalisation
   the kit must not do. Cost is twenty lines; value depends on one dispute ever happening.
2. **Route vendor traffic through Gazelle Proxy instead of the kit's own logging.** *For:* the
   sanctioned evidence path, the one the TPM already trusts, with the HL7 viewer built in.
   *Against:* the Proxy is non-TLS; any vendor on mTLS cannot use it; and a stand-in behind a proxy is
   two intermediaries. The kit's raw logs exist because the Proxy is not always possible. Keep both;
   document when to use which.
3. **Replace `mwl_scp.py` with Gazelle Order Manager plus a thin ADT-to-order shim.** *For:* fewer
   lines of monitor-owned code, sanctioned tool, RAD committee knows its behaviour. *Against:* the
   shim would have to fake an order to get an accession, which inverts EBIW's whole premise (Q28:
   orders are the EMR's choice, not the modality's or EM's), and the accession-persistence rule
   (47.1.1.1) would live in the shim anyway. You end up with the kit plus a dependency on an
   off-floor service.

## 8. Not verified, not guessed

- Any line of `tools/*.py`, `docs/*.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `.gitignore`,
  `requirements.txt`, `events/2026-na-connectathon/**`. Steps 1, 2, 4 of the brief are not done.
- Whether `mllp_receiver.py` is stdlib-only (README says asyncio or socketserver). If yes, the
  MLLP half of step 3 is runnable here on request.
- EBIW rev 3.1 Tables 4.130.4.1.2.1-1 (MWL keys), 4.130.4.1.2.2 (UPS-RS), 4.132.4.1.2.3.x (POCUS
  ORU additions), 4.132.4.2 (ACK), Appendix U (ADT→MWL mapping). Needed for step 5 proper.
- RD 4.128.4.1.2.13 remainder (full OBX-3 value list), 4.128.4.1.3, 4.128.4.2.
- The event's intermediary rule text and the TPM's partner-substitute criteria.
- Whether Gazelle Order Manager's current release exposes Admission ID / Issuer sequences at all.
- What `panel.py` binds to and whether it has auth. Security was de-scoped by the author for this
  pass; the bind address is a functionality question (a vendor on the floor finding port 8090 open).
- Cold-start timing. A file-by-file read is not a clone.
