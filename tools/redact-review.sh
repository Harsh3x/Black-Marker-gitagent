#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

# 1. Safely catch the JSON payload without hanging
PAYLOAD=""
if [ ! -t 0 ]; then
    PAYLOAD=$(timeout 1 cat 2>/dev/null)
fi
if [[ "$1" == {* ]]; then
    PAYLOAD="$1"
fi

# 2. Extract variables using the safe JSON parser
PDF_PATH=$(python3 -c "import sys, json; print(json.loads(sys.argv[1]).get('pdf_path', ''))" "$PAYLOAD" 2>/dev/null)
COMPLIANCE=$(python3 -c "import sys, json; print(json.loads(sys.argv[1]).get('compliance', 'full'))" "$PAYLOAD" 2>/dev/null)

# 3. CLI Fallbacks
if [[ "$1" != {* ]]; then
    [ -z "$PDF_PATH" ] && PDF_PATH="${1:-}"
    [ -z "$COMPLIANCE" ] && COMPLIANCE="${2:-full}"
fi
[ -z "$COMPLIANCE" ] || [ "$COMPLIANCE" = "null" ] && COMPLIANCE="full"

cd "$AGENT_DIR"
mkdir -p output

# 4. Auto-detect PDF if GitClaw forgot it
if [ -z "$PDF_PATH" ] || [ "$PDF_PATH" = "null" ]; then
    PDF_PATH=$(ls *.pdf 2>/dev/null | head -n 1)
fi

# 5. Run the Engine in Review mode
python3 run.py "$PDF_PATH" --review --compliance "$COMPLIANCE" > output/redact_review.log 2>&1

# 6. Format filenames exactly as the Python script does
STEM=$(basename "$PDF_PATH" .pdf)
if [ "$COMPLIANCE" != "full" ]; then
    COMPLIANCE_TAG="_$(echo $COMPLIANCE | tr '[:lower:]' '[:upper:]')"
else
    COMPLIANCE_TAG=""
fi

# Fixed the double underscore issue here
OUTPUT="./output/${STEM}${COMPLIANCE_TAG}_FOR_REVIEW.pdf"
REPORT="./output/${STEM}${COMPLIANCE_TAG}_REDACTION_REPORT.txt"

python3 -c "
import json, os
print(json.dumps({
    'output_path': '$OUTPUT',
    'report_path': '$REPORT',
    'exists': os.path.exists('$OUTPUT')
}))
"
