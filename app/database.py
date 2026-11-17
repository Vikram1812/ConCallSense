# app/database.py
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.models import Base, Company, EarningsCall, GuidanceCommitment
from app.schemas import ExtractedConCallIntelligence

DB_PATH = Path("concallsense.db")
DATABASE_URL = f"sqlite:///{DB_PATH.resolve()}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Creates tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def save_concall_intelligence(
    ticker: str,
    company_name: str,
    fiscal_year: str,
    fiscal_quarter: str,
    intelligence: ExtractedConCallIntelligence
) -> int:
    """Stores the extracted targets into the database."""
    init_db()
    with SessionLocal() as session:
        # 1. Fetch or create Company
        company = session.query(Company).filter_by(ticker=ticker.upper()).first()
        if not company:
            company = Company(ticker=ticker.upper(), company_name=company_name)
            session.add(company)
            session.flush()

        # 2. Fetch or create Earnings Call entry
        call = session.query(EarningsCall).filter_by(
            company_id=company.id,
            fiscal_year=fiscal_year,
            fiscal_quarter=fiscal_quarter
        ).first()

        if not call:
            call = EarningsCall(
                company_id=company.id,
                fiscal_year=fiscal_year,
                fiscal_quarter=fiscal_quarter,
                sentiment_score=intelligence.management_sentiment_score,
                capex_summary=intelligence.capex_summary
            )
            session.add(call)
            session.flush()

        # 3. Insert extracted guidance targets
        saved_items_count = 0
        for item in intelligence.guidance_items:
            commitment = GuidanceCommitment(
                call_id=call.id,
                metric_type=item.metric_type.value,
                target_value=item.target_value,
                target_unit=item.target_unit,
                target_period=item.target_period,
                verbatim_quote=item.verbatim_quote,
                status="PENDING"
            )
            session.add(commitment)
            saved_items_count += 1

        session.commit()
        return saved_items_count