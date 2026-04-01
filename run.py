#!/usr/bin/env python3
"""
Black-Marker: Autonomous PDF Redaction Engine (Async Version)
  1. Extract text page-by-page using PyMuPDF (fitz)
  2. Concurrently query LLM per page using AsyncOpenAI
  3. PyMuPDF searches for exact text strings -> coordinates
  4. PyMuPDF draws permanent black boxes & scrubs metadata
  5. Report shows category breakdown
"""

import sys
import json
import re
import os
import asyncio
from openai import AsyncOpenAI
from pathlib import Path
from collections import defaultdict
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

import fitz  # PyMuPDF

# Load system prompts (Make sure these files exist in your directory)
SOUL       = open("./SOUL.md").read()
RULES      = open("./RULES.md").read()
HUNT_SKILL = open("./skills/hunt-for-pii/SKILL.md").read()


api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("[ERROR] OPENAI_API_KEY not set. Run: export OPENAI_API_KEY=sk-...")
    sys.exit(1)

client = AsyncOpenAI(api_key=api_key)
MODEL  = "gpt-4o-mini"
CONCURRENCY_LIMIT = 5 # Max simultaneous page requests to OpenAI


# ─────────────────────────────────────────────
# Step 2: LLM identifies text + categories (Async)
# ─────────────────────────────────────────────

async def hunt_for_pii_on_page(page_text: str, page_num: int, semaphore: asyncio.Semaphore) -> list[dict]:
    """
    Analyzes a single page for PII concurrently.
    Returns a list of {"text": "...", "category": "..."}.
    """
    if not page_text.strip():
        return []

    system = f"{SOUL}\n\n{RULES}"

    user = f"""
{HUNT_SKILL}

Here is the text for PAGE {page_num} of the document:

{page_text}

Return a JSON object with a single key "findings" containing an array of objects.
Each object must have exactly two fields:
  - "text": the EXACT string as it appears in the document
  - "category": one of PII_NAME | SSN | DOB | ADDRESS | PHONE | EMAIL | MEDICAL | FINANCIAL | CONFIDENTIAL

Deduplicate — include each unique text string once only.

Example expected output:
{{
  "findings": [
    {{"text": "John Doe", "category": "PII_NAME"}},
    {{"text": "523-88-4471", "category": "SSN"}}
  ]
}}
"""
    # Use semaphore to limit concurrent requests and avoid rate limits
    async with semaphore:
        try:
            response = await client.chat.completions.create(
                model=MODEL,
                max_tokens=2048,
                response_format={ "type": "json_object" }, # Forces pure JSON output
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user}
                ]
            )
            raw = response.choices[0].message.content
            findings = json.loads(raw).get("findings", [])
            
            # Attach page number for debugging/reporting context
            for f in findings:
                f["page_num"] = page_num
                
            return findings
        
        except Exception as e:
            print(f"      [!] Error processing page {page_num}: {e}")
            return []


async def process_document_async(pdf_path: str) -> list[dict]:
    """
    Extracts text page-by-page and runs them through the LLM concurrently.
    """
    doc = fitz.open(pdf_path)
    tasks = []
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    print(f"      ✓ Loaded PDF with {len(doc)} pages")

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        tasks.append(hunt_for_pii_on_page(text, page_num, semaphore))
        
    doc.close()

    # Wait for all pages to finish processing
    results = await asyncio.gather(*tasks)
    
    # Flatten results and deduplicate
    all_findings = []
    seen = set()
    
    for page_findings in results:
        for f in page_findings:
            if not f.get("text"): 
                continue
                
            text = str(f["text"])
            category = str(f.get("category", "UNKNOWN"))
            
            identifier = (text, category)
            if identifier not in seen:
                seen.add(identifier)
                all_findings.append({"text": text, "category": category})
                
    return all_findings


# ─────────────────────────────────────────────
# Step 3: Python finds exact coordinates
# ─────────────────────────────────────────────


def normalize_word(w: str) -> str:
    """Removes punctuation and makes lowercase for bulletproof comparison"""
    return re.sub(r'[^a-zA-Z0-9]', '', w).lower()


def find_text_coords_fitz(pdf_path: str, findings: list[dict]) -> list[dict]:
    redactions = []
    doc = fitz.open(pdf_path)

    for page_num, page in enumerate(doc, start=1):
        page_words = page.get_text("words")
        
        # Pre-process words: ignore punctuation-only blocks and standardize text
        clean_page_words = []
        for w in page_words:
            norm = normalize_word(w[4])
            if norm:
                clean_page_words.append((norm, w))

        for finding in findings:
            text = finding["text"]
            category = finding["category"]
            
            # ATTEMPT 1: Native Search (Fast, works for single unbroken lines)
            instances = page.search_for(text)
            if instances:
                for inst in instances:
                    redactions.append({
                        "page_number": page_num,
                        "x0": inst.x0, "y0": inst.y0, "x1": inst.x1, "y1": inst.y1,
                        "text": text, "category": category
                    })
                continue
            
            # ATTEMPT 2: Fuzzy Word-Sequence Matcher 
            # (Catches line breaks & intruding line numbers like "25")
            target_words = [normalize_word(w) for w in text.split()]
            target_words = [w for w in target_words if w] 
            
            if not target_words:
                continue

            i = 0
            while i < len(clean_page_words):
                # If we find the first word, start tracking the sequence
                if clean_page_words[i][0] == target_words[0]:
                    match_rects = []
                    p_idx = i
                    t_idx = 0
                    skips = 0

                    while p_idx < len(clean_page_words) and t_idx < len(target_words):
                        if clean_page_words[p_idx][0] == target_words[t_idx]:
                            # Word matches! Add to redaction list
                            match_rects.append(clean_page_words[p_idx][1])
                            t_idx += 1
                            skips = 0  # Reset skip counter
                        else:
                            # Artifact detected (e.g. Line number 25). Skip it.
                            skips += 1
                            if skips > 4: # Allow up to 4 intruding artifacts between target words
                                break
                        p_idx += 1
                    
                    if t_idx == len(target_words):
                        # Success! We found the sequence despite interruptions.
                        for w_rect in match_rects:
                            redactions.append({
                                "page_number": page_num,
                                "x0": w_rect[0], "y0": w_rect[1], "x1": w_rect[2], "y1": w_rect[3],
                                "text": text, "category": category
                            })
                        i = p_idx - 1 # Fast forward past the matched phrase
                i += 1
                    
    doc.close()
    return redactions



