---
event: IHE North America Connectathon 2026
dates: 2026-10-12 to 2026-10-16
kind: event-doc
expires: 2026-10-16
---
# Troubleshooting diary

One entry per working session, newest first: the floor problems that came up, what the
evidence showed, what was answered or built in response, and where the next session starts.
Individual problems live in `../issues/`; this is the record across them.

## 2026-10-13 (Tue, overnight): repo made public-safe

**Morning checklist for the monitor (three lines):**
1. Skim this tree, then flip GitHub visibility to public (Settings → General → Danger zone).
   Nothing else happens until you do.
2. Done: repo renamed to `RAD.EBIW.tooling` (IHE org convention; GitHub redirects the old name),
   description/homepage/topics set, license Apache-2.0. Add staffers as collaborators or point
   them at fork-and-PR. Background on the convention: the IHE GitHub org uses `DOMAIN.Profile` for spec repos (`ITI.MHD`, `PaLM.DPOW`,
   `DEV.tooling`) and plain kebab-case for cross-domain tooling (`connectathon-artifacts`,
   Apache-2.0). For a personal repo there is no convention to follow; `ihe-connectathon-kit`
   reads fine, `connectathon-kit` if you want it shorter. If it ever moves under the IHE org,
   something like `RAD.EBIW.tooling` would fit their pattern. Ask the TPM only if you want it
   under their org. Add staffers as collaborators or point them at fork-and-PR.
3. Pre-run setup for EBIW_20/30 is now a form: `tools/floor.sh panel`, open
   http://127.0.0.1:8090/encounters, enter the partner identifier, the US and XC AE titles and
   the OID, save, then restart `em` and `ups` from the index page.

**What ran:**
- Backup first: `../ihe-connectathon-2026-PRIVATE-20261012-234222.bundle` plus a full directory
  copy next to it. `git clone <bundle>` restores yesterday's history exactly.
