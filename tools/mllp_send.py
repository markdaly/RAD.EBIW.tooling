#!/usr/bin/env python3
"""
mllp_send.py: send one HL7 v2 message file over MLLP and print the ACK.
Usage: python3 tools/mllp_send.py <file.hl7> <host> <port>
Env (optional, for MLLPS): TLS_CA (server CA bundle), TLS_CERT + TLS_KEY (client identity),
TLS_SERVERNAME (SNI/hostname check, default <host>), TLS_INSECURE=1 to skip verification.
Line endings in the file are normalized to CR before sending; the ACK is printed with CR
rendered as newlines and also written next to the input file as <file>.ack.hl7.
"""
import os, socket, ssl, sys
from pathlib import Path

VT, FS, CR = b"\x0b", b"\x1c", b"\x0d"

def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    path, host, port = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
    raw = path.read_bytes().replace(b"\r\n", b"\r").replace(b"\n", b"\r").rstrip(b"\r") + CR
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
    ack = buf[start + 1:end] if start >= 0 and end >= 0 else buf
    Path(str(path) + ".ack.hl7").write_bytes(ack)
    print(ack.decode("latin-1").replace("\r", "\n"))

if __name__ == "__main__":
    main()
