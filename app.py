import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

# Page setup
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# Updated background image + soft gradient overlay for professional compliance theme
bg_url = "https://img.freepik.com/free-vector/gradient-cyber-technology-background_23-2149128448.jpg"

st.markdown(f"""
<style>
.stApp {{
    background: linear-gradient(120deg, rgba(246,249,251,0.91), rgba(38,70,83,0.13)), url("{bg_url}");
    background-size: cover;
    background-attachment: fixed;
    background-repeat: no-repeat;
    transition: all 1s ease-in-out;
}}
.main-container {{
    background: rgba(255,255,255,0.96);
    border-radius: 15px;
    padding: 2rem;
    backdrop-filter: blur(6px);
    color: #000 !important;
}}
.stMetricValue, .stMetricLabel, .stExpanderHeader, .stMarkdown, .stText, .stButton, .stNumberInput input {{
    color: #000 !important;
}}
.stSidebar, .stSidebar .stText, .stSidebar .stMarkdown {{
    color: #000 !important;
}}
div[data-testid="stDataFrameContainer"] {{
    color: #000 !important;
    background: rgba(255,255,255,0.96) !important;
}}
.priority-high, .priority-standard, .badge {{
    color: #000 !important;
}}
</style>
""", unsafe_allow_html=True)

# Wrap all content in the container
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

# Header
st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
st.markdown("AI-powered compliance analysis for your exact requirements")

# --------- Your existing compliance application code goes here ---------
# User Authentication, load_data(), analyze_project(), generate_pdf_report(),
# main analysis, report generation, and footer.
# ------------------------------------------------------------------------

# Footer
st.markdown("---")
st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)  # Close main-container
