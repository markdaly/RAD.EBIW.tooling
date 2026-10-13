# Install

Tested on macOS (Apple Silicon) and expected to work on any Linux with Python 3.11 or newer.
Windows is untested; WSL should be fine.

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

## First run

```bash
git clone <repo-url> ihe-connectathon-kit
cd ihe-connectathon-kit
tools/floor.sh start
tools/floor.sh status
```

`status` should show four ports listening: 2575 (HL7 in), 2576 (ADT in), 8042 (UPS-RS), 11112
(DICOM MWL). Attach with `tmux attach -t ihe`; the `logs` window has three panes following the
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
