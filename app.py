import streamlit as st
import google.generativeai as genai
import os
import docx2txt
import fitz  
import re
import tempfile
import json


api_key = 'AIzaSyC9WS0oHMIaFCbgqxI-gYzNNwG9rjxRbIk'
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

hr_prompt = """
You are a professional HR manager. Given a resume, extract and return a structured JSON with the following fields:
- skills: [summary]
- experience: [summary]
- education: [list]
- fitment_score (out of 100) for the role of {job_role}
- missing_skills: [list]
- recommended_courses: [{{"title": "...", "platform": "...", "url": "..."}}]

Make the output JSON formatted and parsable.
"""

def extract_text_from_file(uploaded_file):
    ext = os.path.splitext(uploaded_file.name)[-1].lower()
    if ext == ".pdf":
        text = ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            with fitz.open(tmp.name) as doc:
                for page in doc:
                    text += page.get_text()
        return text
    elif ext == ".docx":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(uploaded_file.read())
            return docx2txt.process(tmp.name)
    else:
        return ""

st.set_page_config(page_title="Resume Analyzer", layout="centered")
st.title("📄 AI Resume Screener")
st.write("Upload your resume and get insights like skills, fitment score, and more.")

uploaded_file = st.file_uploader("Upload Resume (.pdf or .docx)", type=["pdf", "docx"])
job_role = st.text_input("Enter Job Role", value="Data Scientist")
if st.button("Analyze"):
    if uploaded_file is None:
        st.warning("Please upload a resume file first.")
    else:
        with st.spinner("Analyzing resume with Gemini..."):
            resume_text = extract_text_from_file(uploaded_file)

            if not resume_text.strip():
                st.error("Empty or invalid resume file.")
            else:
                prompt = hr_prompt.format(job_role=job_role) + f"\n\nResume:\n{resume_text}"
                try:
                    response = model.generate_content(prompt)
                    json_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
                    result = json.loads(json_text)

                    st.success("✅ Resume analyzed successfully!")

                    st.subheader("🔍 Extracted Information")
                    st.markdown(f"**Fitment Score:** {result.get('fitment_score', 'N/A')} / 100")
                    st.markdown("**Skills:** " + result.get("skills", "N/A"))
                    st.markdown("**Experience:** " + result.get("experience", "N/A"))
                    st.markdown("**Education:**")
                    st.write(result.get("education", []))

                    st.markdown("**Missing Skills:**")
                    st.write(result.get("missing_skills", []))

                    st.markdown("**🎓 Recommended Courses:**")
                    for course in result.get("recommended_courses", []):
                        st.markdown(f"- [{course['title']}]({course['url']}) on *{course['platform']}*")

                except Exception as e:
                    st.error("❌ Failed to parse Gemini output.")
                    st.code(response.text, language='json')


elif uploaded_file is None and st.button("Analyze", key="analyze_without_file"):

    st.warning("Please upload a resume file first.")
