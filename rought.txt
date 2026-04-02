
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

# 1. Safely grab input from either an argument or stdin
if [ -n "$1" ]; then
    INPUT="$1"
else
    INPUT=$(timeout 1 cat /dev/stdin)
fi

# 2. Bulletproof Python JSON parsing (strips whitespace and catches errors)
PDF_PATH=$(python3 -c "
import sys, json
raw = sys.argv[1].strip()
try:
    print(json.loads(raw).get('pdf_path', raw))
except Exception:
    print(raw)
" "$INPUT")

# 3. GitClaw Environment Variable Fallback
if [ -z "$PDF_PATH" ] || [ "$PDF_PATH" == "null" ]; then
    PDF_PATH="$pdf_path"
fi

# 4. Write exactly what happened to the log file for debugging
echo "--- NEW RUN ---" > redact.log
echo "RAW INPUT: '$INPUT'" >> redact.log
echo "ENV VAR: '$pdf_path'" >> redact.log
echo "FINAL PDF_PATH: '$PDF_PATH'" >> redact.log

cd "$AGENT_DIR"
mkdir -p output

# 5. Run the engine
python3 run.py "$PDF_PATH" >> redact.log 2>&1

# 6. Format the output
STEM=$(basename "$PDF_PATH" .pdf)
OUTPUT="$AGENT_DIR/output/${STEM}_REDACTED.pdf"
REPORT="$AGENT_DIR/output/redaction_report.txt"

python3 -c "import json, os; print(json.dumps({'output_path': '${OUTPUT}', 'report_path': '${REPORT}', 'exists': os.path.exists('${OUTPUT}')}))"
EOF
