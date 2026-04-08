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
    print(json.loads(raw).get('compliance') or 'full')
except:
    print('full')
PYEOF
)

rm -f "$TMPFILE"

[ -z "$PDF_PATH" ] || [ "$PDF_PATH" = "null" ] && PDF_PATH=$(ls *.pdf 2>/dev/null | head -n 1)
[ -z "$COMPLIANCE" ] || [ "$COMPLIANCE" = "null" ] && COMPLIANCE="full"

cd "$AGENT_DIR"
mkdir -p output

LOG="output/redact.log"
echo "========================================" >> "$LOG"
echo "Timestamp : $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "$LOG"
echo "PDF       : $PDF_PATH" >> "$LOG"
echo "Compliance: $COMPLIANCE" >> "$LOG"
echo "----------------------------------------" >> "$LOG"

python3 run.py "$PDF_PATH" --compliance "$COMPLIANCE" 2>&1 | tee -a "$LOG"

STEM=$(basename "$PDF_PATH" .pdf)
if [ "$COMPLIANCE" != "full" ]; then
    COMPLIANCE_TAG="_$(echo $COMPLIANCE | tr '[:lower:]' '[:upper:]')"
else
    COMPLIANCE_TAG=""
fi

OUTPUT="$AGENT_DIR/output/${STEM}${COMPLIANCE_TAG}_REDACTED.pdf"
REPORT="$AGENT_DIR/output/${STEM}_REDACTION_REPORT.txt"

EXIT_STATUS=$?
echo "Exit code : $EXIT_STATUS" >> "$LOG"
echo "Output    : $OUTPUT" >> "$LOG"
echo "========================================" >> "$LOG"

python3 -c "
import json, os
print(json.dumps({
    'output_path': '$OUTPUT',
    'report_path': '$REPORT',
    'exists': os.path.exists('$OUTPUT')
}))
"
