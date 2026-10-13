# IHE Connectathon kit: brief for AI-assisted sessions

Stand-in IHE actors and monitor notes for Connectathon testing. You are working with a
Connectathon **monitor**: someone who verifies test instances in Gazelle Test Management as a
neutral arbiter and, when a profile is missing a partner actor, stands up a small stand-in so
vendors can test. Assume deep HL7 v2 and DICOM fluency on their side; talk like a peer, dense,
no hand-holding. A gitignored `CLAUDE.local.md` may add personal context; read it if present.

## Hard rules for any stand-in actor or tool
- **Prefer an existing simulator.** Gazelle and NIST tools are listed in `docs/TOOLS.md`. A
  stand-in counts against the event's limit on intermediaries per test run (usually two).
- **One file, one actor, one or two transactions.** A monitor must be able to read it top to
  bottom in about five minutes.
- **Transaction-minimal.** Accept, minimal parsing, correct response or ACK. No "helpful"
  extras; every extra behavior is something a monitor has to decide whether to trust.
- **Log everything raw.** Every inbound and outbound message to a timestamped file under
  `logs/<actor>/<session>/`. Those files are the evidence the vendor attaches in Gazelle.
- **Stateless unless the spec forces state.** When it does (the EBIW Encounter Manager must
  reuse the accession per admission and device), a dict written through to JSON, not a database.
- **Config via env vars.** Ports, AE titles, issuers, paths. Re-pointable on a floor network in
  seconds.
- **Neutrality.** Stand-ins are partner substitutes approved by the event's Technical Project
  Manager. Never build anything that grades, auto-passes, or rewrites a vendor's messages.
- **Stack:** Python 3.11+, `pynetdicom`/`pydicom` for DIMSE, bare asyncio or `socketserver`
  MLLP for HL7 v2, FastAPI for DICOMweb or FHIR. Nothing else without a reason.

## Working style
- Ground answers in the Technical Framework text and cite section and table numbers. If a
  requirement comes from memory, say so in the text.
- When a floor problem arrives, first write `events/<event>/issues/<NNN>-<slug>.md` (next free
  three-digit number) from `events/<event>/floor-support/ISSUE-TEMPLATE.md`, then code.
- No vendor, product, or personal names in committed files, logs, samples or commit messages.
  Roles, Gazelle system keywords, AE titles, hosts and IPs are fine.
- Before ending a session: add an entry to `events/<event>/docs/LOG.md` (what happened, where
  the next session starts) and update the event README status line.

## Where things are
- `docs/RUNNING.md`: every tool, env var, port, log and state location.
- `docs/TROUBLESHOOTING.md`: nothing arrives, AR ACKs, empty worklists, TLS.
- `docs/RAD.md`, `docs/ITI.md`, `docs/TLS-CERTS.md`: profile and transaction cheat sheets.
- `events/<event>/`: the only place event facts live (connection tables, issues, the
  troubleshooting diary in `docs/LOG.md`, floor-support protocol and issue template,
  artifacts). Each file carries a front-matter header naming the event.

## Repo hygiene
- Commits to `main`, small and frequent, one per concern; push after each commit.
- `events/<event>/artifacts/` is tracked (public PKI material from the test CA, captures worth
  keeping). `logs/` is ignored: vendor traffic goes to the vendor, not to git.
- Python tooling: `uv` provisions the interpreter and dependencies (`uv run --with ...`).
