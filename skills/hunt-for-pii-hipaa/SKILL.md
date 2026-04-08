---
name: hunt-for-pii-hipaa
description: HIPAA-mode PII detection. Focuses on Protected Health Information (PHI) as defined by the Health Insurance Portability and Accountability Act.
license: MIT
metadata:
  author: "Harsh"
  version: "1.0.0"
  category: general
---

# Skill: hunt-for-pii (HIPAA Mode)

## Compliance Framework: HIPAA — Protected Health Information (PHI)

HIPAA defines 18 specific PHI identifiers that MUST be redacted.
You are operating in HIPAA compliance mode. Focus on these categories.

---

## The 18 HIPAA PHI Identifiers (redact ALL of these)

1. **Names** — Patient names, relatives, employers
2. **Geographic data** — Street address, city, zip code, county (anything smaller than state)
3. **Dates** — Birth dates, admission dates, discharge dates, death dates, ages over 89
4. **Phone numbers** — Any telephone number
5. **Fax numbers**
6. **Email addresses**
7. **Social Security Numbers**
8. **Medical record numbers**
9. **Health plan beneficiary numbers**
10. **Account numbers** — Bank or financial accounts
11. **Certificate/license numbers** — Driver's license, professional licenses
12. **Vehicle identifiers** — License plate numbers, VIN numbers
13. **Device identifiers** — Serial numbers of medical devices
14. **URLs / Web addresses**
15. **IP addresses**
16. **Biometric identifiers** — Fingerprints, voice prints, retinal scans
17. **Full-face photographs** (flag for manual review)
18. **Any unique identifying number** — Any other unique code or characteristic

## Additionally redact:
- Diagnoses, conditions, treatments, medications tied to a named individual
- Treating physician names and medical facility names when tied to a patient
- Insurance policy numbers
- Procedure codes when tied to a patient

---

## Output Format

Return a single valid JSON array of objects:
- "text": EXACT string as it appears in the document
- "category": one of PHI_NAME | PHI_DATE | PHI_GEOGRAPHIC | PHI_PHONE | PHI_EMAIL | PHI_SSN | PHI_MEDICAL_RECORD | PHI_ACCOUNT | PHI_LICENSE | PHI_IP | PHI_DEVICE | PHI_URL | PHI_BIOMETRIC | PHI_OTHER

Deduplicate — include each unique string once only.
Do NOT wrap in markdown fences.

Example:
[
  {"text": "Michael Henderson", "category": "PHI_NAME"},
  {"text": "March 14, 1979", "category": "PHI_DATE"},
  {"text": "Type 2 Diabetes", "category": "PHI_MEDICAL_RECORD"},
  {"text": "523-88-4471", "category": "PHI_SSN"},
  {"text": "192.168.100.45", "category": "PHI_IP"}
]
