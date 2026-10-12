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

1. **mllp_receiver.py**: generic HL7 v2 responder (Result Aggregator for EBIW RAD-132,
   Order Filler sink, ADT consumer). asyncio TCP, MLLP framing (0x0B … 0x1C 0x0D), log raw
   message, reply AA ACK echoing MSH-10 and swapping sender/receiver. Optional TLS (MLLPS).
2. **mllp_sender.py**: send a message file to a host:port, print ACK. Replays canned v2.5.1
   OMI^O23 / ADT^A04 / ORU^R01 from `samples/`.
3. **mwl_scp.py**: pynetdicom MWL C-FIND SCP from a JSON/YAML worklist file. EBIW Encounter
   Manager mode: generate Study UID + Accession, reuse per (Admission ID, calling AE), with a
   configurable Issuer of Accession.
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