- Tree: new layout (`events/2026-na-connectathon/{docs,issues,artifacts}`, `templates/`),
  generic `CLAUDE.md` with a gitignored `CLAUDE.local.md` for personal context, new README with
  the honesty section, CONTRIBUTING, LICENSE (MIT overnight, switched to Apache-2.0 in the morning to match IHE's connectathon-artifacts; NOTICE added), `docs/INSTALL|RUNNING|TROUBLESHOOTING.md`,
  `requirements.txt`, portable `floor.sh`. People are roles everywhere; hosts, IPs, ports,
  system keywords, test ids and dates are untouched. Gazelle test PDFs removed. Loopback smoke
  test of all three servers, both senders, MWL SCU and UPS-RS passed on the rewritten tree;
  `floor.sh start/status/stop` verified.
- History: `git filter-repo` over all 21 commits with the same replacement list applied to
  blobs and commit messages, PDFs dropped from every commit, path renames carried through so
  `git log --follow` works. Gate: a grep of every blob in every commit for the people/vendor
  list came back empty (LICENSE excluded; it names the copyright holder on purpose). Force-pushed
  to the private origin, tagged `public-v1`. One self-inflicted bug caught: the replacement list
  also hit the LICENSE copyright line; fixed by amending the tip and re-pushing.
- Git author identity left as the repo owner's on every commit, per the plan.

**Also built overnight (your late request):** `tools/panel.py`, a local web panel on
http://127.0.0.1:8090/ (`tools/floor.sh panel`): service status, start/stop/restart, port and
name config written to `.floor.env`, log browser by actor and session, each capture rendered as
an HL7 field table with 2.5.1 names and components, prev/next with `j`/`k`, the paired ACK or
responses one click away, and "download raw" for the byte-exact Gazelle attachment. Header links
to the repo and docs. Console twin: `tools/hl7show.py <file>`. Tested end to end through its
endpoints including a port change plus restart; the panel survives "stop all".

**Research thread merged and applied (01:00 ET).** The overnight research session delivered six
files under `research/` (RAD-130/131/132 monitor checklists, the four from-memory claims
verified with citations, all ten Gazelle EBIW tests transcribed incl. the EBIW_10 patient set
and code set, a tool-gap list). Applied from `research/tool-gaps.md`:
- **M1–M4, U1 (data model):** encounters are rows per procedure and device type; `modality`,
  `scheduled_station_ae_title` and `procedure` per row; Modality and Scheduled Station AE Title
  are SCP matching keys when a row names them, echoed otherwise; accession + Study UID keyed on
  (admission, modality, station) and allocated only for matched rows. `samples/encounters.json`
  now carries the EBIW_10 set (PEREZ..BERGER as `^TEST`, AE titles blank, OID blank) plus the two
  generic rows. Verified against the EBIW_20/30 step 100/110/120/200 expectations over both
  MWL and UPS-RS: 2 / 3 / 2 / 1, correct procedure codes, same accession on both protocols.
- **M5/U5:** issuer sequences carry Universal Entity ID + ISO when `issuer_oid` or
  `ACCESSION_ISSUER_OID` is set. **M6:** repeating PID-3 → Other Patient IDs Sequence, matched.
  **M8:** station = Scheduled Station AE Title from the query. **M10:** PV1-3 → department type
  code via `department_codes`. **U9:** range parsing only for DA/DT shapes.
- **R2/R4:** ACK is always 2.5.1 with a three-component MSH-9; the unparseable path sends
  `MSA|AR` + ERR instead of MSA-3. **R7/R6:** summary line now shows segment counts, PID-2 if
  present, OBR-16/32/44, TQ1-9, first OBX-2/3/11. **R3:** docstring and RUNNING say AA ≠ conformant.
- **X1:** `samples/ADT_A04_ITI-31_EBIW10.hl7` (PEREZ, ADM001, PV1-3 `ED` → 225728007).
  **X2:** issue 002 citations corrected (RAD TF-2 2.4.4.2, RD 4.128.4.1.2.2, OBX-11 = O).
  Sample ORU's Study UID OBX-11 set to `O`.
Not applied, by choice: M7 (SPS start time matching, over-matches harmlessly), M9 (`NPI` vs
`99NPI` scheme designator, cosmetic). All loopback and Gazelle-scenario tests pass; floor.sh
start/status/stop re-verified before shutdown.

**Before the first graded EBIW_20/30 run:** the panel's Encounters page (checklist item 3),
or edit `samples/encounters.json` by hand: name suffix, US/XC AE titles, `issuer_oid`.
Then `tools/floor.sh restart em` and `restart ups`.

**Still open from yesterday:** proxy channels (issue 005), Read_This_First code set, the TLS
ticket's GSS permanent link, first real vendor queries.

## 2026-10-12 (Mon, day 1), end of day: everything in tmux, proxy blocked

- The monitor is Gazelle admin and SUT **TOOL_DDx** (org DDx, host `ddx0`, 10.242.1.184). Four
  configurations approved with proxy ports 11064 (ADT 2576), 11065 (MWL 11112), 11066 (UPS-RS
  8042, URL `http://ddx0:8042/studies`), 11067 (ORU 2575). Recorded in `events/2026-na-connectathon/docs/CONNECTIONS.md`.
- All stand-ins now run from `tools/floor.sh` in tmux session `ihe` (windows ra / em / ups /
  logs). ACK and ITI-31 MSH-3/4 = `SIMULATOR`/`SIMULATOR` to match the registration. UPS-RS
  also answers at `/studies`.
- **Proxy does not forward** (ticket 005): all four proxy ports accept TCP then close in 0.1 s,
  nothing reaches the Mac. Leading cause: target hostname `ddx0` not resolvable from the proxy.
  Needs the Gazelle admin view of the channels. Vendors hit the Mac directly meanwhile.
- No vendor traffic today beyond the 15:07 connectivity ORU. First real queries from the VNA
  vendor's POCUS Manager box (10.242.1.17) and Lightweight Modality (10.242.1.11) still pending.
- Shut down 17:00 ET: `tools/floor.sh stop`; ports 2575/2576/8042/11112 free. `logs/` kept
  on disk (gitignored): two raw HL7 captures from the 15:07 ORU; no accession state or
  ADT-fed encounters yet (all of that only happened in scratch test dirs).

**Next session starts (Tue Oct 13, early):**
1. `tools/floor.sh start` then `tools/floor.sh status` (four ports listening). No live queries
   happened, so `logs/encounter-manager/state.json` does not exist yet: accession numbering
   starts clean at EM2610130001.
2. Proxy (ticket 005): check channel targets/status as admin, then re-test with
   `tools/mllp_send.py samples/ORU_R01_RAD-132_POCUS.hl7 proxy.ihe-europe.net 11067`.
3. Export EBIW_10_Read_This_First from Gazelle and load its patients/codes into
   `samples/encounters.json` (both EBIW tickets wait on it).
4. Ticket 001 (TLS): still waiting on the TPM/vendor for the GSS permanent link and host/port.

## 2026-10-12 (Mon, day 1), sixth session: test definitions in hand, ITI-31 intake

- The monitor is now Gazelle admin and a registered SUT (DDX) for Encounter Manager + Result
  Aggregator, which unlocks the proxy channels. Two test PDFs saved to Gazelle:
  EBIW_35_Full_Workflow-RESTful (13478, Lightweight Modality via UPS-RS, ticket 003) and
  EBIW_POCUS_Simple_Workflow (13884, ticket 004). Monitor checklists copied into the tickets.
- 13884 has no Encounter Manager role (grouped into POCUS_MGR) and makes the Result
  Aggregator *send* ITI-31. Added ADT intake to `tools/mwl_scp.py` (MLLP 2576, Appendix U
  mapping, persisted and shared with UPS-RS) and `samples/ADT_A04_ITI-31.hl7`. Loopback
  passed incl. A08 replace semantics. `mllp_receiver.py` summary line now shows PID-5.
- Second-source check: the first hand-typed PV1 was a pipe short; samples are now generated
  with explicit field numbers. Worth remembering before trusting any hand-typed segment.

**Next session starts:** restart the EM tab with the ADT listener; load EBIW_10_Read_This_First
data; confirm POCUS_MGR identity for 13884 and TPM acceptance; proxy channels for 2575/2576/8042/11112.

## 2026-10-12 (Mon, day 1), fifth session: UPS-RS for the Encounter Manager

- Gazelle test 13478 (login needed, text not captured): the VNA vendor is a **Lightweight
  Modality**, so RAD-130 must be UPS-RS; they have no UPS-RS client yet. Built
  `tools/ups_rs.py` (FastAPI, `GET /workitems`, dicom+json, 204 on no match, dotted sequence
  keys, Table 4.130.4.1.2.2-1 mapping), sharing encounters and `state.json` with
  `mwl_scp.py`. Loopback: shape, dotted accession match, per-station accession, 204,
  wildcard + datetime range, tag-form keys, and the MWL side returning the same accession
  for the same (admission, station). All pass.
- Both Encounter Manager halves run in terminal tabs: MWL 11112 `ENC_MGR`, UPS-RS 8042.
- Tickets renumbered to `NNN-slug` at the monitor's request (autocomplete); convention updated in
  CLAUDE.md, README, the floor-support protocol.
- Result Aggregator still live on 2575; Gazelle proxy access still being chased.

**Next session starts:** capture the 13478 test text and the code set; watch for the first
the VNA vendor's query on either port; proxy in front of the Result Aggregator when access arrives.

## 2026-10-12 (Mon, day 1), fourth session: live Result Aggregator, Encounter Manager stand-in

- Result Aggregator went live on this Mac (10.242.1.184:2575). Vendor probe 15:05, first
  ORU^R01 15:07:57, ACKed AA. Content review (15 findings, v2.4, PID-2 not PID-3, no
  accession, no Study UID OBX, no physician of record, OBX-11 empty, "educational" exam) is
  in the ticket. The monitor: that send was connectivity only, not the graded run. Gazelle proxy
  (proxy.ihe-europe.net = 192.168.2.5, reachable) will sit in front once the monitor has access.
- New request: a VNA (Image Manager) scenario needs an EBIW Encounter Manager. Ticket
  `events/2026-na-connectathon/issues/003-ebiw-encounter-manager.md` quotes RAD TF-1 47.1.1.1 and RAD TF-2 4.130
  (matching/return key tables, POCUS additions, expected actions).
- Built `tools/mwl_scp.py` (pynetdicom MWL SCP, per-(admission, AE) accession + Study UID
  dict written through to state.json, query/response dumps) and `tools/mwl_find.py`, with
  `samples/encounters.json` (two encounters incl. a John Doe). Loopback: match-all, by Patient
  ID, by Admission ID, no-match, accession stable across restart. All pass.
- Open on both EBIW tickets: Gazelle test names, the `EBIW_10_Read_This_First` code set, and
  the vendors' AE titles/endpoints.

**Next session starts:** pull the code set from Gazelle and replace the PLACEHOLDER codes in
`samples/encounters.json`; get the VNA test name and the modality's AE; put the proxy in
front of the Result Aggregator once the monitor has access.

## 2026-10-12 (Mon, day 1), third session: EBIW Result Aggregator stand-in

- New request: a POCUS Manager vendor has no RAD-132 partner; offered to run Mirth
  themselves. Ticket `events/2026-na-connectathon/issues/002-ebiw-result-aggregator.md` explains what a Result
  Aggregator is (RAD TF-1 47.1.1.4, RAD TF-2 4.132, quoted from the rev 3.1 supplement) and
  why a monitor-run receiver beats vendor-run Mirth (neutrality, intermediate count).
- Built `tools/mllp_receiver.py` (asyncio MLLP, raw logging, ACK^R01, optional MLLPS with
  client cert required) and `tools/mllp_send.py`, plus `samples/ORU_R01_RAD-132_POCUS.hl7`.
  Loopback tests: single message, two messages + garbage frame on one connection (AA, AA,
  AR), MLLPS with client cert (AA), MLLPS without (connection refused by TLS). Known gap:
  failed TLS handshakes leave no log line (asyncio swallows SSLError).
- ACK shape taken from memory of RAD TF-2 4.128.4.2; not yet verified against the text.

**Next session starts:** RAD TPM approval for the stand-in, then give the vendor this Mac's
floor IP and port 2575. First real message: read it against the checklist in the ticket.
TLS ticket still waiting on the TPM/vendor for the GSS permanent link and host/port.

## 2026-10-12 (Mon, day 1), second session: verification pass on the TLS ticket

- Re-checked the first session's cert findings against live GSS with a different model
  (Fable 5.1 high vs Opus 5.5 medium). **The RSA-1024 lead was wrong**: that CRL belongs to
  legacy CA id 643, which issues nothing on the floor. The floor CA is id 2656
  (`…OU=Gazelle`), RSA-2048; its SKI matches the AKI of the `/pki/crl/2656/` CRL. Everything
  else in the first pass held up (CRL format, 24h validity, dead `gazelle.ihe.net` path).
- New facts from `s_client` against the Floor simulators (151.80.220.161): SAN has no IP and
  no `connectathon.ihe-catalyst.net`, only `gazelle-tools.ihe-europe.net` resolves to the
  simulator; CDP in leaf **and** CA cert is the 404 `gazelle.ihe.net/pki/crl/2656/` path;
  mTLS ports reject a cert-less client with alert 42; port 10040 is the non-mTLS control.
  GSS generator leafs are 10-year, which trips Apple's 825-day rule for vendor servers.
- Ticket re-ranked: mTLS provisioning first, hostname second; RSA-1024 dropped. Artifacts
  saved: CA 2656 PEM, simulator leaf PEM, both CRLs. Docs TLS-CERTS and FLOOR-TOOLS corrected.

**Next session starts:** get from the TPM/vendor the GSS permanent link, the host string and
port the app uses, and whether a client identity is loaded. Post the two-CA / dead-CDP
finding to the Zulip thread for the Gazelle maintainers.

## 2026-10-12 (Mon, day 1)

- Kit set up: CLAUDE.md, docs (RAD, ITI, TLS-CERTS, FLOOR-TOOLS, TOOLS,
  floor-support protocol), ticket template. Repo hygiene: `.gitignore`, README, this log.
  First push to GitHub (private).
- Dry run of the troubleshooting protocol on a live Zulip thread:
  `events/2026-na-connectathon/issues/001-tls-server-verify-crl.md` (mobile POCUS app, TLS handshake error against
  GSS; CRL Distribution Point on the deprecated `gazelle.ihe.net` host).
- Finding from `events/2026-na-connectathon/artifacts/cacrl.crl`: the CRL signer `CN=IHE Europe CA` has a 128-byte RSA
  signature, so that CA key is RSA-1024. If it is the floor CA, iOS/Android/OpenSSL
  SECLEVEL≥2 reject the chain regardless of root trust. Needs the CA cert to confirm.
- No tools built yet. `docs/TOOLS.md` lists the stand-in designs on the shelf.

**Next session starts:** get the GSS CA cert and check its key size (hypothesis 0 in the
ticket), then the GSS permanent link for the failed handshake. Build `tlscheck.sh` only if
the s_client matrix is needed more than once.
