"""
AI Resume Analyzer — Streamlit App
Upload a resume (PDF/DOCX/TXT), get an ATS score, skill extraction,
improvement suggestions, and an optional job-description match.
"""

import streamlit as st
import pandas as pd
import altair as alt

from analyzer import (
    extract_text,
    extract_skills,
    compute_ats_score,
    compare_skills_to_jd,
    generate_suggestions,
)

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("📄 AI Resume Analyzer")
    st.markdown(
        "Upload your resume to get an **ATS score**, extracted **skills**, "
        "and tailored **improvement suggestions**. Optionally paste a job "
        "description to see how well you match."
    )
    st.markdown("---")
    st.markdown("**Supported formats:** PDF, DOCX, TXT")
    st.markdown("Built with Streamlit · scikit-learn · pdfplumber")

# ---------------------------------------------------------------------------
# Main inputs
# ---------------------------------------------------------------------------
st.title("AI Resume Analyzer")
st.caption("Upload your resume, get instant ATS feedback, and compare against a job description.")

col_upload, col_jd = st.columns(2)

with col_upload:
    uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx", "txt"])

with col_jd:
    jd_text = st.text_area(
        "Paste a job description (optional)",
        height=180,
        placeholder="Paste the job posting here to get a tailored keyword match score...",
    )

analyze_clicked = st.button("🔍 Analyze Resume", type="primary", use_container_width=False)

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
if analyze_clicked:
    if not uploaded_file:
        st.warning("Please upload a resume file first.")
        st.stop()

    with st.spinner("Extracting text..."):
        try:
            file_bytes = uploaded_file.read()
            resume_text = extract_text(file_bytes, uploaded_file.name)
        except Exception as e:
            st.error(f"Couldn't read the file: {e}")
            st.stop()

    if not resume_text.strip():
        st.error("No readable text found in this file. If it's a scanned/image-based PDF, try a text-based version.")
        st.stop()

    with st.spinner("Analyzing resume..."):
        ats_result = compute_ats_score(resume_text, jd_text if jd_text.strip() else None)
        skills_by_category = extract_skills(resume_text)
        jd_comparison = compare_skills_to_jd(resume_text, jd_text) if jd_text.strip() else None
        suggestions = generate_suggestions(ats_result, jd_comparison)

    st.success("Analysis complete!")

    # --- Top metrics row -----------------------------------------------
    score = ats_result["total_score"]
    score_color = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("ATS Score", f"{score}/100", help="Composite score across contact info, sections, skills, language, and length.")
    m2.metric("Skills Detected", len(ats_result["skills_found"]))
    m3.metric("Word Count", ats_result["word_count"])
    if jd_comparison:
        m4.metric("JD Keyword Match", f"{jd_comparison['match_pct']}%")
    else:
        m4.metric("JD Keyword Match", "—")

    st.markdown(f"### {score_color} Overall ATS Score: {score}/100")
    st.progress(min(int(score), 100))

    st.markdown("---")

    # --- Score breakdown --------------------------------------------------
    left, right = st.columns([1.1, 1])

    with left:
        st.subheader("Score Breakdown")
        breakdown_df = pd.DataFrame(
            {"Category": list(ats_result["breakdown"].keys()),
             "Score": list(ats_result["breakdown"].values())}
        )
        chart = (
            alt.Chart(breakdown_df)
            .mark_bar(color="#6C5CE7", cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
            .encode(
                x=alt.X("Score:Q", title="Points"),
                y=alt.Y("Category:N", sort="-x", title=None),
                tooltip=["Category", "Score"],
            )
            .properties(height=260)
        )
        st.altair_chart(chart, use_container_width=True)

    with right:
        st.subheader("Skills Found")
        if skills_by_category:
            for category, skills in skills_by_category.items():
                with st.expander(f"{category} ({len(skills)})", expanded=True):
                    st.write(", ".join(sorted(s.title() for s in skills)))
        else:
            st.info("No recognizable skills found. Make sure your skills are listed clearly (e.g., a dedicated 'Skills' section).")

    st.markdown("---")

    # --- JD Comparison ------------------------------------------------
    if jd_comparison:
        st.subheader("📋 Job Description Match")
        jc1, jc2, jc3 = st.columns(3)
        jc1.metric("Matched Skills", len(jd_comparison["matched"]))
        jc2.metric("Missing Skills", len(jd_comparison["missing"]))
        jc3.metric("Match %", f"{jd_comparison['match_pct']}%")

        mcol, miscol = st.columns(2)
        with mcol:
            st.markdown("**✅ Matched Skills**")
            if jd_comparison["matched"]:
                st.write(", ".join(s.title() for s in jd_comparison["matched"]))
            else:
                st.write("None found.")
        with miscol:
            st.markdown("**❌ Missing Skills (in JD, not in resume)**")
            if jd_comparison["missing"]:
                st.write(", ".join(s.title() for s in jd_comparison["missing"]))
            else:
                st.write("None — great coverage!")

        st.markdown("---")

    # --- Suggestions ------------------------------------------------------
    st.subheader("💡 Suggestions to Improve")
    if suggestions:
        for s in suggestions:
            st.markdown(f"- {s}")
    else:
        st.success("Your resume looks well-optimized! No major issues detected.")

    # --- Raw text expander --------------------------------------------
    with st.expander("View extracted resume text"):
        st.text(resume_text)

else:
    st.info("👆 Upload a resume and click **Analyze Resume** to get started.")
