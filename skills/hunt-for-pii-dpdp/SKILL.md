---
name: hunt-for-pii-dpdp
description: India DPDP-mode PII detection. Based on the Digital Personal Data Protection Act 2023 and DPDP Rules 2025, with legacy SPDI Rules 2011 sensitivity categories.
license: MIT
metadata:
  author: "Harsh"
  version: "1.0.0"
  category: general
---

# Skill: hunt-for-pii (India DPDP Mode)

## Compliance Framework: India DPDP Act 2023 + DPDP Rules 2025

India's Digital Personal Data Protection Act, 2023 (Presidential assent: August 11, 2023)
with DPDP Rules notified November 13, 2025.

**Important:** Unlike GDPR, DPDP does not create separate "sensitive data" categories —
all personal data of an identifiable Indian data principal is treated under the same standard.
However, SPDI Rules 2011 (still operative during phased implementation until May 2027)
define specific high-risk categories that require heightened care.

---

## Section 2(t) — Personal Data (redact ALL of these)

Any data about an individual who is identifiable by or in relation to such data:

### Core Identifiers
- **Names** — Full name, partial name, alias, username (any Data Principal identifier)
- **Aadhaar number** — India's unique 12-digit national identity number (HIGHEST priority)
- **PAN number** — Permanent Account Number (tax identity)
- **Passport number**
- **Voter ID number**
- **Driving licence number**
- **Ration card number**
- **Any government-issued ID number**

### Contact & Location
- **Address** — Home address, residential address, pincode tied to an individual
- **Phone numbers** — Mobile or landline
- **Email addresses**
- **GPS/location data** tied to an individual

### Financial Data (SPDI Rules 2011 — high sensitivity)
- **Bank account numbers** — Savings, current, NRI accounts
- **UPI IDs** (e.g., name@upi, phone@bank)
- **Credit/debit card numbers**
- **Net banking credentials or account details**
- **Salary, income, or compensation figures**
- **Loan account numbers**
- **PF/EPF account numbers**

### Health & Medical Data (SPDI Rules 2011 — high sensitivity)
- **Medical records and history**
- **Diagnoses and conditions** tied to a named individual
- **Medications and prescriptions**
- **ABHA number** (Ayushman Bharat Health Account)
- **Treating physician names** when tied to a patient
- **Hospital/clinic names** when tied to a patient record

### Biometric Data (SPDI Rules 2011 — high sensitivity)
- Fingerprints, iris scans, retinal data
- Any biometric identifier used for authentication

### Sexual Orientation (SPDI Rules 2011 — high sensitivity)
- Any reference to sexual orientation or gender identity tied to an individual

### Digital Identifiers
- **IP addresses** tied to an individual
- **Device IDs** tied to an individual
- **Cookie IDs** or tracking identifiers
- **Social media handles** that identify an individual

---

## Child Data (Section 9 — extra protection)
Any personal data of a person under 18 years of age requires special flagging.
Redact all child identifiers and flag in the report.

---

## Cross-border Transfer Flags
Flag any mention of data being transferred or stored outside India,
as DPDP Rules may restrict this for certain categories.

---

## Output Format

Return a single valid JSON array of objects:
- "text": EXACT string as it appears in the document
- "category": one of DPDP_NAME | DPDP_AADHAAR | DPDP_PAN | DPDP_GOVT_ID | DPDP_CONTACT | DPDP_FINANCIAL | DPDP_HEALTH | DPDP_BIOMETRIC | DPDP_SEXUAL_ORIENTATION | DPDP_DIGITAL | DPDP_CHILD


Deduplicate — include each unique string once only.
Do NOT wrap in markdown fences.

Example:
[
  {"text": "Rajesh Kumar Sharma", "category": "DPDP_NAME"},
  {"text": "4321 8765 1234 5678", "category": "DPDP_AADHAAR",},
  {"text": "ABCDE1234F", "category": "DPDP_PAN"},
  {"text": "Type 2 Diabetes", "category": "DPDP_HEALTH"},
  {"text": "rajesh.sharma@gmail.com", "category": "DPDP_CONTACT"},
  {"text": "SB Account 9876543210", "category": "DPDP_FINANCIAL"}
]
