---
event: IHE North America Connectathon 2026
dates: 2026-10-12 to 2026-10-16
location: George Mason University, Mason Square, Arlington VA
kind: event-index
expires: 2026-10-16
---
# IHE NA Connectathon 2026

Everything in this directory is specific to one event and one private floor network. IP
addresses, ports, proxy ports, Gazelle system keywords and test ids here are real so that the
people on the floor can follow along; none of it is reachable from outside and all of it is
gone after Oct 16. People are referred to by role only.

| Path | Contents |
|---|---|
| `docs/CONNECTIONS.md` | Every listener on the monitor's machine, every target, vendor endpoints, Gazelle configurations and proxy ports. Start here. |
| `docs/FLOOR-TOOLS.md` | Event tool URLs (Gazelle TM, GSS, proxy, Message Capture), subnets, syslog collector ports. |
| `docs/TLS-NA2026.md` | The event's TLS situation: which CA, the dead CRL path, the simulator cert quirks. |
| `docs/LOG.md` | Session diary, newest first. Each entry ends with where the next session starts. |
| `issues/` | One file per floor problem, numbered. 001 TLS/CRL, 002 Result Aggregator, 003 Encounter Manager, 004 POCUS simple workflow, 005 proxy channels. |
| `artifacts/` | Public PKI material from the event's test CA (CA cert, simulator cert, CRLs). No private keys. |
| `research/` | Transcribed requirement checklists and verification notes produced overnight; see each file's front matter for source and status. |
