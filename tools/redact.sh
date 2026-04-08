#!/bin/bash
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

# Use absolute path so log is always written regardless of working dir
LOG="$AGENT_DIR/output/redact.log"

{
    echo "========================================"
    echo "Timestamp : $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "PDF       : $PDF_PATH"
    echo "Compliance: $COMPLIANCE"
    echo "----------------------------------------"
} >> "$LOG"

# Run python — capture exit code even if it fails, don't let set -e kill us
set -o pipefail
python3 run.py "$PDF_PATH" --compliance "$COMPLIANCE" 2>&1 | tee -a "$LOG"
EXIT_STATUS=${PIPESTATUS[0]}

STEM=$(basename "$PDF_PATH" .pdf)
if [ "$COMPLIANCE" != "full" ]; then
    COMPLIANCE_TAG="_$(echo $COMPLIANCE | tr '[:lower:]' '[:upper:]')"
else
    COMPLIANCE_TAG=""
fi

OUTPUT="$AGENT_DIR/output/${STEM}${COMPLIANCE_TAG}_REDACTED.pdf"
REPORT="$AGENT_DIR/output/${STEM}_REDACTION_REPORT.txt"

{
    echo "Exit code : $EXIT_STATUS"
    echo "Output    : $OUTPUT"
    echo "========================================"
    echo ""
} >> "$LOG"

python3 -c "
import json, os
print(json.dumps({
    'output_path': '$OUTPUT',
    'report_path': '$REPORT',
    'exists': os.path.exists('$OUTPUT')
}))
"

exit $EXIT_STATUS
