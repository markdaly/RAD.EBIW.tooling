# Mobile POCUS app: TLS handshake error on "server verify" against GSS; CRL DP host deprecated

- **Source:** Zulip, Support on Gazelle tools → "Gazelle CRL endpoint location does not exist"
  https://ihe-catalyst.zulipchat.com/#narrow/channel/495844-Support-on-Gazelle-tools/topic/Gazelle.20CRL.20endpoint.20location.20does.20not.20exist/with/631039594
- **Opened:** 2026-10-12 10:57 ET (ITI TPM)
- **Status:** needs-evidence (hypotheses re-ranked after verification, Oct 12 12:30 ET)
- **Domain / profile / actor / transaction:** ITI ATNA / Secure Node or Application / ITI-19
  (GSS test 11109-style TLS check). Likely related to EBIW/POCUS testing for the same system.

## Symptom
- A handheld point-of-care ultrasound **mobile app** uses its built-in "server verify" function
  and gets a **TLS handshake error**. The error is visible in GSS logs, but nobody has
  identified which side or which check raised it.
- The vendor reports the **root CA import worked** on the device.
- Separately, the ITI TPM found the CRL Distribution Point
  `https://gazelle.ihe.net/pki/crl/643/cacrl.crl` **no longer resolves**, while
  `https://connectathon.ihe-catalyst.net/pki/crl/643/cacrl.crl` does. He suspects this causes
  server-verification errors "on at least one implementation".
- the Gazelle maintainers: `gazelle.ihe.net` is deprecated; they are "working to resolve".
- Open question from the Gazelle maintainers, unanswered: what exactly is the app doing when it handshakes?
  The TPM says "server verify", but the transport (HTTPS, DICOM-TLS, syslog-TLS) and the
  target endpoint haven't been stated.

## Scope
At least one implementation (mobile app). Unknown whether other stacks are affected. CRL
fetch failure only hurts clients/servers that hard-fail on revocation.

## Evidence so far
- Zulip thread (TPM, the Gazelle maintainers), quoted above.
- GSS shows the handshake error (TPM). No permanent link to the GSS connection result posted.

### Verified Oct 12 ~12:30 ET (second pass, independent re-check of the first pass)
Everything below was observed from the monitor's Mac against the live GSS instance; files in `artifacts/`.

**There are two "IHE Europe CA"s in GSS, and the first pass conflated them.**

| | CA id 643 (legacy) | CA id 2656 (**floor CA**) |
|---|---|---|
| Subject | `C=FR,O=IHE Europe,CN=IHE Europe CA` | `C=FR,O=IHE Europe,CN=IHE Europe CA,OU=Gazelle` |
| Key | **RSA-1024** (modulus from GSS view page) | **RSA-2048** (verified from cert in `artifacts/gss-ca-2656-ihe-europe-ca-gazelle.pem`) |
| Validity | n/a (not fetched) | 2018-11-27 → 2028-11-27, serial 1, self-signed, SHA-512 |
| SKI | (CRL AKI `EC:33:0E:13…`) | `1E:43:73:B4:55:FD:2A:AD:5F:A1:EC:8A:26:89:94:30:6D:62:39:8F` |
| CRL | `/pki/crl/643/cacrl.crl` and `/gss/crl/643/cacrl.crl`, 128-byte sig, revocations from 2015/2017 | `/pki/crl/2656/cacrl.crl` and `/gss/crl/2656/cacrl.crl`, 256-byte sig, AKI matches SKI above, one revocation (serial 06, 2018-11-29) |
| Issues floor certs? | No: every cert in GSS "List certificates" (ids 4610–4631, all issued this week) names CA 2656 as issuer | **Yes** |

So: `artifacts/cacrl.crl` (= `artifacts/cacrl-643-legacy.crl`) is real and is RSA-1024 signed, but it belongs to a CA that is **not in the floor chain**. The CRL number for 643 still increments on every fetch (dynamically generated), which is why it looked alive.

**What the GSS "Floor" server simulators actually present** (`openssl s_client` to 151.80.220.161 ports 10040, 10075, 10077, 10081; identical on all four; leaf saved as `artifacts/gss-simulators-server-cert.pem`):
- Leaf `CN=Gazelle Simulators`, issued by CA 2656, RSA-2048, SHA-512, **valid 2018-11-29 → 2028-11-29**.
- SAN: `gazelle-tools.ihe-europe.net, gazelle-tools.ihe.net, gazelle-tools.ihe-us-test.net, gazelle.ihe.net, gazelle.ihe-europe.net`. **No `connectathon.ihe-catalyst.net`, no IP SAN.**
- EKU: serverAuth, clientAuth, emailProtection, MS smartcard logon.
- **CDP in both leaf and CA cert: `https://gazelle.ihe.net/pki/crl/2656/cacrl.crl`** → HTTP **404** (host resolves to 51.77.180.103; it is the path that is gone, not DNS). Working equivalent: `https://connectathon.ihe-catalyst.net/pki/crl/2656/cacrl.crl` (HTTP 200).
- Chain verifies cleanly against CA 2656, with and without `-crl_check` using the working CRL.
- Hostname: the GSS server list shows the IP `151.80.220.161`. That IP reverse-resolves to `gazelle-tools.ihe-europe.net`, which forward-resolves back to it and **is** in the SAN. `connectathon.ihe-catalyst.net` is a different host (51.83.86.157) and `gazelle.ihe.net` yet another (51.77.180.103). So a client that connects by IP, or by the `connectathon.ihe-catalyst.net` name, **fails hostname verification**; only `gazelle-tools.ihe-europe.net` (or `gazelle-tools.ihe.net`, which does not resolve) passes.
- mTLS: ports 10075/10077/10081 send a CertificateRequest listing both CA 2656 and CA 643 as acceptable; with **no client cert, GSS aborts with alert 42 `bad_certificate`**. Port 10040 ("HTTP non mTLS") completes without a client cert.
- TLS 1.2 only on the Floor simulators (TLS 1.3 ClientHello → alert 40). ECDHE-RSA-AES256-GCM-SHA384 negotiated.

