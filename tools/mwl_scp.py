#!/usr/bin/env python3
"""
mwl_scp.py: DICOM Modality Worklist C-FIND SCP acting as an EBIW Encounter Manager
(RAD-130 Get Encounter Imaging Context, MWL semantics, POCUS Option return keys).
Stand-in for a vendor's modality that needs a RAD-130 responder. RAD TF-2: 4.130; RAD TF-1: 47.1.1.1.

What it does, and nothing else:
  - Serves the encounters in ENCOUNTERS (JSON) as worklist items. One row = one procedure for
    one device type: a patient with a US and an XC procedure under the same admission is two rows
    (Gazelle EBIW_10 data model). Each row may carry its own modality, scheduled station AE
    title and procedure code; rows without them match any modality / AE title and get the
    generic "Perform Imaging" procedure (allowed by 4.130.4.1.3).
  - Matches on the SCP-required keys of Table 4.130.4.1.2.1-1: Patient's Name, Patient ID (primary
    or Other Patient IDs Sequence, 4.130.4.1.3), Issuer of Patient ID, Institution Name,
    Institutional Department Name, Department Type Code, Admission ID, Accession Number (single
    value), SPS Start Date (range), Modality, Scheduled Station AE Title, Scheduled Performing
    Physician's Name. Empty key = match all; '*' and '?' wildcards.
  - Generates Accession Number + Study Instance UID once per (Admission ID, modality, station)
    and keeps returning the same pair (47.1.1.1: same accession for the same admission to the
    same device). Station = Scheduled Station AE Title from the query [IHE-6], else calling AE.
    That is the only state: a dict written through to state.json in the log folder, shared with
    tools/ups_rs.py so DIMSE and REST hand out the same numbers.
  - Echoes Scheduled Station AE Title and Modality from the query (4.130.4.1.3); SPS Start
    Date/Time = now. Issuer sequences carry Local Namespace Entity ID and, when an OID is
    configured, Universal Entity ID + Type ISO (R+ return keys).
  - Returns only the keys the SCU asked for (DICOM C-FIND rules), one response per matching row.
  - Dumps every C-FIND identifier and every response dataset to the log folder, raw.
  - Optional ITI-31 intake (ADT_PORT > 0): accepts HL7 v2 ADT^A01/A04/A05/A08 over MLLP from a
    Result Aggregator / ADT feed, ACKs AA, and adds the encounter (PID-3/4/5/7/8, PV1-3/7/19/44,
    DG1-4; mapping RAD TF-2x Appendix U, Table U-1). PV1-3 point of care is mapped to a
    department type code through "department_codes" in the encounters file. Written to
    logs/encounter-manager/encounters-from-adt.json so ups_rs.py and restarts see it too.
  Nothing is validated or graded; the monitor reads the dumps.

Encounters file (JSON): {"institution": {...}, "procedure": {...default...}, "issuer_oid": "",
  "department_codes": {"<PV1-3.1>": {"value","scheme","meaning"}, ...},
  "encounters": [ {patient_name, patient_id, issuer_of_patient_id, [issuer_of_patient_id_oid],
     [other_patient_ids: [{id, issuer}]], birth_date, sex, admission_id, issuer_of_admission_id,
     [issuer_of_admission_id_oid], admitting_date, admitting_time, department_name,
     department_type{value,scheme,meaning}, reason_for_visit, physician_of_record{name,id,scheme,meaning},
     [modality], [scheduled_station_ae_title], [procedure{description, code{...}}]} ] }

Config (env):
  AE_TITLE          default ENC_MGR            LISTEN_PORT  default 11112
  ENCOUNTERS        default samples/encounters.json
  ACCESSION_ISSUER  Issuer of Accession Number, Local Namespace Entity ID; default ENC_MGR
  ACCESSION_ISSUER_OID  Universal Entity ID for the issuer sequences; default "issuer_oid" from the file, else none
  ACCESSION_PREFIX  prefix to avoid collisions with other issuers; default EM
  UID_ROOT          Study UID root; default 1.2.826.0.1.3680043.10.1431.
  LOG_DIR           default ./logs   (folder logs/encounter-manager/<session>/)
  ADT_PORT          MLLP port for ITI-31 intake; default 2576; 0 disables

Run:  uv run --with pynetdicom --with pydicom python tools/mwl_scp.py
Test: uv run --with pynetdicom --with pydicom python tools/mwl_find.py 127.0.0.1 11112 ENC_MGR
"""
import fcntl, json, os, re, socketserver, sys, threading
from datetime import datetime
from pathlib import Path

