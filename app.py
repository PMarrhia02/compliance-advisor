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
import bcrypt
import time

# --- Initialization ---
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# --- Security Constants ---
SESSION_TIMEOUT = 1800  # 30 minutes
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = 300  # 5 minutes

# --- Custom CSS ---
st.markdown("""
    <style>
        .title { font-size: 2.5em; color: #003366; font-weight: bold; }
        .badge { display: inline-block; padding: 0.25em 0.6em; font-size: 90%; font-weight: 600; border-radius: 0.25rem; }
        .badge-green { background-color: #d4edda; color: #155724; }
        .badge-red { background-color: #f8d7da; color: #721c24; }
        .priority-high { border-left: 4px solid #dc3545; padding-left: 10px; }
        .dashboard-card { border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .footer { text-align: center; margin-top: 3rem; color: #6c757d; }
    </style>
""", unsafe_allow_html=True)

# --- Secure GitHub Client ---
@st.cache_resource
def get_github_client():
    """Initialize GitHub client using environment-secured token"""
    try:
        # Try Streamlit secrets first (for cloud deployment)
        if st.secrets.get("GITHUB_TOKEN"):
            return Github(st.secrets["GITHUB_TOKEN"])
        
        # Fallback to local environment variable
        if os.getenv("GITHUB_TOKEN"):
            return Github(os.getenv("GITHUB_TOKEN"))
        
        st.error("GitHub token not configured")
        return None
    except Exception as e:
        st.error(f"GitHub connection failed: {str(e)}")
        return None

# --- Authentication System ---
def initialize_auth():
    if 'auth' not in st.session_state:
        st.session_state.auth = {
            'logged_in': False,
            'username': None,
            'login_attempts': 0,
            'last_attempt': 0,
            'last_activity': time.time()
        }

def authenticate(username, password):
    # Check lockout status
    if st.session_state.auth['login_attempts'] >= MAX_LOGIN_ATTEMPTS:
        elapsed = time.time() - st.session_state.auth['last_attempt']
        if elapsed < LOCKOUT_TIME:
            remaining = int((LOCKOUT_TIME - elapsed) // 60)
            st.error(f"Too many attempts. Try again in {remaining} minutes.")
            return False
        st.session_state.auth['login_attempts'] = 0

    # Check credentials - uses Streamlit secrets or .env
    env_user = st.secrets.get("ADMIN_USER", os.getenv("ADMIN_USER"))
    env_pass = st.secrets.get("ADMIN_PASS", os.getenv("ADMIN_PASS"))
    
    if username == env_user and bcrypt.checkpw(password.encode(), env_pass.encode()):
        st.session_state.auth.update({
            'logged_in': True,
            'username': username,
            'login_attempts': 0
        })
        return True
    
    st.session_state.auth['login_attempts'] += 1
    st.session_state.auth['last_attempt'] = time.time()
    st.error("Invalid credentials")
    return False

# --- Data Loading ---
def load_compliance_data():
    """Load data from GitHub repo or fallback to Google Sheets"""
    try:
        # Try GitHub first
        repo_path = st.secrets.get("COMPLIANCE_DATA_REPO", os.getenv("COMPLIANCE_DATA_REPO"))
        if repo_path and get_github_client():
            repo = get_github_client().get_repo(repo_path)
            contents = repo.get_contents("compliance_standards.csv")
            return pd.read_csv(BytesIO(contents.decoded_content))
    except Exception as e:
        st.warning(f"GitHub load failed: {str(e)}")
    
    # Fallback to Google Sheets
    try:
        sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(sheet_url)
        required_cols = ['Compliance Name', 'Domain', 'Applies To', 'Checklist 1', 
                        'Checklist 2', 'Checklist 3', 'Followed By Compunnel', 'Why Required']
        return df if all(col in df.columns for col in required_cols) else pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        return pd.DataFrame()

# --- Main App Components ---
def show_login():
    st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
    with st.form("auth_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            if authenticate(username, password):
                st.rerun()
    
    if st.session_state.auth['login_attempts'] >= MAX_LOGIN_ATTEMPTS:
        elapsed = time.time() - st.session_state.auth['last_attempt']
        if elapsed < LOCKOUT_TIME:
            st.warning(f"Account locked. Try again in {int((LOCKOUT_TIME - elapsed) // 60)} minutes.")

def show_main_app():
    # Header
    st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"Welcome, **{st.session_state.auth['username']}**")
    with col2:
        if st.button("Logout"):
            st.session_state.auth['logged_in'] = False
            st.rerun()
    
    # Load data
    compliance_df = load_compliance_data()
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Analysis", "⚙️ Admin"])
    
    with tab1:
        st.header("Compliance Overview")
        if compliance_df.empty:
            st.error("No compliance data loaded")
        else:
            st.dataframe(compliance_df, use_container_width=True)
    
    with tab2:
        st.header("Project Compliance Analysis")
        project_description = st.text_area(
            "Describe your project (include data types and regions):",
            height=150,
            placeholder="e.g., Healthcare app storing patient records in India with EU users..."
        )
        
        if st.button("Analyze Compliance", type="primary"):
            if not project_description.strip():
                st.warning("Please enter a project description")
            else:
                with st.spinner("Analyzing..."):
                    results = analyze_project(project_description, compliance_df)
                    display_results(results)
    
    with tab3:
        if st.session_state.auth['username'] == st.secrets.get("ADMIN_USER", os.getenv("ADMIN_USER")):
            show_admin_tab()
        else:
            st.error("Admin privileges required")

# --- Run Application ---
if __name__ == "__main__":
    initialize_auth()
    
    if st.session_state.auth['logged_in']:
        show_main_app()
    else:
        show_login()
    
    st.markdown("---")
    st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", unsafe_allow_html=True)
