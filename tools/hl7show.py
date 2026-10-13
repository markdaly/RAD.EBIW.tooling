#!/usr/bin/env python3
"""
hl7show.py: pretty-print an HL7 v2 message file in the console, one row per populated field,
with HL7 2.5.1 field names. Read-only. Also the field-name table used by tools/logview.py.

Usage:
  python3 tools/hl7show.py <file.hl7> [more files...]      # table per file
  python3 tools/hl7show.py -                                 # from stdin
  python3 tools/hl7show.py --raw <file.hl7>                  # raw with CR shown as newlines
  python3 tools/hl7show.py --next <file.hl7>                 # print the next capture in the same folder
  python3 tools/hl7show.py --prev <file.hl7>                 # print the previous one
Nothing is validated; unknown fields print with an empty name.
"""
import sys
from pathlib import Path

# HL7 v2.5.1 field names for the segments that show up in IHE RAD/ITI traffic. Numbers are
# HL7 field numbers (MSH-1 is the field separator). Not exhaustive; unknown = "".
NAMES = {
 "MSH": {1:"Field Separator",2:"Encoding Characters",3:"Sending Application",4:"Sending Facility",5:"Receiving Application",
         6:"Receiving Facility",7:"Date/Time of Message",8:"Security",9:"Message Type",10:"Message Control ID",11:"Processing ID",
         12:"Version ID",13:"Sequence Number",14:"Continuation Pointer",15:"Accept Ack Type",16:"Application Ack Type",
         17:"Country Code",18:"Character Set",19:"Principal Language",21:"Message Profile Identifier"},
 "MSA": {1:"Acknowledgment Code",2:"Message Control ID",3:"Text Message",4:"Expected Sequence Number",6:"Error Condition"},
 "ERR": {1:"Error Code and Location",2:"Error Location",3:"HL7 Error Code",4:"Severity",5:"Application Error Code",8:"User Message"},
 "EVN": {1:"Event Type Code",2:"Recorded Date/Time",3:"Date/Time Planned Event",4:"Event Reason Code",5:"Operator ID",6:"Event Occurred",7:"Event Facility"},
 "PID": {1:"Set ID",2:"Patient ID (retired)",3:"Patient Identifier List",4:"Alternate Patient ID",5:"Patient Name",6:"Mother's Maiden Name",
         7:"Date/Time of Birth",8:"Administrative Sex",9:"Patient Alias",10:"Race",11:"Patient Address",12:"County Code",13:"Phone Home",
         14:"Phone Business",15:"Primary Language",16:"Marital Status",17:"Religion",18:"Patient Account Number",19:"SSN",
         22:"Ethnic Group",23:"Birth Place",24:"Multiple Birth Indicator",29:"Patient Death Date/Time",30:"Patient Death Indicator",
         31:"Identity Unknown Indicator",32:"Identity Reliability Code",33:"Last Update Date/Time",34:"Last Update Facility"},
 "PV1": {1:"Set ID",2:"Patient Class",3:"Assigned Patient Location",4:"Admission Type",5:"Preadmit Number",6:"Prior Patient Location",
         7:"Attending Doctor",8:"Referring Doctor",9:"Consulting Doctor",10:"Hospital Service",11:"Temporary Location",
         13:"Re-admission Indicator",14:"Admit Source",15:"Ambulatory Status",16:"VIP Indicator",17:"Admitting Doctor",18:"Patient Type",
         19:"Visit Number",20:"Financial Class",36:"Discharge Disposition",37:"Discharged to Location",39:"Servicing Facility",
         41:"Account Status",44:"Admit Date/Time",45:"Discharge Date/Time",50:"Alternate Visit ID",51:"Visit Indicator"},
 "PV2": {3:"Admit Reason",8:"Expected Admit Date/Time",9:"Expected Discharge Date/Time",22:"Visit Protection Indicator"},
 "ORC": {1:"Order Control",2:"Placer Order Number",3:"Filler Order Number",4:"Placer Group Number",5:"Order Status",6:"Response Flag",
         7:"Quantity/Timing",8:"Parent",9:"Date/Time of Transaction",10:"Entered By",11:"Verified By",12:"Ordering Provider",
         13:"Enterer's Location",14:"Call Back Phone Number",15:"Order Effective Date/Time",16:"Order Control Code Reason",
         17:"Entering Organization",21:"Ordering Facility Name",29:"Order Type"},
 "OBR": {1:"Set ID",2:"Placer Order Number",3:"Filler Order Number",4:"Universal Service Identifier",5:"Priority (retired)",
         6:"Requested Date/Time",7:"Observation Date/Time",8:"Observation End Date/Time",9:"Collection Volume",10:"Collector Identifier",
         11:"Specimen Action Code",12:"Danger Code",13:"Relevant Clinical Information",14:"Specimen Received Date/Time",15:"Specimen Source",
         16:"Ordering Provider",17:"Order Callback Phone Number",18:"Placer Field 1 (Accession Number in RAD-132)",
         19:"Placer Field 2 (Issuer of Accession in RAD-132)",20:"Filler Field 1",21:"Filler Field 2",22:"Results Rpt/Status Change Date/Time",
         23:"Charge to Practice",24:"Diagnostic Serv Sect ID",25:"Result Status",26:"Parent Result",27:"Quantity/Timing",28:"Result Copies To",
         29:"Parent",30:"Transportation Mode",31:"Reason for Study",32:"Principal Result Interpreter",33:"Assistant Result Interpreter",
         34:"Technician",35:"Transcriptionist",36:"Scheduled Date/Time",44:"Procedure Code",45:"Procedure Code Modifier",
         46:"Placer Supplemental Service Information",47:"Filler Supplemental Service Information",49:"Result Handling"},
 "OBX": {1:"Set ID",2:"Value Type",3:"Observation Identifier",4:"Observation Sub-ID",5:"Observation Value",6:"Units",7:"References Range",
         8:"Abnormal Flags",9:"Probability",10:"Nature of Abnormal Test",11:"Observation Result Status",12:"Effective Date of Reference Range",
         13:"User Defined Access Checks",14:"Date/Time of the Observation",15:"Producer's ID",16:"Responsible Observer",17:"Observation Method",
         18:"Equipment Instance Identifier",19:"Date/Time of the Analysis"},
 "TQ1": {1:"Set ID",2:"Quantity",3:"Repeat Pattern",4:"Explicit Time",5:"Relative Time and Units",6:"Service Duration",7:"Start Date/Time",
         8:"End Date/Time",9:"Priority",10:"Condition Text",11:"Text Instruction",12:"Conjunction",13:"Occurrence Duration",14:"Total Occurrences"},
 "DG1": {1:"Set ID",2:"Diagnosis Coding Method",3:"Diagnosis Code",4:"Diagnosis Description",5:"Diagnosis Date/Time",6:"Diagnosis Type",
         15:"Diagnosis Priority",16:"Diagnosing Clinician",19:"Attestation Date/Time"},
 "NTE": {1:"Set ID",2:"Source of Comment",3:"Comment",4:"Comment Type"},
 "IPC": {1:"Accession Identifier",2:"Requested Procedure ID",3:"Study Instance UID",4:"Scheduled Procedure Step ID",5:"Modality",
         6:"Protocol Code",7:"Scheduled Station Name",8:"Scheduled Procedure Step Location",9:"Scheduled AE Title"},
 "ZDS": {1:"Study Instance UID"},
 "AL1": {1:"Set ID",2:"Allergen Type Code",3:"Allergen Code",4:"Allergy Severity",5:"Allergy Reaction"},
 "ROL": {1:"Role Instance ID",2:"Action Code",3:"Role",4:"Role Person"},
 "MRG": {1:"Prior Patient Identifier List",3:"Prior Patient Account Number",7:"Prior Patient Name"},
}


