#!/usr/bin/env python3
"""
Tool: extract_pdf_text
Extracts text from a PDF file and outputs it in a structured format for further processing.
"""

import sys
import json
import pdfplumber


def extract_text(pdf_path: str) -> str:
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            full_text += f"\n--- PAGE {i} ---\n{page.extract_text() or ''}\n"
    return full_text



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: extract_pdf_text.py <pdf_path>"}))
        sys.exit(1)

    pdf_path = sys.argv[1]
    try:
        output = extract_text(pdf_path)
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
