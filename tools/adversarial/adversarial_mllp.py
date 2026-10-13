#!/usr/bin/env python3
"""adversarial_mllp.py -- hostile MLLP sender for loopback-testing mllp_receiver.py (and the
ITI-31 intake on mwl_scp.py). Standard library only. Python 3.11+.

It does NOT grade the receiver. For each case it reports one of:
  RESPONDED  bytes came back inside a frame; MSA-1 / MSA-2 are shown, not judged
  NO_ACK     connection closed by peer without an ACK frame
  TIMEOUT    nothing came back within --timeout seconds
  REFUSED    connect() failed
  RESET      connection reset mid-send/receive
and prints the raw ACK with control bytes escaped so it can be pasted into a Gazelle note.

Message files are read from samples/adversarial/*.hl7. A first line starting with '#' is a
description and is stripped. LF line endings are normalised to CR unless --raw is given.

Usage:
  adversarial_mllp.py --host 127.0.0.1 --port 2575 --dir samples/adversarial            # every oru_*.hl7, normal framing
  adversarial_mllp.py --port 2576 --glob 'adt_*.hl7'                                      # ITI-31 intake
  adversarial_mllp.py --file samples/adversarial/oru_baseline.hl7 --frame no-end         # one file, one framing attack
  adversarial_mllp.py --file ... --frame all                                              # every framing mode
  adversarial_mllp.py --file ... --big 10485760                                           # 10 MiB OBX-5
  adversarial_mllp.py --file ... --concurrent 8                                           # 8 sockets at once
  adversarial_mllp.py --file ... --persist 5                                              # 5 messages, one connection
  adversarial_mllp.py --hold 20                                                           # open socket, send nothing, hold 20 s

Framing modes (--frame):
  ok            <VT> msg <FS><CR>                                   (control)
  no-start      msg <FS><CR>                                        missing 0x0B
  no-end        <VT> msg                                            missing 0x1C 0x0D, then half-close
  no-cr         <VT> msg <FS>                                       missing trailing 0x0D
  two-frames    <VT> m1 <FS><CR><VT> m2 <FS><CR>  in ONE write      two messages, one TCP segment
  two-in-frame  <VT> m1 m2 <FS><CR>                                 two MSH inside one frame
  split         frame written in 1..7-byte chunks with 50 ms gaps   slow sender
  split-at-fs   everything up to <FS>, pause 2 s, then <CR>         terminator straddles a read
  trailing      <VT> msg <FS><CR> + 64 bytes of garbage             bytes after the frame
  empty-frame   <VT><FS><CR>                                        zero-length message
  lf-terms      segments terminated with LF instead of CR            common misconfiguration
  crlf-terms    segments terminated with CR LF                       Windows-y senders
  nul-bytes     <VT> msg-with-0x00-in-OBX-5 <FS><CR>                 NUL inside payload
  start-only    <VT> then close                                     half a frame
"""
import argparse, glob, os, socket, sys, threading, time

VT, FS, CR, LF = b"\x0b", b"\x1c", b"\r", b"\n"
MODES = ["ok", "no-start", "no-end", "no-cr", "two-frames", "two-in-frame", "split", "split-at-fs",
         "trailing", "empty-frame", "lf-terms", "crlf-terms", "nul-bytes", "start-only"]


def esc(b: bytes, limit: int = 600) -> str:
    s = b[:limit].decode("latin-1")
    out = s.replace("\x0b", "<VT>").replace("\x1c", "<FS>").replace("\r", "<CR>\n").replace("\n", "<LF>")
    if len(b) > limit:
        out += f"... [{len(b)} bytes total]"
    return out


def load(path: str, raw: bool) -> bytes:
    data = open(path, "rb").read()
    if data.startswith(b"#"):
        nl = data.find(b"\n")
        data = data[nl + 1:] if nl >= 0 else b""
    if not raw:
        data = data.replace(b"\r\n", b"\r").replace(b"\n", b"\r")
        if not data.endswith(b"\r"):
            data += b"\r"
    return data