def parse(text: str):
    """Return [(segment, [(n, value), ...]), ...] with only populated fields; MSH numbering honored."""
    text = text.replace("\r\n", "\r").replace("\n", "\r")
    out = []
    sep = "|"
    for seg in [s for s in text.split("\r") if s.strip()]:
        name = seg[:3]
        if name == "MSH" and len(seg) > 3:
            sep = seg[3]
            fields = [(1, sep), (2, seg[4:8])] + [(i + 3, v) for i, v in enumerate(seg[8:].split(sep)[1:])]
        else:
            fields = [(i + 1, v) for i, v in enumerate(seg.split(sep)[1:])]
        out.append((name, [(n, v) for n, v in fields if v != ""]))
    return out


def name_of(seg, n):
    return NAMES.get(seg, {}).get(n, "")


def render_console(text: str) -> str:
    lines = []
    for seg, fields in parse(text):
        lines.append(f"\033[1m{seg}\033[0m")
        for n, v in fields:
            comps = [v] if seg == "MSH" and n <= 2 else v.split("^")
            shown = v if len(comps) == 1 else "  ^  ".join(f"\033[2m{i+1}:\033[0m{c}" if c else f"\033[2m{i+1}:\033[0m" for i, c in enumerate(comps))
            lines.append(f"  {seg}-{n:<2} {name_of(seg, n):<40} {shown}")
    return "\n".join(lines)


def neighbor(path: Path, step: int):
    files = sorted(p for p in path.parent.iterdir() if p.is_file() and p.name != "summary.log")
    try:
        return files[files.index(path) + step]
    except (ValueError, IndexError):
        return None


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    raw = "--raw" in args
    step = 1 if "--next" in args else -1 if "--prev" in args else 0
    files = [a for a in args if not a.startswith("--")]
    for f in files:
        p = Path(f)
        if step:
            p = neighbor(p.resolve(), step)
            if p is None:
                sys.exit("no neighbor")
        data = sys.stdin.buffer.read() if f == "-" else p.read_bytes()
        text = data.decode("utf-8", "replace")
        print(f"\033[36m== {p if f != '-' else 'stdin'}\033[0m")
        print(text.replace("\r", "\n") if raw else render_console(text))
