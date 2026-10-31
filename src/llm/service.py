import os
import json
from openai import OpenAI
from src.llm.schema import EnrichRequest, EnrichResponse, BookCategory

def load_prompt() -> str:
    prompt_path = os.path.join("prompts", "enrich-v1.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return "You enrich book records. Return strict JSON matching the schema."

def clean_and_parse_json(raw_content: str) -> dict:
    cleaned = raw_content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())

def log_quarantine(payload: EnrichRequest, raw_output: str, error_msg: str):
    os.makedirs("logs", exist_ok=True)
    quarantine_record = {
        "prompt_version": "enrich-v1",
        "input_payload": payload.model_dump(),
        "raw_model_output": raw_output,
        "error": error_msg
    }
    with open("logs/quarantine.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(quarantine_record) + "\n")

def call_llm_enrichment(payload: EnrichRequest) -> EnrichResponse:
    # 1. Smart Stub Mode Bypass for local testing & evals
    if os.getenv("LLM_STUB", "0") == "1":
        title_lower = payload.title.lower()
        
        if "python" in title_lower or "course" in title_lower or "crash" in title_lower:
            return EnrichResponse(
                category=BookCategory.ACADEMIC,
                summary=f"An educational programming resource: {payload.title}.",
                quality_flags=["stub_mode_active"],
                confidence=0.95
            )
        elif "misc" in title_lower or "object" in title_lower or "thing" in title_lower:
            return EnrichResponse(
                category=BookCategory.OTHER,
                summary=f"Unclear ambiguous item: {payload.title}.",
                quality_flags=["stub_mode_active", "low_confidence_classification"],
                confidence=0.3
            )
        else:
            return EnrichResponse(
                category=BookCategory.FICTION,
                summary=f"Stub summary for '{payload.title}': A captivating literary work.",
                quality_flags=["stub_mode_active"],
                confidence=0.99
            )

    # 2. Real OpenAI Client Initialization
    client = OpenAI(
        base_url=os.getenv("LLM_BASE_URL", "[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)"),
        api_key=os.getenv("LLM_API_KEY", "ollama"),
        timeout=30.0
    )
    model_name = os.getenv("LLM_MODEL", "openrouter/free")
    system_prompt = load_prompt()
    user_content = payload.model_dump_json()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    raw_output = ""
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.0
        )
        raw_output = response.choices[0].message.content
        parsed_data = clean_and_parse_json(raw_output)
        return EnrichResponse.model_validate(parsed_data)
    
    except Exception as first_error:
        error_detail = str(first_error)
        repair_messages = messages + [
            {"role": "assistant", "content": raw_output},
            {
                "role": "user",
                "content": f"Your previous answer was rejected for this reason: {error_detail}. Return only corrected JSON matching the schema with no markdown fences."
            }
        ]
        
        try:
            repair_response = client.chat.completions.create(
                model=model_name,
                messages=repair_messages,
                temperature=0.0
            )
            raw_output = repair_response.choices[0].message.content
            parsed_data = clean_and_parse_json(raw_output)
            return EnrichResponse.model_validate(parsed_data)
            
        except Exception as repair_error:
            log_quarantine(payload, raw_output, str(repair_error))
            raise ValueError(f"Repair failed after second attempt: {str(repair_error)}")