#!/usr/bin/env python3
"""
mllp_send.py: send one HL7 v2 message file over MLLP and print the ACK.
Usage: python3 tools/mllp_send.py <file.hl7> <host> <port>
Env (optional, for MLLPS): TLS_CA (server CA bundle), TLS_CERT + TLS_KEY (client identity),
TLS_SERVERNAME (SNI/hostname check, default <host>), TLS_INSECURE=1 to skip verification.
Line endings in the file are normalized to CR before sending; the ACK is printed with CR
rendered as newlines.
Logging: the exact bytes sent and the ACK go to logs/<SEND_ACTOR>/send-<YYYYMMDD>/ as
<ts>-out-<host>_<port>-<MSH-9>.out.hl7 and .ack.hl7, with a line in that folder's summary.log
(also for a failed send). SEND_ACTOR default result-aggregator (ITI-31 in EBIW_POCUS_Simple_Workflow
step 10 is the Result Aggregator's); LOG_DIR default logs. These files are the sender-side evidence.
"""
import os, socket, ssl, sys
from datetime import datetime
from pathlib import Path

VT, FS, CR = b"\x0b", b"\x1c", b"\x0d"

def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    path, host, port = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
    raw = path.read_bytes().replace(b"\r\n", b"\r").replace(b"\n", b"\r").rstrip(b"\r") + CR
    msh = (raw.split(CR, 1)[0].decode("latin-1").split("|") + [""] * 12)
    folder = Path(os.environ.get("LOG_DIR", "logs")) / os.environ.get("SEND_ACTOR", "result-aggregator") / f"send-{datetime.now():%Y%m%d}"
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"{datetime.now():%Y%m%d-%H%M%S}-out-{host}_{port}-{msh[8].replace('^', '_') or 'unknown'}"
    def log(line):
        with (folder / "summary.log").open("a") as f:
            f.write(f"{datetime.now():%H:%M:%S} {line}\n")
    (folder / f"{stem}.out.hl7").write_bytes(raw)
    try:
        ack = exchange(raw, host, port)
    except Exception as e:
        log(f"SEND {msh[8]} MSH-10={msh[9]} to {host}:{port} FAILED {type(e).__name__}: {e} file={stem}.out.hl7 (from {path.name})")
        raise
    (folder / f"{stem}.ack.hl7").write_bytes(ack)
    msa = next((seg.split("|") for seg in ack.decode("latin-1").split("\r") if seg.startswith("MSA|")), ["", "(no MSA)"])
    log(f"SEND {msh[8]} MSH-10={msh[9]} to {host}:{port} -> {'|'.join(msa[1:3])} file={stem}.out.hl7 (from {path.name})")
    print(ack.decode("latin-1").replace("\r", "\n"))
    print(f"logged: {folder / stem}.out.hl7 + .ack.hl7", file=sys.stderr)


def exchange(raw, host, port):
    sock = socket.create_connection((host, port), timeout=10)
    if os.environ.get("TLS_CA") or os.environ.get("TLS_CERT") or os.environ.get("TLS_INSECURE"):
        ctx = ssl.create_default_context(cafile=os.environ.get("TLS_CA"))
        if os.environ.get("TLS_INSECURE"):
            ctx.check_hostname, ctx.verify_mode = False, ssl.CERT_NONE
        if os.environ.get("TLS_CERT"):
            ctx.load_cert_chain(os.environ["TLS_CERT"], os.environ.get("TLS_KEY"))
        sock = ctx.wrap_socket(sock, server_hostname=os.environ.get("TLS_SERVERNAME", host))
    sock.sendall(VT + raw + FS + CR)
    buf = b""
    while FS + CR not in buf:
        chunk = sock.recv(65536)
        if not chunk:
            break
        buf += chunk
    sock.close()
    start, end = buf.find(VT), buf.find(FS + CR)
    return buf[start + 1:end] if start >= 0 and end >= 0 else buf


if __name__ == "__main__":
    main()
