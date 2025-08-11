import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from github import Github
import os
from dotenv import load_dotenv

# --- Initialization ---
load_dotenv()
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# --- GitHub Integration ---
@st.cache_resource
def get_github_client():
    """Initialize GitHub client with token from .env"""
    return Github(os.getenv("GITHUB_TOKEN"))

def create_github_issue(repo_name, title, body):
    """Create an issue in specified GitHub repo"""
    try:
        repo = get_github_client().get_repo(repo_name)
        repo.create_issue(title=title, body=body)
        return True
    except Exception as e:
        st.error(f"Failed to create issue: {str(e)}")
        return False

# --- Custom CSS ---
st.markdown("""
    <style>
        .title { font-size: 2.5em; color: #003366; font-weight: bold; }
        .badge { display: inline-block; padding: 0.25em 0.6em; font-size: 90%; font-weight: 600; border-radius: 0.25rem; }
        .badge-green { background-color: #d4edda; color: #155724; }
        .badge-red { background-color: #f8d7da; color: #721c24; }
        .badge-blue { background-color: #d1ecf1; color: #0c5460; }
        .priority-high { border-left: 4px solid #dc3545; padding-left: 10px; margin: 8px 0; }
        .priority-standard { border-left: 4px solid #fd7e14; padding-left: 10px; margin: 8px 0; }
        .dashboard-card { border-radius: 10px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .footer { text-align: center; font-size: 0.9em; color: gray; margin-top: 3rem; }
    </style>
""", unsafe_allow_html=True)

# --- Authentication ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
    with st.form("auth"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if username == os.getenv("ADMIN_USER") and password == os.getenv("ADMIN_PASS"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()

# --- Main App ---
st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
st.markdown("AI-powered compliance analysis with GitHub integration")

# --- Data Loading ---
@st.cache_data
def load_compliance_data():
    """Load compliance data from GitHub repo"""
    try:
        repo = get_github_client().get_repo(os.getenv("COMPLIANCE_DATA_REPO"))
        contents = repo.get_contents("compliance_standards.csv")
        return pd.read_csv(BytesIO(contents.decoded_content))
    except Exception as e:
        st.error(f"Failed to load compliance data: {str(e)}")
        return pd.DataFrame()

compliance_df = load_compliance_data()

# --- Project Analysis UI ---
tab1, tab2, tab3 = st.tabs(["🏠 Dashboard", "🔍 Analysis", "⚙️ GitHub Actions"])

with tab1:
    st.header("Compliance Overview")
    if not compliance_df.empty:
        st.dataframe(compliance_df, use_container_width=True)
    else:
        st.warning("No compliance data loaded")

with tab2:
    project_description = st.text_area(
        "Describe your project (include data types and regions):",
        height=150,
        placeholder="e.g., Healthcare app storing patient records in India..."
    )

    if st.button("Analyze Compliance"):
        if not project_description.strip():
            st.warning("Please enter a project description")
            st.stop()
        
        # ... [Keep your existing analyze_project() and visualization code] ...

with tab3:
    st.header("GitHub Integration")
    repo_name = st.text_input("Target repository (owner/repo)", "your-org/your-repo")
    issue_title = st.text_input("Issue title")
    issue_body = st.text_area("Issue description", height=150)
    
    if st.button("Create GitHub Issue"):
        if create_github_issue(repo_name, issue_title, issue_body):
            st.success("Issue created successfully!")
            
# --- PDF Report Generation --- 
# ... [Keep your existing generate_pdf_report() function] ...

# --- Footer ---
st.markdown("---")
st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro | GitHub Integrated</div>", unsafe_allow_html=True)
