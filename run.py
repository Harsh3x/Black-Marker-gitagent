#!/usr/bin/env python3
"""
Black-Marker: Autonomous PDF Redaction Engine (Async Version)
  1. Extract text page-by-page using PyMuPDF (fitz)
  2. Concurrently query LLM per page using AsyncOpenAI
  3. PyMuPDF searches for exact text strings -> coordinates
  4. PyMuPDF draws permanent black boxes & scrubs metadata
  5. Report shows category breakdown per compliance framework

  Flags:
    --review      Human-in-the-Loop workflow (Yellow Highlights)
    --compliance  hipaa | gdpr | dpdp | full (default: full)
"""

import sys
import json
import os
import re
import asyncio
import argparse
from openai import AsyncOpenAI
from pathlib import Path
from collections import defaultdict
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

import fitz  # PyMuPDF

# ─────────────────────────────────────────────
# Compliance skill map
# ─────────────────────────────────────────────

COMPLIANCE_SKILLS = {
    "hipaa": "./skills/hunt-for-pii-hipaa/SKILL.md",
    "gdpr":  "./skills/hunt-for-pii-gdpr/SKILL.md",
    "dpdp":  "./skills/hunt-for-pii-dpdp/SKILL.md",
    "full":  "./skills/hunt-for-pii/SKILL.md",
}

COMPLIANCE_LABELS = {
    "hipaa": "HIPAA (US Health)",
    "gdpr":  "GDPR (EU)",
    "dpdp":  "DPDP Act 2023 (India)",
    "full":  "Full (All Frameworks)",
}

# Load system prompts — skill overridden at runtime based on --compliance
SOUL  = open("./SOUL.md").read()
RULES = open("./RULES.md").read()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("[ERROR] OPENAI_API_KEY not set. Run: export OPENAI_API_KEY=sk-...")
    sys.exit(1)

client = AsyncOpenAI(api_key=api_key)
MODEL = "gpt-4o-mini"
CONCURRENCY_LIMIT = 5


# ─────────────────────────────────────────────
# Step 2: LLM identifies text + categories
# ─────────────────────────────────────────────

async def hunt_for_pii_on_page(
    page_text: str,
    page_num: int,
    semaphore: asyncio.Semaphore,
    hunt_skill: str,
    compliance: str
) -> list[dict]:
    if not page_text.strip():
        return []

    system = f"{SOUL}\n\n{RULES}"
    user = f"""
{hunt_skill}

Here is the text for PAGE {page_num} of the document:

{page_text}

Return a JSON object with a single key "findings" containing an array of objects.
Each object must have exactly two fields:
  - "text": the EXACT string as it appears in the document
  - "category": the appropriate category for the {compliance.upper()} compliance framework
    as defined in the skill instructions above.

Deduplicate — include each unique text string once only.
"""
    async with semaphore:
        try:
            response = await client.chat.completions.create(
                model=MODEL,
                max_tokens=2048,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user}
                ]
            )
            raw = response.choices[0].message.content
            findings = json.loads(raw).get("findings", [])
            for f in findings:
                f["page_num"] = page_num
            return findings
        except Exception as e:
            print(f"      [!] Error processing page {page_num}: {e}")
            return []


