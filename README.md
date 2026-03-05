# Legal Document Triage Assistant

An AI-powered document triage system built for a District Attorney's office. Upload legal PDFs and instantly get document classification, plain-English summaries, and extracted entities — all powered by a local LLM with no data leaving your machine.

---

## What It Does (For Non-Technical Readers)

This tool helps legal professionals quickly understand what a document is and what it contains, without reading every page.

**Upload a PDF and get:**

1. **Document Classification** — Is this a warrant, complaint, police report, subpoena, or something else? The system tells you with a confidence score.

2. **Plain-English Summary** — A 3-6 sentence summary of the document's key facts: who's involved, what happened, when, where, and what legal action is being taken.

3. **Extracted Entities** — Automatically pulls out:
   - Names of people (officers, defendants, witnesses, judges)
   - Dates (incident dates, filing dates, hearing dates)
   - Locations (addresses, cities, courts)
   - Offenses (crimes, charges, statute numbers)

4. **Batch Processing** — Upload multiple documents at once. Get a summary table showing all results at a glance, then drill into any document for details.

5. **History & Recall** — Every processed document is saved. Click any past result in the sidebar to instantly see its classification, summary, and entities again — no re-processing needed.

6. **Export Options:**
   - **PDF Report** — Download a formatted triage report for any document (current or past)
   - **CSV Export** — Download the full history as a spreadsheet for record-keeping or analysis

7. **Analytics Dashboard** *(coming soon)* — Charts showing document type distribution, confidence trends, most frequent entities, and processing timeline.

**Privacy:** Everything runs locally on your machine. The AI model (Llama 3) runs through Ollama — no data is sent to external servers. Supabase is used for persistent storage only.

---

## Tech Stack (For Technical Readers)

| Component       | Technology                     | Purpose                                |
|-----------------|--------------------------------|----------------------------------------|
| Frontend        | Streamlit                      | Web UI with file upload, display, export |
| LLM             | Ollama + Llama 3 (local)       | Classification, summarization, entity extraction |
| PDF Parsing     | pdfplumber                     | Text extraction from PDF files         |
| Database        | Supabase (PostgreSQL)          | Persistent storage, history, analytics |
| PDF Reports     | fpdf2                          | Generate downloadable triage reports   |
| HTTP Client     | requests                       | Communicate with Ollama REST API       |

**Key architectural decisions:**
- All LLM calls use Ollama's `format: "json"` parameter for reliable structured output
- `temperature: 0.0` for deterministic, reproducible results
- Defensive error handling throughout — functions return error dicts, never raise exceptions
- Session state caching prevents re-processing on Streamlit reruns

---

## Document Types

| Category        | Description                                              |
|-----------------|----------------------------------------------------------|
| `warrant`       | Authorizes law enforcement to search, seize, or arrest   |
| `complaint`     | Formal document initiating a criminal case               |
| `police_report` | Law enforcement report of an incident or investigation   |
| `subpoena`      | Legal order to testify or produce documents              |
| `other`         | Anything that doesn't fit the above                      |

---

## Project Structure

```
legal-triage-assistant/
├── app.py                          # Streamlit frontend (upload, display, export)
├── pipeline/
│   ├── classifier.py               # Document classification via Ollama
│   ├── summarizer.py               # Document summarization via Ollama
│   ├── extractor.py                # Entity extraction via Ollama
│   └── pdf_reader.py               # PDF text extraction via pdfplumber
├── db/
│   └── supabase_client.py          # Supabase save, fetch, history
├── export/
│   ├── csv_export.py               # History → CSV string
│   └── pdf_report.py               # Single result → PDF bytes
├── pages/
│   └── analytics.py                # Analytics dashboard (coming soon)
├── prompts/
│   ├── triage_prompt.txt           # Classification prompt template
│   ├── extract_prompt.txt          # Entity extraction prompt template
│   └── summary_prompt.txt          # Summarization prompt template
├── sample_docs/
│   ├── sample_warrant.pdf          # Sample search warrant
│   ├── sample_complaint.pdf        # Sample criminal complaint
│   └── sample_police_report.pdf    # Sample police incident report
├── .env.example                    # Environment variable template
├── .gitignore                      # Protects .env from commits
├── requirements.txt                # Python dependencies
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed with Llama 3 pulled
- A [Supabase](https://supabase.com/) project (free tier works)

### Installation

```bash
# 1. Clone the repo
git clone <repo-url>
cd legal-triage-assistant

