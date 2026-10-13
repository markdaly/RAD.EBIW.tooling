---
event: IHE NA Connectathon 2026
source: RAD TF-2 rev 23.0 (2025-08-08) Sections 2.2, 2.3.1, 2.4.1.2, 2.4.4.1-2.4.4.3 (pp. 38-50); IHE RAD Supplement Results Distribution (RD) rev 1.2 (2019-08-09) 4.128.4.1.2.2, 4.128.4.1.2.8, 4.128.4.2 (pp. 30, 40-41, 52); IHE RAD Supplement EBIW rev 3.1 4.132.3, 4.132.4.1.2, 4.132.4.2; Apple Support 103769 "Requirements for trusted certificates in iOS 13 and macOS 10.15" and 102028 "About upcoming limits on trusted certificates"
status: verified (each claim quoted against the published text; residual doubts flagged inline)
---
# Four claims made from memory, checked

## (a) "RAD TF-2 4.128.4.2 Acknowledge Imaging Result = HL7 v2.5.1 original-mode ACK, MSH-9 ACK^R01^ACK, MSA-1 AA|AE|AR, MSA-2 = MSH-10"

**Verdict: confirmed, with one correction on where the text lives.**

- Section 4.128 is NOT in RAD TF-2 rev 23.0 Final Text. RAD TF-2 p. 588 (rev 23.0) lists "4.128 Send Imaging Result [RAD-128]" only as a placeholder pointing to the Results Distribution (RD) Trial Implementation supplement. The normative text is RD rev 1.2, Section 4.128.4.2 (p. 52). EBIW 4.132.4.2 says: "The Sender and Receiver shall implement the Acknowledge Imaging Result message as described in Section 4.128.4.2."
- RD 4.128.4.2.2 Message Semantics, verbatim: "The message is an HL7 2.5.1 MSA-1 Original Mode Acknowledgement message. The Receiver is the HL7 acknowledgment sender. The Sender is the HL7 acknowledgment recipient. The Receiver is not required to send any attributes within the MSA segment beyond what is specified in the HL7 standard. See ITI TF-2x: C.2.3 for the list of all required and optional fields within the MSA segment."
- RD 4.128.4.2.3 Expected Actions: "If the HL7 ORU was invalid, the Receiver shall send an error message indicating that the received ORU message was invalid. Otherwise, the Receiver shall respond with valid acknowledgment message."
- Original mode is also the RAD-wide default: RAD TF-2 2.4.1.2 "Applications that receive HL7 messages shall send acknowledgments using the HL7 Original Mode (versus Enhanced Acknowledgment Mode) unless otherwise specified in an IHE RAD transaction."
- MSA-1 values: RAD TF-2 2.4.4.3 (Table 2.4-7 text, p. 50): "This field shall contain the value AA, AE or AR when using Original Acknowledgement Mode, or CA, CE or CR when using Enhanced Acknowledgement Mode."
- MSA-2: same section: "This field contains the message control ID from Field MSH-10-Message Control ID of the incoming message for which the acknowledgement is sent."
- MSH-9 of the ACK: no IHE text spells out `ACK^R01^ACK`. What is normative: RAD TF-2 2.4.4.2 MSH-9 "All three components are required" (applies to every v2.5.1 message incl. ACK, Table 2.4-6 governs the ACK MSH per 2.4.4.1); HL7 v2.5.1 ch. 2 defines the general ACK structure as `ACK` with the trigger of the original message, hence `ACK^R01^ACK`. Gazelle EBIW_25/35 step 55 only checks MSA-1 AA and MSA-2. So `ACK^R01^ACK` is correct. If a receiver sends `ACK^R01` or `ACK`, the section to cite is RAD TF-2 2.4.4.2 (MSH-9 components), not 4.128.4.2 (which only fixes original mode).
- Also from 2.4.4.3: MSA-3 and MSA-6 are X (not supported) in v2.5.1 IHE ACKs; errors go in ERR (2.4.4.4). `tools/mllp_receiver.py` writes "MSA|AR||Cannot parse MSH" (MSA-3 populated) on unparseable input; see tool-gaps.md.
- ITI TF-2x C.2.3 (the MSA field list RD points to) was not fetched; unverified, but it is the same AA/AE/AR + MSA-2 content.

## (b) "The Study Instance UID OBX in RAD-128/RAD-132 uses OBX-3 = 113014^DICOM Study^DCM and carries the UID in OBX-5 (and what OBX-2 is)"

**Verdict: confirmed. OBX-2 = ST, OBX-11 = O.**

