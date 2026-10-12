# IHE NA Connectathon 2026 — Monitor Support Kit

## Who you're working with
the monitor is a volunteer **Connectathon monitor** at the IHE North America Connectathon,
Oct 12–16 2026, George Mason University, Mason Square (Arlington, VA). ~25 yrs medical
imaging informatics; reads HL7 v2 and DICOM natively. Talk to him as a peer: dense,
no hand-holding, profanity fine.

He wears two hats this week:
1. **Monitor**: verifying test instances in Gazelle Test Management (neutral arbiter).
2. **Contingency tool-builder**: when a profile is missing a partner actor, he may stand
   up a small stand-in actor so vendors can test. You write those tools.

## Hard rules for any stand-in actor / tool
- **Max 2 intermediates per profile run.** Every tool you build counts as one. Prefer
  existing Gazelle/NIST simulators (see docs/TOOLS.md) before writing anything.
- **Relatively simple, monitor-readable.** One file, one actor, one or two
  transactions. A monitor must be able to read it top-to-bottom in ~5 minutes.
- **Transaction-minimal behavior.** Do what the transaction requires: accept, minimal
  validation, correct response/ACK. No "helpful" extras; every extra behavior is
  something a monitor has to decide whether to trust.
- **Log everything raw.** Every inbound/outbound message to a timestamped file
  (DICOM datasets dumped per association, HL7 v2 verbatim with ACK, HTTP request/
  response). Logs are evidence the vendor attaches in Gazelle.
- **Stateless unless the spec forces state** (e.g., EBIW Encounter Manager must reuse
  the accession per admission+device → a dict, not a DB).
- **Config via env vars or a short YAML**: AE title, port, issuer, endpoints. Must be
  re-pointable on the Connectathon network in seconds.
- **Neutrality:** tools are partner stand-ins approved by the Technical Project Manager.
  Never build anything that grades, auto-passes, or rewrites a vendor's messages.
- Stack defaults: Python 3.11+, `pynetdicom`/`pydicom` for DIMSE, a bare asyncio MLLP
  socket server (or `hl7` lib) for v2, FastAPI for DICOMweb/FHIR. No frameworks beyond
  that without a reason.

## Floor reality (from monitors on site, Oct 12)
- Radiology testing is light. **No AI profiles in play**; EBIW may be.
- Almost no FHIR. Lots of nudging vendors onto **HL7 v2.5.1** (MSH-12, OMI^O23 vs
  ORM^O01, IPC segment).
- TLS on the floor uses the **Gazelle Security Suite (GSS) CA** (CA id 643), issued from
  https://connectathon.ihe-catalyst.net/gss (fiddly UX). The old `gazelle.ihe.net` host is
  deprecated, and certs whose CRL Distribution Point points there hit a dead URL. iOS/mobile
  devices struggle with trust and client identities. See docs/TLS-CERTS.md.
- Systems under test have fixed IPs and `*.na2026.net` hostnames from Gazelle. Endpoints and
  network: docs/FLOOR-TOOLS.md.
- Support chat is **Zulip** (ihe-catalyst.zulipchat.com); test management is **Gazelle**
  (https://connectathon.ihe-catalyst.net/tm).

## Docs to load as needed
- `docs/RAD.md`: Radiology profiles, transactions, test notes, spec errata
- `docs/ITI.md`: IT Infrastructure profiles, ATNA/TLS policy, tooling
- `docs/TLS-CERTS.md`: cert/CRL/iOS trust troubleshooting
- `docs/FLOOR-TOOLS.md`: NA 2026 tool URLs, syslog collector ports, subnets, proxy
- `docs/TOOLS.md`: existing simulators + stand-in actor designs
- `docs/TROUBLESHOOTING-PROTOCOL.md`: how the monitor relays tickets from Zulip/Gazelle and
  how a ticket becomes a problem statement
- `tickets/`: one markdown file per problem statement (see `tickets/TEMPLATE.md`)

## Working style
- Ground answers in the Technical Framework text; cite section/transaction numbers.
  If a requirement is from memory, say so.
- When a ticket arrives, first write `tickets/<NNN>-<slug>.md` (next free number, no date prefix) from the template, then code.
- Keep vendor names out of committed files and logs unless the monitor says otherwise.

## Repo hygiene
- Commits go straight to `main`, small and frequent, one per ticket/tool/doc change. Only
  this Claude Code session commits; the parallel chat session edits files in the tree.
- Before ending a session: add an entry to `docs/LOG.md` (what happened, where the next
  session starts) and update the status table in `README.md`.
- `artifacts/` is tracked, keys included (private network, own CA, wiped after the event).
  `logs/` from stand-in tools is ignored: vendor traffic goes to the vendor, not to git.
- Python tooling: `uv` and Homebrew python@3.13 are on this Mac; system python3 is 3.9.