from pydicom import Dataset
from pydicom.sequence import Sequence
from pydicom.uid import generate_uid
from pynetdicom import AE, evt
from pynetdicom.sop_class import ModalityWorklistInformationFind, Verification

AE_TITLE = os.environ.get("AE_TITLE", "ENC_MGR")
PORT = int(os.environ.get("LISTEN_PORT", "11112"))
ENCOUNTERS = Path(os.environ.get("ENCOUNTERS", "samples/encounters.json"))
ISSUER = os.environ.get("ACCESSION_ISSUER", "ENC_MGR")
PREFIX = os.environ.get("ACCESSION_PREFIX", "EM")
UID_ROOT = os.environ.get("UID_ROOT", "1.2.826.0.1.3680043.10.1431.")
SESSION_DIR = Path(os.environ.get("LOG_DIR", "logs")) / "encounter-manager" / datetime.now().strftime("%Y%m%d-%H%M%S")
SESSION_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = Path(os.environ.get("LOG_DIR", "logs")) / "encounter-manager" / "state.json"
ADT_PORT = int(os.environ.get("ADT_PORT", "2576"))
ADT_FILE = Path(os.environ.get("LOG_DIR", "logs")) / "encounter-manager" / "encounters-from-adt.json"
CONF = json.loads(ENCOUNTERS.read_text())
ISSUER_OID = os.environ.get("ACCESSION_ISSUER_OID", CONF.get("issuer_oid", ""))
state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}  # "admission|modality|station" -> {accession, study_uid}
counter = 0
PLACEHOLDER = re.compile(r"^\[.*\]$")  # "[MODALITY_AET]" style values in a transcribed file mean "not configured"


def log(line):
    stamped = f"{datetime.now().strftime('%H:%M:%S')} {line}"
    print(stamped, flush=True)
    with (SESSION_DIR / "summary.log").open("a") as f:
        f.write(stamped + "\n")


def cfg(enc, key, default=""):
    v = enc.get(key, default)
    return default if isinstance(v, str) and PLACEHOLDER.match(v) else v


def row_key(e):
    return f"{e.get('admission_id','')}|{cfg(e, 'modality')}|{cfg(e, 'scheduled_station_ae_title')}"


def encounters():
    """Sample-file rows plus those received over ITI-31 (re-read each call: ups_rs.py is a
    separate process and writes the same file). An ADT for an admission the file already has
    overlays its patient/visit fields onto every row of that admission (one per device type),
    keeping the row's modality, station AE title and procedure; otherwise it is a row of its own."""
    rows = [dict(e) for e in CONF["encounters"]]
    adts = json.loads(ADT_FILE.read_text()) if ADT_FILE.exists() else []
    for adt in adts:
        same = [r for r in rows if r.get("admission_id") == adt["admission_id"]]
        for r in same:
            r.update({k: v for k, v in adt.items() if k not in ("modality", "scheduled_station_ae_title", "procedure")})
        if not same:
            rows.append(adt)
    return rows


