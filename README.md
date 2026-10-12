# IHE NA Connectathon 2026: monitor support kit

Working notes, problem statements, and small stand-in actors for a volunteer monitor at the
IHE North America Connectathon, Oct 12–16 2026, George Mason University, Arlington VA.

Two jobs this week:

1. **Monitor.** Verify test instances in Gazelle Test Management; relay vendor problems from
   Zulip into written problem statements with evidence.
2. **Contingency tool-builder.** When a profile is missing a partner actor, stand up a
   minimal, monitor-readable stand-in (one file, one actor, raw logging) so vendors can test.

Private repo. Vendor names stay out of committed files.

## Status

| Day | State |
|---|---|
| Mon Oct 12 | Kit assembled; one TLS/CRL ticket open (`tickets/20261012-tls-server-verify-crl.md`), verified against live GSS: floor CA is 2048-bit (id 2656), RSA-1024 lead dropped, mTLS/hostname now top hypotheses. No tools built yet. |

Per-session detail: [docs/LOG.md](docs/LOG.md).

## Layout

| Path | Contents |
|---|---|
| `CLAUDE.md` | Project brief and hard rules for stand-in tools |
| `docs/RAD.md`, `docs/ITI.md` | Radiology and IT Infrastructure profile/transaction cheat sheets |
| `docs/TLS-CERTS.md` | Cert, CRL, and iOS trust triage, with the openssl commands |
| `docs/FLOOR-TOOLS.md` | NA 2026 tool URLs, syslog collector, subnets, proxy |
| `docs/TOOLS.md` | Existing simulators to use first; stand-in actor designs to build on request |
| `docs/TROUBLESHOOTING-PROTOCOL.md` | How a Zulip/Gazelle thread becomes a ticket, then a tool |
| `docs/LOG.md` | Session log |
| `tickets/` | One markdown file per problem statement, from `tickets/TEMPLATE.md` |
| `artifacts/` | Evidence (CRLs, certs, captures). Tracked, keys included: private network, own CA, wiped after the event |
| `tools/` | Stand-in actors, when built. Each is one Python file; config by env vars; logs to `logs/<actor>/<ts>/` (ignored) |

## Using it

- **New problem:** copy `tickets/TEMPLATE.md` to `tickets/<yyyymmdd>-<slug>.md`, fill symptom,
  scope, evidence, ranked hypotheses, missing evidence. Code only after the ticket exists.
- **TLS triage:** run the commands in `docs/TLS-CERTS.md` against the leaf, issuer, and
  `openssl s_client -showcerts` output.
- **Stand-in actor:** check `docs/TOOLS.md` for an existing simulator first. If one is built,
  it goes in `tools/`, runs with Python 3.11+ in a `.venv` (`uv venv && uv pip install -r requirements.txt`; Homebrew python@3.13 and `uv` are on this Mac), and is documented at the top of its
  own file.

## Repo hygiene

- Commits go straight to `main`, small and frequent, one per ticket/tool/doc change.
- Only the Claude Code session commits; the parallel chat session edits files.
- Every session ends with a `docs/LOG.md` entry and the status table above brought up to date.
- Licensing and other logistics are deferred; private repo for now.
