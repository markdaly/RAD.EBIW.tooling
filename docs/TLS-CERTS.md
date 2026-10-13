# TLS, certificates, CRLs, and mobile trust: floor troubleshooting

## Event-specific situation
See `events/<event>/docs/TLS-<event>.md` for which CA the floor uses, known CRL path problems and simulator certificate quirks.

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
