# NA 2026 floor: tool endpoints and network (from Zulip, Oct 9–12)

Source: Zulip, 2026 IHE North America Connectathon Floor → topics "tools & support" and "network".
Re-check Zulip for changes; this snapshot is from Mon Oct 12 ~noon ET.

## Tool endpoints
| Tool | Endpoint |
|---|---|
| Gazelle Test Management | https://connectathon.ihe-catalyst.net/tm/home.seam |
| Gazelle Security Suite: cert generator (no CSR) | https://connectathon.ihe-catalyst.net/gss/request/withoutcsr.seam |
| GSS Syslog Collector (list) | https://connectathon.ihe-catalyst.net/gss/syslog/list.seam |
| GSS CA CRL (CA id 643), **working** | https://connectathon.ihe-catalyst.net/pki/crl/643/cacrl.crl |
| GSS CA CRL, **deprecated host, does not resolve** | https://gazelle.ihe.net/pki/crl/643/cacrl.crl |
| Gazelle Proxy | proxy.ihe-europe.net / 192.168.2.5 (enabled for Connectathon and Plugathon sessions) |
| NIST DEV/PCD tool (devices) | https://ihe-pcd.ihe-catalyst.net/pcdtool/#/home ("Context-free" tab: /#/cf) |

**Note:** the old `gazelle.ihe.net` host is deprecated (the Gazelle maintainers confirmed). Anything still
pointing there (CRL Distribution Points in certs, bookmarks, tool configs) is suspect.

## GSS Syslog Collector (ITI-20 target for test 11117)
- Host: 151.80.220.161 (public) / 192.168.2.4 (floor)
- UDP 3001 · TCP 3102 · TLS 3202
- Known issue thread (Support on Gazelle tools): "GSS Syslog Collector is not up". Check
  status before blaming a vendor's syslog sender.

## Network
- Connectathon subnet: 10.242.1.0/24, DHCP from .125 up
- Plugathon subnet: 10.242.2.0/24, DHCP from .125 up
- Systems under test get a **fixed IP + hostname under `na2026.net`** from Gazelle (system →
  network configuration). FQDN for cert SANs = `<gazelle hostname>.na2026.net`.
- Laptops and other devices: DHCP.
- Cloud-hosted systems see floor traffic from public IPs **129.174.231.124–126**; vendors must
  allow these in their firewalls.
- Wi-Fi SSID and passphrase: posted in the Zulip "network" topic (not copied here).

## Where to ask
- Gazelle tool problems: Zulip channel **Support on Gazelle tools**, one topic per issue with
  a clear title. the Gazelle maintainers answer there.
- Profile/test questions: **Support from IHE Domain TPMs**. ITI TPM is active on TLS/ATNA.
