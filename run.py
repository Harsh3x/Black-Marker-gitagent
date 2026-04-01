#!/usr/bin/env python3
"""
Black-Marker: Autonomous PDF Redaction Engine
  1. Extract raw text from PDF
  2. LLM returns {text, category} objects
  3. Python searches PDF for exact text strings → coordinates
  4. PyMuPDF draws permanent black boxes
  5. Report shows category breakdown
"""

import sys
import json
import os
import re
from openai import OpenAI
from pathlib import Path
from collections import defaultdict
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from tools.extract_pdf_text import extract_text

import pdfplumber
import fitz  # PyMuPDF

SOUL       = open("./SOUL.md").read()
RULES      = open("./RULES.md").read()
HUNT_SKILL = open("./skills/hunt-for-pii/SKILL.md").read()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("[ERROR] OPENAI_API_KEY not set. Run: export OPENAI_API_KEY=sk-...")
    sys.exit(1)

client = OpenAI(api_key=api_key)
MODEL  = "gpt-4o-mini"


# ─────────────────────────────────────────────
# Step 2: LLM identifies text + categories
# ─────────────────────────────────────────────

def hunt_for_pii(raw_text: str) -> list[dict]:
    """
    Returns list of {"text": "...", "category": "..."}.
    Categories: PII_NAME, SSN, DOB, ADDRESS, PHONE, EMAIL,
                MEDICAL, FINANCIAL, CONFIDENTIAL
    """
    system = f"{SOUL}\n\n{RULES}"
    user = f"""
{HUNT_SKILL}

Here is the full text of the document:

{raw_text}

Return a single valid JSON array of objects with exactly two fields each:
  - "text": the EXACT string as it appears in the document
  - "category": one of PII_NAME | SSN | DOB | ADDRESS | PHONE | EMAIL | MEDICAL | FINANCIAL | CONFIDENTIAL

Deduplicate — include each unique text string once only.
Do not wrap in markdown fences.

Example:
[
  {{"text": "John Doe", "category": "PII_NAME"}},
  {{"text": "523-88-4471", "category": "SSN"}},
  {{"text": "4721 Maple Grove Drive", "category": "ADDRESS"}},
  {{"text": "Project Nighthawk", "category": "CONFIDENTIAL"}},
  {{"text": "March 14, 1979", "category": "DOB"}}
]
"""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=2048,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user}
        ]
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    findings = json.loads(raw)
    assert isinstance(findings, list)
    return [
        {"text": str(f["text"]), "category": str(f.get("category", "UNKNOWN"))}
        for f in findings if f.get("text")
    ]


# ─────────────────────────────────────────────
# Step 3: Python finds exact coordinates
# ─────────────────────────────────────────────

def find_text_coords(pdf_path: str, findings: list[dict]) -> list[dict]:
    """
    Returns redaction dicts including text and category for the report.
    """
    redactions = []

    # Build a lookup: text → category
    category_map = {f["text"]: f["category"] for f in findings}
    texts = list(category_map.keys())

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=False)

            for text in texts:
                pattern = r"\s+".join(re.escape(t) for t in text.split())
                for match in re.finditer(pattern, page_text, re.IGNORECASE):
                    matched_words = find_words_in_span(page_text, words, match.start(), match.end())
                    if matched_words:
                        redactions.append({
                            "page_number": page_num,
                            "x0": min(w["x0"]    for w in matched_words) - 2,
                            "y0": min(w["top"]    for w in matched_words) - 2,
                            "x1": max(w["x1"]     for w in matched_words) + 2,
                            "y1": max(w["bottom"] for w in matched_words) + 2,
                            "text":     text,
                            "category": category_map[text]
                        })

    return redactions


def find_words_in_span(page_text: str, words: list, start: int, end: int) -> list:
    matched, cursor = [], 0
    for word in words:
        idx = page_text.find(word["text"], cursor)
        if idx == -1:
            continue
        word_end = idx + len(word["text"])
        cursor = word_end
        if word_end > start and idx < end:
            matched.append(word)
    return matched


# ─────────────────────────────────────────────
# Step 4: Draw permanent black boxes
# ─────────────────────────────────────────────

def apply_black_boxes(pdf_path: str, redactions: list, output_path: str) -> dict:
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
            page.add_redact_annot(fitz.Rect(r["x0"], r["y0"], r["x1"], r["y1"]),
                                  fill=(0, 0, 0), cross_out=False)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                               graphics=fitz.PDF_REDACT_LINE_ART_NONE)
        pages_affected.add(page_idx + 1)

    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()

    return {
        "success": True,
        "output_path": output_path,
        "total_redactions": len(redactions),
        "pages_affected": sorted(pages_affected)
    }


