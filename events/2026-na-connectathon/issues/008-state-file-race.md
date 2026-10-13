---
event: IHE North America Connectathon 2026
dates: 2026-10-12 to 2026-10-16
kind: issue
opened: 2026-10-13 10:45 ET
status: fixed
expires: 2026-10-16
---
# Encounter Manager state file: two processes, no lock, non-atomic writes

- **Source:** the adversarial review of 2026-10-13 (section 2, "state-json-atomic-write"),
  confirmed by reading the code. No floor failure observed.
- **Domain / profile / actor / transaction:** RAD EBIW / Encounter Manager / RAD-130 (MWL and
  UPS-RS), ITI-31 intake

## Symptom
None seen yet. Failure modes, by construction:
1. `mwl_scp.py` and `ups_rs.py` are separate processes sharing `context_for()` and
   `logs/encounter-manager/state.json`. Each re-reads the file, computes `n = len(state) + 1`
   and writes. Two allocations at the same moment (an MWL and a UPS-RS query for different
   devices) can produce **the same accession number for two different contexts**, or one
   process overwriting the other's new context. The second breaks RAD TF-1 47.1.1.1 (same
   admission and device must get the same accession every time).
2. `write_text` truncates then writes. A reader in the other process can see an empty or
   partial file, `json.loads` raises, and that query fails.
3. Same for `encounters-from-adt.json` (written by the ADT thread, read by both processes).

## Scope
Only when MWL and UPS-RS (or ITI-31) traffic overlaps within milliseconds. Unlikely with one or
two vendors, but the result would be a wrong accession in a graded run.

## Next action
Done: `context_for()` holds an exclusive `fcntl.flock` on `state.json.lock` across
read-allocate-write; state and ADT files are written to a temp file and `os.replace`d. Still
JSON files, no database.

## Resolution
Fixed in `tools/mwl_scp.py`. Concurrency test in the commit message.
