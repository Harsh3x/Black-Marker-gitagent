# Black-Marker : GitAgent

**An Autonomous, Human-in-the-Loop Legal Redaction Agent.**

Black-Marker is an enterprise-grade AI agent built on the GitAgent/GitClaw framework. It acts as an ultra-paranoid, risk-averse legal clerk designed to prevent data leaks by autonomously hunting down and redacting Personally Identifiable Information (PII) and confidential data from PDF documents.

## The Problem
Manual document redaction is slow, expensive, and prone to human error. However, handing full, destructive control of legal or medical documents over to a fully autonomous LLM is dangerous. 


## 💡 The Solution
Black-Marker bridges the gap using a **Human-in-the-Loop (HITL) architecture** and a strict **Separation of Concerns**:
1. **Semantic Reasoning (LLM):** Uses AsyncOpenAI to semantically hunt for PII (Names, SSNs, Medical, Financial, etc.) across the document text.
2. **Deterministic Execution (PyMuPDF):** The LLM does *not* draw the boxes. Once the LLM identifies the target text, deterministic Python code maps the coordinates and draws the boxes, ensuring pixel-perfect accuracy.
3. **The Review Phase:** Before permanently destroying data, the agent generates a `_FOR_REVIEW.pdf` with yellow highlights, allowing a human to verify the redactions. 
4. **The Final Commit:** Once approved, the agent finalizes the document with permanent black boxes and completely scrubs the PDF metadata.


<img width="2816" height="1536" alt="Gemini_Generated_Image_qalz71qalz71qalz" src="https://github.com/user-attachments/assets/77dc2a8a-f720-4512-b5bd-1dd902a01e6d" />


---

##  Architecture & Resilience

```bash
black-marker-agent/
├── agent.yaml                 # Main config (Model: gpt-4.1-mini, tools list, memory settings)
├── SOUL.md                    # Core Identity: "You are an ultra-paranoid legal redaction clerk..." + # Workflow Triggers: "When user says 'Review', run redact-review."
├── RULES.md                   # Strict Constraints: "NEVER output PII. NEVER use cli."
├── .env                       # (Ignored by Git) OPENAI_API_KEY
├── .gitignore                 # Ignore output/ and memory/
│
├── memory/
│   └── MEMORY.md              # GitClaw's persistent memory (auto-generated)
│
├── output/                    # (Local only) Where your PDFs live
│   ├── test_deposition.pdf
│   ├── _FOR_REVIEW.pdf
│   └── _FINAL_REDACTED.pdf
│
├── tools/
│   ├── redact.yaml            # Declarative schema for autonomous redaction
│   ├── redact.sh              # The Bash wrapper for run.py to permaantently redact
│   ├── redact-review.yaml     # Declarative schema for HITL review
│   ├── redact-review.sh       # The Bash wrapper for run.py --review to review redactions
│   ├── finalize-redactions.yaml # Declarative schema for finalizing
│   └── finalize-redactions.sh # The Bash wrapper for finalize_redactions.py to finalize redactions
│
├── scripts/                   # Core Python engines (called by the tools)
│   ├── run.py                 # The PyMuPDF/AsyncOpenAI engine
│   └── finalize_redactions.py # The script that strips highlights & applies black boxes
│
└── skills/                    # Specialized LLM prompts injected based on the compliance flag
    ├── hunt-for-pii/
    │   └── SKILL.md           # The 'full' instructions (maximum redaction, default)
    ├── hunt-for-pii-hipaa/
    │   └── SKILL.md           # The 'hipaa' instructions (18 PHI identifiers)
    ├── hunt-for-pii-gdpr/
    │   └── SKILL.md           # The 'gdpr' instructions (EU Personal + Special Category)
    └── hunt-for-pii-dpdp/
        └── SKILL.md           # The 'dpdp' instructions (India DPDPA + SPDI Rules)

```

Black-Marker isn't just a Python script; it is a suite of custom, highly resilient agent tools (`redact`, `redact-review`, `finalize-redactions`). 

**Key Engineering Features:**
* **Unbreakable Bash Wrappers:** The custom tool wrappers are engineered to survive LLM hallucinations, dropped context windows, and malformed JSON payloads. They utilize `stdin` polling and AI Resilience Fallbacks to ensure the agent never hangs.
* **Metadata Scrubbing:** The finalization step doesn't just draw black boxes; it permanently destroys the underlying text layer and strips all PDF metadata to prevent reverse-engineering.
* **Safe Reporting:** The agent generates text-based redaction reports detailing the *categories* and *frequencies* of redacted data without ever leaking the sensitive data itself into the agent's memory or terminal output.

---

## Quick Start

### Prerequisites
* Python 3.10+
* `gitclaw` / GitAgent framework installed locally.
* An OpenAI API Key.

### Installation
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Harsh3x/Black-Marker-gitagent.git](https://github.com/Harsh3x/Black-Marker-gitagent.git)
   cd Black-Marker-gitagent
   ```

2.**Install Python dependencies:**
  ```bash
  pip install pymupdf openai python-dotenv
  ```

3.Set up your environment variables:
  Create a .env file in the root directory:

  ```bash
  OPENAI_API_KEY=sk-your-openai-api-key
  ```
4.Make the tools executable:
  ```bash
  chmod +x tools/*.sh
  ```
---

## 💻 Usage & Workflow
Start the agent from the root directory:

```bash
gitclaw --dir .
```
### 1. Human-in-the-Loop Workflow (Recommended)
Ask the agent to review a document and specify a compliance framework (`HIPAA`, `GDPR`, `DPDP`, or `Full`). It will hunt for sensitive data specific to that framework and generate a highlighted PDF for your approval.

**You:** *"Review test_deposition.pdf under HIPAA guidelines."*
*(Note: If you forget to specify a framework, Black-Marker will pause and demand that you choose one before proceeding).*

Check the generated `output/test_deposition_HIPAA_FOR_REVIEW.pdf`. Open it in any PDF reader and ensure the yellow highlights cover the correct data. If it looks correct, tell the agent to finalize it.

**You:** *"Looks good, finalize it."*

The agent will strip the yellow highlights, apply permanent black boxes, completely destroy the underlying text, scrub the metadata, and output `output/test_deposition_HIPAA_FINAL_REDACTED.pdf`. The original unredacted file is safely deleted from the output directory.

### 2. Fully Autonomous Redaction
If you trust the agent for standard documents, you can skip the review phase and black out the document immediately based on the selected ruleset.

**You:** *"Redact test_deposition.pdf using GDPR rules."*

The agent will instantly apply the redactions, scrub the metadata, and generate `output/test_deposition_GDPR_REDACTED.pdf`.

---
**All Available Compliance Frameworks:**
* **HIPAA:** Targets US healthcare data (18 PHI identifiers).
* **GDPR:** Targets EU citizen data and special categories.
* **DPDP:** Targets Indian digital personal data and SPDI rules.
* **Full:** Maximum redaction across all frameworks + confidential IP.
---


## License
This project is licensed under the MIT License.


# Built for the GitAgent Hackathon.
