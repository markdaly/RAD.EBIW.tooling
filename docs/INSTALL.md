# Install

Tested on macOS (Apple Silicon) and on Ubuntu 22.04, 24.04 and 26.04 (x64 and ARM; 26.04 with its
default Rust coreutils, also as a bare container image run by a non-root user): every push runs
`tools/smoke.sh` there (`.github/workflows/ubuntu-smoke.yml`). Windows is untested; WSL should be fine.

## Prerequisites

- **Git.**
- **uv** (recommended): installs the right Python and the dependencies per run, nothing global.
  `curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`.
- **tmux** if you want `tools/floor.sh` to run everything in one session:
  `brew install tmux` or `apt install tmux`. Each tool also runs on its own without it.
- **openssl** CLI for the TLS triage commands in `docs/TLS-CERTS.md` (preinstalled on macOS and
  most Linux).

Without uv: Python 3.11+ and `pip install -r requirements.txt` in a venv, then replace
`uv run --with ... python` with `python` in the commands below.

## Dependencies

| Package | Used by | License |
|---|---|---|
| pydicom, pynetdicom | `mwl_scp.py`, `mwl_find.py`, `ups_rs.py` | MIT |
| fastapi, uvicorn | `ups_rs.py` | MIT, BSD-3 |
| (stdlib only) | `mllp_receiver.py`, `mllp_send.py` | |

`uv run --with pynetdicom --with pydicom --with fastapi --with uvicorn python tools/<tool>.py`
pulls them into a cached environment on first run (needs network once).

## Ubuntu (22.04, 24.04, 26.04)

The same steps the CI runs:

```bash
sudo apt update && sudo apt install -y git tmux curl
curl -LsSf https://astral.sh/uv/install.sh | sh        # then open a new terminal (adds ~/.local/bin)
git clone https://github.com/markdaly/RAD.EBIW.tooling.git && cd RAD.EBIW.tooling
tools/smoke.sh                                           # 22 checks on spare ports, then cleans up
tools/floor.sh start
```

- **Run `tools/smoke.sh` before the event, on a network with internet.** The first run downloads
  Python and the packages into uv's cache; after that the kit needs no internet.
- **Port 80.** Linux keeps ports below 1024 for root, so the panel serves only 8090 and says so in
  its tmux window. To serve the bare IP too, until the next reboot:
  `sudo sysctl -w net.ipv4.ip_unprivileged_port_start=80`, then
  `tools/floor.sh panel-stop && tools/floor.sh panel`.
- **Firewall.** Ubuntu ships ufw inactive. If `sudo ufw status` says active:
  `sudo ufw allow 80,2575,2576,8042,8090,11112/tcp`.
- **Floor IP:** `hostname -I`.
- **Event pages.** The panel's `howto` page and `CONNECTIONS.md` describe the event's registered
  system (host, IP, Gazelle system keyword). A second machine registered as its own Gazelle system
  needs its own copy: copy `events/<event>/docs/HOWTO.md`, change the IP and system keyword, and
  start the panel with `PANEL_HOWTO=<path to the copy>`.

## First run

```bash
git clone <repo-url> ihe-connectathon-kit
cd ihe-connectathon-kit
tools/floor.sh start
tools/floor.sh status
```

`status` should show the four servers listening: 2575 (HL7 in), 2576 (ADT in), 8042 (UPS-RS),
11112 (DICOM MWL), plus the panel on 80 and 8090 (8090 only on Linux without the sysctl in the Ubuntu section). Attach with `tmux attach -t ihe`; the `logs` window has three panes following the
servers. Stop everything with `tools/floor.sh stop`.

Loopback check before pointing a vendor at it:

```bash
python3 tools/mllp_send.py samples/ORU_R01_RAD-132_POCUS.hl7 127.0.0.1 2575
```

You should get an ACK with `MSA|AA|MSG00001` and a new pair of files under
`logs/result-aggregator/<session>/`.

## Network

- The tools bind `0.0.0.0`. On macOS the application firewall is usually off for a floor laptop;
  if it is on, allow incoming connections for the Python binary uv provisions, or run with the
  firewall off for the event.
- Fixed IP on the floor network: ask the event's network desk or read it off your Gazelle
  system's network configuration. Vendors need the IP (or the Gazelle proxy port in front of it),
  never a hostname that may not resolve on the floor DNS.
- TLS (MLLPS, HTTPS) is optional on every tool via `TLS_CERT`, `TLS_KEY`, `TLS_CA`. Certificates
  come from the event's Gazelle Security Suite; see `docs/TLS-CERTS.md`.

## Where files land

| Path | What |
|---|---|
| `logs/<actor>/<YYYYMMDD-HHMMSS>/` | one folder per server start: `summary.log` plus every raw message, ACK, query and response |
| `logs/encounter-manager/state.json` | accession and Study UID per (Admission ID, station); survives restarts |
| `logs/encounter-manager/encounters-from-adt.json` | encounters received over ITI-31 |

`logs/` is gitignored. Delete the two JSON files for a clean numbering at the start of an event.
