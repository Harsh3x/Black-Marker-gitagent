#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

# Read both pdf_path and compliance from gitclaw JSON stdin
INPUT=$(cat /dev/stdin)

PDF_PATH=$(python3 -c "
import sys, json
raw = '''$INPUT'''.strip()
path = ''
if raw:
    try: path = json.loads(raw).get('pdf_path', '')
    except: path = raw
print(path.strip())
")

COMPLIANCE=$(python3 -c "
import sys, json
raw = '''$INPUT'''.strip()
compliance = 'full'
if raw:
    try: compliance = json.loads(raw).get('compliance', 'full')
    except: pass
print(compliance.strip())
")

cd "$AGENT_DIR"

# Fallback: if no path given, use first PDF in current dir
if [ -z "$PDF_PATH" ] || [ "$PDF_PATH" = "null" ]; then
    PDF_PATH=$(ls *.pdf 2>/dev/null | head -n 1)
fi

mkdir -p output

python3 run.py "$PDF_PATH" --review --compliance "$COMPLIANCE" > output/redact_review.log 2>&1

# Review mode always outputs _FOR_REVIEW.pdf (no compliance tag — not yet redacted)
STEM=$(basename "$PDF_PATH" .pdf)
OUTPUT="./output/${STEM}_FOR_REVIEW.pdf"
REPORT="./output/${STEM}_REDACTION_REPORT.txt"

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
