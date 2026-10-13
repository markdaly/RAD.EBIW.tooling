---
event: IHE North America Connectathon 2026
dates: 2026-10-12 to 2026-10-16
kind: floor-support
expires: 2026-10-16
---
# Floor support protocol: support chat / Gazelle → written issue → fix or stand-in

How a vendor problem on the floor turns into something written down, with evidence, and then
either an answer or a tool. The monitor does the talking; the repo does the remembering.

## Roles
- **The monitor (on the floor):** logged into the event's support chat and Gazelle. Talks to
  vendors and TPMs, collects certs, logs, screenshots and captures, runs commands on site machines.
- **The repo:** one issue file per problem (`../issues/NNN-slug.md`, next free number, from
  `ISSUE-TEMPLATE.md`), the session diary (`../docs/LOG.md`), connection tables, artifacts.
- **Stand-ins (`tools/`):** built only when a profile is missing a partner actor and the TPM
  agrees, as described in the repo README.

## Flow
1. A problem arrives: a support-chat thread, a Gazelle test instance, or a vendor at the table.
2. Write the issue file before touching anything: symptom with exact error text, scope,
   evidence so far with its source, ranked hypotheses each with how to confirm it, missing
   evidence as a checklist, next action.
3. Collect the missing evidence from the vendor or the tools (cert PEMs, `openssl s_client`
   output, raw captures, proxy links).
4. Update the issue: narrow to a root cause, or state the fix in plain words (config, reissue,
   trust store), or scope a stand-in.
5. Relay the answer in the support chat or at the table. Vendor and product names stay out of
   the repo; roles and Gazelle system keywords only.
6. Close with a **Resolution** section. Add a line to `../docs/LOG.md` at the end of the session.

## What good evidence looks like
- TLS: `openssl s_client -showcerts` output, leaf and issuer PEMs, the exact client error, the
  client stack and version, which root bundle the client trusts.
- DICOM: association log (A-ASSOCIATE-RQ/AC/RJ with AE titles and presentation contexts),
  status codes, a dump of the offending dataset.
- HL7 v2: the raw message with segment separators intact, and the ACK (MSA-1/MSA-3, ERR).
- HTTP / DICOMweb / FHIR: request line, headers, body, response status and body.
- Always: Gazelle test instance id, system keywords, timestamps, proxy permanent links.

## Rules of the floor
- Monitors are neutral. A stand-in accepts, logs and answers; it never grades or rewrites what a
  vendor sent. Judgement happens in the Gazelle test instance, by a person.
- Raw captures go to the vendor for their Gazelle attachment and stay out of git (`logs/`).
- Nothing changes a Gazelle test status, posts to the support chat, or submits a form except
  the monitor, deliberately.