async def process_document_async(pdf_path: str, hunt_skill: str, compliance: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    tasks = []
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    print(f"      ✓ Loaded PDF with {len(doc)} pages")
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        tasks.append(hunt_for_pii_on_page(text, page_num, semaphore, hunt_skill, compliance))

    doc.close()
    results = await asyncio.gather(*tasks)

    all_findings = []
    seen = set()
    for page_findings in results:
        for f in page_findings:
            if not f.get("text"):
                continue
            text     = str(f["text"])
            category = str(f.get("category", "UNKNOWN"))
            if (text, category) not in seen:
                seen.add((text, category))
                all_findings.append({"text": text, "category": category})
    return all_findings


# ─────────────────────────────────────────────
# Step 3: Robust Coordinate Mapping
# ─────────────────────────────────────────────

def normalize_word(w: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]', '', w).lower()


def find_text_coords_fitz(pdf_path: str, findings: list[dict]) -> list[dict]:
    redactions = []
    doc = fitz.open(pdf_path)

    for page_num, page in enumerate(doc, start=1):
        page_words       = page.get_text("words")
        clean_page_words = [(normalize_word(w[4]), w) for w in page_words if normalize_word(w[4])]

        for finding in findings:
            text     = finding["text"]
            category = finding["category"]

            # ATTEMPT 1: Native fitz search (handles most cases)
            instances = page.search_for(text)
            if instances:
                for inst in instances:
                    redactions.append({
                        "page_number": page_num,
                        "x0": inst.x0, "y0": inst.y0,
                        "x1": inst.x1, "y1": inst.y1,
                        "text": text, "category": category
                    })
                continue

            # ATTEMPT 2: Fuzzy word-sequence matcher (handles spacing/hyphenation issues)
            target_words = [normalize_word(w) for w in text.split() if normalize_word(w)]
            if not target_words:
                continue

            i = 0
            while i < len(clean_page_words):
                if clean_page_words[i][0] == target_words[0]:
                    match_rects, p_idx, t_idx, skips = [], i, 0, 0
                    while p_idx < len(clean_page_words) and t_idx < len(target_words):
                        if clean_page_words[p_idx][0] == target_words[t_idx]:
                            match_rects.append(clean_page_words[p_idx][1])
                            t_idx += 1
                            skips = 0
                        else:
                            skips += 1
                            if skips > 3:
                                break
                        p_idx += 1

                    if t_idx == len(target_words):
                        for w_rect in match_rects:
                            redactions.append({
                                "page_number": page_num,
                                "x0": w_rect[0], "y0": w_rect[1],
                                "x1": w_rect[2], "y1": w_rect[3],
                                "text": text, "category": category
                            })
                        i = p_idx - 1
                i += 1

    doc.close()
    return redactions


# ─────────────────────────────────────────────
# Step 4: Draw Annotations (Review or Redact)
# ─────────────────────────────────────────────

def apply_annotations(
    pdf_path: str,
    redactions: list,
    output_path: str,
    review_mode: bool
) -> dict:
    doc = fitz.open(pdf_path)
    pages_affected = set()
    by_page = defaultdict(list)

    for r in redactions:
        by_page[r["page_number"] - 1].append(r)

    for page_idx, page_reds in by_page.items():
        if page_idx >= len(doc):
            continue
        page = doc[page_idx]

        for r in page_reds:
            height   = r["y1"] - r["y0"]
            width    = r["x1"] - r["x0"]
            margin_y = height * 0.15
            margin_x = width  * 0.01
            rect = fitz.Rect(
                r["x0"] + margin_x, r["y0"] + margin_y,
                r["x1"] - margin_x, r["y1"] - margin_y
            )

            if review_mode:
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=(1, 1, 0))  # Yellow
                annot.update()
            else:
                page.add_redact_annot(rect, fill=(0, 0, 0), cross_out=False)

        if not review_mode:
            page.apply_redactions(
                images=fitz.PDF_REDACT_IMAGE_NONE,
                graphics=fitz.PDF_REDACT_LINE_ART_NONE
            )

        pages_affected.add(page_idx + 1)

    doc.set_metadata({})  # Always scrub metadata
    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()

    return {
        "success":          True,
        "output_path":      output_path,
        "total_redactions": len(redactions),
        "pages_affected":   sorted(pages_affected)
    }


# ─────────────────────────────────────────────
# Step 5: Report Generation
# ─────────────────────────────────────────────

