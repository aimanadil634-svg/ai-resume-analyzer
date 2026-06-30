"""
Core analysis engine for the AI Resume Analyzer.
Handles: file text extraction, skill extraction, ATS scoring,
job-description comparison, and improvement suggestions.
"""

import re
import io
from collections import Counter

import pdfplumber
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from skills_db import ALL_SKILLS, STRONG_ACTION_VERBS, WEAK_PHRASES, ATS_PROBLEM_SECTIONS


# --------------------------------------------------------------------------
# Text extraction
# --------------------------------------------------------------------------

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_chunks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_chunks.append(page_text)
    return "\n".join(text_chunks)


def extract_text_from_docx(file_bytes: bytes) -> str:
    document = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in document.paragraphs)


def extract_text(file_bytes: bytes, filename: str) -> str:
    filename_lower = filename.lower()
    if filename_lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif filename_lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    elif filename_lower.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        raise ValueError("Unsupported file type. Please upload PDF, DOCX, or TXT.")


# --------------------------------------------------------------------------
# Skill extraction
# --------------------------------------------------------------------------

def extract_skills(text: str) -> dict:
    """
    Returns {category: [skills found]} using whole-word/phrase matching
    against the curated skills database.
    """
    text_lower = " " + re.sub(r"\s+", " ", text.lower()) + " "
    found = {}
    for skill, category in ALL_SKILLS.items():
        # word-boundary-ish match; handles multi-word skills and symbols like c++/c#
        pattern = re.escape(skill).replace(r"\ ", r"[\s\-]+")
        if re.search(rf"(?<![a-zA-Z0-9]){pattern}(?![a-zA-Z0-9])", text_lower):
            found.setdefault(category, []).append(skill)
    return found


def flatten_skills(skill_dict: dict) -> set:
    flat = set()
    for skills in skill_dict.values():
        flat.update(skills)
    return flat


# --------------------------------------------------------------------------
# Resume structure / formatting checks (ATS-relevant)
# --------------------------------------------------------------------------

def check_sections(text: str) -> dict:
    text_lower = text.lower()
    found = {}
    for section in ATS_PROBLEM_SECTIONS:
        found[section] = section in text_lower
    return found


def check_contact_info(text: str) -> dict:
    email_found = bool(re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text))
    phone_found = bool(re.search(r"(\+?\d{1,3}[\s-]?)?\(?\d{3,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}", text))
    linkedin_found = "linkedin.com" in text.lower()
    return {"email": email_found, "phone": phone_found, "linkedin": linkedin_found}


def check_weak_language(text: str) -> list:
    text_lower = text.lower()
    hits = []
    for phrase in WEAK_PHRASES:
        if phrase in text_lower:
            hits.append(phrase)
    return hits


def count_action_verbs(text: str) -> int:
    text_lower = text.lower()
    count = 0
    for verb in STRONG_ACTION_VERBS:
        count += len(re.findall(rf"\b{verb}\b", text_lower))
    return count


def has_quantified_achievements(text: str) -> bool:
    # looks for numbers/percentages near typical achievement language
    return bool(re.search(r"\b\d+(\.\d+)?\s*%|\$\s?\d+|\b\d{2,}\b", text))


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


# --------------------------------------------------------------------------
# ATS Scoring
# --------------------------------------------------------------------------

