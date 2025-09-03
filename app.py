import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import bcrypt
import time

# --- Initialization ---
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# --- Demo Credentials ---
DEMO_CREDENTIALS = {
    "admin": {
        "password_hash": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()),
        "role": "admin"
    }
}

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

    # Check against demo credentials
    if username in DEMO_CREDENTIALS and bcrypt.checkpw(password.encode(), DEMO_CREDENTIALS[username]["password_hash"]):
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
        # Try GitHub first (simplified)
        # For demo purposes, we'll use sample data
        sample_data = {
            'Compliance Name': ['GDPR', 'HIPAA', 'PCI DSS', 'ISO 27001', 'SOC 2'],
            'Domain': ['Data Privacy', 'Healthcare', 'Payment Security', 'Information Security', 'Service Organizations'],
            'Applies To': ['EU data, personal data', 'Healthcare data', 'Payment card data', 'Information assets', 'Service organizations'],
            'Checklist 1': ['Data mapping', 'Access controls', 'Network security', 'Risk assessment', 'Security policies'],
            'Checklist 2': ['Consent management', 'Audit controls', 'Data encryption', 'Security controls', 'Monitoring'],
            'Checklist 3': ['Breach notification', 'Transmission security', 'Vulnerability management', 'Continuous improvement', 'Third-party management'],
            'Followed By Compunnel': ['Yes', 'Partial', 'Yes', 'Yes', 'Partial'],
            'Why Required': ['Legal requirement for EU data', 'US healthcare regulation', 'Payment card industry standard', 'International security standard', 'Service organization compliance']
        }
        return pd.DataFrame(sample_data)
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        return pd.DataFrame()

# --- Analysis Functions ---
def analyze_project(project_description, compliance_df):
    """Analyze project compliance requirements"""
    # Simple keyword-based analysis for demo purposes
    keywords = project_description.lower()
    applicable_standards = []
    
    for _, row in compliance_df.iterrows():
        score = 0
        if 'health' in keywords and 'hipaa' in row['Compliance Name'].lower():
            score += 3
        if 'payment' in keywords and 'pci' in row['Compliance Name'].lower():
            score += 3
        if 'eu' in keywords or 'europe' in keywords and 'gdpr' in row['Compliance Name'].lower():
            score += 3
        if 'security' in keywords and ('iso' in row['Compliance Name'].lower() or 'soc' in row['Compliance Name'].lower()):
            score += 2
        if 'service' in keywords and 'soc' in row['Compliance Name'].lower():
            score += 2
            
        if score > 0:
            standard = row.to_dict()
            standard['relevance_score'] = score
            applicable_standards.append(standard)
    
    # Sort by relevance score
    applicable_standards.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    return {
        "applicable_standards": applicable_standards,
        "summary": f"Based on your project description, {len(applicable_standards)} compliance standards apply."
    }

def display_results(results):
    """Display analysis results"""
    st.subheader("Compliance Requirements")
    for standard in results["applicable_standards"]:
        with st.expander(standard.get('Compliance Name', 'Unknown Standard')):
            st.write(f"Domain: {standard.get('Domain', 'N/A')}")
            st.write(f"Applies To: {standard.get('Applies To', 'N/A')}")
            st.write(f"Why Required: {standard.get('Why Required', 'N/A')}")
    
    st.success(results["summary"])

# --- Admin Functions ---
def show_admin_tab():
    """Show admin panel"""
    st.header("Admin Panel")
    st.info("This is the admin panel. Demo users can access this with admin credentials.")
    
    # Display demo credentials for convenience
    with st.expander("Demo Credentials"):
        st.write("**Admin Account:**")
        st.code("Username: admin\nPassword: admin123")

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
        if st.session_state.auth['username'] == "admin":
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
