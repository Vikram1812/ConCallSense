# main.py
import sys
from pathlib import Path
from app.parser import TranscriptParser
from app.extractor import LocalConCallExtractor
from app.database import save_concall_intelligence


def process_concall(pdf_path: Path, ticker: str, company_name: str, fy: str, quarter: str, extractor: LocalConCallExtractor):
    """Processes a single concall PDF from extraction to database storage."""
    print("=" * 70)
    print(f"[*] Processing: {company_name} ({ticker}) - {quarter} {fy}")
    print(f"[*] PDF Path  : {pdf_path}")
    print("=" * 70)

    if not pdf_path.exists():
        print(f"[!] File not found: {pdf_path.resolve()}")
        print("[!] Skipping this company. Please ensure the PDF is placed in data/samples/.\n")
        return

    # 1. Parse PDF
    print("[1/3] Parsing PDF transcript and identifying speaker turns...")
    parser = TranscriptParser(pdf_path)
    parsed_call = parser.process()
    print(f"      Extracted {len(parsed_call.management_remarks)} management remark blocks and {len(parsed_call.qa_session)} Q&A turns.")

    if not parsed_call.management_remarks:
        print("      [!] Warning: No management remarks found. Splitting might require adjustment.")

    # 2. Extract intelligence via LM Studio
    print("[2/3] Extracting structured guidance and sentiment via LM Studio...")
    try:
        intelligence = extractor.extract_intelligence(parsed_call)
    except Exception as e:
        print(f"      [!] Error during LLM extraction: {e}")
        return

    print(f"      Sentiment Score: {intelligence.management_sentiment_score}")
    print(f"      Guidance Targets Found: {len(intelligence.guidance_items)}")
    for item in intelligence.guidance_items:
        print(f"       • [{item.metric_type.value}] {item.target_value} {item.target_unit} ({item.target_period})")

    # 3. Save to database
    print("[3/3] Saving records to concallsense.db...")
    saved_count = save_concall_intelligence(
        ticker=ticker,
        company_name=company_name,
        fiscal_year=fy,
        fiscal_quarter=quarter,
        intelligence=intelligence
    )
    print(f"[✓] Saved {saved_count} guidance targets for {ticker} into database.\n")


def main():
    # Define batch tasks for Tamilnad Mercantile Bank (TMB) and Restaurant Brands Asia (RBA)
    batch_queue = [
        {
            "pdf_path": Path("data/samples/tmb_concall.pdf"),
            "ticker": "TMB",
            "company_name": "Tamilnad Mercantile Bank Limited",
            "fy": "FY26",
            "quarter": "Q3",
        },
        {
            "pdf_path": Path("data/samples/rba_concall.pdf"),
            "ticker": "RBA",
            "company_name": "Restaurant Brands Asia Limited",
            "fy": "FY26",
            "quarter": "Q3",
        },
    ]

    print(f"Starting ConCallSense batch pipeline for {len(batch_queue)} companies...\n")
    
    # Initialize the local LLM extractor once to reuse the client connection
    extractor = LocalConCallExtractor()

    for item in batch_queue:
        process_concall(
            pdf_path=item["pdf_path"],
            ticker=item["ticker"],
            company_name=item["company_name"],
            fy=item["fy"],
            quarter=item["quarter"],
            extractor=extractor
        )

    print("=" * 70)
    print("[✓] Batch processing complete! Open concallsense.db to view all stored companies.")
    print("=" * 70)


if __name__ == "__main__":
    main()