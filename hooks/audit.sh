#!/bin/bash
# Hook: pre_tool_use audit logger
# Runs before every tool call — logs invocation without logging sensitive data

AUDIT_FILE="$(dirname "$0")/../memory/audit.jsonl"
mkdir -p "$(dirname "$AUDIT_FILE")"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TOOL_NAME="${GITCLAW_TOOL_NAME:-unknown}"
SESSION_ID="${GITCLAW_SESSION_ID:-unknown}"

# Log tool name + timestamp only — never the actual PDF content or findings
echo "{\"timestamp\": \"$TIMESTAMP\", \"tool\": \"$TOOL_NAME\", \"session\": \"$SESSION_ID\", \"event\": \"pre_tool_use\"}" >> "$AUDIT_FILE"

exit 0  # Always allow — this is logging only
