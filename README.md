# AI Resume Analyzer

A Streamlit app that analyzes resumes, extracts skills, scores ATS-friendliness, and compares against job descriptions.

## Features
- **Upload resume** — PDF, DOCX, or TXT
- **AI/NLP skill extraction** — detects 100+ skills across programming, data science, cloud, business, and design categories
- **ATS score (0–100)** — weighted across contact info, section headers, skills coverage, action-verb/impact language, and length
- **Improvement suggestions** — concrete, prioritized fixes (missing sections, weak phrasing, no quantified results, etc.)
- **Job description comparison** — paste a JD to get a TF-IDF similarity score plus matched/missing keyword lists

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (typically `http://localhost:8501`).

## Project structure

```
resume_analyzer/
├── app.py          # Streamlit UI
├── analyzer.py      # Core logic: text extraction, scoring, JD comparison, suggestions
├── skills_db.py      # Curated skills database + action-verb/weak-phrase lists
└── requirements.txt
```

## How the ATS score works

| Category | Points | What it checks |
|---|---|---|
| Contact Information | 10 | Email, phone, LinkedIn present |
| Standard Sections | 20 | Experience, Education, Skills headers present |
| Skills Coverage | 20 | Number of recognized skills found |
| Impact & Language | 20 | Strong action verbs + quantified achievements (%, $, numbers) |
| Length & Density | 10 | Word count in the 350–900 ideal range |
| Job Description Match | 20 | TF-IDF cosine similarity to the pasted JD (only when JD provided) |

If no job description is provided, the first five categories (80 pts total) are rescaled to 100.

## Notes / Limitations
- Works best with text-based PDFs/DOCX; scanned/image-only PDFs won't extract text (no OCR built in).
- Skill matching is keyword-based against a curated list (`skills_db.py`) — easy to extend with more skills/synonyms.
- This is a heuristic ATS approximation, not a guarantee of how any specific real-world ATS will score the resume.

## Extending it
- Add more skills/synonyms to `skills_db.py`.
- Swap the TF-IDF JD matcher for embeddings (e.g., sentence-transformers) for more semantic matching.
- Add OCR (e.g., `pytesseract`) to support scanned PDFs.
