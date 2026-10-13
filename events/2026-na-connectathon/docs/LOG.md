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

## 2026-10-13 (Tue, day 2), end of day: hand-off

**Late news (16:30 ET):** an EHR vendor that had declined is now registered for ENCOUNTER_MGR-EBIW and
RESULT_AGGREGATOR-EBIW, correctly, but sends direct (skips the proxy). Both TPMs are reworking the
Gazelle test instances; maybe not resolved today. A real partner beats a stand-in, so TOOL_DDx
likely becomes backup for those roles.

**State at hand-off:** all five listeners up on ddx0 / 10.242.1.99 in tmux `ihe` and `ihe-panel`
(em/ups restarted 10:34 on the locked state code, ra 10:40, panel on 80 and 8090 since 11:30); Mac
on AC, system sleep off, lid must stay open. Tree clean, pushed. main: admin bypass on, 1 approval
required. Ubuntu CI (22.04/24.04/26.04 x64+ARM, bare 26.04) green. Vendor files in
`events/*/artifacts/` are untracked and locally excluded (`.git/info/exclude`), never commit them.

**Shutdown, ~17:05 ET:** the monitor stopped the kit for the day (tmux gone, all ports closed; no
sleep). Last traffic: the POCUS Manager probed 2575 directly at 17:00:57 (connect/close, no data);
no step-120 ORU received. Restart Wed with `tools/floor.sh start` (also starts the panel).

**Resume here (Wed):**
1. Ask the TPMs how the instances landed. If the EHR vendor holds EM/RA in an instance, TOOL_DDx is
   out of it: reword `docs/HOWTO.md` and `docs/CONNECTIONS.md` to "backup partner", and the
   step-10 ADT sent today may need redoing by the vendor. Their skipping the proxy means no Message
   Capture: push them onto their proxy channels before graded runs.
2. If TOOL_DDx stays RA for the POCUS Manager: its step-120 ORU arrives on 11067; check PV1-19 =
   ADM001 (the ADT sent today) and read it against `research/rad-132-checklists.md`.
3. Before any worklist run: issuer OID on the Encounters page (still blank, so Issuer of Accession
   Number UEI/Type return empty), then per partner: identifier + AE titles, restart em and ups.
4. Watcher: `python3 -I -u tools/floorwatch.py logs` as a Monitor source (30 min max, re-arm; it
   resumes from its saved positions).
5. Friend's Ubuntu laptop: `docs/INSTALL.md` Ubuntu section; their own HOWTO copy via PANEL_HOWTO.

## 2026-10-13 (Tue, day 2), afternoon: EBIW_POCUS_Simple_Workflow step 10 sent; waiting on step 120

- **Step 10 (ITI-31) done, 13:42 ET:** TOOL_DDx as Result Aggregator sent ADT^A04 (PEREZ / EBIW001 /
  ADM001, MSH-5 `SS_VIEWPOINT`) to the POCUS Manager through its proxy channel 11008; AA back.
  Evidence: Message Capture, plus `logs/result-aggregator/send-20261013/` (`.out.hl7` + `.ack.hl7`).
  Their ACK's MSH-7 runs six hours ahead (their clock or zone); told the monitor, worth checking in
  their ORU. This POCUS Manager serves its own worklist (proxy 11005), so our Encounter Manager is
  not in this run.
- **Step 120 not yet received** by 16:20 ET. When it arrives: PV1-19 should carry ADM001 (the
  encounter round trip for step 150), then the RAD-132 checklist.
- **Watcher:** a scratch-folder monitor follows every summary log and the five listeners
  (passive check, never connects), re-armed every 30 min, resumes from saved read positions.
- **Small fix:** sender summary lines name the source file, not its full path (the live page is
  floor-visible).
- Other vendor questions today (a sample MWL response, two images, a pcap review) were answered as
  one-off feedback in chat, not kept in the repo; their files stay untracked and locally excluded.
- Gazelle test instances still being sorted out on the event side; possibly not today.

**Next session starts:** step 120 ORU from the POCUS Manager on 11067 (review + ADM001 check); set
the issuer OID on the Encounters page before any worklist run; Encounters page per partner before
each EBIW_20/30 run.

## 2026-10-13 (Tue, day 2), 11:25-11:40 ET: panel styling and tablet fit; Ubuntu compatibility

