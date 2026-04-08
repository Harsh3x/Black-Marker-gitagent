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

# CLI Fallback
if [[ "$1" != {* ]] && [ -z "$PDF_PATH" ]; then
    PDF_PATH="$1"
fi

cd "$AGENT_DIR"

# 3. Fallback: If GitClaw passes a bad/empty path, grab the actual review file
if [ -z "$PDF_PATH" ] || [ ! -f "$PDF_PATH" ]; then
    PDF_PATH=$(ls output/*_FOR_REVIEW.pdf 2>/dev/null | head -n 1)
fi

# 4. SAFETY CHECK: If it STILL doesn't exist, abort gracefully!
if [ -z "$PDF_PATH" ] || [ ! -f "$PDF_PATH" ]; then
    echo "{\"output_path\": \"\", \"report_path\": \"\", \"exists\": false, \"error\": \"No _FOR_REVIEW.pdf file found. You must run redact-review first.\"}"
    exit 0
fi

mkdir -p output
python3 finalize_redactions.py "$PDF_PATH" > output/finalize_error.log 2>&1

# 5. Format filenames exactly as the Python script does
STEM=$(basename "$PDF_PATH" .pdf)
CLEAN_STEM=${STEM/_FOR_REVIEW/}

OUTPUT="./output/${CLEAN_STEM}_FINAL_REDACTED.pdf"
REPORT="./output/${CLEAN_STEM}_REDACTION_REPORT.txt"

# 6. CLEANUP PHASE: Destroy originals and logs if the final file exists
if [ -f "$OUTPUT" ]; then
    # Delete the yellow-highlighted review file
    rm -f "$PDF_PATH" 
    
    # Delete the error log
    rm -f output/finalize_error.log 
    
    # Strip compliance tags to find and destroy the original unredacted source PDF
    ORIGINAL_BASE=$(echo "$CLEAN_STEM" | sed -E 's/_(HIPAA|GDPR|DPDP)$//')
    rm -f "./${ORIGINAL_BASE}.pdf"
fi

# 7. Return JSON to GitClaw
python3 -c "
import json, os
print(json.dumps({
    'output_path': '$OUTPUT',
    'report_path': '$REPORT',
    'exists': os.path.exists('$OUTPUT')
}))
"