def compute_ats_score(text: str, jd_text: str = None) -> dict:
    """
    Computes a composite ATS-friendliness score out of 100, broken into
    weighted sub-scores. If a job description is supplied, keyword match
    against the JD is included; otherwise that weight is redistributed.
    """
    scores = {}
    notes = []

    sections = check_sections(text)
    contact = check_contact_info(text)
    weak_hits = check_weak_language(text)
    action_verbs = count_action_verbs(text)
    quantified = has_quantified_achievements(text)
    wc = word_count(text)
    skills_found = flatten_skills(extract_skills(text))

    # 1. Contact info completeness (10 pts)
    contact_score = sum(contact.values()) / len(contact) * 10
    scores["Contact Information"] = round(contact_score, 1)
    if not contact["email"]:
        notes.append("No email address detected — ATS systems and recruiters need this to reach you.")
    if not contact["phone"]:
        notes.append("No phone number detected — add one for faster recruiter contact.")
    if not contact["linkedin"]:
        notes.append("Consider adding your LinkedIn URL.")

    # 2. Section completeness (20 pts)
    core_sections = ["experience", "education", "skills"]
    sections_present = sum(1 for s in core_sections if sections.get(s) or sections.get("work experience"))
    section_score = sections_present / len(core_sections) * 20
    scores["Standard Sections"] = round(section_score, 1)
    for s in core_sections:
        if not sections.get(s) and not (s == "experience" and sections.get("work experience")):
            notes.append(f"Missing or unclear '{s.title()}' section header — use a standard heading so ATS parsers can find it.")

    # 3. Skills presence (20 pts) — having a healthy number of recognizable skills
    skill_count = len(skills_found)
    skill_score = min(skill_count / 12, 1.0) * 20
    scores["Skills Coverage"] = round(skill_score, 1)
    if skill_count < 6:
        notes.append("Few recognizable technical/professional skills found — list relevant tools, languages, and competencies explicitly.")

    # 4. Strong language & impact (20 pts)
    verb_score = min(action_verbs / 8, 1.0) * 10
    quant_score = 10 if quantified else 0
    impact_score = verb_score + quant_score
    scores["Impact & Language"] = round(impact_score, 1)
    if action_verbs < 5:
        notes.append("Use more strong action verbs (e.g., 'led', 'built', 'optimized') to start bullet points.")
    if not quantified:
        notes.append("Add quantified achievements (numbers, %, $) — e.g., 'Increased revenue by 18%'.")
    if weak_hits:
        notes.append(f"Replace weak phrasing like \"{weak_hits[0]}\" with action-driven language.")

    # 5. Length / density (10 pts)
    if 350 <= wc <= 900:
        length_score = 10
    elif 200 <= wc < 350 or 900 < wc <= 1200:
        length_score = 6
        notes.append("Resume length is slightly off the ideal range (350–900 words) — tighten or expand content.")
    else:
        length_score = 3
        notes.append("Resume length is far from the ideal range (350–900 words) for ATS and recruiter readability.")
    scores["Length & Density"] = round(length_score, 1)

    # 6. JD Match (20 pts) — only if JD provided
    jd_match_pct = None
    if jd_text and jd_text.strip():
        jd_match_pct = compute_jd_similarity(text, jd_text)
        jd_score = jd_match_pct / 100 * 20
        scores["Job Description Match"] = round(jd_score, 1)
    else:
        # redistribute weight proportionally across existing categories
        notes.append("No job description provided — add one for a tailored keyword-match score.")

    total = sum(scores.values())
    # normalize to 100 if JD wasn't included (max possible was 80)
    if jd_text is None or not jd_text.strip():
        total = total / 80 * 100

    return {
        "total_score": round(min(total, 100), 1),
        "breakdown": scores,
        "notes": notes,
        "jd_match_pct": jd_match_pct,
        "skills_found": skills_found,
        "word_count": wc,
    }


# --------------------------------------------------------------------------
# Job Description Comparison
# --------------------------------------------------------------------------

def compute_jd_similarity(resume_text: str, jd_text: str) -> float:
    """TF-IDF cosine similarity between resume and JD, returned as a percentage."""
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf = vectorizer.fit_transform([resume_text, jd_text])
        sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return round(sim * 100, 1)
    except ValueError:
        return 0.0


def compare_skills_to_jd(resume_text: str, jd_text: str) -> dict:
    resume_skills = flatten_skills(extract_skills(resume_text))
    jd_skills = flatten_skills(extract_skills(jd_text))

    matched = resume_skills & jd_skills
    missing = jd_skills - resume_skills
    extra = resume_skills - jd_skills

    match_pct = round(len(matched) / len(jd_skills) * 100, 1) if jd_skills else 0.0

    return {
        "matched": sorted(matched),
        "missing": sorted(missing),
        "extra": sorted(extra),
        "match_pct": match_pct,
        "jd_skill_count": len(jd_skills),
        "resume_skill_count": len(resume_skills),
    }


# --------------------------------------------------------------------------
# Suggestions generator
# --------------------------------------------------------------------------

def generate_suggestions(ats_result: dict, jd_comparison: dict = None) -> list:
    suggestions = list(ats_result["notes"])

    if jd_comparison and jd_comparison["missing"]:
        top_missing = ", ".join(jd_comparison["missing"][:8])
        suggestions.append(
            f"Add these job-relevant keywords if you genuinely have the experience: {top_missing}."
        )
    if jd_comparison and jd_comparison["match_pct"] < 50:
        suggestions.append(
            "Overall keyword overlap with the job description is low — tailor your skills and "
            "experience bullet points to mirror the JD's language more closely."
        )

    # de-duplicate while preserving order
    seen = set()
    deduped = []
    for s in suggestions:
        if s not in seen:
            deduped.append(s)
            seen.add(s)
    return deduped
