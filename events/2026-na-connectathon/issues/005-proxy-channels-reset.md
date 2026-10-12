# Gazelle Proxy channels for TOOL_DDx accept TCP then close immediately; nothing forwarded

- **Source:** the monitor's own validation of the new proxy channels, Oct 12 16:45 ET. No Zulip thread yet.
- **Opened:** 2026-10-12 16:50 ET
- **Status:** needs-evidence (Gazelle admin side)
- **Domain / profile / actor / transaction:** infrastructure; affects every transaction into
  TOOL_DDx through the proxy (RAD-132, ITI-31, RAD-130 MWL and UPS-RS)

## Symptom
- Four approved configurations for TOOL_DDx (ddx0 / 10.242.1.184) got proxy ports 11064
  (2576), 11065 (11112), 11066 (8042), 11067 (2575).
- From this Mac, `proxy.ihe-europe.net` (192.168.2.5) **accepts TCP on all four ports, then
  closes the connection ~0.1 s later without any data**, before the client sends anything.
  curl reports "Recv failure: Connection reset by peer"; MLLP sends get `ConnectionResetError`.
- **Nothing arrives at the stand-ins** (all four listening, verified with `lsof`; firewall off).
- Direct connections to the Mac from the floor work (the 15:07 ORU came in from 10.242.1.9).

## Scope
Only our system's channels tested. Unknown whether other systems' proxy channels forward.

## Evidence so far
- `nc -z proxy.ihe-europe.net 11064..11067`: connect succeeds.
- Raw socket test on 11067: proxy sends EOF 0.1 s after connect, no bytes.
- Floor DNS: `scutil` shows nameserver 192.168.2.4, search domain `na2026.net`. Direct queries
  to 192.168.2.4 time out from this Mac; `ddx0.na2026.net`, `ge263.na2026.net` do not resolve
  here. The proxy host's own resolver may differ.
- Proxy host 192.168.2.5 serves 403 on `/`; https://proxy.ihe-europe.net/ is a Drupal redirect;
  no channel UI found anonymously. Message Capture (login) is presumably where channels show.

## Hypotheses (ranked)
1. **Proxy forwards to the hostname `ddx0`, which does not resolve on the proxy host**, so its
   outbound connect fails instantly and it closes ours. Immediate close (not a multi-second
   timeout) fits a resolution failure or a refused connect, and refused is ruled out by our
   listeners. **Confirm:** in Gazelle admin, open the channel/configuration detail and see
   whether the target is the IP or the hostname; check whether the network record for ddx0
   has been pushed to DNS (Gazelle TM → Administration → network / DNS export), or ask the Gazelle maintainers.
2. **Channels created but not started** on the proxy after the configurations were approved.
   Gazelle proxy historically needed a "restart channels" action. **Confirm:** channel status
   in Message Capture / proxy admin; try a re-approve or re-save of one configuration.
3. **Proxy cannot route to 10.242.1.0/24.** Less likely: the proxy is "enabled for Connectathon
   sessions" and the floor subnet is the whole point. **Confirm:** test another vendor's
   proxy port (any approved HL7 responder config) from here; if it holds the connection open,
   routing is fine and the problem is ours (1 or 2).

## Missing evidence
- [ ] Channel detail for 11064–11067 (target host/IP, status) from the Gazelle admin side.
- [ ] One other system's proxy port behavior (hold vs instant close).
- [ ] Whether `ddx0.na2026.net` resolves from a floor machine that uses 192.168.2.4 successfully.

## Next action
the monitor (admin): look at the channel detail; if the target is `ddx0`, get the DNS record
published or switch the config host to the IP; if channels show stopped, start them. Re-test with
`tools/mllp_send.py samples/ORU_R01_RAD-132_POCUS.hl7 proxy.ihe-europe.net 11067`; success =
`MSA|AA` back and a line in `logs/result-aggregator/<session>/summary.log` from 192.168.2.5.
If it stays broken, post to Zulip "Support on Gazelle tools" with the symptom line above.

## Resolution
_Open._
