#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

TMPFILE=$(mktemp)
cat /dev/stdin > "$TMPFILE"

PDF_PATH=$(python3 - "$TMPFILE" << 'PYEOF'
import sys, json
try:
    raw = open(sys.argv[1]).read().strip()
    print(json.loads(raw).get('pdf_path', ''))
except:
    print('')
PYEOF
)

COMPLIANCE=$(python3 - "$TMPFILE" << 'PYEOF'
import sys, json
try:
    raw = open(sys.argv[1]).read().strip()
    print(json.loads(raw).get('compliance', 'full') or 'full')
except:
    print('full')
PYEOF
)

rm -f "$TMPFILE"

[ -z "$PDF_PATH" ] || [ "$PDF_PATH" = "null" ] && PDF_PATH=$(ls *.pdf 2>/dev/null | head -n 1)
[ -z "$COMPLIANCE" ] || [ "$COMPLIANCE" = "null" ] && COMPLIANCE="full"

cd "$AGENT_DIR"
mkdir -p output

python3 run.py "$PDF_PATH" --review --compliance "$COMPLIANCE" > output/redact_review.log 2>&1

if [ "$COMPLIANCE" != "full" ]; then
    COMPLIANCE_TAG="_$(echo $COMPLIANCE | tr '[:lower:]' '[:upper:]')"
else
    COMPLIANCE_TAG=""
fi

STEM=$(basename "$PDF_PATH" .pdf)
OUTPUT="./output/${STEM}_${COMPLIANCE_TAG}_FOR_REVIEW.pdf"
REPORT="./output/${STEM}_${COMPLIANCE_TAG}_REDACTION_REPORT.txt"

python3 -c "
import json, os
print(json.dumps({
    'output_path': '$OUTPUT',
    'report_path': '$REPORT',
    'exists': os.path.exists('$OUTPUT')
}))
"
