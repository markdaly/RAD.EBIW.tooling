---
event: IHE North America Connectathon 2026
dates: 2026-10-12 to 2026-10-16
kind: event-doc
expires: 2026-10-16
---
# TLS on the NA 2026 floor

- Floor TLS uses the **GSS CA (id 643)**. Every participant must trust it. Leaf certs come
  from the GSS generator: https://connectathon.ihe-catalyst.net/gss/request/withoutcsr.seam
  (fiddly UX; people get CN/SAN/type wrong). SAN must be `<gazelle hostname>.na2026.net`.
  Certificate type "Client and Server", 2048-bit.
- **Two CAs named "IHE Europe CA" live in GSS.** The floor CA is **id 2656**
  (`…CN=IHE Europe CA,OU=Gazelle`, RSA-2048, 2018→2028, PEM in
  `events/2026-na-connectathon/artifacts/gss-ca-2656-ihe-europe-ca-gazelle.pem`). **Id 643** (`…CN=IHE Europe CA`, no OU,
  RSA-1024) is legacy and issues nothing on the floor; it only shows up in the simulators'
  acceptable-client-CA list. Don't use a 643 CRL or 643 cert for anything.
- **CRL DP issue (verified Oct 12 12:30 ET):** the GSS server simulators' leaf **and** the CA
  2656 cert carry CDP `https://gazelle.ihe.net/pki/crl/2656/cacrl.crl`. The host resolves; the
  path returns **404**. Working: `https://connectathon.ihe-catalyst.net/pki/crl/2656/cacrl.crl`
  (also `/gss/crl/2656/cacrl.crl`). Vendor certs generated this week already carry the
  catalyst CDP. the Gazelle maintainers are fixing it as of Oct 12 11:04. Ticket: `events/2026-na-connectathon/issues/001-tls-server-verify-crl.md`.
- **GSS Floor server simulators** (151.80.220.161, ports 10075 DICOM / 10077 raw / 10078 HL7 /
  10081 HTTPS / 10082 syslog; 10040 = HTTPS **without** mTLS): cert `CN=Gazelle Simulators`,
  SAN only `gazelle-tools.ihe-europe.net`, `gazelle.ihe.net`, `gazelle.ihe-europe.net` (+ two
  dead names). **No IP SAN, no `connectathon.ihe-catalyst.net`.** Connect by
  `gazelle-tools.ihe-europe.net` or hostname checks fail. TLS 1.2 only. mTLS ports send
  alert 42 `bad_certificate` if the client presents nothing.
- **GSS generator leaf certs are valid 10 years.** Apple rejects TLS *server* certs issued after
  2019-07-01 with validity > 825 days, private roots included (from memory, HT210176). Any iOS
  client verifying a vendor server that uses a fresh GSS cert will fail on that alone; the
  simulator cert (issued 2018) is exempt.
- ATNA TLS is **mutual**: both nodes present certs. Mobile apps that import only the root
  have no client identity.
- iOS/iPadOS devices are failing to trust the chain.


Generic triage commands and the mobile-trust rules: `docs/TLS-CERTS.md` at the repo root.