# Labels covering all four compliance frameworks
CATEGORY_LABELS = {
    # Full / generic
    "PII_NAME":     "Personal Name",
    "SSN":          "Social Security Number",
    "DOB":          "Date of Birth",
    "ADDRESS":      "Address",
    "PHONE":        "Phone Number",
    "EMAIL":        "Email Address",
    "MEDICAL":      "Medical Information",
    "FINANCIAL":    "Financial Data",
    "CONFIDENTIAL": "Confidential / Proprietary",
    "IP_ADDRESS":   "IP Address",
    "DIGITAL_ID":   "Digital Identity / Username",
    "LICENSE":      "License / ID Number",
    "UNKNOWN":      "Uncategorised",
    # HIPAA
    "PHI_NAME":          "PHI — Name",
    "PHI_DATE":          "PHI — Date",
    "PHI_GEOGRAPHIC":    "PHI — Geographic Data",
    "PHI_PHONE":         "PHI — Phone / Fax",
    "PHI_EMAIL":         "PHI — Email",
    "PHI_SSN":           "PHI — Social Security Number",
    "PHI_MEDICAL_RECORD":"PHI — Medical Record",
    "PHI_ACCOUNT":       "PHI — Account Number",
    "PHI_LICENSE":       "PHI — Certificate / License",
    "PHI_IP":            "PHI — IP Address",
    "PHI_DEVICE":        "PHI — Device Identifier",
    "PHI_URL":           "PHI — URL / Web Address",
    "PHI_BIOMETRIC":     "PHI — Biometric Identifier",
    "PHI_OTHER":         "PHI — Other Unique Identifier",
    # GDPR
    "GDPR_PERSONAL":  "GDPR — Personal Data (Art. 4)",
    "GDPR_SPECIAL":   "GDPR — Special Category (Art. 9)",
    "GDPR_CRIMINAL":  "GDPR — Criminal Data (Art. 10)",
    "GDPR_ONLINE":    "GDPR — Online Identifier",
    "GDPR_FINANCIAL": "GDPR — Financial Data",
    "GDPR_LOCATION":  "GDPR — Location Data",
    "GDPR_HEALTH":    "GDPR — Health Data",
    # DPDP
    "DPDP_NAME":               "DPDP — Name",
    "DPDP_AADHAAR":            "DPDP — Aadhaar Number",
    "DPDP_PAN":                "DPDP — PAN Number",
    "DPDP_GOVT_ID":            "DPDP — Government ID",
    "DPDP_CONTACT":            "DPDP — Contact Information",
    "DPDP_FINANCIAL":          "DPDP — Financial Data",
    "DPDP_HEALTH":             "DPDP — Health Data",
    "DPDP_BIOMETRIC":          "DPDP — Biometric Data",
    "DPDP_SEXUAL_ORIENTATION": "DPDP — Sexual Orientation",
    "DPDP_DIGITAL":            "DPDP — Digital Identifier",
    "DPDP_CHILD":              "DPDP — Child Data (S.9)",
}


def generate_report(
    pdf_path: str,
    findings: list[dict],
    redactions: list[dict],
    output_path: str,
    compliance: str
) -> str:
    pages       = sorted(set(r["page_number"] for r in redactions))
    found_texts = set(r["text"] for r in redactions)
    unmatched   = [f for f in findings if f["text"] not in found_texts]

    boxes_by_cat = defaultdict(int)
    for r in redactions:
        boxes_by_cat[r["category"]] += 1

    texts_by_cat = defaultdict(set)
    for f in findings:
        texts_by_cat[f["category"]].add(f["text"])

    report  = "==========================================\n"
    report += "       BLACK-MARKER REDACTION REPORT\n"
    report += "==========================================\n"
    report += f"Document   : {Path(pdf_path).name}\n"
    report += f"Processed  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"Model      : {MODEL} (Async)\n"
    report += f"Compliance : {COMPLIANCE_LABELS.get(compliance, compliance.upper())}\n\n"

    report += "SUMMARY\n"
    report += "-------\n"
    report += f"Unique sensitive strings : {len(findings)}\n"
    report += f"Redaction boxes applied  : {len(redactions)}\n"
    report += f"Pages affected           : {', '.join(map(str, pages)) if pages else 'None'}\n"
    report += f"Output file              : {Path(output_path).name}\n\n"

    report += "REDACTIONS BY CATEGORY\n"
    report += "----------------------\n"
    report += f"{'Category':<40} {'Strings':>8}  {'Boxes':>6}\n"
    report += f"{'-'*40}  {'-'*8}  {'-'*6}\n"
    for cat in sorted(boxes_by_cat.keys()):
        label   = CATEGORY_LABELS.get(cat, cat)
        strings = len(texts_by_cat[cat])
        boxes   = boxes_by_cat[cat]
        report += f"{label:<40} {strings:>8}  {boxes:>6}\n"

    if unmatched:
        report += f"\nUNMATCHED ({len(unmatched)} — manual review required)\n"
        report += "-" * 44 + "\n"
        for f in unmatched:
            label = CATEGORY_LABELS.get(f["category"], f["category"])
            # Never print the actual sensitive value — category only
            report += f"  [{label}]  value not found in text layer\n"
        report += "These may exist in scanned/image regions or span line-breaks.\n"

    report += "\n==========================================\n"
    report += "Original file NOT placed in /output.\n"
    report += "Metadata scrubbed. Only the redacted copy exists.\n"
    report += "==========================================\n"

    stem = Path(pdf_path).stem
    compliance_tag = f"_{compliance.upper()}" if compliance != "full" else ""
    with open(f"output/{stem}{compliance_tag}_REDACTION_REPORT.txt", "w") as fh:
        fh.write(report)

    return report


