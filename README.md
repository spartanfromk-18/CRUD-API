# Create Stage 6 README first
cat << 'EOF' > README.md
# Task API — FastAPI CRUD Service (W2 · A1)

A lightweight RESTful CRUD API built with **Python** and **FastAPI** that manages an in-memory to-do list. Includes input validation, proper HTTP status codes, interactive OpenAPI/Swagger documentation at `/docs`, query filtering, pagination, and runtime statistics.

## Quickstart (Run in Under 1 Minute)

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