# 2. Install dependencies
pip install -r requirements.txt

# 3. Make sure Ollama is running with Llama 3
ollama pull llama3
ollama serve   # skip if already running

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your Supabase URL and anon key

# 5. Create the database table (run in Supabase SQL Editor)
```

```sql
CREATE TABLE IF NOT EXISTS triage_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    filename TEXT NOT NULL,
    classification TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    reasoning TEXT,
    summary TEXT DEFAULT '',
    persons TEXT[] DEFAULT ARRAY[]::TEXT[],
    dates TEXT[] DEFAULT ARRAY[]::TEXT[],
    locations TEXT[] DEFAULT ARRAY[]::TEXT[],
    offenses TEXT[] DEFAULT ARRAY[]::TEXT[],
    raw_text TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable Row Level Security with open access
ALTER TABLE triage_results ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all operations" ON triage_results
    FOR ALL USING (true) WITH CHECK (true);
```

### Run the App

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

### Quick Test (CLI)

```bash
# Test each pipeline module individually
python pipeline/classifier.py        # Classifies a sample warrant
python pipeline/extractor.py         # Extracts entities from a sample warrant
python pipeline/summarizer.py        # Summarizes a sample warrant
python pipeline/pdf_reader.py sample_docs/sample_warrant.pdf  # Extracts PDF text
```

---

## Features in Detail

### Single Document Upload
Upload one PDF → see classification, summary, and entities displayed directly on the page. Results are auto-saved to Supabase.

### Batch Upload
Upload multiple PDFs → progress bar tracks processing → summary table shows all results at a glance → click any document's expander to see full details.

### Clickable History
The sidebar shows the 10 most recent results as buttons. Click any one to instantly display its stored classification, summary, and entities from Supabase — no re-processing.

### PDF Report Download
A "Download PDF Report" button appears after each document's results (including past results from history). Generates a formatted report with classification, summary, and all extracted entities.

### CSV Export
An "Export History as CSV" button in the sidebar downloads all recent results as a spreadsheet. Entity arrays (persons, dates, etc.) are joined with semicolons into single cells.

---

## Data Flow

```
PDF Upload
    │
    ▼
pdf_reader.py ──→ Extract text from PDF
    │
    ▼
classifier.py ──→ Classify into 5 categories (Ollama)
    │
    ▼
summarizer.py ──→ Generate plain-English summary (Ollama)
    │
    ▼
extractor.py ──→ Extract persons, dates, locations, offenses (Ollama)
    │
    ▼
supabase_client.py ──→ Save all results to database
    │
    ▼
app.py ──→ Display results + download buttons
```

---

## Development Log

### Phase 1, Step 1 — Project Structure
Created the folder skeleton with empty files. No issues.

### Phase 1, Step 2 — Document Classifier (`pipeline/classifier.py`)

**What was built:**
- `prompts/triage_prompt.txt` — Prompt instructing the model to classify into 5 categories and return structured JSON (classification, confidence, reasoning).
- `pipeline/classifier.py` — Sends document text to Ollama's `/api/chat` endpoint, parses JSON response, validates the category.

**Design decisions:**
- `temperature: 0.0` — deterministic output for consistent classification.
- `timeout: 120s` — local models can be slower than cloud APIs.
- `format: "json"` — Ollama parameter that forces clean JSON output.
- Validates returned category against the allowed set before returning.
- Graceful error dict returned on failure (never raises exceptions).

**Issues encountered and resolved:**

1. **`ollama serve` → "address already in use"**
   - **Cause:** Ollama was already running in the background.
   - **Resolution:** Not a real error. Confirmed Ollama was active and proceeded.

2. **JSON parsing failure — regex approach**
   - **Cause:** Llama 3 returned JSON with literal `\n` and `\"` escape characters (double-encoded). The regex `re.search(r"\{.*\}", raw, re.DOTALL)` failed to match.
   - **Attempted fix:** Multi-strategy `_parse_json_response` helper with direct parse, markdown stripping, unicode-escape decoding, and substring extraction.
   - **Result:** Still failed — `unicode_escape` decoding couldn't reliably handle the double-encoded output.

