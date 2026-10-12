#!/usr/bin/env python3
"""
mllp_receiver.py: generic HL7 v2 receiver over MLLP. Stand-in for any actor whose only job
on the wire is "accept the message, log it, send an ACK". Built for the EBIW Result
Aggregator (RAD-132 Notify of Imaging Results, ORU^R01), usable as an Order Filler sink
or ADT consumer unchanged.

Behavior (RAD TF-2 4.132.4.1.3 / 4.128.4.2, HL7 v2.5.1 ch.2 original-mode ACK):
  - Accept one or more MLLP frames per TCP connection: <VT 0x0B> message <FS 0x1C><CR 0x0D>.
  - Write every inbound message and every outbound ACK to disk, byte-for-byte.
  - Reply ACK^<trigger>^ACK with MSA-1 = AA and MSA-2 = inbound MSH-10.
    If MSH cannot be parsed, reply MSA-1 = AR. Nothing else is validated: the monitor
    reads the captured message against the profile; this tool does not grade.
  - Stateless. Multiple messages for the same study are simply logged in order.

Config (env vars):
  LISTEN_HOST   default 0.0.0.0
  LISTEN_PORT   default 2575
  ACTOR         log folder name, default result-aggregator
  LOG_DIR       default ./logs
  ACK_APP       MSH-3 of the ACK, default SIMULATOR (matches the Gazelle HL7 config "SIMULATOR / SIMULATOR")
  ACK_FACILITY  MSH-4 of the ACK, default SIMULATOR (Gazelle convention for monitor-run senders)
  TLS_CERT / TLS_KEY   PEM server identity; both set => MLLPS (TLS 1.2+)
  TLS_CA        PEM CA bundle; if set, client certificate is REQUIRED (ATNA mutual TLS)
                Note: a client that fails the TLS handshake never reaches this code, so it
                leaves no log line here (asyncio swallows SSLError unless in debug mode).
                Diagnose those with `openssl s_client` from the sending side.

Run:  LISTEN_PORT=2575 python3 tools/mllp_receiver.py
Logs: logs/<ACTOR>/<session ts>/<msg ts>-<n>-<MSH-9>.in.hl7 and .ack.hl7, plus summary.log
"""
import asyncio, os, ssl, sys
from datetime import datetime
from pathlib import Path

VT, FS, CR = b"\x0b", b"\x1c", b"\x0d"

HOST = os.environ.get("LISTEN_HOST", "0.0.0.0")
PORT = int(os.environ.get("LISTEN_PORT", "2575"))
ACTOR = os.environ.get("ACTOR", "result-aggregator")
ACK_APP = os.environ.get("ACK_APP", "SIMULATOR")
ACK_FAC = os.environ.get("ACK_FACILITY", "SIMULATOR")
SESSION_DIR = Path(os.environ.get("LOG_DIR", "logs")) / ACTOR / datetime.now().strftime("%Y%m%d-%H%M%S")
SESSION_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY = SESSION_DIR / "summary.log"
counter = 0


def log(line: str) -> None:
    stamped = f"{datetime.now().strftime('%H:%M:%S')} {line}"
    print(stamped, flush=True)
    with SUMMARY.open("a") as f:
        f.write(stamped + "\n")


def parse_msh(msg: bytes):
    """Return (fields of MSH as list, field_sep) or (None, None). MSH-1 is the separator
    itself, so fields[0]='MSH', fields[1]=encoding chars, fields[2]=MSH-3, ... fields[n-1]=MSH-n."""
    text = msg.decode("latin-1")
    first = text.split("\r", 1)[0].split("\n", 1)[0]
    if not first.startswith("MSH") or len(first) < 9:
        return None, None
    sep = first[3]
    return first.split(sep), sep


def field(fields, n, default=""):
    i = n - 1  # MSH-n lives at index n-1 because MSH-1 (the separator) is consumed by split
    return fields[i] if fields and i < len(fields) else default