# ─────────────────────────────────────────────
# Step 4: Draw permanent black boxes & Scrub Metadata
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
             # FIX: Shrink the bounding box to prevent eating adjacent lines
            height = r["y1"] - r["y0"]
            width = r["x1"] - r["x0"]
            
            # 15% vertical reduction on top and bottom avoids line-spacing bleeds
            margin_y = height * 0.18
            # 1% horizontal reduction avoids eating commas/periods next to the redacted word
            margin_x = width * 0.01  
            
            rect = fitz.Rect(
                r["x0"] + margin_x, 
                r["y0"] + margin_y, 
                r["x1"] - margin_x, 
                r["y1"] - margin_y
            )

            page.add_redact_annot(rect, fill=(0, 0, 0), cross_out=False)
            
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
        pages_affected.add(page_idx + 1)

    # SECURE: Scrub document metadata (Author, title, etc.) to prevent hidden PII leaks
    doc.set_metadata({}) 

    # Save completely clean document
    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()

    return {
        "success": True,
        "output_path": output_path,
        "total_redactions": len(redactions),
        "pages_affected": sorted(pages_affected)
    }


# ─────────────────────────────────────────────
# Report Generation
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

    boxes_by_cat = defaultdict(int)
    for r in redactions:
        boxes_by_cat[r["category"]] += 1

    texts_by_cat = defaultdict(set)
    for f in findings:
        texts_by_cat[f["category"]].add(f["text"])

    report  = "==========================================\n"
    report += "       BLACK-MARKER REDACTION REPORT\n"
    report += "==========================================\n"
    report += f"Document : {Path(pdf_path).name}\n"
    report += f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"Model    : {MODEL} (Async)\n\n"

    report += "SUMMARY\n"
    report += "-------\n"
    report += f"Unique sensitive strings : {len(findings)}\n"
    report += f"Redaction boxes applied  : {len(redactions)}\n"
    report += f"Pages affected           : {', '.join(map(str, pages)) if pages else 'None'}\n"
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
            report += f"  [{label}]  {f['text']}\n"
        report += "These may exist in scanned/image regions or span across line-breaks.\n"

    report += "\n==========================================\n"
    report += "Original file NOT placed in /output.\n"
    report += "Metadata scrubbed. Only the redacted copy exists.\n"
    report += "==========================================\n"

    with open("output/redaction_report.txt", "w") as fh:
        fh.write(report)

    return report


# ─────────────────────────────────────────────
# Main Async Orchestrator
# ─────────────────────────────────────────────

async def redact_async(pdf_path: str):
    print(f"\n[BLACK-MARKER] Initiating async redaction: {pdf_path}")
    print(f"[BLACK-MARKER] Model: {MODEL}")
    print("=" * 50)

    print("[1/4] Extracting text & Hunting for PII concurrently...")
    findings = await process_document_async(pdf_path)
    
    print(f"      ✓ {len(findings)} sensitive string(s) identified")
    for f in findings:
        print(f"        • [{f['text']}] [{f['category']}] [REDACTED]")

    if not findings:
        print("\n[BLACK-MARKER] No sensitive data detected.")
        return

    print("\n[2/4] Searching PDF for exact text locations...")
    redactions = find_text_coords_fitz(pdf_path, findings)
    found_texts = set(r["text"] for r in redactions)
    unmatched_count = len([f for f in findings if f["text"] not in found_texts])
    print(f"      ✓ {len(redactions)} location(s) found, {unmatched_count} unmatched")

    stem = Path(pdf_path).stem
    output_path = f"output/{stem}_REDACTED.pdf"
    print(f"\n[3/4] Applying permanent black-box redactions & scrubbing metadata...")
    result = apply_black_boxes(pdf_path, redactions, output_path)
    print(f"      ✓ {result['total_redactions']} box(es) across page(s) {result['pages_affected']} -> {output_path}")

    print("\n[4/4] Generating Report...")
    report = generate_report(pdf_path, findings, redactions, output_path)
    print("\n" + "=" * 50)
    print(report)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_async.py <path_to_pdf>")
        sys.exit(1)
        
    os.makedirs("output", exist_ok=True)
    
    # Run the async event loop
    asyncio.run(redact_async(sys.argv[1]))