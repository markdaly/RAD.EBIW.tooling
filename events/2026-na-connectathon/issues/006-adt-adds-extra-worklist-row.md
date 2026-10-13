---
event: IHE North America Connectathon 2026
dates: 2026-10-12 to 2026-10-16
kind: issue
opened: 2026-10-13 09:20 ET
status: fixed
expires: 2026-10-16
---
# ITI-31 ADT for an EBIW_10 admission adds a third, modality-less worklist row

- **Source:** the monitor's pre-run check of the running Encounter Manager, Tue 09:15 ET. No
  vendor traffic involved.
- **Domain / profile / actor / transaction:** RAD EBIW / Encounter Manager / ITI-31 intake
  feeding RAD-130 (MWL) and UPS-RS

## Symptom
The 01:00 loopback test sent `samples/ADT_A04_ITI-31_EBIW10.hl7` (PEREZ, ADM001) to the ADT
port. The stored row has no `modality` or `scheduled_station_ae_title`, so its row key is
`ADM001||`, distinct from the configured `ADM001|US|` and `ADM001|XC|` rows. Rows without a
modality match any modality, so a PEREZ query returns three items where the EBIW_20/30
step 100 expectation is two (US and XC). The startup line showed "14 encounters (13 from
samples/encounters.json)".

## Scope
Any graded EBIW_20/30 run where an ITI-31 ADT arrives for an admission that the EBIW_10 set
already carries per device type. Affects both MWL and UPS-RS: `ups_rs.py` reads the same
`encounters()`.

## Evidence so far
- `tools/mwl_scp.py` `encounters()`: ADT rows were merged by row key, so an ADT only replaced a
  configured row when both lacked a modality.
- `logs/encounter-manager/encounters-from-adt.json`: one PEREZ row from the loopback test,
  control ID ADT00010.

## Hypotheses (ranked)
1. Merge-by-row-key is wrong for per-device rows: confirmed by reading the code.

## Next action
Done: an ADT row now overlays its patient and visit fields onto every configured row with
the same Admission ID. Modality, station AE title and procedure stay from the configured row.
It stands alone only when no configured row has that admission. The stale loopback file was
moved aside to `encounters-from-adt.json.loopback-20261013`.

## Resolution
Fixed in `tools/mwl_scp.py` `encounters()`. Takes effect on the next restart of em and ups
(`tools/floor.sh` or the panel). Loopback re-test in the commit message.
