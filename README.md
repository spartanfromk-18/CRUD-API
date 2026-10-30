# Task API — FastAPI CRUD Service (W2 · A1)

A lightweight RESTful CRUD API built with Python and FastAPI that manages an in-memory to-do list[cite: 8]. Includes input validation, proper HTTP status codes, interactive OpenAPI/Swagger documentation at `/docs`, query filtering, pagination, and runtime statistics[cite: 11, 12, 13].

## Quickstart

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Stage 7 — AI vs Me
1. **Validation:** AI returned 422 instead of 400 on empty body requests[cite: 11, 13].
2. **IDs:** AI used `len(tasks) + 1` causing collisions after deletion[cite: 13].
3. **Updates:** AI model required `title` on every `PUT` request[cite: 11, 13].
