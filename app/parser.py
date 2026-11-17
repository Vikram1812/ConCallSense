# app/parser.py
import re
from pathlib import Path
from typing import List, Optional, Tuple  # <-- Add Optional here
import pdfplumber

from app.schemas import DialogueTurn, ParsedConCall, SpeakerRole


class TranscriptParser:
    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"Transcript PDF not found at {self.pdf_path}")

    def _clean_page_text(self, text: str) -> str:
        """Removes page numbers, headers, footers, and standardized disclaimers."""
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()

            # Skip common header/footer artifacts in Indian earnings transcripts
            if not stripped:
                continue
            if re.match(r"^Page \d+ of \d+$", stripped, re.IGNORECASE):
                continue
            if re.match(r"^\d+$", stripped):  # Standalone page numbers
                continue
            if re.search(r"(Earnings Conference Call|Quarterly Call|Earnings Call Transcript)", stripped, re.IGNORECASE) and len(stripped) < 80:
                continue

            cleaned_lines.append(stripped)

        return "\n".join(cleaned_lines)

    def extract_full_text(self) -> Tuple[str, int]:
        """Extracts and cleans text across all pages in the PDF."""
        all_pages_text = []

        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)
            for page in pdf.pages:
                raw_text = page.extract_text(layout=False) or ""
                cleaned = self._clean_page_text(raw_text)
                if cleaned:
                    all_pages_text.append(cleaned)

        return "\n\n".join(all_pages_text), total_pages

    def split_remarks_and_qa(self, full_text: str) -> Tuple[str, str]:
        """Splits transcript into Management Remarks and the Q&A Session."""
        qa_triggers = [
            r"Question-and-Answer Session",
            r"Questions and Answers",
            r"Q&A Session",
            r"Question and Answer Session",
            r"Open the floor for questions",
        ]

        pattern = r"(" + "|".join(qa_triggers) + r")"
        split_match = re.search(pattern, full_text, re.IGNORECASE)

        if split_match:
            split_pos = split_match.start()
            remarks_text = full_text[:split_pos].strip()
            qa_text = full_text[split_pos:].strip()
            return remarks_text, qa_text

        # Fallback if no clear Q&A boundary text is matched
        return full_text, ""

    def _determine_speaker_role(self, speaker_name: str, org: Optional[str]) -> SpeakerRole:
        name_lower = speaker_name.lower()
        if any(term in name_lower for term in ["moderator", "operator", "host"]):
            return SpeakerRole.OPERATOR
        if org and any(term in org.lower() for term in ["capital", "securities", "research", "investments", "asset", "bank"]):
            return SpeakerRole.ANALYST
        return SpeakerRole.MANAGEMENT

    def parse_dialogue_turns(self, text_block: str) -> List[DialogueTurn]:
        """Detects speaker turn prefixes and maps them to DialogueTurn structures."""
        # Matches patterns like:
        # 'K. Krithivasan:'
        # 'Mohit Jain (BNP Paribas):'
        # 'Operator:'
        speaker_pattern = re.compile(
            r"(?m)^(?P<speaker>[A-Z][A-Za-z\s\.\-]{2,40})(?:\s*\((?P<org>[^)]+)\))?\s*:\s*(?P<content>.*?)(?=(?:^[A-Z][A-Za-z\s\.\-]{2,40}(?:\s*\([^)]+\))?\s*:|\Z))",
            re.DOTALL
        )

        turns: List[DialogueTurn] = []
        for match in speaker_pattern.finditer(text_block):
            speaker_raw = match.group("speaker").strip()
            org_raw = match.group("org").strip() if match.group("org") else None
            content = match.group("content").strip()

            # Clean up internal linebreaks within a single utterance
            content_cleaned = " ".join(content.split())

            if len(content_cleaned) < 5:
                continue

            role = self._determine_speaker_role(speaker_raw, org_raw)

            turns.append(
                DialogueTurn(
                    speaker=speaker_raw,
                    role=role,
                    organization=org_raw,
                    text=content_cleaned
                )
            )

        return turns

    def process(self) -> ParsedConCall:
        full_text, total_pages = self.extract_full_text()
        remarks_raw, qa_raw = self.split_remarks_and_qa(full_text)

        remarks_turns = self.parse_dialogue_turns(remarks_raw)
        qa_turns = self.parse_dialogue_turns(qa_raw)

        return ParsedConCall(
            file_name=self.pdf_path.name,
            total_pages=total_pages,
            management_remarks=remarks_turns,
            qa_session=qa_turns
        )