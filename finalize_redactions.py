#!/usr/bin/env python3
"""
Black-Marker: Finalizer Script
Takes a PDF that has been reviewed by a human (containing highlight/redaction annotations),
converts all user-approved annotations into permanent black redaction boxes, and scrubs metadata.
"""

import fitz  # PyMuPDF
import sys
import os
from pathlib import Path

def finalize_pdf(pdf_path: str):
    print(f"\n[BLACK-MARKER] Finalizing Reviewed PDF: {pdf_path}")
    print("=" * 50)
    
    doc = fitz.open(pdf_path)
    total_redactions = 0
    pages_affected = set()

    print("[1/3] Scanning for human-approved annotations...")
    
    for page_num, page in enumerate(doc, start=1):
        rects_to_redact = []
        
        # 1. Gather all highlight or box annotations on the page
        for annot in page.annots():
            # Support Highlight, Square/Rectangle, or Draft Redaction annotations
            if annot.type[0] in (fitz.PDF_ANNOT_HIGHLIGHT, fitz.PDF_ANNOT_SQUARE, fitz.PDF_ANNOT_REDACT):
                rects_to_redact.append(annot.rect)
                # Delete the original annotation so it doesn't leave a ghost color behind
                page.delete_annot(annot)
        
        # 2. Draw official permanent redaction boxes over those areas
        if rects_to_redact:
            for rect in rects_to_redact:
                page.add_redact_annot(rect, fill=(0, 0, 0), cross_out=False)
                total_redactions += 1
            
            # 3. Apply the permanent destruction of text
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
            pages_affected.add(page_num)

    # Determine Output Name
    stem = Path(pdf_path).stem.replace("_FOR_REVIEW", "")
    output_path = f"output/{stem}_FINAL_REDACTED.pdf"

    print(f"[2/3] Destroying text data and applying black boxes...")
    print(f"[3/3] Scrubbing document metadata...")
    doc.set_metadata({})
    
    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()

    print("\n" + "=" * 50)
    print("      SUCCESS!")
    print(f"      ✓ Converted {total_redactions} human-approved highlights to black boxes.")
    print(f"      ✓ Pages affected: {sorted(pages_affected)}")
    print(f"      ✓ Saved permanent copy to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python finalize_redactions.py <path_to_reviewed_pdf>")
        sys.exit(1)
        
    os.makedirs("output", exist_ok=True)
    finalize_pdf(sys.argv[1])