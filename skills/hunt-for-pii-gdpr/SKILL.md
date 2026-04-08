---
name: hunt-for-pii-gdpr
description: GDPR-mode PII detection. Focuses on personal data of EU data subjects as defined by the General Data Protection Regulation (EU) 2016/679.
license: MIT
metadata:
  author: "Harsh"
  version: "1.0.0"
  category: general
---

# Skill: hunt-for-pii (GDPR Mode)

## Compliance Framework: GDPR — Personal Data & Special Category Data

GDPR defines "personal data" broadly as any information relating to an identified
or identifiable natural person. You are operating in GDPR compliance mode.

---

## Article 4 — Personal Data (redact ALL of these)

- **Names** — Full name, partial name, username, alias
- **Identification numbers** — National ID, passport, tax ID, social security
- **Location data** — Home address, GPS coordinates, postcode
- **Online identifiers** — IP address, cookie IDs, device IDs, email addresses
- **Physical identifiers** — Any detail that could identify a person physically
- **Economic data** — Bank accounts, salary, financial status
- **Cultural/social identity** — Any cultural, social, or personal identity markers

---

## Article 9 — Special Category Data (highest sensitivity, always redact)

These require explicit consent and carry higher penalties if leaked:

1. **Racial or ethnic origin**
2. **Political opinions**
3. **Religious or philosophical beliefs**
4. **Trade union membership**
5. **Genetic data**
6. **Biometric data** used for unique identification
7. **Health data** — Diagnoses, medications, treatments, medical history
8. **Sex life or sexual orientation**
9. **Criminal convictions and offences**

---

## Article 10 — Criminal Data (redact)
- Criminal convictions, charges, offences
- Related security measures

---

## Additionally redact (GDPR best practice):
- Professional email addresses (they identify a natural person)
- Job titles when combined with name or location
- Any combination of data points that together identify a person

---

## Output Format

Return a single valid JSON array of objects:
- "text": EXACT string as it appears in the document
- "category": one of GDPR_PERSONAL | GDPR_SPECIAL | GDPR_CRIMINAL | GDPR_ONLINE | GDPR_FINANCIAL | GDPR_LOCATION | GDPR_HEALTH

Deduplicate — include each unique string once only.
Do NOT wrap in markdown fences.

Example:
[
  {"text": "Michael Henderson", "category": "GDPR_PERSONAL"},
  {"text": "Type 2 Diabetes", "category": "GDPR_HEALTH"},
  {"text": "192.168.100.45", "category": "GDPR_ONLINE"},
  {"text": "m.henderson79@gmail.com", "category": "GDPR_ONLINE"}
]
