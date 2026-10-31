cat << 'EOF' > README.md
# 🚀 Enterprise Task & LLM Enrichment API

> A production-grade, modular FastAPI backend integrating Supabase Authentication with a robust, self-healing LLM book enrichment pipeline, complete with strict Pydantic validation, prompt-as-code versioning, automated quarantine logging, and regression evaluation suites.

---

## 🛠️ Tech Stack & Architecture

- **Backend Framework:** FastAPI (Asynchronous REST API)
- **Authentication:** Supabase Auth (JWT Bearer Token verification & secure dependency guards)
- **AI / LLM Integration:** OpenAI SDK (Compatible with OpenRouter, Nebius, and local Ollama instances)
- **Validation & Schemas:** Pydantic v2 (Strict type safety for requests and responses)
- **Reliability & Resilience:** One-shot parse-and-repair retry loop with automated quarantine logging (`logs/quarantine.jsonl`)
- **Evaluation Framework:** Automated regression harness (`scripts/run_evals.py` & `evals/cases.json`)

---

## 📂 Project Structure

```text
CRUD-API/
├── main.py                  # Single app instance, middleware & router aggregation
├── prompts/
│   └── enrich-v1.md         # Versioned prompt-as-code
├── src/
│   ├── llm/
│   │   ├── schema.py        # Pydantic data contracts (EnrichRequest, EnrichResponse)
│   │   └── service.py       # Core LLM invocation, cleaning, repair loop & quarantine
│   └── routes/
│       ├── enrich.py        # LLM enrichment endpoint router
│       └── ...              # Supabase Auth & protected routes
├── evals/
│   └── cases.json           # Hand-labeled test cases for regression testing
├── scripts/
│   └── run_evals.py         # Automated prompt evaluation runner
└── logs/
    └── quarantine.jsonl     # Unrepairable payload quarantine logs
