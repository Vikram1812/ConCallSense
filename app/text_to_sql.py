# app/text_to_sql.py
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List
import sqlparse
from openai import OpenAI

DB_PATH = Path("concallsense.db")

SCHEMA_CONTEXT = """
Database Schema:
Table: companies (
    id INTEGER PRIMARY KEY,
    ticker VARCHAR(20) UNIQUE,  -- e.g. 'TCS', 'INFY'
    company_name VARCHAR(255)
)

Table: earnings_calls (
    id INTEGER PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    fiscal_year VARCHAR(10),     -- e.g. 'FY26'
    fiscal_quarter VARCHAR(10),  -- e.g. 'Q1', 'Q2', 'Q3'
    sentiment_score FLOAT,       -- 0.0 to 1.0
    capex_summary TEXT
)

Table: guidance_commitments (
    id INTEGER PRIMARY KEY,
    call_id INTEGER REFERENCES earnings_calls(id),
    metric_type VARCHAR(50),     -- 'REVENUE', 'EBITDA_MARGIN', 'PAT', 'CAPEX', 'VOLUME_GROWTH'
    target_value NUMERIC(15, 2),
    target_unit VARCHAR(20),     -- 'PERCENT', 'CRORE', 'LAKH'
    target_period VARCHAR(30),   -- e.g. 'Q4 FY26', 'FY27'
    verbatim_quote TEXT,
    status VARCHAR(20)           -- 'PENDING', 'MET', 'MISSED'
)
"""

SYSTEM_PROMPT = f"""
You are an expert SQL engineer for ConCallSense.
Translate the user's natural language question into a valid SQLite SELECT query.
{SCHEMA_CONTEXT}

Strict Rules:
1. ONLY return the raw SQL query. Do NOT include markdown blocks (no ```sql), explanations, or notes.
2. Generate ONLY read-only queries (SELECT). Never generate INSERT, UPDATE, DELETE, DROP, or ALTER.
3. Match company tickers in uppercase (e.g., 'TCS', 'INFY').
4. Join tables using explicit foreign keys (companies.id = earnings_calls.company_id, etc.).
"""


class TextToSQLAgent:
    def __init__(self, base_url: str = "http://localhost:1234/v1", api_key: str = "not-needed"):
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def _is_safe_query(self, sql: str) -> bool:
        """Ensures the generated SQL is strictly a read-only SELECT statement."""
        clean_sql = sql.strip().strip(";").lower()
        forbidden = ["drop", "delete", "insert", "update", "alter", "truncate", "create", "replace"]
        for word in forbidden:
            if re.search(rf"\b{word}\b", clean_sql):
                return False
        return clean_sql.startswith("select") or clean_sql.startswith("with")

    def _clean_sql(self, raw_output: str) -> str:
        """Strips markdown code tags if the LLM returned them."""
        cleaned = re.sub(r"```(?:sql)?", "", raw_output, flags=re.IGNORECASE)
        return cleaned.strip()

    def query(self, user_question: str) -> Dict[str, Any]:
        # Step 1: Generate SQL via local LM Studio
        response = self.client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_question}
            ],
            temperature=0.0,
            max_tokens=300
        )

        raw_sql = response.choices[0].message.content or ""
        generated_sql = self._clean_sql(raw_sql)

        # Step 2: Validate Security Guardrails
        if not self._is_safe_query(generated_sql):
            return {
                "question": user_question,
                "error": "Query blocked by safety validator: only SELECT statements are permitted.",
                "raw_generated": generated_sql
            }

        # Step 3: Execute on SQLite
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(generated_sql)
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            conn.close()

            return {
                "question": user_question,
                "generated_sql": generated_sql,
                "row_count": len(results),
                "data": results
            }
        except Exception as err:
            return {
                "question": user_question,
                "generated_sql": generated_sql,
                "error": f"Database execution error: {str(err)}"
            }