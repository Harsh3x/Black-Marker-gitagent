#!/bin/bash
# Tool: finalize_redactions
# Parses pdf_path from gitclaw JSON stdin, calls finalize_redactions.py

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

PDF_PATH=$(cat /dev/stdin | python3 -c "import sys,json; print(json.load(sys.stdin)['pdf_path'])")

cd "$AGENT_DIR"
mkdir -p output

python3 finalize_redactions.py "$PDF_PATH"

STEM=$(basename "$PDF_PATH" .pdf | sed 's/_FOR_REVIEW//')
OUTPUT="$AGENT_DIR/output/${STEM}_FINAL_REDACTED.pdf"

python3 -c "
import json, os
output = '$OUTPUT'
print(json.dumps({
    'output_path': output,
    'exists': os.path.exists(output)
}))
"