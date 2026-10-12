#!/usr/bin/env python3
"""
ups_rs.py: UPS-RS Search endpoint acting as an EBIW Encounter Manager for Lightweight
Modalities (RAD-130 Get Encounter Imaging Context, UPS-RS semantics). RAD TF-2: 4.130.4.1.2.2,
mapping Table 4.130.4.1.2.2-1; DICOM PS3.18 Worklist Service (UPS-RS) Search Transaction.

Shares encounters, Study UID / accession generation and the state file with tools/mwl_scp.py,
so a device gets the same accession whether it asks over DIMSE or REST (key = Admission ID +
station name / AE title). Run both, or just this one.

  GET {BASE_PATH}/workitems?<attribute>=<value>&...  -> 200 application/dicom+json [ {...}, ... ]
  (also served at every path in ROUTES, default "/workitems,/studies": some clients are
   configured with a DICOMweb-style root and append /studies; same UPS body either way)
                                                      -> 204 when nothing matches
  Query keys: any DICOM keyword or 8-hex tag, dotted for sequences
  (e.g. PatientID=MRN1, AdmissionID=V1, ReferencedRequestSequence.AccessionNumber=EM...,
   ScheduledStationNameCodeSequence.CodeValue=MYAE, ScheduledStationClassCodeSequence.CodeValue=US,
   ScheduledProcedureStepStartDateTime=20261012-20261013). '*' '?' wildcards, '-' ranges.
  includefield / fuzzymatching / offset / limit are accepted; the full workitem is always returned.
  Every request (URL + headers) and response body is written to logs/encounter-manager/<session>/.

Config (env): LISTEN_PORT default 8042, BASE_PATH default "", ROUTES default "/workitems,/studies", plus everything
mwl_scp.py reads (ENCOUNTERS, ACCESSION_ISSUER, ACCESSION_PREFIX, UID_ROOT, LOG_DIR).
TLS_CERT + TLS_KEY turn on HTTPS.

Run:  uv run --with pynetdicom --with pydicom --with fastapi --with uvicorn python tools/ups_rs.py
Test: curl -s 'http://127.0.0.1:8042/workitems?PatientID=MRN12345&ScheduledStationNameCodeSequence.CodeValue=LWM1' | python3 -m json.tool
"""
import json, os, re, sys
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response
from pydicom import Dataset
from pydicom.datadict import keyword_for_tag, tag_for_keyword
from pydicom.sequence import Sequence
from pydicom.uid import generate_uid

sys.path.insert(0, str(Path(__file__).parent))
import mwl_scp as em  # encounters, context_for(), worklist_item(), log(), SESSION_DIR

PORT = int(os.environ.get("LISTEN_PORT", "8042"))
BASE = os.environ.get("BASE_PATH", "").rstrip("/")
ROUTES = [r.strip() for r in os.environ.get("ROUTES", "/workitems,/studies").split(",") if r.strip()]
CID29 = {"US": "Ultrasound", "XC": "External-camera Photography", "OT": "Other", "SC": "Secondary Capture"}  # PS3.16 CID 29 subset
app = FastAPI(title="EBIW Encounter Manager (UPS-RS)")
counter = 0


def code(value, scheme, meaning):
    ds = Dataset(); ds.CodeValue, ds.CodingSchemeDesignator, ds.CodeMeaning = value, scheme, meaning
    return ds


def workitem(enc, station, modality):
    """MWL worklist item re-shaped as a UPS instance per Table 4.130.4.1.2.2-1."""
    q = Dataset()  # minimal 'query' so worklist_item() echoes station/modality
    sps = Dataset(); sps.ScheduledStationAETitle = station; sps.Modality = modality
    q.ScheduledProcedureStepSequence = Sequence([sps])
    m = em.worklist_item(enc, station, q)           # generates/reuses accession + Study UID
    s = m.ScheduledProcedureStepSequence[0]
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    u = Dataset()
    u.SpecificCharacterSet = "ISO_IR 100"
    # UPS identity / state (PS3.4 CC.2.5-3 required return keys)
    u.SOPClassUID = "1.2.840.10008.5.1.4.34.6.1"   # Unified Procedure Step - Push SOP Class
    u.SOPInstanceUID = generate_uid(prefix=em.UID_ROOT, entropy_srcs=[m.StudyInstanceUID, station])
    u.ProcedureStepState = "SCHEDULED"
    u.InputReadinessState = "READY"
    u.ScheduledProcedureStepPriority = "MEDIUM"
    u.ScheduledProcedureStepModificationDateTime = now
    u.WorklistLabel = "EBIW"
    # "Same" attributes: copied at top level
    for kw in ["PatientName", "PatientID", "IssuerOfPatientID", "OtherPatientIDsSequence", "PatientBirthDate",
               "PatientSex", "InstitutionName", "InstitutionCodeSequence", "InstitutionAddress",
               "InstitutionalDepartmentName", "InstitutionalDepartmentTypeCodeSequence", "AdmissionID",
               "IssuerOfAdmissionIDSequence", "AdmittingDate", "AdmittingTime", "ReasonForVisit",
               "PhysiciansOfRecord", "PhysiciansOfRecordIdentificationSequence", "StudyInstanceUID"]:
        setattr(u, kw, m.get(kw))
    # Imaging Service Request / Requested Procedure: inside Referenced Request Sequence (0040,A370)
    rr = Dataset()
    rr.StudyInstanceUID = m.StudyInstanceUID
    rr.AccessionNumber = m.AccessionNumber
    rr.IssuerOfAccessionNumberSequence = m.IssuerOfAccessionNumberSequence
    rr.RequestedProcedureID = m.RequestedProcedureID
    rr.RequestedProcedureDescription = m.RequestedProcedureDescription
    rr.RequestedProcedureCodeSequence = m.RequestedProcedureCodeSequence
    u.ReferencedRequestSequence = Sequence([rr])
    # Scheduled Procedure Step mappings
    u.ScheduledStationNameCodeSequence = Sequence([code(station, "99IHE", station)])          # AE title as code meaning
    u.ScheduledStationClassCodeSequence = Sequence([code(modality, "DCM", CID29.get(modality, modality))])
    u.ScheduledProcedureStepStartDateTime = s.ScheduledProcedureStepStartDate + s.ScheduledProcedureStepStartTime
    u.ProcedureStepLabel = s.ScheduledProcedureStepDescription
    u.ScheduledWorkitemCodeSequence = m.RequestedProcedureCodeSequence
    hp = Dataset(); hp.HumanPerformerName = s.ScheduledPerformingPhysicianName
    hp.HumanPerformerCodeSequence = m.PhysiciansOfRecordIdentificationSequence[0].PersonIdentificationCodeSequence
    u.ScheduledHumanPerformersSequence = Sequence([hp])
    return u


