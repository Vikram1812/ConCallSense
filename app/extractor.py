# app/extractor.py
import json
from openai import OpenAI
from app.schemas import ExtractedConCallIntelligence, ParsedConCall


class LocalConCallExtractor:
    def __init__(self, base_url: str = "http://localhost:1234/v1", api_key: str = "not-needed"):
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def extract_intelligence(self, parsed_data: ParsedConCall, model_name: str = "local-model") -> ExtractedConCallIntelligence:
        # Concatenate management opening remarks
        remarks_text = "\n\n".join([
            f"{turn.speaker} ({turn.role.value}): {turn.text}"
            for turn in parsed_data.management_remarks
        ])

        # Keep input prompt compact for fast local evaluation
        max_chars = 4000
        truncated_text = remarks_text[:max_chars]

        # Get JSON schema from Pydantic model
        schema = ExtractedConCallIntelligence.model_json_schema()

        system_prompt = (
            "You are a financial analyst. Extract structured forward-looking guidance from the provided "
            "management remarks. Strict rules:\n"
            "1. Extract at most 3 top quantitative guidance items.\n"
            "2. Keep quotes very short (under 15 words).\n"
            "3. Extract at most 3 key headwinds.\n"
            "4. Return ONLY a valid JSON object matching the requested schema. No Markdown blocks, no commentary."
        )

        # Send standard OpenAI JSON schema format that LM Studio expects
        response = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze these management remarks:\n\n{truncated_text}"}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "ExtractedConCallIntelligence",
                    "strict": False,
                    "schema": schema
                }
            },
            temperature=0.1,
            max_tokens=1500
        )

        raw_content = response.choices[0].message.content or "{}"
        
        # Clean any accidental markdown wrap
        raw_content = raw_content.replace("```json", "").replace("```", "").strip()

        # Parse into Pydantic model
        return ExtractedConCallIntelligence.model_validate_json(raw_content)