# Tools: existing simulators first, stand-in actors second

## Rule
≤ 2 intermediates per profile run; each must be simple and monitor-readable. Check whether
an existing simulator covers the gap before building anything.

## Existing simulators / validators
| Need | Tool |
|---|---|
| ADT / PAM / PDQ / PIX source or consumer | Gazelle PatientManager |
| Order Placer / Order Filler / MWL (RAD, CARD, EYE) | Gazelle OrderManager |
| HL7 v2 / CDA / DICOM / FHIR / audit validation | Gazelle EVSClient |
| TLS client/server, certs, syslog collector | Gazelle Security Suite |
| Traffic capture between partners | Gazelle Proxy |
| XDS registry/repository, XCA gateways, XDS-I | NIST XDS Toolkit |
| MHD source/recipient, FHIR recording proxy | NIST FHIR Toolkit (Asbestos) |
| Full PACS behavior (if a heavy stand-in is unavoidable) | Orthanc, dcm4chee-arc (Docker) |
| CLI DICOM SCU/SCP | dcm4che `storescu`, `findscu`, `movescu`, `mppsscu`, `storescp`; DCMTK `storescp`, `findscu`, `wlmscpfs` |
| DICOM validation | dciodvfy (dicom3tools), Pixelmed validator, Gazelle EVS |

## Stand-in actor designs (build only on request)
Each is one Python file with env-var config and raw logging to `./logs/<actor>/<ts>/`.

1. **mllp_receiver.py** — **BUILT 2026-10-12** (`tools/mllp_receiver.py`): generic HL7 v2
   responder (Result Aggregator for EBIW RAD-132, Order Filler sink, ADT consumer). asyncio
   TCP, MLLP framing (0x0B … 0x1C 0x0D), logs every message and ACK raw to
   `logs/<ACTOR>/<session>/`, replies `ACK^<trigger>^ACK` / `MSA|AA|<MSH-10>`, `AR` if MSH
   won't parse. Env config; optional MLLPS with required client cert (`TLS_CERT/TLS_KEY/TLS_CA`).
   Run: `LISTEN_PORT=2575 python3 tools/mllp_receiver.py`. Ticket: `tickets/20261012-ebiw-result-aggregator.md`.
2. **mllp_send.py** — **BUILT 2026-10-12** (`tools/mllp_send.py`): send a message file to a
   host:port, print and save the ACK. Sample: `samples/ORU_R01_RAD-132_POCUS.hl7` (RAD-132
   POCUS Option ORU^R01; OBX-3 `113014^DICOM Study^DCM` for the Study UID is from memory of
   RAD-128, check before citing).
3. **mwl_scp.py** — **BUILT 2026-10-12** (`tools/mwl_scp.py`): pynetdicom MWL C-FIND SCP as
   EBIW Encounter Manager (RAD-130 MWL semantics + POCUS Option return keys). Encounters from
   `samples/encounters.json`; Study UID + Accession generated once per (Admission ID, calling
   AE) and kept in `logs/encounter-manager/state.json`; echoes Scheduled Station AE Title and
   Modality; SPS start = now; "Perform Imaging" generic procedure. Dumps every query and
   response. Run: `uv run --with pynetdicom --with pydicom python tools/mwl_scp.py`.
   Test SCU: `tools/mwl_find.py <host> <port> <AE> [PatientID] [AdmissionID]`.
   Codes in the sample are PLACEHOLDERS until `EBIW_10_Read_This_First` is pulled from Gazelle.
   Ticket: `tickets/20261012-ebiw-encounter-manager.md`.
4. **store_scp.py**: pynetdicom C-STORE SCP (+ optional Storage Commitment N-ACTION /
   N-EVENT-REPORT). Writes files + `dcmdump`-style header log. Minimal Image Manager receive side.
5. **qr_scp.py**: C-FIND/C-MOVE over a folder of files written by store_scp (Image Manager
   query/retrieve side). Keep separate from store_scp to stay single-purpose.
6. **stow_receiver.py**: FastAPI STOW-RS endpoint (RAD-108) for WIC / EBIW Lightweight
   Modality. Accepts multipart/related application/dicom, writes files, returns the DICOM
   JSON response.
7. **wado_rs.py**: FastAPI QIDO-RS/WADO-RS over a folder (WIA Imaging Document Responder).
8. **store_scu.py / mpps_scu.py**: modality-side SCU to drive a vendor's Image Manager
   (C-STORE a test set, MPPS N-CREATE/N-SET).
9. **tlscheck.sh**: wraps the openssl commands in TLS-CERTS.md for a host:port + root bundle.

## Libraries
- pydicom / pynetdicom: https://pydicom.github.io/pynetdicom/
- python-hl7 (parsing + MLLP client): https://python-hl7.readthedocs.io/
- FastAPI: https://fastapi.tiangolo.com/
- dcm4che tools: https://github.com/dcm4che/dcm4che
- DCMTK: https://dicom.offis.de/dcmtk
- Orthanc: https://orthanc.uclouvain.be/

## Test data
- IHE Connectathon artifacts: https://github.com/IHE/connectathon-artifacts
- XDS-I/WIA studies: C3L-00277, C3N-00953, TCGA-G4-6304, IHEBLUE-199 (from TCIA; see Gazelle
  DICOM_QR_Test_Data preparatory test).
- OrderManager codes: https://gazelle.ihe.net/common/order-manager/orderHierarchy4Radiology.xml