def context_for(admission_id, modality, station, create=True):
    """One accession + Study UID per (admission, device), forever (RAD TF-1 47.1.1.1).
    create=False returns a placeholder for rows that have none yet, so matching can run before
    anything is allocated; only matched rows get a real pair."""
    key = f"{admission_id}|{modality}|{station}"
    # ups_rs.py is a second process on the same file: lock across read-allocate-write so both
    # hand out the same pair and never the same accession for two keys (issue 008).
    with open(STATE_FILE.with_name(STATE_FILE.name + ".lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if STATE_FILE.exists():
            state.update(json.loads(STATE_FILE.read_text()))
        if key not in state and not create:
            return {"accession": "", "study_uid": ""}
        if key not in state:
            n = len(state) + 1
            state[key] = {"accession": f"{PREFIX}{datetime.now().strftime('%y%m%d')}{n:04d}",
                          "study_uid": generate_uid(prefix=UID_ROOT)}
            write_atomic(STATE_FILE, json.dumps(state, indent=1))
            log(f"NEW CONTEXT admission={admission_id} modality={modality} station={station} -> {state[key]}")
        return state[key]


def write_atomic(path, text):
    """Readers in the other process see the old file or the new one, never a partial one."""
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def code_item(c):
    ds = Dataset()
    ds.CodeValue, ds.CodingSchemeDesignator, ds.CodeMeaning = c["value"], c["scheme"], c["meaning"]
    return ds


def issuer_item(local, oid=""):
    ds = Dataset()
    ds.LocalNamespaceEntityID = local
    if oid:
        ds.UniversalEntityID, ds.UniversalEntityIDType = oid, "ISO"
    return ds


def worklist_item(enc, calling_ae, query, create=True):
    """Full return-key set for one row (Tables 4.130.4.1.2.1-1 and 4.130.4.1.2.1.1-1)."""
    inst = CONF["institution"]
    proc = cfg(enc, "procedure", None) or CONF["procedure"]
    sps_q = query.ScheduledProcedureStepSequence[0] if "ScheduledProcedureStepSequence" in query and query.ScheduledProcedureStepSequence else Dataset()
    q_station = str(sps_q.get("ScheduledStationAETitle", "") or "")
    q_modality = str(sps_q.get("Modality", "") or "")
    station = cfg(enc, "scheduled_station_ae_title") or q_station or calling_ae   # echoed when the row has none
    modality = cfg(enc, "modality") or q_modality or "US"
    ctx = context_for(enc["admission_id"], modality, q_station or calling_ae, create)
    now = datetime.now()
    ds = Dataset()
    ds.SpecificCharacterSet = "ISO_IR 100"
    # Patient
    ds.PatientName, ds.PatientID, ds.IssuerOfPatientID = enc["patient_name"], enc["patient_id"], cfg(enc, "issuer_of_patient_id")
    others = []
    for o in enc.get("other_patient_ids", []):
        it = Dataset(); it.PatientID = o.get("id", ""); it.IssuerOfPatientID = o.get("issuer", ""); others.append(it)
    ds.OtherPatientIDsSequence = Sequence(others)
    ds.PatientBirthDate, ds.PatientSex = enc.get("birth_date", ""), enc.get("sex", "")
    # Visit
    ds.InstitutionName, ds.InstitutionAddress = inst["name"], inst["address"]
    ds.InstitutionCodeSequence = Sequence([code_item(inst["code"])])
    ds.InstitutionalDepartmentName = enc.get("department_name", "")
    ds.InstitutionalDepartmentTypeCodeSequence = Sequence([code_item(enc["department_type"])] if enc.get("department_type") else [])
    ds.AdmissionID = enc["admission_id"]
    ds.IssuerOfAdmissionIDSequence = Sequence([issuer_item(cfg(enc, "issuer_of_admission_id"), cfg(enc, "issuer_of_admission_id_oid") or ISSUER_OID)])
    ds.AdmittingDate, ds.AdmittingTime = enc.get("admitting_date", ""), enc.get("admitting_time", "")
    ds.ReasonForVisit = enc.get("reason_for_visit", "")
    por = enc.get("physician_of_record") or {}
    phys = Dataset(); phys.PersonName = por.get("name", "")
    phys.PersonIdentificationCodeSequence = Sequence([code_item({"value": por.get("id", ""), "scheme": por.get("scheme", ""), "meaning": por.get("meaning", "")})] if por else [])
    ds.PhysiciansOfRecordIdentificationSequence = Sequence([phys])
    ds.PhysiciansOfRecord = por.get("name", "")
    # Imaging Service Request / Requested Procedure (generated)
    ds.AccessionNumber = ctx["accession"]
    ds.IssuerOfAccessionNumberSequence = Sequence([issuer_item(ISSUER, ISSUER_OID)])
    ds.StudyInstanceUID = ctx["study_uid"]
    ds.RequestedProcedureDescription = proc["description"]
    ds.RequestedProcedureCodeSequence = Sequence([code_item(proc["code"])])
    ds.RequestedProcedureID = ctx["accession"]
    # Scheduled Procedure Step: "scheduled" details even though nothing was (4.130.4.1.3)
    sps = Dataset()
    sps.ScheduledStationAETitle = station
    sps.Modality = modality
    sps.ScheduledProcedureStepStartDate = now.strftime("%Y%m%d")
    sps.ScheduledProcedureStepStartTime = now.strftime("%H%M%S")
    sps.ScheduledProcedureStepDescription = proc["description"]
    sps.ScheduledProcedureStepID = ctx["accession"]
    sps.ScheduledPerformingPhysicianName = por.get("name", "")
    ds.ScheduledProcedureStepSequence = Sequence([sps])
    return ds


# ---- matching ---------------------------------------------------------------------------------
def match_str(key, value):
    """DICOM wildcard / single-value match. Empty key matches anything."""
    key = str(key or "")
    if key == "":
        return True
    pat = re.escape(key).replace(r"\*", ".*").replace(r"\?", ".")
    return re.fullmatch(pat, str(value or ""), re.IGNORECASE) is not None


def match_date(key, value):
    key = str(key or "")
    if key == "":
        return True
    if "-" in key:
        lo, hi = key.split("-", 1)
        return (not lo or lo <= value) and (not hi or value <= hi)
    return key == value


def matches(query, item, enc):
    ids = [(item.PatientID, item.IssuerOfPatientID)] + [(o.PatientID, o.IssuerOfPatientID) for o in item.OtherPatientIDsSequence]
    q_pid, q_iss = query.get("PatientID", ""), query.get("IssuerOfPatientID", "")
    checks = [
        match_str(query.get("PatientName", ""), item.PatientName),
        any(match_str(q_pid, pid) and match_str(q_iss, iss) for pid, iss in ids),   # 4.130.4.1.3: primary or Other Patient IDs
        match_str(query.get("InstitutionName", ""), item.InstitutionName),
        match_str(query.get("InstitutionalDepartmentName", ""), item.InstitutionalDepartmentName),
        match_str(query.get("AdmissionID", ""), item.AdmissionID),
        str(query.get("AccessionNumber", "") or "") in ("", item.AccessionNumber) and not (query.get("AccessionNumber", "") and not item.AccessionNumber),  # IHE-4: single value; unallocated rows never match an accession
    ]
    q_dept = query.get("InstitutionalDepartmentTypeCodeSequence")
    if q_dept and len(q_dept) and q_dept[0].get("CodeValue", ""):
        checks.append(bool(item.InstitutionalDepartmentTypeCodeSequence) and q_dept[0].CodeValue == item.InstitutionalDepartmentTypeCodeSequence[0].CodeValue)
    q_sps = query.get("ScheduledProcedureStepSequence")
    if q_sps and len(q_sps):
        q, s = q_sps[0], item.ScheduledProcedureStepSequence[0]
        checks += [
            match_date(q.get("ScheduledProcedureStepStartDate", ""), s.ScheduledProcedureStepStartDate),
            match_str(q.get("ScheduledPerformingPhysicianName", ""), s.ScheduledPerformingPhysicianName),
            # Modality and Scheduled Station AE Title are SCP matching keys (Table 4.130.4.1.2.1-1).
            # A row that names a modality / AE title only matches that one; a row without is for any
            # device and simply echoes the query's value (4.130.4.1.3).
            match_str(q.get("Modality", ""), s.Modality) if cfg(enc, "modality") else True,
            match_str(q.get("ScheduledStationAETitle", ""), s.ScheduledStationAETitle) if cfg(enc, "scheduled_station_ae_title") else True,
        ]
    return all(checks)


def project(item, query):
    """Return only the attributes the SCU asked for (C-FIND), filled from the worklist item."""
    out = Dataset()
    for elem in query:
        if elem.tag.group == 0x0008 and elem.tag.element == 0x0005:
            out.SpecificCharacterSet = item.SpecificCharacterSet
            continue
        if elem.VR == "SQ":
            src = item.get(elem.keyword)
            if src is None or not len(src):
                out.add_new(elem.tag, "SQ", Sequence([]))
            else:
                sub_q = elem.value[0] if len(elem.value) else Dataset()
                out.add_new(elem.tag, "SQ", Sequence([project(s, sub_q) if len(sub_q) else s for s in src]))
        else:
            out.add_new(elem.tag, elem.VR, item.get(elem.keyword, ""))
    return out


# ---- handlers ---------------------------------------------------------------------------------
def handle_find(event):
    global counter
    counter += 1
    calling_ae = event.assoc.requestor.ae_title.strip()
    peer = f"{event.assoc.requestor.address}:{event.assoc.requestor.port}"
    query = event.identifier
    stem = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{counter:04d}-{calling_ae}"
    (SESSION_DIR / f"{stem}.query.txt").write_text(str(query))
    sps_q = query.ScheduledProcedureStepSequence[0] if "ScheduledProcedureStepSequence" in query and len(query.ScheduledProcedureStepSequence) else Dataset()
    log(f"C-FIND #{counter} from {calling_ae}@{peer} keys: " + ", ".join(
        f"{e.keyword}={e.value!r}" for e in list(query) + list(sps_q) if e.VR != "SQ" and e.value != ""))
    n = 0
    for enc in encounters():
        if event.is_cancelled:
            yield 0xFE00, None
            return
        item = worklist_item(enc, calling_ae, query, create=False)
        if matches(query, item, enc):
            n += 1
            item = worklist_item(enc, calling_ae, query)   # allocate (or reuse) the accession + Study UID now
            resp = project(item, query)
            (SESSION_DIR / f"{stem}.resp{n}.txt").write_text(str(resp))
            log(f"  -> match {n}: {item.PatientName} {item.PatientID} adm={item.AdmissionID} "
                f"mod={item.ScheduledProcedureStepSequence[0].Modality} acc={item.AccessionNumber} study={item.StudyInstanceUID}")
            yield 0xFF00, resp
    log(f"  C-FIND #{counter} done, {n} match(es)")
    yield 0x0000, None


# ---- ITI-31 intake: ADT -> encounter (RAD TF-2x Appendix U, Table U-1) -----------------------
VT, FS, CR = b"\x0b", b"\x1c", b"\x0d"


def adt_to_encounter(msg: str):
    seg = {}
    for line in msg.replace("\n", "\r").split("\r"):
        if len(line) > 3 and line[3] == "|" and line[:3] not in seg:
            seg[line[:3]] = line.split("|")
    f = lambda name, n: (seg.get(name, []) + [""] * 50)[n]
    comp = lambda v, i: (v.split("^") + [""] * 10)[i]
    if "PID" not in seg or "PV1" not in seg:
        return None
    pid3s = [p for p in f("PID", 3).split("~") if p]
    pid3 = pid3s[0] if pid3s else ""
    pv1_3, pv1_7, pv1_19 = f("PV1", 3), f("PV1", 7), f("PV1", 19)
    npi = comp(pv1_7, 0)
    phys_name = f"{comp(pv1_7, 1)}^{comp(pv1_7, 2)}".strip("^")
    poc, dept = comp(pv1_3, 0), comp(pv1_3, 8) or comp(pv1_3, 0)
    dept_code = CONF.get("department_codes", {}).get(poc) or {"value": poc, "scheme": "99IHE", "meaning": dept}
    return {
        "patient_name": "^".join(f("PID", 5).split("^")[:2]),
        "patient_id": comp(pid3, 0),
        "issuer_of_patient_id": comp(pid3, 3).split("&")[0],
        "other_patient_ids": [{"id": comp(p, 0), "issuer": comp(p, 3).split("&")[0]} for p in pid3s[1:]],
        "birth_date": f("PID", 7)[:8],
        "sex": f("PID", 8),
        "admission_id": comp(pv1_19, 0),
        "issuer_of_admission_id": comp(pv1_19, 3).split("&")[0],
        "admitting_date": f("PV1", 44)[:8],
        "admitting_time": f("PV1", 44)[8:14],
        "department_name": dept,
        "department_type": dept_code,
        "reason_for_visit": f("DG1", 4) or comp(f("DG1", 3), 1),
        "physician_of_record": {"name": phys_name, "id": npi, "scheme": "NPI" if npi else "99IHE", "meaning": phys_name},
        "_source": f"ITI-31 {f('MSH', 8)} ctrl {f('MSH', 9)} at {datetime.now().isoformat(timespec='seconds')}",
    }


class ADTHandler(socketserver.StreamRequestHandler):
    def handle(self):
        peer = "%s:%s" % self.client_address
        buf = b""
        while True:
            chunk = self.request.recv(65536)
            if not chunk:
                break
            buf += chunk
            while VT in buf and FS + CR in buf:
                start, end = buf.find(VT), buf.find(FS + CR)
                raw, buf = buf[start + 1:end], buf[end + 2:]
                stem = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-adt-{peer.replace(':', '_')}"
                (SESSION_DIR / f"{stem}.in.hl7").write_bytes(raw)
                text = raw.decode("latin-1")
                msh = (text.split("\r", 1)[0].split("|") + [""] * 12)
                enc = adt_to_encounter(text)
                if enc and enc["admission_id"]:
                    existing = json.loads(ADT_FILE.read_text()) if ADT_FILE.exists() else []
                    existing = [e for e in existing if row_key(e) != row_key(enc)] + [enc]
                    write_atomic(ADT_FILE, json.dumps(existing, indent=1))
                    code = "AA"
                    log(f"ITI-31 {msh[8]} from {peer}: added/updated encounter {enc['admission_id']} "
                        f"{enc['patient_name']} {enc['patient_id']} ({len(encounters())} encounters now) file={stem}.in.hl7")
                else:
                    code = "AR"
                    log(f"ITI-31 from {peer}: no PID/PV1-19, rejected (AR) file={stem}.in.hl7")
                trig = msh[8].split("^")[1] if "^" in msh[8] else ""
                ack = (f"MSH|^~\\&|SIMULATOR|SIMULATOR|{msh[2]}|{msh[3]}|{datetime.now().strftime('%Y%m%d%H%M%S')}||"
                       f"ACK^{trig}^ACK|ACK{datetime.now().strftime('%H%M%S%f')}|{msh[10] or 'P'}|{msh[11] or '2.5'}\r"
                       f"MSA|{code}|{msh[9]}\r")
                if code == "AR":
                    ack += "ERR|||207^Application internal error^HL70357|E|||||No PID segment or empty PV1-19\r"
                ack = ack.encode("latin-1")
                (SESSION_DIR / f"{stem}.ack.hl7").write_bytes(ack)
                self.request.sendall(VT + ack + FS + CR)


def start_adt_listener():
    if ADT_PORT <= 0:
        return
    srv = socketserver.ThreadingTCPServer(("0.0.0.0", ADT_PORT), ADTHandler)
    srv.allow_reuse_address = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    log(f"ITI-31 ADT intake listening on MLLP port {ADT_PORT}")


def handle_open(event):
    log(f"ASSOC open from {event.assoc.requestor.ae_title.strip()}@{event.assoc.requestor.address}")


def handle_close(event):
    log(f"ASSOC close {event.assoc.requestor.ae_title.strip()}@{event.assoc.requestor.address}")


if __name__ == "__main__":
    ae = AE(ae_title=AE_TITLE)
    ae.add_supported_context(ModalityWorklistInformationFind)
    ae.add_supported_context(Verification)
    start_adt_listener()
    log(f"Encounter Manager {AE_TITLE} on port {PORT}; {len(encounters())} encounters ({len(CONF['encounters'])} from {ENCOUNTERS}); "
        f"issuer={ISSUER}{' oid=' + ISSUER_OID if ISSUER_OID else ''} prefix={PREFIX}; logs in {SESSION_DIR}; {len(state)} remembered contexts")
    ae.start_server(("0.0.0.0", PORT), block=True, evt_handlers=[
        (evt.EVT_C_FIND, handle_find), (evt.EVT_CONN_OPEN, handle_open), (evt.EVT_CONN_CLOSE, handle_close)])
