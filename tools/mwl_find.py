#!/usr/bin/env python3
"""
mwl_find.py: minimal RAD-130 MWL C-FIND SCU for testing an Encounter Manager (ours or a vendor's).
Usage: python3 tools/mwl_find.py <host> <port> <called AE> [PatientID] [AdmissionID]
Sends the EBIW required SCU matching keys (Table 4.130.4.1.2.1-1 / POCUS table) and asks for
the required return keys; prints every response. Our own AE title: MOD_TEST, Modality US.
"""
import sys
from pydicom import Dataset
from pydicom.sequence import Sequence
from pynetdicom import AE
from pynetdicom.sop_class import ModalityWorklistInformationFind

host, port, called = sys.argv[1], int(sys.argv[2]), sys.argv[3]
pid = sys.argv[4] if len(sys.argv) > 4 else ""
adm = sys.argv[5] if len(sys.argv) > 5 else ""

q = Dataset()
q.SpecificCharacterSet = "ISO_IR 100"
for kw in ["PatientName", "PatientID", "IssuerOfPatientID", "PatientBirthDate", "PatientSex",
           "InstitutionName", "InstitutionAddress", "InstitutionalDepartmentName", "AdmissionID",
           "AdmittingDate", "AdmittingTime", "ReasonForVisit", "AccessionNumber",
           "RequestedProcedureDescription", "StudyInstanceUID", "PhysiciansOfRecord"]:
    setattr(q, kw, "")
q.PatientID, q.AdmissionID = pid, adm
q.OtherPatientIDsSequence = Sequence([])
code = Dataset(); code.CodeValue = ""; code.CodingSchemeDesignator = ""; code.CodeMeaning = ""
q.InstitutionCodeSequence = Sequence([Dataset(code)])
q.InstitutionalDepartmentTypeCodeSequence = Sequence([Dataset(code)])
q.RequestedProcedureCodeSequence = Sequence([Dataset(code)])
iss = Dataset(); iss.LocalNamespaceEntityID = ""; iss.UniversalEntityID = ""; iss.UniversalEntityIDType = ""
q.IssuerOfAccessionNumberSequence = Sequence([Dataset(iss)])
q.IssuerOfAdmissionIDSequence = Sequence([Dataset(iss)])
pic = Dataset(); pic.PersonIdentificationCodeSequence = Sequence([Dataset(code)])
q.PhysiciansOfRecordIdentificationSequence = Sequence([pic])
sps = Dataset()
sps.ScheduledStationAETitle = "MOD_TEST"       # IHE-6: our own AE title
sps.Modality = "US"                            # IHE-7: our own modality
sps.ScheduledProcedureStepStartDate = ""; sps.ScheduledProcedureStepStartTime = ""
sps.ScheduledProcedureStepDescription = ""; sps.ScheduledPerformingPhysicianName = ""
q.ScheduledProcedureStepSequence = Sequence([sps])

ae = AE(ae_title="MOD_TEST")
ae.add_requested_context(ModalityWorklistInformationFind)
assoc = ae.associate(host, port, ae_title=called)
if not assoc.is_established:
    sys.exit("association rejected")
n = 0
for status, ds in assoc.send_c_find(q, ModalityWorklistInformationFind):
    if status and status.Status in (0xFF00, 0xFF01) and ds is not None:
        n += 1
        print(f"===== response {n}\n{ds}")
    elif status:
        print(f"===== final status 0x{status.Status:04X}")
assoc.release()
print(f"{n} worklist item(s)")
