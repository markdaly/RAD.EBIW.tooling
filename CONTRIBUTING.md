# Contributing

Thanks for picking this up mid-event. The bar is low and the rules are few.

## Flow

1. Fork the repo, or branch if you have write access: `git checkout -b fix/<what>`.
2. Make the change. Keep each tool one file; if you need a second file, say why in the PR.
3. Loopback-test it (below). Paste the relevant output in the PR.
4. Open a PR against `main`. Title: what changed and for which transaction, e.g.
   "mwl_scp: match on Scheduled Performing Physician's Name (RAD-130 Table 4.130.4.1.2.1-1)".
5. Someone with write access merges. If nobody is around and you are on the floor with a vendor
   waiting, run from your branch; merge later.

Commits go straight to `main` once merged; no release process, no tags beyond the odd marker.
Small commits, one concern each. Mention the issue file if there is one
(`events/<event>/issues/NNN-slug.md`).

## Rules that are not negotiable

These exist because a monitor has to read the tool and decide whether to trust what it did.

- **Stand-ins never judge.** No validation beyond what is needed to answer, no scoring, no
  rewriting of vendor messages, no "helpful" fixes of what the vendor sent. If you want to check
  a message against the spec, write a checklist in `docs/` for a human to use.
- **Log everything raw.** Every inbound message and every outbound response goes to a file under
  `logs/<actor>/<session>/` before anything else happens. If you add a transaction, add its log.
- **Stateless unless the spec forces it.** When it does, a dict written through to a JSON file.
- **One file, one actor, one or two transactions.** Readable top to bottom in five minutes.
- **Env-var config.** Ports, AE titles, issuers, file paths. Nothing hard-coded to one network.
- **No vendor, product or personal names** in committed files, logs, samples or commit messages.
  Roles ("the VNA vendor", "the POCUS Manager vendor"), Gazelle system keywords, AE titles, hosts
  and IPs are fine. `logs/` is gitignored for this reason; keep it that way.
- **Cite the spec.** Any behavior that follows from an IHE requirement names the section or table
  in a comment or docstring. If it is from memory, say "from memory" in the text.
- Python 3.11+, `pydicom`/`pynetdicom` for DIMSE, bare asyncio or `socketserver` for MLLP,
  FastAPI for DICOMweb. No new frameworks without a sentence of justification.

## Loopback-testing a change

Everything can be exercised from one laptop. Use a scratch log directory so you do not mix test
traffic with floor evidence.

```bash
# Result Aggregator: receive and ACK
LISTEN_PORT=2585 LOG_DIR=/tmp/kitlogs uv run --with pynetdicom --with pydicom python tools/mllp_receiver.py &
python3 tools/mllp_send.py samples/ORU_R01_RAD-132_POCUS.hl7 127.0.0.1 2585     # expect MSA|AA|MSG00001
```

```bash
# Encounter Manager, MWL side + ADT intake
LISTEN_PORT=11122 ADT_PORT=2586 LOG_DIR=/tmp/kitlogs uv run --with pynetdicom --with pydicom python tools/mwl_scp.py &
uv run --with pynetdicom --with pydicom python tools/mwl_find.py 127.0.0.1 11122 ENC_MGR MRN12345   # expect 1 worklist item
python3 tools/mllp_send.py samples/ADT_A04_ITI-31.hl7 127.0.0.1 2586                                # expect MSA|AA
```

```bash
# Encounter Manager, UPS-RS side (shares state with the MWL side through LOG_DIR)
LISTEN_PORT=8052 LOG_DIR=/tmp/kitlogs uv run --with pynetdicom --with pydicom --with fastapi --with uvicorn python tools/ups_rs.py &
curl -s 'http://127.0.0.1:8052/workitems?PatientID=MRN12345&ScheduledStationNameCodeSequence.CodeValue=TEST' | python3 -m json.tool | head
```

Check that the accession returned over MWL and over UPS-RS for the same admission and station
is the same, that a bogus Patient ID returns zero items (MWL) and 204 (UPS-RS), and that every
request left a file under `/tmp/kitlogs`.

## Adding a stand-in

Copy the shape of an existing one: docstring at the top with what it does, what it does not do,
env vars, run line and test line; config block; raw-logging helper; the transaction; `main`.
Add a row to the table in `README.md` and a paragraph to `docs/TOOLS.md` and `docs/RUNNING.md`.
Prefer an existing Gazelle or NIST simulator if one exists (`docs/TOOLS.md` lists them); a
stand-in counts against the event's limit of intermediaries per test run.

## License of contributions

Apache-2.0, same as the repo. By opening a PR you agree your contribution is licensed under it
(the standard Apache inbound = outbound understanding; no CLA).

## Where things go

| Thing | Place |
|---|---|
| A new floor problem | `events/<event>/issues/NNN-slug.md` from `events/<event>/floor-support/ISSUE-TEMPLATE.md`, next free number |
| Ports, IPs, proxy ports, who connects to what | `events/<event>/docs/CONNECTIONS.md` |
| What happened in a session, where the next one starts | `events/<event>/docs/LOG.md` |
| Certs, CRLs, captures worth keeping | `events/<event>/artifacts/` (never private keys of anything real) |
| Vendor traffic | `logs/`, gitignored, handed to the vendor |