def inflate_obx5(msg: bytes, size: int) -> bytes:
    """Replace OBX-5 of the first TX payload OBX with `size` bytes of 'A'."""
    segs = msg.split(CR)
    for i, s in enumerate(segs):
        f = s.split(b"|")
        if f and f[0] == b"OBX" and len(f) > 5 and f[2] == b"TX":
            f[5] = b"A" * size
            segs[i] = b"|".join(f)
            return CR.join(segs)
    # no TX OBX: append one
    segs.insert(len(segs) - 1, b"OBX|99|TX|18748-4^Diagnostic Imaging Report^LN|1|" + b"A" * size + b"|||N^Normal^HL70078|||F||||RID13173^Normal^RadLex")
    return CR.join(segs)


def frame_bytes(mode: str, msg: bytes, msg2: bytes | None):
    """Return list of (bytes, delay_after_s) writes, plus whether to half-close after."""
    halfclose = False
    if mode == "ok":
        w = [(VT + msg + FS + CR, 0)]
    elif mode == "no-start":
        w = [(msg + FS + CR, 0)]
    elif mode == "no-end":
        w = [(VT + msg, 0)]; halfclose = True
    elif mode == "no-cr":
        w = [(VT + msg + FS, 0)]; halfclose = True
    elif mode == "two-frames":
        w = [(VT + msg + FS + CR + VT + (msg2 or msg) + FS + CR, 0)]
    elif mode == "two-in-frame":
        w = [(VT + msg + (msg2 or msg) + FS + CR, 0)]
    elif mode == "split":
        fb = VT + msg + FS + CR
        import random
        random.seed(7)
        w, i = [], 0
        while i < len(fb):
            n = random.randint(1, 7)
            w.append((fb[i:i + n], 0.05)); i += n
    elif mode == "split-at-fs":
        w = [(VT + msg + FS, 2.0), (CR, 0)]
    elif mode == "trailing":
        w = [(VT + msg + FS + CR + b"GARBAGE" * 9 + b"X", 0)]
    elif mode == "empty-frame":
        w = [(VT + FS + CR, 0)]
    elif mode == "lf-terms":
        w = [(VT + msg.replace(CR, LF) + FS + CR, 0)]
    elif mode == "crlf-terms":
        w = [(VT + msg.replace(CR, CR + LF) + FS + CR, 0)]
    elif mode == "nul-bytes":
        w = [(VT + msg.replace(b"Normal study.", b"Nor\x00mal study.") + FS + CR, 0)]
    elif mode == "start-only":
        w = [(VT, 0)]; halfclose = True
    else:
        raise SystemExit(f"unknown frame mode {mode}")
    return w, halfclose


def read_frames(sock: socket.socket, timeout: float, want: int = 1) -> tuple[list[bytes], bytes, str]:
    """Read until `want` complete MLLP frames arrive, the peer closes, or timeout. Returns (frames, raw, status)."""
    sock.settimeout(timeout)
    buf, frames, status = b"", [], "TIMEOUT"
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            chunk = sock.recv(65536)
            if not chunk:
                status = "NO_ACK" if not frames else "RESPONDED"
                break
            buf += chunk
            while True:
                s = buf.find(VT); e = buf.find(FS + CR)
                if s < 0 or e < 0 or e < s:
                    break
                frames.append(buf[s + 1:e]); buf = buf[e + 2:]
            if len(frames) >= want:
                status = "RESPONDED"; break
    except socket.timeout:
        status = "RESPONDED" if frames else "TIMEOUT"
    except (ConnectionResetError, BrokenPipeError):
        status = "RESET"
    return frames, buf, status


def msa(frame: bytes) -> str:
    out = []
    for s in frame.split(CR):
        f = s.split(b"|")
        if f[0] == b"MSH" and len(f) > 9:
            out.append(f"ACK MSH-9={f[8].decode('latin-1')} MSH-10={f[9].decode('latin-1')}")
        if f[0] == b"MSA" and len(f) > 2:
            out.append(f"MSA-1={f[1].decode('latin-1')} MSA-2={f[2].decode('latin-1')}" + (f" MSA-3={f[3].decode('latin-1')}" if len(f) > 3 and f[3] else ""))
    return "; ".join(out) or "(no MSH/MSA parsed)"