RD 4.128.4.1.2.8 "OBX Segment - DICOM Study Instance UID", Table 4.128.4.1.2.8-1 (p. 40) and field text (pp. 40-41):
- "Field OBX-2 Value Type shall have the value "ST" to indicate that OBX-5 is a text string."
- "Field OBX-3 Observation Identifier shall have the value "113014^DICOM Study^DCM" in the first three components."
- "Field OBX-5 Observation Value shall include the Study Instance UID." One UID per OBX; multiple studies -> repeat with OBX-4 sub-IDs.
- "Field OBX-11 Observation Result Status shall have the value "O" (Order detail description - no result)."
- Table row for OBX-5 lists DT "HD" and LEN 99999; the text says ST. Treat as a table typo; ST is what the example shows: `OBX|7|ST|113014^DICOM Study^DCM|1|1.2.840.113532.7.7345.3453445346802.34534||||||O|...`
- OBX-23/24/25 (performing organization) "should be populated" (C in the table).
- EBIW Table 4.132.4.1.2-1 references exactly this section for the unbracketed "OBX Observation/Result (DICOM Study Instance UID)" row. Gazelle EBIW_90 checks OBX-2 ST, OBX-3 113014^DICOM Study^DCM, OBX-5 UID, OBX-11 O, matching.
- Caveat on optionality: EBIW's table shows the segment unbracketed (required); RD 4.128.4.1.2.8 says "shall be included if the DICOM Study Instance UID(s) is known". For RAD-132 the UID is always known (it came from RAD-130), so treat as required.

## (c) "RAD TF-2 2.3.1 conventions require all three components of MSH-9"

**Verdict: the requirement is real; the section number is wrong. It is RAD TF-2 2.4.4.2, reinforced by RD 4.128.4.1.2.2.**

- RAD TF-2 2.3.1 (rev 23.0, pp. 40-42) is "Static definition – Segment level and Data Type level": the column legend (SEQ, LEN, DT, Usage R/R+/RE/O/C/CE/X, Cardinality, TBL#, ITEM#). It says nothing about MSH-9. (EBIW 4.132.3 and 4.132.4.1.2 cite "RAD TF-2: 2.3.1 Conventions for HL7 v2.5.1 messages", which is an older title; the current 2.3 heading is "HL7 Profiling Conventions".)
- RAD TF-2 2.4.4.2 Message Control, Table 2.4-6 (MSH, v2.5.1) and text (p. 48), verbatim: "MSH-9 Message Type (MSG), required: Components: <Message Code (ID)> ^ <Trigger Event (ID)> ^ <Message Structure (ID)> Definition: This field contains the message type, trigger event, and the message structure ID for the message. All three components are required."
- Same section, MSH-12: "The first component SHALL be populated with the value "2.5.1" or higher, representing HL7 Version 2.5.1 or higher. See Section 2.4.1.3."
- RD 4.128.4.1.2.2 MSH Segment (p. 30), verbatim: "Field MSH-9-Message Type shall have three components. The first component shall have a value of ORU; the second component shall have a value of R01. The third component shall have a value of ORU_R01."
- Gazelle EBIW_90: "MSH-9 Message Type: value = ORU^R01^ORU_R01".
- Consequence for issue 002 finding #2: cite RAD TF-2 2.4.4.2 and RD 4.128.4.1.2.2, not 2.3.1.

## (d) "Apple requires TLS server certificates issued after 2019-07-01 to have validity <= 825 days, private roots included (Apple HT210176 or successor)"

**Verdict: confirmed for the 825-day rule including private roots. The HT number now resolves to article 103769. A second, stricter 398-day rule exists but applies only to Apple-preinstalled public roots.**

- Apple Support 103769, "Requirements for trusted certificates in iOS 13 and macOS 10.15" (successor of HT210176), quotes:
  - "All TLS server certificates must comply with these new security requirements in iOS 13 and macOS 10.15" (no exemption for private/enterprise roots stated).
  - "TLS server certificates must have a validity period of 825 days or fewer" and this applies to "all TLS server certificates issued after July 1, 2019" (NotBefore decides).
  - Also required: RSA keys >= 2048 bits for leaf and issuing CAs; SHA-2 family signatures; DNS name in Subject Alternative Name; ExtendedKeyUsage containing id-kp-serverAuth. (The page also states SHA-1 and RSA < 2048 are rejected for all certs regardless of issue date; that sentence was not quoted back verbatim by the fetch and is marked unverified here.)
- Apple Support 102028, "About upcoming limits on trusted certificates": certificates issued on or after 2020-09-01 "must not have a validity period greater than 398 days", and "This change will affect only TLS server certificates issued from the Root CAs preinstalled with" iOS/macOS; it "will not affect certificates issued from user-added or administrator-added Root CAs."
- Net for the floor (issue 001): a GSS-issued 10-year leaf trips the 825-day rule on any iOS 13+/macOS 10.15+ client even with the GSS CA installed as a trusted root; the 398-day rule does not apply to the GSS CA. The 825-day limit is also what the TLS-CERTS.md triage should cite. Android has no equivalent validity cap (unverified; from memory).
