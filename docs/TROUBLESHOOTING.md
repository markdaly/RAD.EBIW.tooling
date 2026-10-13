# Troubleshooting

Symptoms first, in the order they happen on a floor.

## A server will not start

- **`Address already in use`**: something still holds the port. `lsof -nP -iTCP:<port> -sTCP:LISTEN`
  shows it; `tools/floor.sh stop` kills the tmux session; a stray process from a manual run
  needs `kill <pid>`.
- **`uv: command not found`**: install uv (`docs/INSTALL.md`) or run with a venv and
  `pip install -r requirements.txt`, then `python tools/<tool>.py`.
- **`ModuleNotFoundError: pydicom`**: you ran plain `python3` instead of
  `uv run --with pynetdicom --with pydicom ... python`.
- **`floor.sh` prints `declare: -A: invalid option`**: old copy of the script; macOS ships bash
  3.2. Current script does not use associative arrays.
- **A tmux window shows the server exited**: the error is on screen; `tools/floor.sh restart <win>`
  after fixing it.

## Nothing arrives

The console line `CONNECT from <ip>` followed by `CLOSE` with no `MSG` means a TCP probe, not a
message. No `CONNECT` at all means the vendor never reached the port.

1. **Right IP?** Floor laptops often have two interfaces. `ifconfig | grep 'inet '` and give the
   vendor the floor one. Hostnames may not resolve on the floor DNS; give the IP.
2. **Firewall.** macOS: System Settings → Network → Firewall; off, or allow the Python binary.
3. **Vendor's side.** Ask for their engine's log line. "Connection refused" = wrong IP or port
   or server down; "timeout" = firewall or wrong subnet; "reset" = TLS mismatch (they used TLS,
   the server is plain, or vice versa).
4. **Through the Gazelle proxy.** Connect to the proxy port yourself:
   `nc -z -G 3 <proxy-host> <proxy-port>`. Accepts then resets within a second = the proxy could
   not reach the target it was given (hostname not resolvable, channel not started). Check the
   configuration's host field and the channel status in Gazelle; try the IP.
5. **Unframed bytes.** `WARN <peer>: N unframed bytes at close, saved` means data arrived without
   MLLP framing (no `0x0B` / `0x1C 0x0D`). The vendor sent raw HL7 over TCP, or TLS bytes to a
   plain port. Look at the `-partial.bin` file.

## ACK says AR

`MSA|AR||Cannot parse MSH`: the first segment was not `MSH` with a readable field separator.
Usually a framing or encoding problem (UTF-16, a BOM, CRLF inside the frame). Open the `.in.hl7`
in a hex viewer. The receiver does not reject on content; every parseable message gets `AA`.

## Worklist returns nothing

- `C-FIND #n ... done, 0 match(es)`: the query keys did not match any encounter. The console
  prints the non-empty keys; compare with `samples/encounters.json` (or whatever `ENCOUNTERS`
  points at). Patient ID and Admission ID are exact unless the SCU sends a wildcard.
- The SCU got an association reject: AE title mismatch. The SCP accepts any called AE, so the
  reject is on the SCU side (wrong host/port) or a TLS expectation.
- Dates: SPS Start Date in the response is always today; a date-range query for another day
  returns nothing, which is correct.
- Same admission, different accession: the key is (Admission ID, modality, station), where
  station is the Scheduled Station AE Title in the query (MWL) or the Station Name Code
  (UPS-RS). Same admission to the same device gives the same accession (RAD TF-1 47.1.1.1);
  another device or the other procedure under that admission gets its own.
- A row names a modality or AE title and never matches: those are matching keys when set.
  Blank them in the encounters file to make a row match any device.

## UPS-RS returns 204 or 404

- `204`: no encounter matched the query parameters. Check spelling of dotted keys
  (`ScheduledStationNameCodeSequence.CodeValue`, not `...CodeMeaning` unless that is what you set).
- `404`: wrong path. Served paths are in `ROUTES` (default `/workitems` and `/studies`), under
  `BASE_PATH` if set. The console shows them at start.
- Client expects Accession at top level: UPS instances carry it in Referenced Request Sequence
  (0040,A370). A QIDO-RS client looking for `00080050` at top level is querying the wrong service.

## ITI-31 ADT is rejected

`ITI-31 from <peer>: no PID/PV1-19, rejected (AR)`: the message had no PID segment or an empty
PV1-19 Visit Number. The Encounter Manager keys encounters on PV1-19; nothing else is required.
Count the pipes in PV1: a hand-typed segment that is one pipe short puts the visit number in
PV1-18.

## TLS

- Server side: `TLS_CERT` and `TLS_KEY` set, `TLS_CA` set if the client must present a cert.
  A client that fails the handshake leaves no log line (the error is swallowed before the
  handler runs); diagnose from the client with
  `openssl s_client -connect <host>:<port> -cert client.pem -key client.key -CAfile ca.pem`.
- Cert content problems (SAN, validity, CRL distribution point, key size, mobile trust) are in
  `docs/TLS-CERTS.md` with the openssl commands.

## Panel

- `tools/floor.sh panel` says "already running": `tools/floor.sh panel-stop` first.
- Port 8090 busy: `PANEL_PORT=8091 tools/floor.sh panel`.
- Config saved but ports did not change: the form writes `.floor.env`; it applies on the next
  `restart <win>` or `start`. The status block on the panel shows what is actually listening.
- A capture renders as plain text instead of a field table: the file name does not end in
  `.hl7`, or the first segment is not `MSH`. The raw download still works.

## Evidence for Gazelle

Hand the vendor the raw pair from `logs/<actor>/<session>/`: the `.in.hl7` with its `.ack.hl7`,
the `.query.txt` with its `.respN.txt`, or the `.request.txt` with its `.response.json`. The
`summary.log` line gives the timestamp. Do not edit any of them.

## Resetting between tests

`tools/floor.sh stop`, delete `logs/encounter-manager/state.json` and
`encounters-from-adt.json` if you want fresh accessions and only the sample encounters, then
`tools/floor.sh start`. Old session folders stay; they are evidence.