def build_ack(msg: bytes) -> tuple[bytes, str]:
    fields, sep = parse_msh(msg)
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    if fields is None:
        ack = "\r".join([
            f"MSH|^~\\&|{ACK_APP}|{ACK_FAC}|||{now}||ACK|{now}|P|2.5.1",
            "MSA|AR||Cannot parse MSH",
        ]) + "\r"
        return ack.encode("latin-1"), "AR"
    enc = field(fields, 2, "^~\\&")
    comp = enc[0] if enc else "^"
    sending_app, sending_fac = field(fields, 3), field(fields, 4)
    msg_type = field(fields, 9)
    trigger = msg_type.split(comp)[1] if comp in msg_type else ""
    ctrl_id = field(fields, 10)
    proc_id = field(fields, 11, "P")
    version = field(fields, 12, "2.5.1")
    ack_type = f"ACK{comp}{trigger}{comp}ACK" if trigger else "ACK"
    ack = sep.join(["MSH", enc, ACK_APP, ACK_FAC, sending_app, sending_fac, now, "",
                    ack_type, f"ACK{now}{counter:04d}", proc_id, version]) + "\r"
    ack += sep.join(["MSA", "AA", ctrl_id]) + "\r"
    return ack.encode("latin-1"), "AA"


def summarize(msg: bytes) -> str:
    """One line for the console: the fields a monitor looks at first. Read-only, no grading."""
    segs = {}
    for seg in msg.decode("latin-1").replace("\n", "\r").split("\r"):
        if len(seg) > 3 and seg[3] == "|" and seg[:3] not in segs:
            segs[seg[:3]] = seg.split("|")
    def g(seg, n):
        s = segs.get(seg)
        if not s:
            return "-"
        i = n - 1 if seg == "MSH" else n  # MSH-1 is the separator, so MSH indexes shift by one
        return s[i] if i < len(s) else "-"
    return (f"MSH-9={g('MSH',9)} MSH-10={g('MSH',10)} MSH-12={g('MSH',12)} "
            f"PID-3={g('PID',3)} PID-5={g('PID',5)} PV1-19={g('PV1',19)} OBR-4={g('OBR',4)} "
            f"OBR-18={g('OBR',18)} OBR-19={g('OBR',19)} OBR-25={g('OBR',25)} OBX-5(1st)={g('OBX',5)}")


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    global counter
    peer = "%s:%s" % writer.get_extra_info("peername")[:2]
    log(f"CONNECT from {peer}")
    buf = b""
    try:
        while True:
            chunk = await reader.read(65536)
            if not chunk:
                break
            buf += chunk
            while True:
                start = buf.find(VT)
                end = buf.find(FS + CR, start + 1) if start >= 0 else -1
                if start < 0 or end < 0:
                    break
                msg = buf[start + 1:end]
                buf = buf[end + 2:]
                counter += 1
                ack, status = build_ack(msg)
                fields, _ = parse_msh(msg)
                mtype = field(fields, 9).replace("^", "_") if fields else "UNPARSED"
                stem = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{counter:04d}-{mtype}"
                (SESSION_DIR / f"{stem}.in.hl7").write_bytes(msg)
                (SESSION_DIR / f"{stem}.ack.hl7").write_bytes(ack)
                writer.write(VT + ack + FS + CR)
                await writer.drain()
                log(f"MSG #{counter} from {peer} -> {status}  {summarize(msg)}  file={stem}.in.hl7")
    except (ConnectionResetError, asyncio.IncompleteReadError, ssl.SSLError) as e:
        log(f"ERROR {peer}: {e}")
    finally:
        if buf.strip(b"\r\n\x0b\x1c"):
            (SESSION_DIR / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-partial.bin").write_bytes(buf)
            log(f"WARN {peer}: {len(buf)} unframed bytes at close, saved")
        writer.close()
        log(f"CLOSE {peer}")


def tls_context():
    cert, key, ca = os.environ.get("TLS_CERT"), os.environ.get("TLS_KEY"), os.environ.get("TLS_CA")
    if not (cert and key):
        return None
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(cert, key)
    if ca:
        ctx.load_verify_locations(ca)
        ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


async def main() -> None:
    ctx = tls_context()
    server = await asyncio.start_server(handle, HOST, PORT, ssl=ctx)
    log(f"{ACTOR} listening on {HOST}:{PORT} {'MLLPS' if ctx else 'MLLP'}"
        f"{' (client cert required)' if ctx and ctx.verify_mode == ssl.CERT_REQUIRED else ''}; logs in {SESSION_DIR}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