# ---- matching: dotted keyword/tag paths against the workitem -------------------------------
def values_at(ds, path):
    """All values found at a dotted path, e.g. 'ReferencedRequestSequence.AccessionNumber'."""
    head, _, rest = path.partition(".")
    if re.fullmatch(r"[0-9A-Fa-f]{8}", head):
        head = keyword_for_tag(int(head, 16)) or head
    if head not in ds:
        return []
    el = ds[head]
    if el.VR == "SQ":
        return [v for item in el.value for v in values_at(item, rest)] if rest else []
    return [str(el.value)]


def match(key, value):
    if key == "":
        return True
    if "-" in key and re.fullmatch(r"[0-9.\-]*", key):      # date/time range
        lo, hi = key.split("-", 1)
        return (not lo or lo <= value[:len(lo)]) and (not hi or value[:len(hi)] <= hi)
    pat = re.escape(key).replace(r"\*", ".*").replace(r"\?", ".")
    return re.fullmatch(pat, value, re.IGNORECASE) is not None


def matches(u, params):
    for k, v in params.items():
        if k in ("includefield", "fuzzymatching", "offset", "limit") or v == "":
            continue
        vals = values_at(u, k)
        if not vals or not any(match(v, x) for x in vals):
            return False
    return True


def search(request: Request):
    global counter
    counter += 1
    params = dict(request.query_params)
    peer = request.client.host if request.client else "?"
    station = (params.get("ScheduledStationNameCodeSequence.CodeValue")
               or params.get("ScheduledStationNameCodeSequence.CodeMeaning") or peer)
    modality = params.get("ScheduledStationClassCodeSequence.CodeValue", "US")
    stem = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-ups{counter:04d}-{station}"
    (em.SESSION_DIR / f"{stem}.request.txt").write_text(
        f"{request.method} {request.url}\n" + "".join(f"{k}: {v}\n" for k, v in request.headers.items()))
    em.log(f"UPS-RS search #{counter} from {peer} station={station} modality={modality} params={params}")
    hits = [workitem(enc, station, modality) for enc in em.encounters()]
    hits = [u for u in hits if matches(u, params)]
    off, lim = int(params.get("offset", 0)), int(params.get("limit", 0) or 0)
    hits = hits[off: off + lim] if lim else hits[off:]
    for u in hits:
        em.log(f"  -> {u.PatientName} {u.PatientID} adm={u.AdmissionID} "
               f"acc={u.ReferencedRequestSequence[0].AccessionNumber} study={u.StudyInstanceUID}")
    em.log(f"  UPS-RS search #{counter} done, {len(hits)} match(es)")
    if not hits:
        (em.SESSION_DIR / f"{stem}.response.txt").write_text("204 No Content\n")
        return Response(status_code=204)
    body = json.dumps([u.to_json_dict() for u in hits])
    (em.SESSION_DIR / f"{stem}.response.json").write_text(body)
    return Response(content=body, media_type="application/dicom+json")


for _route in ROUTES:
    app.add_api_route(BASE + _route, search, methods=["GET"])

if __name__ == "__main__":
    em.log(f"Encounter Manager UPS-RS on port {PORT}, paths {', '.join(BASE + r for r in ROUTES)}; "
           f"{len(em.encounters())} encounters; issuer={em.ISSUER} prefix={em.PREFIX}")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning",
                ssl_certfile=os.environ.get("TLS_CERT"), ssl_keyfile=os.environ.get("TLS_KEY"))