3. **JSON parsing failure — final fix**
   - **Root cause:** Ollama's default text output mode doesn't guarantee clean JSON.
   - **Resolution:** Added `"format": "json"` to the Ollama API request. This forces the model to output valid, parseable JSON at the source — eliminating all downstream parsing issues. Removed all workaround code.

### Phase 1, Step 3 — Entity Extractor (`pipeline/extractor.py`)

**What was built:**
- `prompts/extract_prompt.txt` — Prompt instructing the model to extract persons, dates, locations, and offenses from document text.
- `pipeline/extractor.py` — `extract_entities(text)` function that sends text to Ollama, parses the response, and validates all 4 entity keys.

**Design decisions:**
- Reused the same Ollama patterns from the classifier (`format: "json"`, `temperature: 0.0`, `timeout: 120s`).
- Validates that all expected keys exist and are lists — defaults to empty list if missing.

**Issues encountered:** None — `format: "json"` worked cleanly on the first run.

### Phase 1, Step 4 — PDF Reader (`pipeline/pdf_reader.py`)

**What was built:**
- `pipeline/pdf_reader.py` — `extract_text_from_pdf(file)` function using pdfplumber.
- `sample_docs/sample_warrant.pdf` — Sample search warrant PDF for testing.

**Issues encountered:**
1. **`fpdf2` not installed** — Needed to create the sample PDF. Installed as a dev dependency.

**Test result:** Extracted 730 characters from `sample_warrant.pdf` — clean text output.

### Phase 1, Step 5 — Streamlit Frontend (`app.py`)

**What was built:**
- `app.py` — Streamlit app that ties all pipeline modules together.

**Issues encountered:** None — all pipeline modules integrated cleanly on the first run.

### Phase 2 — Supabase Backend (`db/supabase_client.py`)

**What was built:**
- `db/supabase_client.py` — `save_triage_result()` and `get_triage_history()`.
- `triage_results` table in Supabase.

**Issues encountered and resolved:**

1. **Anon key can't run raw SQL**
   - **Resolution:** User created the table manually via Supabase SQL Editor.

2. **Row Level Security (RLS) blocking inserts**
   - **Cause:** Supabase enables RLS by default on new tables.
   - **Resolution:** Added an "Allow all operations" RLS policy.

### Phase 3 — Enhancements

**Enhancement 1: Document Summarization**
- Added `pipeline/summarizer.py` and `prompts/summary_prompt.txt`.
- Generates 3-6 sentence plain-English summaries via Ollama.
- Summary displayed between classification and entities in the UI.
- Saved to Supabase (`summary` column added via ALTER TABLE).
- No issues — worked on first run.

**Enhancement 2: Multi-PDF Batch Upload**
- Refactored `app.py` to accept multiple files with progress bar.
- Batch summary table shows all results at a glance.
- Per-document expanders for detailed results.
- Session state caching prevents re-processing on Streamlit reruns.
- **Issue:** Nested `st.expander` not allowed in Streamlit. Fixed by using `st.toggle` for extracted text display inside batch expanders.

**Enhancement 3: Export & Reporting**
- Added `export/pdf_report.py` — generates formatted PDF triage reports via fpdf2.
- Added `export/csv_export.py` — exports history as CSV.
- PDF download button appears after each document's results and in history view.
- CSV export button in sidebar.
- **Issue:** `fpdf2` `.output()` returns `bytearray` but Streamlit expects `bytes`. Fixed with `bytes()` wrapper.

**Enhancement 2b: Clickable History**
- Sidebar history items converted from static text to clickable buttons.
- Clicking a past result loads its full details from Supabase (classification, summary, entities).
- PDF report download available for past results too.
- This demonstrates the value of Supabase — stored results are instantly recalled without re-processing.
