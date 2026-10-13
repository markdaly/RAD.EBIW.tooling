# IHE IT Infrastructure (ITI): Connectathon reference

Canonical index: https://profiles.ihe.net/ITI/ (TF Rev 20.2, 2025-11-11, HTML)

## Profiles likely on the floor
ATNA, CT, PIX/PDQ (v2), PIXm/PDQm/PMIR, XDS.b, XDS-SD, XCA, XCPD, XDR, XDM, MHD, MHDS,
DSUB/DSUBm, RMD, XUA, IUA, BPPC, SVS/SVCM, MPQ, mCSD, BALP, sIPS.

Recent revisions:
- IUA rev 2026-06-18
- MHD 4.2.4 (R4); MHD 5.0.0 (R5) published 2025-12-19
- BALP 1.1.4 (2025-10-31)
- RESTful ATNA (Query and Feed) rev 2025-11-25
- PDQm 3.2.0, PIXm 3.1.0, PMIR 1.6.0 (all 2025-11-06)
- Public comment mid-2026: MHD, Verifiable Health Links (VHL), De-Identification Handbook.

## Key transactions
| # | Name |
|---|---|
| ITI-1 | Maintain Time (CT, NTP) |
| ITI-8 / ITI-9 | Patient Identity Feed / PIX Query (v2) |
| ITI-18 | Registry Stored Query |
| ITI-19 | Authenticate Node (TLS) |
| ITI-20 | Record Audit Event (syslog TLS/UDP, or FHIR Feed) |
| ITI-21 | Patient Demographics Query (v2) |
| ITI-38 / ITI-39 | Cross Gateway Query / Retrieve (XCA) |
| ITI-41 | Provide & Register Document Set-b |
| ITI-42 | Register Document Set-b |
| ITI-43 | Retrieve Document Set |
| ITI-55 | Cross Gateway Patient Discovery (XCPD) |
| ITI-65 / 66 / 67 / 68 | MHD Provide Document Bundle / Find Lists / Find DocRefs / Retrieve |
| ITI-71 / 72 | IUA Get Access Token / Incorporate Access Token |
| ITI-78 | PDQm |
| ITI-83 | PIXm |

## ATNA / TLS policy at Connectathons
- TLS 1.2 with one of: TLS_DHE_RSA_WITH_AES_128_GCM_SHA256,
  TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256, TLS_DHE_RSA_WITH_AES_256_GCM_SHA384,
  TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384.
- Certificates: historically **only from Gazelle Security Suite (GSS)** (2048-bit CA; FQDN in
  subjectAltName, so FQDN-validation option works). Confirm which CA the event uses in
  `events/<event>/docs/`; triage commands in `docs/TLS-CERTS.md`.
- TLS 1.0 floor options retired in 2021 (CP-ITI-1247).
- ITI-20 over syslog uses the **DICOM audit schema** (PS3.15 A.5.1); GSS validates only that.
  RFC 5424 message, RFC 5425 TLS framing, RFC 5426 UDP. FHIR Feed option uses AuditEvent
  mapped per RESTful ATNA.
- ARRs choose TLS, UDP, and/or FHIR; Gazelle shows compatible partners for `ATNA_Logging_*`.
- GSS test numbers:
  - 11099 read resources page
  - 11100 get certificate
  - 11106 ATNA Questionnaire (required for credit; must be "Ready for review")
  - 11109 TLS handshake vs GSS simulators (client and server; paste permanent links)
  - 11110 error cases: Corrupted, Expired, Revoked, Self-Signed, Unknown,
    Without_Authentication, Wrong_Key
  - 11116 audit message content
  - 11117 syslog transport to the GSS Syslog Collector (RFC 5424 parse must succeed)
  - 11118 AuditEvent resource check
- Monitor checks on 11109: server tests PASSED with SUT host/port matching Gazelle config;
  client tests blue dot with host IP matching config.

## Pass criteria
- Thorough testing: generally 3 partners per peer-to-peer test. If only 1–2 partners exist,
  all available partners. Zero partners means the profile is dropped.
- Supportive testing (previously passed): one verified peer-to-peer test; must still help others.
- XC* family: one verified peer-to-peer test passes; Responding GWs from 2 different
  communities is enough.

## Tooling
- **Gazelle Security Suite (GSS)**: certs, TLS simulators, syslog collector, ATNA questionnaire.
  The event's instance URL and ports are in `events/<event>/docs/FLOOR-TOOLS.md`.
- **Gazelle EVSClient**: validators for HL7 v2/v3, CDA, DICOM, FHIR, audit messages.
  https://gazelle.ihe.net/EVSClient
- **Gazelle Proxy**: captures traffic between partners; monitors use it as evidence.
- **Gazelle PatientManager / OrderManager**: simulators for PAM/PDQ/PIX and order workflows.
- **NIST XDS Toolkit**: XDS/XCA simulators and validators. https://github.com/usnistgov/iheos-toolkit2
- **NIST FHIR Toolkit ("Asbestos")**: MHD Document Source/Recipient testing, recording proxy,
  TestScript engine. https://github.com/usnistgov/asbestos/wiki
- **MITRE Inferno**: general FHIR testing.

## Common ITI floor failures
- Cert chain: leaf without intermediate, CA not in trust store, SAN missing FQDN, wrong EKU.
- Syslog framing: octet-counting missing on TLS syslog (RFC 5425), BOM issues, bad PRI.
- Audit schema: RFC 3881 legacy schema instead of DICOM schema.
- XDS metadata: wrong affinity-domain codes (codes.xml), patient ID not in the registry's
  domain, missing sourcePatientId/Info, hash/size mismatch.
- XCA: homeCommunityId missing on queries without patient ID; async not supported on a
  Responding GW.
- MHD: comprehensive vs minimal metadata confusion; Bundle type/transaction semantics.

## Links
- ITI TF: https://profiles.ihe.net/ITI/TF/Volume1/index.html
- HIE whitepaper (map of document sharing): https://profiles.ihe.net/ITI/HIE-Whitepaper/index.html
- ATNA tests / GSS policy: https://gazelle.ihe-europe.net/book/export/html/352
- MHD test plan: https://profiles.ihe.net/ITI/MHD/testplan.html
- Connectathon FAQ: https://gazelle.ihe-europe.net/node/601
- XC* pass criteria: https://gazelle.ihe-europe.net/node/984
