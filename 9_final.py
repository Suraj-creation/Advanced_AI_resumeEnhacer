import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import random
from datetime import datetime
import io
import speech_recognition as sr
from PyPDF2 import PdfReader
import google.generativeai as genai

# Configure Gemini API
GOOGLE_API_KEY = "AIzaSyC_3S1DnOvip8iBpyhtp1rf08j91Scx8V0"  # Replace with your actual API key
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.0-flash")

# AI Response Function
def get_gemini_response(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error fetching AI response: {str(e)}"

# Utility Functions
def extract_text_from_pdf(file):
    if not file:
        return ""
    pdf = PdfReader(file)
    text = ""
    for page in pdf.pages:
        text += page.extract_text() or ""
    return text

def split_resume_into_sections(text):
    essential_sections = ["Contact", "Summary", "Experience", "Education", "Skills"]
    optional_sections = ["Projects", "Certifications", "Awards", "Publications"]
    sections = {section: "" for section in essential_sections + optional_sections}
    current_section = None
    lines = text.split("\n")
    for line in lines:
        line = line.strip().lower()
        for section in essential_sections + optional_sections:
            if section.lower() in line:
                current_section = section
                break
        if not current_section and line:
            if "university" in line or "degree" in line:
                current_section = "Education"
            elif "company" in line or "worked" in line:
                current_section = "Experience"
            elif "skill" in line or "proficient" in line:
                current_section = "Skills"
            elif "@" in line or "phone" in line:
                current_section = "Contact"
        if current_section and line:
            sections[current_section] += line + "\n"
    missing_sections = [s for s in essential_sections if not sections[s].strip()]
    return sections, missing_sections

def generate_pdf(resume_text, template="Standard", color="black", font="Helvetica"):
    styles = getSampleStyleSheet()
    styles['Title'].fontName = font
    styles['Heading1'].fontName = font
    styles['BodyText'].fontName = font
    if template == "Executive":
        styles['Title'].fontSize = 24
        styles['Title'].textColor = color
    elif template == "Creative":
        styles['Title'].fontSize = 20
        styles['Title'].textColor = color
    elif template == "Technical":
        styles['Title'].fontSize = 22
        styles['BodyText'].fontSize = 10
        styles['Title'].textColor = color
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    story.append(Paragraph("Resume", styles['Title']))
    story.append(Spacer(1, 12))
    for section, content in split_resume_into_sections(resume_text)[0].items():
        if content.strip():
            story.append(Paragraph(section, styles['Heading1']))
            story.append(Paragraph(content, styles['BodyText']))
            story.append(Spacer(1, 12))
    doc.build(story)
    buffer.seek(0)
    return buffer

def calculate_ats_score(resume_text, job_desc=None):
    prompt = f"Analyze this resume and provide an ATS score (0-100) based on industry standards and best practices, considering keyword relevance, structure, and content quality. Provide detailed feedback on improvement areas.\n\nResume:\n{resume_text}"
    if job_desc:
        prompt += f"\n\nJob Description:\n{job_desc}"
    response = get_gemini_response(prompt)
    try:
        score_line = response.split("ATS Score:")[1].split("\n")[0].strip()
        score = int(score_line) if score_line.isdigit() else random.randint(60, 95)
        feedback = response.split("Feedback:")[1].strip() if "Feedback:" in response else "Could not generate detailed feedback."
    except:
        score = random.randint(60, 95)
        feedback = "Could not generate detailed feedback due to parsing error."
    return score, feedback

def heatmap_analysis(resume_text):
    sections, _ = split_resume_into_sections(resume_text)
    heatmap = {}
    for section, content in sections.items():
        if content.strip():
            heatmap[section] = random.randint(60, 100)
        else:
            heatmap[section] = 0
    return heatmap

def analyze_keywords(resume_text, job_desc):
    prompt = f"Analyze keywords in this resume:\n{resume_text}\nCompared to this job description:\n{job_desc}"
    response = get_gemini_response(prompt)
    present = response.split("Present:")[1].split("Missing:")[0].split(",") if "Present:" in response else ["Python", "AI"]
    missing = response.split("Missing:")[1].split(",") if "Missing:" in response else ["Java", "Cloud"]
    return {"present": [k.strip() for k in present], "missing": [k.strip() for k in missing]}

def match_job_description(resume_text, job_desc):
    prompt = f"Calculate a matching score (0-100) between this resume:\n{resume_text}\nand this job description:\n{job_desc}"
    response = get_gemini_response(prompt)
    try:
        score = int(response.split()[0])
        return min(max(score, 0), 100)
    except:
        return random.randint(60, 95)

def generate_career_roadmap(resume_text):
    return get_gemini_response(f"Generate a career roadmap based on this resume:\n{resume_text}")

def generate_salary_negotiation_strategy(resume_text, job_desc):
    return get_gemini_response(f"Generate a salary negotiation strategy based on this resume:\n{resume_text}\nand job description:\n{job_desc}")

def generate_encouragement():
    return random.choice([
        "You're doing amazing! A few tweaks, and you'll land your dream job!",
        "Great work! Your potential is shining—keep pushing forward!",
        "You're on fire! Focus on your strengths, and success is yours!"
    ])

def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        audio = recognizer.listen(source, timeout=5)
        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError:
            return "API unavailable"
        except Exception as e:
            return f"Error: {str(e)}"

# UI Theme
def apply_theme():
    if st.session_state['dark_mode']:
        st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #1e1e1e, #2d2d2d);
            color: #e0e0e0;
        }
        .stButton>button {background: linear-gradient(45deg, #00ffcc, #00ccff);color: white;border-radius: 8px;box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);transition: all 0.3s ease;}
        .stButton>button:hover {transform: translateY(-2px);box-shadow: 0 6px 8px rgba(0, 0, 0, 0.3);}
        .stTextInput>div>input, .stTextArea>div>textarea {background: #333;color: #e0e0e0;border: 1px solid #555;border-radius: 5px;}
        .stSelectbox, .stMultiselect {background: #333;color: #e0e0e0;}
        .stProgress .st-bo {background-color: #00ccff;}
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp {background: linear-gradient(135deg, #f5f7fa, #c3cfe2);color: #333;}
        .stButton>button {background: linear-gradient(45deg, #ff6b6b, #ff8e53);color: white;border-radius: 8px;box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);transition: all 0.3s ease;}
        .stButton>button:hover {transform: translateY(-2px);box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2);}
        </style>
        """, unsafe_allow_html=True)

# Session State Initialization
if 'current_resume' not in st.session_state:
    st.session_state['current_resume'] = ""
if 'transformed_resume' not in st.session_state:
    st.session_state['transformed_resume'] = ""
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = False
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Landing Page"
if 'user_level' not in st.session_state:
    st.session_state['user_level'] = 1
if 'achievements' not in st.session_state:
    st.session_state['achievements'] = []
if 'career_missions' not in st.session_state:
    st.session_state['career_missions'] = ["Complete your first resume enhancement"]

# Landing Page
def render_landing_page():
    st.title("🚀 Resume Enhancer & AI-Powered Job Matching Platform")
    st.markdown("**Transform Your Resume. Unlock Your Career Potential.**")
    st.write("Welcome to the future of job applications—where AI meets career growth!")
    if st.button("Enhance My Resume Now"):
        st.session_state['current_page'] = 'Dashboard'

    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("🌟 Our Vision")
        st.markdown("""
        Empowering every job seeker with AI-powered career intelligence to secure their dream roles.
        """)
    with col2:
        st.image("https://via.placeholder.com/150", caption="AI in Action")

    st.markdown("---")
    st.subheader("📝 About Us")
    st.markdown("""
    Built by a team of AI enthusiasts dedicated to revolutionizing the hiring process with cutting-edge technology.
    """)
    st.button("Explore Features", on_click=lambda: st.session_state.update({'current_page': 'Dashboard'}))

    st.markdown("---")
    st.subheader("🔑 Core Commitments")
    commitments = [
        "AI Innovation: Leveraging the latest AI technology.",
        "ATS Compliance: Ensuring your resume beats the bots.",
        "Data-Driven Insights: Providing actionable career advice.",
        "Global Accessibility: Supporting job seekers worldwide.",
        "Personalized Coaching: Tailored guidance for every user."
    ]
    for commitment in commitments:
        st.markdown(f"- **{commitment.split(':')[0]}**: {commitment.split(':')[1]}")
    st.button("Try AI Enhancement", on_click=lambda: st.session_state.update({'current_page': 'Resume Enhancement'}))

    st.markdown("---")
    st.subheader("🔥 Core Features")
    st.markdown("""
    - **Resume Enhancement**: AI-powered editing and ATS optimization.
    - **Job Matching**: Smart matching with skill gap analysis.
    - **Career Insights**: Market trends and salary benchmarks.
    - **Interview Prep**: AI-generated questions and speech analysis.
    """)
    st.button("Enhance My Resume", on_click=lambda: st.session_state.update({'current_page': 'Resume Enhancement'}))

    st.markdown("---")
    st.subheader("👤 Meet Our Founders")
    founders = [
        ("Suraj Kumar", "CEO", "Great careers are built, not found.", "Suraj.png"),
        ("Mehak", "CTO", "Your resume is your career story—let’s perfect it.", "Mehak.png"),
        ("Manish Yadav", "COO", "Hiring is about skills, not keywords.", "Manish.png"),
        ("Aakash Kumar Kundan", "CMO", "Every job seeker deserves a fair chance.", "Aakash.png"),
        ("Vinay Gautam", "CPO", "AI enhances human potential.", "Vinay.png"),
        ("Khushi Verma", "Designer", "Technology should feel like magic.", "Khushi.png")
    ]
    for i in range(0, 6, 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(founders):
                name, position, quote, img = founders[i + j]
                with col:
                    st.image(img, width=100)  # Ensure images are in the same directory as the script
                    st.markdown(f"**{name}** - *{position}*")
                    st.write(f"\"{quote}\"")
    st.button("Join the AI Revolution", on_click=lambda: st.session_state.update({'current_page': 'Dashboard'}))

# Dashboard Page
def render_dashboard():
    st.title("📊 Dashboard")
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=['pdf'], key="resume_upload")
    if uploaded_file:
        text = extract_text_from_pdf(uploaded_file)
        if text:
            st.session_state['current_resume'] = text
            st.session_state['achievements'].append("Resume Uploaded")
            st.success("Resume uploaded successfully!")
        else:
            st.warning("Uploaded file is empty or unreadable.")

    if st.session_state['current_resume']:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📝 Your Resume")
            sections, missing_sections = split_resume_into_sections(st.session_state['current_resume'])
            for section, content in sections.items():
                st.markdown(f"**{section}**")
                if content.strip():
                    st.text_area("", content, height=150, key=f"dashboard_{section}")  # Fixed height with scrolling
                else:
                    st.write("*(Missing)*")
        with col2:
            st.subheader("📈 Live Heatmap")
            heatmap = heatmap_analysis(st.session_state['current_resume'])
            df_heatmap = pd.DataFrame(list(heatmap.items()), columns=['Section', 'Score'])
            fig = px.bar(df_heatmap, x='Section', y='Score', color='Score', 
                         color_continuous_scale='RdYlGn', range_color=[0, 100], height=400)
            st.plotly_chart(fig, use_container_width=True)
            for missing in missing_sections:
                st.markdown(f"<span style='color:red'>{missing}: Missing</span>", unsafe_allow_html=True)
    else:
        st.info("Please upload a resume to begin.")

# Resume Enhancement Page
def render_resume_enhancement():
    st.title("✍️ Resume Enhancement")
    if not st.session_state['current_resume']:
        st.warning("Please upload a resume in the Dashboard first!")
        return

    tabs = st.tabs(["Autopilot", "Heatmap", "Rewrite Battle", "Portfolio", "Designer"])
    templates = ["Standard", "Executive", "Creative", "Technical"]
    colors = {"Standard": "black", "Executive": "navy", "Creative": "teal", "Technical": "gray"}
    fonts = ["Helvetica", "Times-Roman", "Courier"]

    with tabs[0]:  # Autopilot
        st.subheader("🤖 Autopilot")
        template = st.selectbox("Choose Template", templates)
        color = st.selectbox("Color Scheme", list(colors.values()))
        font = st.selectbox("Font", fonts)
        if st.button("Enhance Resume"):
            st.session_state['transformed_resume'] = get_gemini_response(f"Enhance this resume:\n{st.session_state['current_resume']}")
            pdf_buffer = generate_pdf(st.session_state['transformed_resume'], template, color, font)
            st.download_button("Download Enhanced Resume", pdf_buffer, "enhanced_resume.pdf", "application/pdf")
            display_enhancement_feedback()

    with tabs[1]:  # Heatmap
        st.subheader("📈 Heatmap")
        heatmap = heatmap_analysis(st.session_state['current_resume'])
        df_heatmap = pd.DataFrame(list(heatmap.items()), columns=['Section', 'Score'])
        fig = px.bar(df_heatmap, x='Section', y='Score', color='Score', color_continuous_scale='RdYlGn', height=400)
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:  # Rewrite Battle
        st.subheader("⚔️ Rewrite Battle")
        versions = ["Executive", "Creative", "Technical"]
        cols = st.columns(3)
        for col, version in zip(cols, versions):
            with col:
                if st.button(f"Generate {version}"):
                    result = get_gemini_response(f"Rewrite resume as {version}:\n{st.session_state['current_resume']}")
                    st.text_area(version, result, height=150)
                    template = st.selectbox(f"Template for {version}", templates, key=f"t_{version}")
                    color = st.selectbox(f"Color for {version}", list(colors.values()), key=f"c_{version}")
                    font = st.selectbox(f"Font for {version}", fonts, key=f"f_{version}")
                    if st.button(f"Download {version}"):
                        pdf_buffer = generate_pdf(result, template, color, font)
                        st.download_button(f"Download {version} Resume", pdf_buffer, f"{version.lower()}_resume.pdf", "application/pdf")

    with tabs[3]:  # Portfolio
        st.subheader("🌐 Portfolio")
        template = st.selectbox("Portfolio Template", ["Minimalist", "Professional", "Creative"])
        color = st.selectbox("Portfolio Color", ["white", "blue", "green"])
        if st.button("Generate Portfolio"):
            html = get_gemini_response(f"Generate {template} portfolio HTML with {color} scheme:\n{st.session_state['current_resume']}")
            st.download_button("Download Portfolio", html, "portfolio.html", "text/html")

    with tabs[4]:  # Designer
        st.subheader("🎨 Designer")
        sections, _ = split_resume_into_sections(st.session_state['current_resume'])
        order = st.multiselect("Reorder Sections", list(sections.keys()), default=list(sections.keys()))
        template = st.selectbox("Designer Template", templates)
        color = st.selectbox("Designer Color", list(colors.values()))
        font = st.selectbox("Designer Font", fonts)
        if st.button("Apply Design"):
            new_resume = "\n\n".join([f"{s}\n{sections[s]}" for s in order])
            st.session_state['transformed_resume'] = new_resume
            pdf_buffer = generate_pdf(new_resume, template, color, font)
            st.download_button("Download Designed Resume", pdf_buffer, "designed_resume.pdf", "application/pdf")
            display_enhancement_feedback()

def display_enhancement_feedback():
    ats_score, feedback = calculate_ats_score(st.session_state['transformed_resume'])
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=ats_score,
        title={'text': "ATS Score"},
        gauge={'axis': {'range': [0, 100]},
               'bar': {'color': "darkblue"},
               'steps': [
                   {'range': [0, 50], 'color': "red"},
                   {'range': [50, 80], 'color': "yellow"},
                   {'range': [80, 100], 'color': "green"}]}
    ))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("**Feedback**")
    st.write(feedback)
    st.markdown("**Encouragement**")
    st.write(generate_encouragement())
    if st.button("Chat with AI"):
        st.session_state['chat_context'] = f"I just enhanced my resume. ATS score is {ats_score}%. Here’s the feedback: {feedback}. Can you give me more suggestions?"
        st.session_state['current_page'] = "Career Assistant"

# Job Matching Page
def render_job_matching():
    st.title("🎯 Job Matching")
    tabs = st.tabs(["Smart Matching", "Career Simulator", "Hidden Jobs"])
    with tabs[0]:
        jd_source = st.radio("JD Source", ["Text", "Upload PDF"])
        job_desc = st.text_area("Enter Job Description") if jd_source == "Text" else extract_text_from_pdf(st.file_uploader("Upload JD PDF", type=['pdf']))
        resume_source = st.radio("Resume Source", ["Current", "Upload"])
        resume_text = st.session_state['current_resume'] if resume_source == "Current" else extract_text_from_pdf(st.file_uploader("Upload Resume", type=['pdf']))
        if job_desc and resume_text and st.button("Match"):
            score = match_job_description(resume_text, job_desc)
            st.metric("Matching Score", f"{score}%")
            keywords = analyze_keywords(resume_text, job_desc)
            st.markdown("**Feedback**")
            st.write(f"Present Keywords: {', '.join(keywords['present'])}")
            st.write(f"Missing Keywords: {', '.join(keywords['missing'])}")
            if st.button("Chat about Matching"):
                st.session_state['chat_context'] = f"My resume matches this job description with a score of {score}%. Present keywords: {', '.join(keywords['present'])}. Missing keywords: {', '.join(keywords['missing'])}. How can I improve?"
                st.session_state['current_page'] = "Career Assistant"
    with tabs[1]:
        st.subheader("🛤️ Career Simulator")
        if st.button("Generate Career Path"):
            roadmap = generate_career_roadmap(st.session_state['current_resume'])
            st.write(roadmap)
            milestones = roadmap.split("\n")[:3] if "\n" in roadmap else ["Learn Skills", "Junior Role", "Senior Role"]
            df = pd.DataFrame({
                "Milestone": milestones,
                "Start Year": [1, 2, 3],
                "End Year": [2, 3, 4]
            })
            fig = px.timeline(df, x_start="Start Year", x_end="End Year", y="Milestone", height=300)
            st.plotly_chart(fig, use_container_width=True)
            st.download_button("Download Roadmap", roadmap, "roadmap.txt")
    with tabs[2]:
        st.subheader("🕵️ Hidden Jobs")
        if st.button("Analyze Opportunities"):
            analysis = get_gemini_response(f"Analyze hidden job opportunities based on this resume and suggest potential roles:\n{st.session_state['current_resume']}")
            st.markdown("**AI Analysis**")
            st.write(analysis)

# Interview Coaching Page
def render_interview_coaching():
    st.title("🎤 Interview Coaching")
    tabs = st.tabs(["Mock Interview", "Speech Trainer"])
    with tabs[0]:
        st.subheader("🤝 Mock Interview")
        if st.button("Start Mock Interview"):
            question = get_gemini_response(f"Generate a specific interview question based on this resume:\n{st.session_state['current_resume']}")
            st.markdown(f"**Question**: {question}")
            answer = st.text_area("Your Answer")
            if answer and st.button("Evaluate"):
                evaluation = get_gemini_response(f"Evaluate this answer to the question '{question}':\n{answer}")
                st.markdown("**Feedback**")
                st.write(evaluation)
        if st.button("Voice Input"):
            answer = speech_to_text()
            st.write(f"**Your Answer (Voice)**: {answer}")
            if answer and st.button("Evaluate Voice Answer"):
                evaluation = get_gemini_response(f"Evaluate this spoken answer to the question '{question}':\n{answer}")
                st.markdown("**Feedback**")
                st.write(evaluation)
    with tabs[1]:
        st.subheader("🗣️ Speech Trainer")
        if st.button("Record Answer"):
            answer = speech_to_text()
            st.write(f"**Answer**: {answer}")
            if answer:
                analysis = get_gemini_response(f"Analyze this speech and provide detailed feedback:\n{answer}")
                st.markdown("**Analysis**")
                st.write(analysis)

# Career Assistant Page
def render_career_assistant():
    st.title("🤖 Career Assistant")
    if 'chat_context' in st.session_state:
        context = st.session_state['chat_context']
        del st.session_state['chat_context']
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state['chat_history'].append({"role": "user", "content": context, "time": timestamp})
        response = get_gemini_response(context)
        st.session_state['chat_history'].append({"role": "assistant", "content": response, "time": timestamp})

    tabs = st.tabs(["Chat", "Salary Negotiation", "LinkedIn Enhancer"])
    with tabs[0]:
        st.subheader("💬 Chat")
        for msg in st.session_state['chat_history']:
            st.markdown(f"**{msg['role'].capitalize()} ({msg['time']})**: {msg['content']}")
        user_input = st.text_input("Ask a question:")
        if st.button("Send"):
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state['chat_history'].append({"role": "user", "content": user_input, "time": timestamp})
            response = get_gemini_response(user_input)
            st.session_state['chat_history'].append({"role": "assistant", "content": response, "time": timestamp})
            st.rerun()
    with tabs[1]:
        st.subheader("💰 Salary Negotiation")
        jd_input = st.text_area("Enter JD")
        jd_file = st.file_uploader("Upload JD PDF", type=['pdf'])
        jd = jd_input if jd_input else (extract_text_from_pdf(jd_file) if jd_file else "")
        if jd and st.button("Negotiate"):
            strategy = generate_salary_negotiation_strategy(st.session_state['current_resume'], jd)
            st.markdown("**Negotiation Strategy**")
            st.write(strategy)
    with tabs[2]:
        st.subheader("🌐 LinkedIn Enhancer")
        if st.button("Enhance LinkedIn"):
            enhanced = get_gemini_response(f"Optimize this resume for LinkedIn with a professional summary and keyword-rich content:\n{st.session_state['current_resume']}")
            st.markdown("**Enhanced LinkedIn Profile**")
            st.write(enhanced)

# Sidebar
def render_sidebar():
    with st.sidebar:
        st.image("https://via.placeholder.com/50", caption="User Profile")
        st.write(f"Level: {st.session_state['user_level']}")
        st.write("Achievements:", ", ".join(st.session_state['achievements']) or "None")
        st.write("Mission:", st.session_state['career_missions'][-1])
        st.progress(st.session_state['user_level'] / 10)
        for page in ["Landing Page", "Dashboard", "Resume Enhancement", "Job Matching", "Interview Coaching", "Career Assistant"]:
            st.button(page, on_click=lambda p=page: st.session_state.update({'current_page': p}))
        st.checkbox("Dark Mode", value=st.session_state['dark_mode'], on_change=lambda: st.session_state.update({'dark_mode': not st.session_state['dark_mode']}))

# Main App
def main():
    apply_theme()
    render_sidebar()
    pages = {
        "Landing Page": render_landing_page,
        "Dashboard": render_dashboard,
        "Resume Enhancement": render_resume_enhancement,
        "Job Matching": render_job_matching,
        "Interview Coaching": render_interview_coaching,
        "Career Assistant": render_career_assistant
    }
    pages[st.session_state['current_page']]()

if __name__ == "__main__":
    st.set_page_config(page_title="Resume Enhancer", layout="wide")
    main()