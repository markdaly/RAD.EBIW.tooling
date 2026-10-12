# Session log

One entry per working session, newest first. Each ends with where the next session starts.
Tickets live in `tickets/`; this is the cross-ticket record.

## 2026-10-12 (Mon, day 1), fourth session: live Result Aggregator, Encounter Manager stand-in

- Result Aggregator went live on this Mac (10.242.1.184:2575). Vendor probe 15:05, first
  ORU^R01 15:07:57, ACKed AA. Content review (15 findings, v2.4, PID-2 not PID-3, no
  accession, no Study UID OBX, no physician of record, OBX-11 empty, "educational" exam) is
  in the ticket. the monitor: that send was connectivity only, not the graded run. Gazelle proxy
  (proxy.ihe-europe.net = 192.168.2.5, reachable) will sit in front once the monitor has access.
- New request: a VNA (Image Manager) scenario needs an EBIW Encounter Manager. Ticket
  `tickets/20261012-ebiw-encounter-manager.md` quotes RAD TF-1 47.1.1.1 and RAD TF-2 4.130
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
  themselves. Ticket `tickets/20261012-ebiw-result-aggregator.md` explains what a Result
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
  TROUBLESHOOTING-PROTOCOL), ticket template. Repo hygiene: `.gitignore`, README, this log.
  First push to GitHub (private).
- Dry run of the troubleshooting protocol on a live Zulip thread:
  `tickets/20261012-tls-server-verify-crl.md` (mobile POCUS app, TLS handshake error against
  GSS; CRL Distribution Point on the deprecated `gazelle.ihe.net` host).
- Finding from `artifacts/cacrl.crl`: the CRL signer `CN=IHE Europe CA` has a 128-byte RSA
  signature, so that CA key is RSA-1024. If it is the floor CA, iOS/Android/OpenSSL
  SECLEVEL≥2 reject the chain regardless of root trust. Needs the CA cert to confirm.
- No tools built yet. `docs/TOOLS.md` lists the stand-in designs on the shelf.

**Next session starts:** get the GSS CA cert and check its key size (hypothesis 0 in the
ticket), then the GSS permanent link for the failed handshake. Build `tlscheck.sh` only if
the s_client matrix is needed more than once.
