# samples/adversarial

Hostile inputs for the stand-ins. Synthetic data only; no vendor, product or personal names.
First line of each file is a `#` header saying what it exercises; `tools/adversarial/adversarial_mllp.py`
strips it. Files are stored with LF line endings for diff-ability; the driver sends CR.

Each message is one case. Framing attacks (missing 0x0B/0x1C/0x0D, two messages per frame, split
writes, 10 MiB OBX-5, concurrent connections, persistent connections) are driver modes, not files:

    tools/adversarial/adversarial_mllp.py --port 2575                 # every oru_*.hl7, normal framing
    tools/adversarial/adversarial_mllp.py --port 2576 --glob 'adt_*'  # ITI-31 intake
    tools/adversarial/adversarial_mllp.py --file samples/adversarial/oru_baseline.hl7 --frame all
    tools/adversarial/adversarial_mllp.py --file samples/adversarial/oru_baseline.hl7 --big 10485760
    tools/adversarial/adversarial_mllp.py --file samples/adversarial/oru_baseline.hl7 --concurrent 8

The drivers report RESPONDED / NO_ACK / TIMEOUT / RESET / REFUSED and print the raw ACK. They do not
grade. The one result that is always a finding is silence.

**Run these against an isolated instance** (scratch `LOG_DIR`, spare ports), never against the
servers vendors are using: the ADT cases add encounters and the ORU cases fill the session logs.
Spec references for why each message exists: `events/2026-na-connectathon/research/adversarial-review-2026-10-13.md` §4.
Results of the 2026-10-13 run are in the event diary (`events/2026-na-connectathon/docs/LOG.md`).
