# TLS, certificates, CRLs, and iOS trust: floor troubleshooting

## Situation (NA 2026)
- Floor TLS uses the **GSS CA (id 643)**. Every participant must trust it. Leaf certs come
  from the GSS generator: https://connectathon.ihe-catalyst.net/gss/request/withoutcsr.seam
  (fiddly UX; people get CN/SAN/type wrong). SAN must be `<gazelle hostname>.na2026.net`.
  Certificate type "Client and Server", 2048-bit.
- **Two CAs named "IHE Europe CA" live in GSS.** The floor CA is **id 2656**
  (`…CN=IHE Europe CA,OU=Gazelle`, RSA-2048, 2018→2028, PEM in
  `artifacts/gss-ca-2656-ihe-europe-ca-gazelle.pem`). **Id 643** (`…CN=IHE Europe CA`, no OU,
  RSA-1024) is legacy and issues nothing on the floor; it only shows up in the simulators'
  acceptable-client-CA list. Don't use a 643 CRL or 643 cert for anything.
- **CRL DP issue (verified Oct 12 12:30 ET):** the GSS server simulators' leaf **and** the CA
  2656 cert carry CDP `https://gazelle.ihe.net/pki/crl/2656/cacrl.crl`. The host resolves; the
  path returns **404**. Working: `https://connectathon.ihe-catalyst.net/pki/crl/2656/cacrl.crl`
  (also `/gss/crl/2656/cacrl.crl`). Vendor certs generated this week already carry the
  catalyst CDP. the Gazelle maintainers is fixing it as of Oct 12 11:04. Ticket: `tickets/20261012-tls-server-verify-crl.md`.
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

## Triage commands (run on any participant laptop)
```bash
# Inspect a cert
openssl x509 -in leaf.pem -noout -text | sed -n '/Subject:/p;/Issuer:/p;/Not After/p;/Subject Alternative Name/,+1p;/Extended Key Usage/,+1p;/CRL Distribution/,+3p;/Authority Information Access/,+3p'

# What does the server actually present (full chain)?
openssl s_client -connect host.domain:443 -servername host.domain -showcerts </dev/null

# Verify chain against the Connectathon root
openssl verify -CAfile connectathon-root.pem -untrusted intermediate.pem leaf.pem

# Verify WITH CRL checking (reproduces revocation-check failures)
openssl verify -crl_check -CAfile connectathon-root.pem -CRLfile ca.crl leaf.pem

# Is the CRL endpoint reachable / what does it return?
curl -sv -o /tmp/ca.crl "<CRL DP URL from the cert>" && openssl crl -inform DER -in /tmp/ca.crl -noout -text | head -20

# DICOM TLS / HL7 MLLPS / syslog TLS are raw TLS; same s_client without -servername if no SNI
```

## CRL Distribution Point failures: what breaks and for whom
- Clients that **hard-fail on revocation** (some Java stacks with
  `com.sun.net.ssl.checkRevocation=true` / `ocsp.enable`, Windows Schannel in some modes,
  some .NET configs) reject the handshake when the CDP is unreachable or 404.
- Most OpenSSL-based stacks don't fetch CRLs at all unless configured; they won't notice.
- Browsers mostly soft-fail for private roots.
- Fixes in order of preference: (1) publish a CRL at the CDP URL (empty CRL signed by the CA
  is fine); (2) reissue certs without a CDP extension; (3) per-client workaround:
  disable revocation checking for the Connectathon trust anchor only.
- GSS test 11110 includes an `IHE_ErrorCase_Revoked` case, so the GSS CA has its own CRL
  semantics. Don't confuse the GSS CA with the floor's private root.

## iOS / iPadOS trust requirements (verify against current Apple docs)
- Installing a root via profile is **not enough**: Settings → General → About →
  Certificate Trust Settings → enable full trust for that root.
- Server certs must have the hostname in **subjectAltName** (CN is ignored).
- Must include **EKU serverAuth** (id-kp-serverAuth).
- RSA ≥ 2048 or ECDSA, SHA-2 signatures; SHA-1 rejected.
- Validity: ≤ 825 days for certs chaining to user-installed/private roots (≤ 398 days rule
  applies to publicly trusted roots).
- Missing intermediate on the server = failure (iOS won't AIA-fetch reliably for private PKI).
- MDM/profile must contain the **root**, not just the leaf; a leaf-only profile won't install
  as a trust anchor.
- If the device uses the cert as a **client** cert (mTLS), it needs a PKCS#12 with private key
  + chain, EKU clientAuth, and an app that can actually present it (Safari via profile
  identity; many apps can't).

## Problem-statement checklist for a cert ticket
1. Which endpoint (host:port, protocol: HTTPS / DICOM-TLS / MLLPS / syslog-TLS)?
2. Client stack (iOS version + app, Java version, OpenSSL, .NET, browser)?
3. Exact error string / alert code (unknown_ca, bad_certificate, certificate_expired, etc.).
4. `openssl x509 -text` of leaf + issuer; `s_client -showcerts` output.
5. Root installed? Fully trusted (iOS)? Chain complete?
6. CDP/AIA present? Reachable from the Connectathon network?
7. Which generator was used, and with what field values (CN, SAN, key size, EKU)?