- **Panel styling:** fonts and colors only, light and dark following the device; monospace for
  HL7 IDs and values. **Tablet fit** (monitor's iPad screenshot): no viewport tag and nowrap
  code cells made the howto overflow past the header; fixed and checked at 1024 and 768 px.
- **Bug found while styling:** the live page (`/tail`) never ran in a browser (an unescaped
  `\n` in its script). Earlier checks were status codes only; now verified in headless Chrome.
- **Ubuntu:** `tools/smoke.sh` (22 checks, own tmux session, ports and temp logs; safe beside
  the live kit) passes on macOS beside the live kit and on stock Ubuntu 22.04 and 24.04 in CI
  (`.github/workflows/ubuntu-smoke.yml`), which also proves the port 80 sysctl. floor.sh:
  `ss` for port checks on Linux, `FLOOR_SESSION` / `FLOOR_ENV` overrides, LOG_DIR passed into
  windows. Ubuntu steps in `docs/INSTALL.md`.

- **Ubuntu 26.04 added** (11:50 ET): native x64 and ARM runners plus a bare `ubuntu:26.04`
  container as a non-root user with only the INSTALL.md packages. All pass, on uutils (Rust)
  coreutils too; the port 80 sysctl works on 22.04, 24.04 and 26.04.

- **Decision, one partner at a time:** four Modality systems are registered against EBIW, but
  tests run one at a time, so the encounter set stays single-partner. Before each run: Encounters
  page (partner identifier, that partner's AE titles), then restart em and ups. Accessions stay
  separate per device because state is keyed by admission and AE title. No multi-partner build.

**For the friend's Ubuntu laptop:** follow the INSTALL Ubuntu section, run `tools/smoke.sh` at
home first (uv cache). If it is registered as its own Gazelle system, it needs its own HOWTO
copy (`PANEL_HOWTO`): the shipped one names ddx0 / 10.242.1.99 / TOOL_DDx.

## 2026-10-13 (Tue, day 2), 10:30-10:50 ET: review fixes, connection page published

- **Connection page published** (`docs/CONNECTIONS.md`, PR #2 plus a follow-up commit): where to
  send per role (proxy first, direct fallback), how to use the panel, test walkthroughs, and how
  configuration changes are made. All four proxy channels were probed before publishing
  (11064 connect held, 11065 C-ECHO 0x0000, 11066 HTTP 204, 11067 ORU AA). A line-by-line check
  corrected three things before vendors saw them: the UPS-RS modality wording (tested on an
  isolated instance), TPM approval stated as recorded, and an invented chat sentence removed.
  The PR merged one commit early; the corrections went to main as `a29c7d4`.
- **Decision, panel exposure:** the log browser is readable by the whole floor on purpose. With
  one or two vendors per profile and TOOL_DDx in the middle, each vendor's partner is the other
  vendor and needs to see the same captures; the proxy's Message Capture shows them anyway.
  Only control actions are restricted to the panel's own machine. Not a finding for later reviews.
- **Issue 008, fixed:** the race between `mwl_scp.py` and `ups_rs.py` on `state.json` was real.
  8 processes x 50 allocations: old code 384 errors, 3 duplicate accessions, corrupt file; new
  code (flock + atomic replace) none. em and ups restarted onto it at 10:34.
- **Adversarial corpus**, run only against isolated instances on scratch ports: no crash or
  traceback across 26 messages, 14 framing modes, 10 MiB and 8 concurrent senders; captures
  byte-exact. One defect fixed: ACK MSH-9 is now always three components (`ACK^^ACK`); ra
  restarted at 10:40. Edge-case behaviour documented in RUNNING.md. The DIMSE and
  concurrency-shell drivers were not run.
- Two priority errata from the review added to the RAD-132 clarification list (OFI 12-13).
- **Repo cleanup:** review kit folded in (`samples/adversarial/`, `tools/adversarial/adversarial_mllp.py`,
  `research/adversarial-review-2026-10-13.md`), zip deleted; merged PR branch deleted, GitHub now
  deletes head branches on merge; `github-hardening.sh` matches the live rule (admin bypass, 1
  approval) so re-running it does not re-lock.
- **Panel on port 80 too** (11:25 ET): a tablet with a stale cached DNS answer could not reach
  `ddx0.na2026.net:8090`, and a bare IP goes to port 80. The panel now listens on 80 and 8090
  (`PANEL_PORT` comma list, unbindable ports skipped). The handout URL is http://10.242.1.99/
  (hostname where floor DNS is used); `/howto` is the vendor get-started page.
- **Watching tools:** panel `live` page (`/tail`, all actors' summaries merged by time, captures
  linked); tmux files pane shows write times, actor and kind instead of month/day only.

**Open for the monitor:** pre-run setup on the Encounters page per partner (AE titles still blank, partner identifier
still `TEST`). Since then: the monitor confirmed TPM approval for the Encounter Manager stand-in
(it serves other EBIW tests too) and flushed the DNS cache; the review kit was folded into the
repo (below) and the zip deleted.

## 2026-10-13 (Tue, day 2), late morning: first vendor traffic, proxy fixed, panel on the floor

- **Issue 007, fixed:** a POCUS Manager vendor sent RAD-132 through the proxy and got no ACK.
  Floor DNS still had ddx0 at the old DHCP address (.184), so the proxy forwarded to nothing.
  Direct to 10.242.1.99:2575 worked at 10:10:11 (AA). The message was a known-bad one kept for
  connectivity; it is byte-identical to Monday's, so issue 002's review stands (plus a correction:
  Z-segments are prohibited, RAD TF-2 2.4.1.5). DNS fixed 10:25; the proxy re-test returned AA
  from 192.168.2.5, which also **closes issue 005**.
- **Panel on the floor:** `floor.sh start` starts it; listens on all interfaces; POSTs are 403
  from other machines; banner on every page (green ADMIN locally, amber READ-ONLY elsewhere).
- **mllp_send.py logs outbound:** `.out.hl7` + `.ack.hl7` + summary line under
  `logs/result-aggregator/send-<date>/`, failures included. Needed for EBIW_POCUS_Simple_Workflow
  step 10, where the Result Aggregator (us) initiates ITI-31 to the POCUS Manager.
- **Adversarial review delivered** as `docs/review-kit-2026-10-13.zip` (untracked, not committed).
  Web-only, never saw the code. Its drivers are written to run against the live services; not
  run. Confirmed by reading code: `state.json` writes are not atomic and two processes allocate
  `n = len(state)+1`, so a simultaneous MWL and UPS-RS allocation could hand out one accession
  for two contexts. Spec errata A-C in its section 4.3 are worth the clarification list.

**Next session starts:** step 10 with the vendor (their ADT listener host:port and MSH-5/6;
patient from the EBIW_10 set); run the review's MLLP corpus against an isolated instance; decide
on the state-file lock. Main still has admin bypass on and PR #2 open.

## 2026-10-13 (Tue, day 2), morning: services live, worklist pre-run fixes, main locked

- Services up from 09:04 ET on ddx0 / 10.242.1.184 (ra 2575, adt 2576, em 11112, ups 8042,
  panel 8090 local). No vendor traffic yet.
- ~09:30 ET the Mac moved to **static 10.242.1.99** (below the .125+ DHCP pool, router .1).
  CONNECTIONS.md and issues 003/004/005 updated; entries above this line keep the address
  that was true at the time. The Gazelle ddx0 host entry has to follow.
- **Issue 006, fixed:** an ITI-31 ADT for an EBIW_10 admission added a third, modality-less row
  beside the US/XC rows, so a PEREZ worklist returned a duplicate item (same accession).
  `encounters()` now overlays ADT fields onto that admission's rows. Reproduced on the old
  code and verified on scratch ports.
- **Loopback residue cleared before the first graded run:** `encounters-from-adt.json` and
  `state.json` (three contexts on test stations MOD_TEST/SCREENSHOT, EM2610130001-0003) moved
  to `*.loopback-20261013` under `logs/encounter-manager/`; state reset to `{}`; em and ups
  restarted at 09:18 with 0 remembered contexts. Accession numbering restarts at EM2610130001.
- **main locked for an adversarial review:** `enforce_admins` on and one approving review
  required, so nothing on the owner's token can push to main or merge its own PR.
  `tools/github-hardening.sh` now applies that as the default. Commits after this point sit
  local (or on a branch) until the monitor relaxes the rule.

**Next session starts:** Encounters page (US/XC AE titles, issuer OID), then the proxy
channels (issue 005). Unlock main after the review to resume push-after-commit.

## 2026-10-13 (Tue, overnight): repo made public-safe

**State at hand-off (Tue 01:45 ET):** repo is PUBLIC at `markdaly/RAD.EBIW.tooling`, Apache-2.0,
branch protection + Dependabot + secret scanning + private vulnerability reporting + CodeQL all on
(`tools/github-hardening.sh`). Tree clean, pushed, no servers running, pre-rewrite backups beside
the repo. Research thread merged and its findings applied.

**Resume here (Tue morning):**
1. `tools/floor.sh start` and `tools/floor.sh panel`; http://127.0.0.1:8090/encounters for the
   EBIW_20/30 pre-run setup (partner identifier, US/XC AE titles, OID), then restart em + ups.
2. Proxy channels still reset on connect (issue 005): check channel target/status in Gazelle as
   admin, re-test with `tools/mllp_send.py samples/ORU_R01_RAD-132_POCUS.hl7 proxy.ihe-europe.net 11067`.
3. Issue 001 (TLS): still waiting on the TPM/vendor for the GSS permanent link and host/port.
4. First real vendor queries have not happened yet; watch the `logs` window or the panel.

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