# ─────────────────────────────────────────────
# Main Async Orchestrator
# ─────────────────────────────────────────────

async def redact_async(pdf_path: str, review_mode: bool, compliance: str):
    # Load the correct skill for this compliance mode
    skill_path = COMPLIANCE_SKILLS.get(compliance, COMPLIANCE_SKILLS["full"])
    hunt_skill = open(skill_path).read()

    print(f"\n[BLACK-MARKER] Initiating async redaction: {pdf_path}")
    print(f"[BLACK-MARKER] Mode      : {'REVIEW (Highlights)' if review_mode else 'AUTONOMOUS (Blackout)'}")
    print(f"[BLACK-MARKER] Compliance: {COMPLIANCE_LABELS.get(compliance, compliance.upper())}")
    print("=" * 50)

    print("[1/4] Extracting text & hunting for PII concurrently...")
    findings = await process_document_async(pdf_path, hunt_skill, compliance)

    print(f"      ✓ {len(findings)} sensitive string(s) identified:")
    for f in findings:
        # Never print actual values — category only
        print(f"        • [{f['category']}] [REDACTED]")

    if not findings:
        print("\n[BLACK-MARKER] No sensitive data detected.")
        return

    print("\n[2/4] Searching PDF for exact text locations...")
    redactions = find_text_coords_fitz(pdf_path, findings)
    print(f"      ✓ {len(redactions)} location(s) mapped")

    stem = Path(pdf_path).stem
    # Calculate the tag once for all outputs
    compliance_tag = f"_{compliance.upper()}" if compliance != "full" else ""

    if review_mode:
        output_path = f"output/{stem}{compliance_tag}_FOR_REVIEW.pdf"
        print(f"\n[3/4] Applying yellow highlights for human review...")
    else:
        output_path = f"output/{stem}{compliance_tag}_REDACTED.pdf"
        print(f"\n[3/4] Applying permanent black-box redactions...")

    result = apply_annotations(pdf_path, redactions, output_path, review_mode)
    print(f"      ✓ {result['total_redactions']} box(es) applied → {output_path}")

    print("\n[4/4] Generating report...")
    report = generate_report(pdf_path, findings, redactions, output_path, compliance)
    print("\n" + "=" * 50)
    print(report)
    print(f"Task complete! Check {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Black-Marker PDF Redaction")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument(
        "--compliance",
        choices=["hipaa", "gdpr", "dpdp", "full"],
        default="full",
        help="Compliance framework: hipaa | gdpr | dpdp | full (default: full)"
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="Review mode — yellow highlights instead of permanent black boxes"
    )
    args = parser.parse_args()

    os.makedirs("output", exist_ok=True)
    asyncio.run(redact_async(args.pdf_path, args.review, args.compliance))