def one_case(host, port, label, writes, halfclose, timeout, want=1, hold=0.0):
    t0 = time.monotonic()
    try:
        s = socket.create_connection((host, port), timeout=timeout)
    except OSError as e:
        return f"[{label}] REFUSED {e}"
    try:
        if hold:
            time.sleep(hold)
        for data, delay in writes:
            s.sendall(data)
            if delay:
                time.sleep(delay)
        if halfclose:
            try:
                s.shutdown(socket.SHUT_WR)
            except OSError:
                pass
        frames, rest, status = read_frames(s, timeout, want)
    except (ConnectionResetError, BrokenPipeError) as e:
        return f"[{label}] RESET during send: {e}"
    finally:
        s.close()
    dt = time.monotonic() - t0
    lines = [f"[{label}] {status} in {dt:.2f}s, {len(frames)} frame(s)"]
    for i, fr in enumerate(frames):
        lines.append(f"  frame {i+1}: {msa(fr)}")
        lines.append("  raw: " + esc(fr).replace("\n", "\n       "))
    if rest:
        lines.append(f"  unframed trailing bytes: {esc(rest, 120)}")
    return "\n".join(lines)


def ctrl_id(msg: bytes) -> str:
    f = msg.split(CR)[0].split(b"|")
    return f[9].decode("latin-1") if len(f) > 9 else "?"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default=os.environ.get("MLLP_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("MLLP_PORT", "2575")))
    ap.add_argument("--dir", default="samples/adversarial")
    ap.add_argument("--glob", default="oru_*.hl7")
    ap.add_argument("--file", action="append", help="specific file(s); overrides --dir/--glob")
    ap.add_argument("--frame", default="ok", help="framing mode or 'all'")
    ap.add_argument("--raw", action="store_true", help="send file bytes as-is (no LF->CR)")
    ap.add_argument("--big", type=int, default=0, help="inflate OBX-5 to N bytes")
    ap.add_argument("--concurrent", type=int, default=0, help="N simultaneous connections")
    ap.add_argument("--persist", type=int, default=0, help="N messages on one connection")
    ap.add_argument("--hold", type=float, default=0, help="connect, wait N s before first byte (or alone: hold and close)")
    ap.add_argument("--timeout", type=float, default=10.0)
    a = ap.parse_args()

    files = a.file or sorted(glob.glob(os.path.join(a.dir, a.glob)))
    if a.hold and not files:
        print(one_case(a.host, a.port, f"hold {a.hold}s no bytes", [], True, a.timeout, hold=a.hold)); return
    if not files:
        raise SystemExit("no input files")
    modes = MODES if a.frame == "all" else [a.frame]

    for path in files:
        msg = load(path, a.raw)
        if a.big:
            msg = inflate_obx5(msg, a.big)
        msg2 = msg.replace(ctrl_id(msg).encode(), (ctrl_id(msg) + "B").encode(), 1)
        name = os.path.basename(path) + (f" +big={a.big}" if a.big else "")

        if a.persist:
            s = socket.create_connection((a.host, a.port), timeout=a.timeout)
            print(f"[{name}] persistent connection, {a.persist} messages")
            for i in range(a.persist):
                m = msg.replace(ctrl_id(msg).encode(), f"{ctrl_id(msg)}P{i}".encode(), 1)
                try:
                    s.sendall(VT + m + FS + CR)
                    frames, _, status = read_frames(s, a.timeout)
                    print(f"  #{i} {status} " + (msa(frames[0]) if frames else ""))
                    if status != "RESPONDED":
                        break
                except OSError as e:
                    print(f"  #{i} RESET {e}"); break
            s.close(); continue

        if a.concurrent:
            results = [None] * a.concurrent
            def run(i):
                m = msg.replace(ctrl_id(msg).encode(), f"{ctrl_id(msg)}C{i}".encode(), 1)
                w, hc = frame_bytes("ok", m, None)
                results[i] = one_case(a.host, a.port, f"{name} conc#{i}", w, hc, a.timeout)
            ts = [threading.Thread(target=run, args=(i,)) for i in range(a.concurrent)]
            [t.start() for t in ts]; [t.join() for t in ts]
            print("\n".join(results))
            ok = sum(1 for r in results if "RESPONDED" in r.splitlines()[0])
            print(f"  summary: {ok}/{a.concurrent} responded"); continue

        for mode in modes:
            w, hc = frame_bytes(mode, msg, msg2)
            want = 2 if mode in ("two-frames", "two-in-frame") else 1
            print(one_case(a.host, a.port, f"{name} frame={mode}", w, hc, a.timeout, want=want, hold=a.hold))
            print()


if __name__ == "__main__":
    main()
