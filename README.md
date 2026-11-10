# ConCallSense

An autonomous AI-driven financial research engine engineered to ingest Indian listed company (NSE/BSE) earnings conference call transcripts, extract quantitative forward-looking management guidance, and enable natural language analytics via local Text-to-SQL.

---

## Architecture Overview

1. **Deterministic Parsing (`app/parser.py`)**: Reads multi-page transcript PDFs, strips headers/footers, and segments content into Opening Remarks vs. Q&A using speaker-attribution heuristics.
2. **Local LLM Extraction (`app/extractor.py`)**: Uses local models hosted via LM Studio (OpenAI-compatible endpoint) with strict Pydantic schemas to extract forward-looking metrics (Revenue, EBITDA Margins, CapEx) and sentiment.
3. **Relational Persistence (`app/database.py`, `app/models.py`)**: Normalizes extracted disclosures across `companies`, `earnings_calls`, and `guidance_commitments` using SQLAlchemy and SQLite.
4. **Text-to-SQL Query Engine (`app/text_to_sql.py`, `ask_db.py`)**: Translates plain-English financial queries into multi-table SQL joins with AST/regex safety enforcement (read-only execution).

---

## Tech Stack

* **Language & Runtime:** Python 3.11+
* **Document Processing:** `pdfplumber`
* **Local Inference:** LM Studio (OpenAI API compatibility on `http://localhost:1234/v1`)
* **Data Validation:** `pydantic`
* **Storage & ORM:** `SQLAlchemy`, `SQLite`
* **Query Validation:** `sqlparse`

---

## Project Structure

```text
ConCallSense/
├── app/
│   ├── __init__.py
│   ├── database.py       # Engine initialization & session management
│   ├── extractor.py      # LLM structured schema extraction
│   ├── models.py         # SQLAlchemy relational database models
│   ├── parser.py         # Transcript segmentation & speaker extraction
│   ├── schemas.py        # Pydantic validation schemas
│   └── text_to_sql.py    # SQL prompt generator & query execution agent
├── data/
│   └── samples/          # Local concall transcript PDFs (git-ignored)
├── ask_db.py             # Interactive CLI for Text-to-SQL querying
├── main.py               # Batch ingestion pipeline runner
├── requirements.txt      # Project dependencies
└── README.md
