#!/bin/bash
# Tool: redact_pdf_review
# Same as redact.sh but passes --review flag

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

PDF_PATH=$(cat /dev/stdin | python3 -c "import sys,json; print(json.load(sys.stdin)['pdf_path'])")

cd "$AGENT_DIR"
mkdir -p output

python3 run.py "$PDF_PATH" --review

STEM=$(basename "$PDF_PATH" .pdf)
OUTPUT="$AGENT_DIR/output/${STEM}_FOR_REVIEW.pdf"
REPORT="$AGENT_DIR/output/redaction_report.txt"

python3 -c "
import json, os
output = '$OUTPUT'
report = '$REPORT'
print(json.dumps({
    'output_path': output,
    'report_path': report,
    'exists': os.path.exists(output)
}))
"