**Vendor leaf certs from the GSS generator this week** (e.g. GSS cert id 4631, viewed in GSS): RSA-2048, SHA-512, SAN `<host>.na2026.net`, EKU serverAuth+clientAuth, CDP `https://connectathon.ihe-catalyst.net/gss/crl/2656/cacrl.crl` (correct host), **validity 10 years (2026-10-12 → 2036-10-12)**.

## Hypotheses (ranked)
1. **Mutual TLS: the app presents no client cert (or one GSS can't chain).** Verified: every Floor simulator except 10040 demands a client cert and rejects the handshake with `bad_certificate` (42) when none is sent. A mobile app with only the root imported has no identity to present. This produces exactly "handshake error, visible in GSS logs, root import worked". **Confirm:** GSS permanent link for the failed connection; the alert will be 42 sent by the server if this is it. Quick A/B: point the app at port **10040** (non-mTLS); if that passes, it's mTLS provisioning.
2. **Hostname mismatch.** If the app targets `151.80.220.161` or `connectathon.ihe-catalyst.net`, iOS/Android/Java all fail SAN matching (no IP SAN, wrong name). This surfaces as the *client* aborting (iOS: `bad_certificate`/`unknown_ca`-ish alert from the client side, GSS logs "handshake failure" with no client cert received). **Confirm:** what host string the app uses; retry with `gazelle-tools.ihe-europe.net`.
3. **iOS validity-period rule, but only for vendor-issued server certs, not the GSS simulator.** Apple requires TLS server certs issued after 2019-07-01 to have ≤ 825 days validity (from memory of Apple HT210176; applies to private roots too). The simulator leaf was issued 2018-11-29, so it is **exempt**. GSS-generated vendor certs (10-year, issued Oct 2026) are **not**: an iOS client verifying a vendor's PACS/gateway with a GSS-issued cert will fail on this regardless of trust settings. Not the cause of the GSS simulator failure, but the next thing that bites POCUS→PACS on the floor.
4. **Device trust not actually enabled (iOS)**, or the app uses its own bundled trust store. Unchanged from first pass; still plausible, still needs the device checked (Settings → General → About → Certificate Trust Settings).
5. **Revocation hard-fail on the dead CDP.** The dead CDP is real (404, `gazelle.ihe.net/pki/crl/2656/...`) and sits in both the simulator leaf and the CA cert itself. iOS does not fetch CRLs for TLS, so this does not explain the mobile app; it will hit Java/.NET/Windows stacks with revocation checking on, and any 11109 run where the *server side* checks the client cert's CDP. the Gazelle maintainers reissuing certs with the catalyst CDP, or publishing the CRL at the old path, fixes it.

**Dropped:** ~~RSA-1024 CA~~. The floor CA (2656) is 2048-bit; the 1024-bit key belongs to legacy CA 643, which issues nothing on the floor. iOS/Android/SECLEVEL arguments about key size do not apply. The one place CA 643 still appears is the simulators' acceptable-client-CA list, which is harmless.

Ruled out: cipher mismatch (ECDHE-RSA-GCM offered and negotiated; iOS supports it).

## Missing evidence
- [x] CA cert key size: **2048** (CA 2656). Legacy CA 643 is 1024 and not in the chain.
- [x] Simulator server cert: SAN, CDP, validity, EKU (see above).
- [ ] GSS permanent link to the failed connection (TLS/SSL → Connection logs); note who sent the alert and which alert.
- [ ] App platform (iOS/Android + version) and what "server verify" connects to: **host string** (IP vs name) and **port** (10040 vs an mTLS port).
- [ ] Is a client cert/PKCS#12 provisioned in the app? Which CN / serial?
- [ ] Reproduce from a floor laptop with the vendor's client cert:
      `openssl s_client -connect gazelle-tools.ihe-europe.net:10081 -servername gazelle-tools.ihe-europe.net -cert client.pem -key client.key -CAfile artifacts/gss-ca-2656-ihe-europe-ca-gazelle.pem`
      then without `-cert/-key` (expect alert 42), then against 10040 without a client cert (expect success).
- [ ] On the device: root full-trust toggle state (iOS); Safari against `https://gazelle-tools.ihe-europe.net:10040/` should load (or at least not complain about trust) if the root is trusted.

## Next action
the monitor: ask the TPM/vendor for (a) the GSS permanent link, (b) host string + port the app uses, (c) whether a client identity is loaded. Tell them the 10040 vs 10081 A/B and the `gazelle-tools.ihe-europe.net` name. Post the two-CA finding and the dead-CDP path (`/pki/crl/2656/` on `gazelle.ihe.net`, 404) to the Zulip thread for the Gazelle maintainers; the fix on their side is CDP reissue or a redirect from the old path. No code needed yet; `tlscheck.sh` only if the s_client matrix gets run more than once.

## Resolution
_Open._
