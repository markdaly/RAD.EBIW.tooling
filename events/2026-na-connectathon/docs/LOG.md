# Session log

One entry per working session, newest first. Each ends with where the next session starts.
Tickets live in `tickets/`; this is the cross-ticket record.

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