# ─────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────

CATEGORY_LABELS = {
    "PII_NAME":     "Personal Name",
    "SSN":          "Social Security Number",
    "DOB":          "Date of Birth",
    "ADDRESS":      "Address",
    "PHONE":        "Phone Number",
    "EMAIL":        "Email Address",
    "MEDICAL":      "Medical Information",
    "FINANCIAL":    "Financial Data",
    "CONFIDENTIAL": "Confidential / Proprietary",
    "UNKNOWN":      "Uncategorised",
}

def generate_report(pdf_path: str, findings: list[dict], redactions: list[dict], output_path: str) -> str:
    pages        = sorted(set(r["page_number"] for r in redactions))
    found_texts  = set(r["text"] for r in redactions)
    unmatched    = [f for f in findings if f["text"] not in found_texts]

    # Count boxes per category
    boxes_by_cat = defaultdict(int)
    for r in redactions:
        boxes_by_cat[r["category"]] += 1

    # Unique texts per category
    texts_by_cat = defaultdict(set)
    for f in findings:
        texts_by_cat[f["category"]].add(f["text"])

    report  = "==========================================\n"
    report += "       BLACK-MARKER REDACTION REPORT\n"
    report += "==========================================\n"
    report += f"Document : {Path(pdf_path).name}\n"
    report += f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"Model    : {MODEL}\n\n"

    report += "SUMMARY\n"
    report += "-------\n"
    report += f"Unique sensitive strings : {len(findings)}\n"
    report += f"Redaction boxes applied  : {len(redactions)}\n"
    report += f"Pages affected           : {', '.join(map(str, pages))}\n"
    report += f"Output file              : {Path(output_path).name}\n\n"

    report += "REDACTIONS BY CATEGORY\n"
    report += "----------------------\n"
    report += f"{'Category':<30} {'Strings':>8}  {'Boxes':>6}\n"
    report += f"{'-'*30}  {'-'*8}  {'-'*6}\n"
    for cat in sorted(boxes_by_cat.keys()):
        label   = CATEGORY_LABELS.get(cat, cat)
        strings = len(texts_by_cat[cat])
        boxes   = boxes_by_cat[cat]
        report += f"{label:<30} {strings:>8}  {boxes:>6}\n"

    if unmatched:
        report += f"\nUNMATCHED ({len(unmatched)} — manual review required)\n"
        report += "-" * 44 + "\n"
        for f in unmatched:
            label = CATEGORY_LABELS.get(f["category"], f["category"])
            report += f"  [{label}]  text not found in text layer\n"
        report += "These may exist in scanned/image regions.\n"

    report += "\n==========================================\n"
    report += "Original file NOT placed in /output.\n"
    report += "Only the redacted copy exists.\n"
    report += "==========================================\n"

    with open("output/redaction_report.txt", "w") as fh:
        fh.write(report)

    return report


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def redact(pdf_path: str):
    print(f"\n[BLACK-MARKER] Initiating redaction: {pdf_path}")
    print(f"[BLACK-MARKER] Model: {MODEL}")
    print("=" * 50)

    print("[1/4] Extracting raw text from PDF...")
    raw_text = extract_text(pdf_path)
    print(f"      ✓ {len(raw_text)} chars extracted")

    print("[2/4] Hunting for PII and confidential data...")
    findings = hunt_for_pii(raw_text)
    print(f"      ✓ {len(findings)} sensitive string(s) identified:")
    for f in findings:
        print(f"        • [{f['category']}] [REDACTED]")

    if not findings:
        print("\n[BLACK-MARKER] No sensitive data detected.")
        return

    print("[3/4] Searching PDF for exact text locations...")
    redactions = find_text_coords(pdf_path, findings)
    found_texts = set(r["text"] for r in redactions)
    unmatched_count = len([f for f in findings if f["text"] not in found_texts])
    print(f"      ✓ {len(redactions)} location(s) found, {unmatched_count} unmatched")

    stem = Path(pdf_path).stem
    output_path = f"output/{stem}_REDACTED.pdf"
    print(f"[4/4] Applying permanent black-box redactions → {output_path}")
    result = apply_black_boxes(pdf_path, redactions, output_path)
    print(f"      ✓ {result['total_redactions']} box(es) across page(s) {result['pages_affected']}")

    report = generate_report(pdf_path, findings, redactions, output_path)
    print("\n" + "=" * 50)
    print(report)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py <path_to_pdf>")
        sys.exit(1)
    os.makedirs("output", exist_ok=True)
    redact(sys.argv[1])