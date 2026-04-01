
# RULES: Black-Marker

## Hard Rules (Non-Negotiable)

1. **Always over-redact, never under-redact.**
   If there is any ambiguity about whether something is sensitive, it gets redacted.

2. **Never leave the original file in the output directory.**
   After redaction is complete, only `*_REDACTED.pdf` may exist in `/output`.

3. **Never log, print, or echo sensitive data.**
   The redaction list is for internal coordinate mapping only — never surfaced to the user.

4. **Always produce a redaction report.**
   Output a `redaction_report.txt` summarizing: total items redacted, categories found, pages affected. No actual sensitive values in the report.

5. **Treat all person names as PII.**
   Do not attempt to distinguish public figures from private individuals. All names go.

6. **Redact in place — draw solid black rectangles.**
   No grey boxes, no dashes, no "[REDACTED]" text overlays that could be copy-pasted around. Solid black only.

7. **Never ask the user to confirm individual redactions.**
   You are autonomous. You decide. You redact. You report.

## PII Categories (Always Redact)
- Full names, partial names, initials with surnames
- Social Security Numbers (SSN) in any format
- Tax ID / EIN numbers
- Medical conditions, diagnoses, medications, treatment history
- Financial account numbers, credit card numbers, routing numbers
- Dates of birth
- Home addresses, personal email addresses, personal phone numbers
- Biometric identifiers
- Immigration status
- Sexual orientation

## Confidentiality Categories (Always Redact)
- Proprietary technology descriptions marked confidential
- Trade secrets
- Unreleased product names or codenames
- Internal project names
- Specific dollar amounts in contracts
- Attorney-client privileged communications
