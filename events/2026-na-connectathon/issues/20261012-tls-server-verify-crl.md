# Mobile POCUS app: TLS handshake error on "server verify" against GSS; CRL DP host deprecated

- **Source:** Zulip, Support on Gazelle tools → "Gazelle CRL endpoint location does not exist"
  https://ihe-catalyst.zulipchat.com/#narrow/channel/495844-Support-on-Gazelle-tools/topic/Gazelle.20CRL.20endpoint.20location.20does.20not.20exist/with/631039594
- **Opened:** 2026-10-12 10:57 ET (ITI TPM)
- **Status:** needs-evidence
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
- `artifacts/cacrl.crl`, fetched from the working connectathon.ihe-catalyst.net endpoint and
  inspected by the monitor/Claude on Oct 12:
  - Valid DER CRL v2. Issuer `C=FR, O=IHE Europe, CN=IHE Europe CA`; sha512WithRSA.
  - lastUpdate 2026-10-12 15:39:58Z, nextUpdate 2026-10-13 15:39:58Z (**24h validity**:
    anything caching it goes stale daily). Only 2 revoked serials (019B 2015, 04CE 2017).
  - **Signature is 128 bytes → the issuing CA key is RSA-1024.**
    (`openssl asn1parse`: signature BIT STRING length 129 = 1 pad byte + 128.)

## Hypotheses (ranked)
0. **RSA-1024 CA key is rejected by modern client stacks (NEW, strong).** If the CA that
   signed the CRL is the same CA that issues floor certs, the trust anchor is RSA-1024.
   - **iOS/iPadOS 13+ and macOS 10.15+:** TLS server certs **and issuing CAs** using RSA must
     be ≥ 2048 bits, or they are not trusted for TLS. Importing and fully trusting the root
     does not override this. That fits "root import worked but handshake fails."
   - **Android / BoringSSL** and **OpenSSL at SECLEVEL ≥ 2** (Debian/Ubuntu defaults, many
     containers) also reject 1024-bit RSA in the chain ("ca key too small" / "ee key too small").
   - Java's `jdk.certpath.disabledAlgorithms` includes `RSA keySize < 1024`, so 1024 passes
     there. That would explain why Java/older stacks work and mobile doesn't.
   - GSS docs say "CA with a key of 2048 length", so either this CRL's issuer isn't the floor CA,
     or the docs are stale. **Confirm:** download the CA cert from GSS and run
     `openssl x509 -in ca.pem -noout -text | grep "Public-Key"`. Also check the leaf's
     Issuer DN against `IHE Europe CA`.
   - If confirmed, the only real fix is a new ≥2048-bit CA (the Gazelle maintainers). Device-side workarounds
     don't exist on iOS.
1. **Mutual TLS: the app presents no client cert, or the wrong one.** ATNA node
   authentication is bidirectional, and the GSS TLS server simulators require client cert
   auth. A mobile app with only the root imported has no client identity (needs a PKCS#12
   with key + chain, EKU clientAuth, provisioned to the app or the device). GSS would log
   this as a handshake failure on its side, matching "we see it in GSS".
   **Confirm:** the GSS connection detail (alert, e.g. `certificate_required` /
   `handshake_failure` / `bad_certificate`, and whether a client cert was received).
2. **GSS-side revocation check on the client cert fails** because the client cert's CDP
   points at the dead `gazelle.ihe.net` host. Only bites if the GSS simulator enforces CRL
   checking. It would hit every client with an old-CDP cert, not just this app.
   **Confirm:** dump the client cert's CDP; check whether other participants' 11109 runs pass
   with certs issued from the same CA.
3. **Device trust not actually enabled (iOS).** On iOS, installing the root profile ≠
   trusted. It must be enabled under Settings → General → About → Certificate Trust
   Settings. Or the app ignores the OS store and uses its own bundled trust store, so
   importing into the OS does nothing for the app. Would surface as the *client* aborting
   (`unknown_ca`/`bad_certificate` alert sent by the client).
   **Confirm:** platform and version; is full trust toggled on; does Safari on the same
   device load an HTTPS page served with a GSS-issued cert without a warning?
4. **Hostname/SAN mismatch.** App connects by IP or a hostname not in the server cert's SAN.
   iOS ignores CN and requires a SAN match (IP SAN if connecting by IP).
   **Confirm:** what host/IP the app targets vs SAN in the server cert (`openssl s_client`).
5. **Client-side revocation hard-fail.** The app checks the server cert's CDP, hits the dead
   host, and aborts. Less likely: iOS/Android default stacks don't hard-fail revocation for
   private roots, but an app with custom trust logic might.
   **Confirm:** whether the GSS server simulator cert's CDP points at `gazelle.ihe.net`;
   repeat once the Gazelle maintainers republishes or reissues.

Ruled out unless shown otherwise: cipher mismatch (GSS simulators offer ECDHE-GCM suites;
iOS supports them, though iOS no longer supports DHE suites).

## Missing evidence
- [ ] **CA cert key size** (fastest discriminator for hypothesis 0): download the GSS CA cert, `openssl x509 -noout -text | grep Public-Key`; compare its Subject to the CRL issuer `CN=IHE Europe CA`.
- [ ] GSS permanent link to the failed connection (TLS/SSL → results); note who sent the alert and which alert.
- [ ] App platform (iOS/Android + version) and what "server verify" connects to (host, port, protocol).
- [ ] Is a client cert/PKCS#12 provisioned in the app? Which CN / serial?
- [ ] Leaf + issuer PEMs for both sides; check the CDP and SAN: `openssl x509 -in cert.pem -noout -text`
- [ ] Reproduce from a floor laptop with the same client cert:
      `openssl s_client -connect <gss-sim-host>:<port> -cert client.pem -key client.key -CAfile root.pem -servername <host>`
      then run again without `-cert/-key`, to separate mTLS from trust issues.
- [ ] On the device: root full-trust toggle state (iOS), Safari test against a GSS-cert HTTPS endpoint.

## Next action
the monitor: get items 1–3 from the TPM/vendor (GSS permanent link is the fastest discriminator
between hypotheses 1/2 and 3/4). No code needed yet. If mTLS provisioning on iOS is the
blocker, a likely deliverable is a one-page "provision a GSS client identity on iOS" recipe,
plus a small `tlscheck.sh` that runs the s_client matrix (with/without client cert, with/without CRL check).

## Resolution
_Open._
