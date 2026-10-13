---
event: IHE North America Connectathon 2026
dates: 2026-10-12 to 2026-10-16
kind: issue
opened: 2026-10-13 10:10 ET
status: workaround in place
expires: 2026-10-16
---
# Vendor's message "came through" but got no ACK: ddx0 still resolves to the old IP

- **Source:** floor report via the monitor, Tue ~10:05 ET. A POCUS-side vendor sent to TOOL_DDx
  and saw the message go out with no ACK back.
- **Domain / profile / actor / transaction:** RAD EBIW / Result Aggregator or Encounter
  Manager (TOOL_DDx) / most likely RAD-132 ORU^R01 to 2575, possibly ITI-31 to 2576

## Symptom
The vendor's sender reports the message delivered (or visible on the proxy side) but no ACK.
Nothing reached the stand-ins on this Mac.

## Scope
Every path into TOOL_DDx that goes by hostname `ddx0` or through the Gazelle proxy. Direct
connections to 10.242.1.99 are unaffected.

## Evidence so far
- The monitor's Mac moved from DHCP 10.242.1.184 to static, reserved 10.242.1.99 at ~09:30 ET.
- `logs/result-aggregator/*/summary.log`: no `CONNECT` line since the 09:04 start. The receiver
  logs every TCP connect, so no socket from anyone reached port 2575. No ADT or C-FIND
  captures either. All four listeners up (`lsof`), firewall off.
- Floor DNS, queried directly at 10:08 ET:
  ```
  dig @192.168.2.5 ddx0.na2026.net A   ->  10.242.1.184
  dig @192.168.2.4 ddx0.na2026.net A   ->  timed out
  ```
- 10.242.1.184 does not answer (no ping, ARP incomplete). Connects to it time out, so a
  sender sees no ACK.
- Proxy channel re-test at 10:08 ET: `mllp_send.py samples/ORU_R01_RAD-132_POCUS.hl7
  proxy.ihe-europe.net 11067` gives `ConnectionResetError`, and nothing arrives (issue 005
  unchanged).
- The Gazelle configurations for TOOL_DDx still carry host ddx0 / 10.242.1.184.

## Hypotheses (ranked)
1. **The proxy forwards to ddx0 / .184, which now goes nowhere.** Confirmed: DNS, plus the
   vendor's own report that they sent through the proxy.
2. The vendor targeted the right address but a different port. Not supported by our logs:
   no listener saw a connect.

## Missing evidence
- [x] Path: the vendor sent through the Gazelle proxy (monitor, 10:12 ET), so the proxy took
      the message and could not forward it to ddx0. The vendor is re-sending direct to .99.
- [ ] The vendor's sender error text, for the record.

## Next action
- Floor team: DNS A record `ddx0.na2026.net` → 10.242.1.99 (in progress, Tue 10:00 ET).
- Monitor, as Gazelle admin: the ddx0 host IP in the TOOL_DDx configurations → 10.242.1.99,
  then check the proxy channels' target (issue 005).
- Meanwhile, the vendor sends directly to **10.242.1.99:2575** (RAD-132) or **:2576** (ITI-31),
  MSH-5/6 `SIMULATOR`/`SIMULATOR`, and attaches the files under `logs/` to the Gazelle test
  instance.
- Re-test after the DNS fix: `dig @192.168.2.5 ddx0.na2026.net A` returns .99, then the
  proxy send above returns an ACK and a `CONNECT from 192.168.2.5` appears in the summary.

## Resolution
Workaround confirmed 10:10:11 ET: the vendor sent direct to 10.242.1.99:2575 and got
`MSA|AA|1` (file `logs/result-aggregator/20261013-094740/20261013-101011-0001-ORU_R01.in.hl7`,
reviewed in issue 002). Closes when DNS says .99 and a proxy send returns an ACK.
