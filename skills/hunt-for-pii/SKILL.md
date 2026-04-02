---
name: hunt-for-pii
description: skill to identify personally identifiable information (PII) and confidential business information in extracted PDF text
license: MIT
allowed-tools: []
metadata:
  author: "Harsh"
  version: "1.0.0"
  category: general
---

# Skill: Hunt for PII

## Purpose
Analyze extracted PDF text and identify every piece of sensitive data that must be redacted.
Return a structured list of findings — never the raw sensitive values in output logs.

## Input
You will receive the full extracted text of a document, page by page.

## Your Task
Scan for ALL of the following categories. Be aggressive — flag anything that could be sensitive.

---

## PII Categories

### Personal Identifiers
- **Full names**: "John Smith", "Dr. Sarah Connor", "Mr. J. Williams" — any combination of first/last name
- **Initials + surname**: "J. Smith", "R.K. Narayan"
- **SSN**: `XXX-XX-XXXX`, `XXXXXXXXX`, or any 9-digit number in legal context
- **Date of birth**: any date associated with a person's age or birth
- **Passport / license numbers**: alphanumeric IDs tied to individuals

### Contact & Location
- **Home addresses**: street address, apartment numbers, zip codes tied to individuals
- **Personal email**: any email that isn't a corporate/org domain in legal context
- **Personal phone numbers**: any phone number

### Medical & Health
- **Diagnoses**: "diagnosed with", "suffers from", condition names tied to a person
- **Medications**: drug names when associated with a specific individual
- **Treatment history**: procedures, hospitalizations, therapy
- **Mental health**: any psychological or psychiatric references

### Financial
- **Bank account numbers**
- **Credit/debit card numbers**
- **Routing numbers**
- **Specific salary/compensation figures**
- **Loan amounts tied to individuals**

## Confidential Business Categories

- **Trade secrets**: proprietary processes, formulas, algorithms described in detail
- **Unreleased product names or codenames**
- **Internal project names** (e.g., "Project Falcon", "Operation Sunrise")
- **Contract dollar amounts** (unless publicly filed)
- **Attorney-client privileged content**: anything prefixed with "Privileged and Confidential"
- **Proprietary technical specifications**


## Rules
- When in doubt, include it — over-flagging is correct behavior
- Flag every occurrence — if a name appears 12 times, flag all 12
- Do not deduplicate — the redaction engine needs every instance
