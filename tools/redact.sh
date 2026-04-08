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

python3 run.py "$PDF_PATH" --compliance "$COMPLIANCE"

# Output filename includes compliance tag (except 'full')
STEM=$(basename "$PDF_PATH" .pdf)
if [ "$COMPLIANCE" != "full" ]; then
    COMPLIANCE_TAG="_$(echo $COMPLIANCE | tr '[:lower:]' '[:upper:]')"
else
    COMPLIANCE_TAG=""
fi

OUTPUT="$AGENT_DIR/output/${STEM}${COMPLIANCE_TAG}_REDACTED.pdf"
REPORT="$AGENT_DIR/output/${STEM}_REDACTION_REPORT.txt"

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
