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

# Background image + animated gradient overlay
bg_url = "https://images.unsplash.com/photo-1677165605399-9e2f1e9a6e3e?crop=entropy&cs=tinysrgb&fit=max&ixid=MnwzNjUyOXwwfDF8c2VhcmNofDkxfHxmb2xkZXJzfGVufDB8fHx8fDE2NzYxNzYwMjA&ixlib=rb-1.2.1&q=80&w=1080"

st.markdown(f"""
<style>
/* Full page background with gradient animation */
.stApp {{
    background-image: linear-gradient(120deg, rgba(0,0,0,0.15), rgba(0,0,0,0.15)), url("{bg_url}");
    background-size: cover;
    background-attachment: fixed;
    background-repeat: no-repeat;
    transition: all 1s ease-in-out;
}}

/* Animated gradient on hover */
.stApp:hover {{
    background-image: linear-gradient(120deg, rgba(0,0,0,0.25), rgba(0,0,0,0.25)), url("{bg_url}");
}}

/* Main content container */
.main-container {{
    background: rgba(255, 255, 255, 0.88);
    border-radius: 15px;
    padding: 2rem;
    backdrop-filter: blur(6px);
    color: #000 !important;
}}

/* Ensure text inside Streamlit components is readable */
.stMetricValue, .stMetricLabel, .stExpanderHeader, .stMarkdown, .stText, .stButton, .stNumberInput input {{
    color: #000 !important;
}}
.stSidebar, .stSidebar .stText, .stSidebar .stMarkdown {{
    color: #000 !important;
}}
div[data-testid="stDataFrameContainer"] {{
    color: #000 !important;
    background: rgba(255,255,255,0.88) !important;
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
