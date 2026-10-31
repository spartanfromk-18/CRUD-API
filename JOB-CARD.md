# Job card

- **What it does (one sentence):** Enriches a scraped book record with a standardized genre category, a concise one-sentence summary, and quality verification flags.
- **Input:** JSON object containing book fields (`title`, `price_gbp`, `availability`, `rating`, `description`, `source_page`).
- **Output:** 
  ```json
  {
    "category": "one of [Fiction, Non-Fiction, Sci-Fi, Fantasy, Mystery, Biography, Academic, Other]",
    "summary": "string, 1-2 sentences summarizing the book based on description",
    "quality_flags": ["list of strings, e.g., 'missing_description' or 'normal'"],
    "confidence": 0.0-1.0
  }