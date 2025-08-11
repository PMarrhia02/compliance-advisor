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
import hashlib
import bcrypt

# --- Initialization ---
load_dotenv()
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# --- Security Constants ---
SESSION_TIMEOUT = 1800  # 30 minutes in seconds
PEPPER = os.getenv("PEPPER", "default-pepper-value").encode()  # Extra security layer

# --- Authentication Utilities ---
def hash_password(password: str) -> str:
    """Securely hash password with bcrypt and pepper"""
    salted = password.encode() + PEPPER
    return bcrypt.hashpw(salted, bcrypt.gensalt()).decode()

def verify_password(input_password: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    salted = input_password.encode() + PEPPER
    return bcrypt.checkpw(salted, stored_hash.encode())

# --- GitHub Integration ---
@st.cache_resource
def get_github_client():
    """Initialize GitHub client with token"""
    return Github(os.getenv("GITHUB_TOKEN"))

def load_from_github(repo_path: str, file_path: str) -> pd.DataFrame:
    """Load DataFrame from GitHub repo"""
    try:
        repo = get_github_client().get_repo(repo_path)
        content = repo.get_contents(file_path)
        return pd.read_csv(BytesIO(content.decoded_content))
    except Exception as e:
        st.error(f"GitHub Error: {str(e)}")
        return pd.DataFrame()

# --- UI Components ---
def setup_page_styles():
    """Inject custom CSS"""
    st.markdown("""
    <style>
        .title { font-size: 2.5em; color: #003366; font-weight: bold; }
        .badge { display: inline-block; padding: 0.25em 0.6em; font-size: 90%; 
                font-weight: 600; border-radius: 0.25rem; }
        .badge-green { background-color: #d4edda; color: #155724; }
        .badge-red { background-color: #f8d7da; color: #721c24; }
        .priority-high { border-left: 4px solid #dc3545; padding-left: 10px; }
        .dashboard-card { border-radius: 10px; padding: 15px; 
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .footer { text-align: center; margin-top: 3rem; color: #6c757d; }
    </style>
    """, unsafe_allow_html=True)

# --- Authentication Flow ---
def show_login_page():
    """Display login form"""
    st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
    
    with st.form("auth_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            if authenticate_user(username, password):
                st.session_state.last_activity = pd.Timestamp.now()
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    if st.button("Forgot Password?"):
        handle_password_reset()

def authenticate_user(username: str, password: str) -> bool:
    """Verify user credentials"""
    # 1. Check environment variables
    env_user = os.getenv("ADMIN_USER")
    env_pass = os.getenv("ADMIN_PASS")
    
    if username == env_user and verify_password(password, env_pass):
        st.session_state.user = {"username": username, "role": "admin"}
        return True
    
    # 2. Check hardcoded demo credentials (remove in production)
    demo_user = "demo_admin"
    demo_pass_hash = hash_password("Demo@123")
    
    if username == demo_user and verify_password(password, demo_pass_hash):
        st.warning("Using demo credentials - configure .env for production")
        st.session_state.user = {"username": username, "role": "user"}
        return True
    
    return False

# --- Main Application ---
def main_app():
    """Core application after authentication"""
    # Session timeout check
    if (pd.Timestamp.now() - st.session_state.last_activity).seconds > SESSION_TIMEOUT:
        st.warning("Session expired. Please log in again.")
        del st.session_state.user
        st.rerun()
    
    st.session_state.last_activity = pd.Timestamp.now()
    
    # Header
    st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"Welcome, **{st.session_state.user['username']}**")
    with col2:
        if st.button("Logout"):
            del st.session_state.user
            st.rerun()
    
    # Load data
    compliance_df = load_from_github(
        os.getenv("COMPLIANCE_DATA_REPO"),
        "compliance_standards.csv"
    )
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Analysis", "⚙️ Admin"])
    
    with tab1:
        show_dashboard(compliance_df)
        
    with tab2:
        show_analysis_tab(compliance_df)
        
    with tab3:
        if st.session_state.user["role"] == "admin":
            show_admin_tab()
        else:
            st.error("Admin privileges required")

# --- Tab Components ---
def show_dashboard(df: pd.DataFrame):
    """Display compliance dashboard"""
    st.header("Compliance Overview")
    
    if df.empty:
        st.warning("No compliance data loaded")
        return
    
    # Key metrics
    met = len(df[df["Compliant"] == True])
    total = len(df)
    compliance_rate = (met / total) * 100 if total > 0 else 0
    
    cols = st.columns(3)
    cols[0].metric("Total Standards", total)
    cols[1].metric("Compliant", f"{met} ({compliance_rate:.1f}%)")
    cols[2].metric("Pending", total - met)
    
    # Data table
    st.dataframe(df, use_container_width=True)

def show_analysis_tab(df: pd.DataFrame):
    """Project analysis interface"""
    st.header("Project Compliance Analysis")
    
    project_desc = st.text_area(
        "Describe your project (include industry, data types, and regions):",
        height=150,
        placeholder="e.g., Healthcare app processing EU patient data..."
    )
    
    if st.button("Analyze Compliance"):
        if not project_desc.strip():
            st.warning("Please enter a project description")
            return
        
        # ... [Your existing analysis logic here] ...
        
        # Demo result
        st.success("Analysis complete!")
        st.json({
            "industry": "Healthcare",
            "regulations": ["HIPAA", "GDPR"],
            "compliance_score": 78
        })

def show_admin_tab():
    """Admin management interface"""
    st.header("Administration")
    
    # User management
    with st.expander("User Accounts"):
        st.write("User management functionality would go here")
    
    # GitHub actions
    with st.expander("GitHub Integration"):
        repo = st.text_input("Repository (owner/repo)", "your-org/your-repo")
        issue_title = st.text_input("Issue Title")
        issue_body = st.text_area("Issue Description", height=100)
        
        if st.button("Create GitHub Issue"):
            try:
                get_github_client().get_repo(repo).create_issue(
                    title=issue_title,
                    body=issue_body
                )
                st.success("Issue created successfully!")
            except Exception as e:
                st.error(f"Failed: {str(e)}")

# --- Entry Point ---
if __name__ == "__main__":
    setup_page_styles()
    
    # Initialize session
    if "user" not in st.session_state:
        st.session_state.user = None
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = pd.Timestamp.now()
    
    # Route to appropriate view
    if st.session_state.user:
        main_app()
    else:
        show_login_page()
    
    # Footer
    st.markdown("---")
    st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", 
               unsafe_allow_html=True)
