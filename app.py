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
        "password": "admin123",  # Plain text password for demo
        "role": "admin",
        "name": "Administrator"
    },
    "user": {
        "password": "user123",   # Plain text password for demo
        "role": "user",
        "name": "Demo User"
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
        .dashboard-card { 
            border-radius: 10px; 
            padding: 15px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            background-color: #f8f9fa;
            margin-bottom: 15px;
        }
        .footer { text-align: center; margin-top: 3rem; color: #6c757d; }
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            background-color: white;
        }
        .stButton>button {
            width: 100%;
        }
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
            remaining = int((LOCKOUT_TIME - elapsed) // 60) + 1
            st.error(f"Too many attempts. Try again in {remaining} minutes.")
            return False
        st.session_state.auth['login_attempts'] = 0

    # Check against demo credentials
    if username in DEMO_CREDENTIALS and password == DEMO_CREDENTIALS[username]["password"]:
        st.session_state.auth.update({
            'logged_in': True,
            'username': username,
            'login_attempts': 0,
            'role': DEMO_CREDENTIALS[username]["role"],
            'name': DEMO_CREDENTIALS[username]["name"],
            'last_activity': time.time()
        })
        return True
    
    st.session_state.auth['login_attempts'] += 1
    st.session_state.auth['last_attempt'] = time.time()
    st.error("Invalid credentials")
    return False

# --- Data Loading ---
def load_compliance_data():
    """Load sample compliance data"""
    try:
        # Sample compliance data
        data = {
            'Compliance Name': ['GDPR', 'HIPAA', 'PCI DSS', 'ISO 27001', 'SOC 2'],
            'Domain': ['Data Privacy', 'Healthcare', 'Payment Security', 'Information Security', 'Service Organizations'],
            'Applies To': ['EU data, personal data', 'Healthcare data', 'Payment card data', 'Information assets', 'Service organizations'],
            'Checklist 1': ['Data mapping', 'Access controls', 'Network security', 'Risk assessment', 'Security policies'],
            'Checklist 2': ['Consent management', 'Audit controls', 'Data encryption', 'Security controls', 'Monitoring'],
            'Checklist 3': ['Breach notification', 'Transmission security', 'Vulnerability management', 'Continuous improvement', 'Third-party management'],
            'Followed By Compunnel': ['Yes', 'Partial', 'Yes', 'Yes', 'Partial'],
            'Why Required': ['Legal requirement for EU data', 'US healthcare regulation', 'Payment card industry standard', 'International security standard', 'Service organization compliance']
        }
        return pd.DataFrame(data)
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
    if not results["applicable_standards"]:
        st.info("No specific compliance standards identified for your project based on the description.")
        return
        
    st.subheader("Compliance Requirements")
    
    for standard in results["applicable_standards"]:
        with st.expander(f"{standard.get('Compliance Name', 'Unknown Standard')} (Relevance: {standard.get('relevance_score', 0)}/5)"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Domain:** {standard.get('Domain', 'N/A')}")
                st.write(f"**Applies To:** {standard.get('Applies To', 'N/A')}")
            with col2:
                status = standard.get('Followed By Compunnel', 'No')
                color = "green" if status == 'Yes' else "orange" if status == 'Partial' else "red"
                st.write(f"**Followed By Compunnel:** :{color}[{status}]")
            
            st.write(f"**Why Required:** {standard.get('Why Required', 'N/A')}")
            
            st.write("**Key Checklists:**")
            st.write(f"1. {standard.get('Checklist 1', 'N/A')}")
            st.write(f"2. {standard.get('Checklist 2', 'N/A')}")
            st.write(f"3. {standard.get('Checklist 3', 'N/A')}")
    
    st.success(results["summary"])

# --- PDF Generation ---
def generate_pdf_report(results, project_description):
    """Generate PDF report for compliance analysis"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("Compliance Advisor Pro - Analysis Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Project Description
    story.append(Paragraph("Project Description:", styles['Heading2']))
    story.append(Paragraph(project_description, styles['BodyText']))
    story.append(Spacer(1, 12))
    
    # Summary
    story.append(Paragraph("Analysis Summary:", styles['Heading2']))
    story.append(Paragraph(results["summary"], styles['BodyText']))
    story.append(Spacer(1, 12))
    
    # Compliance Standards
    story.append(Paragraph("Applicable Compliance Standards:", styles['Heading2']))
    
    for standard in results["applicable_standards"]:
        story.append(Paragraph(standard.get('Compliance Name', 'Unknown Standard'), styles['Heading3']))
        story.append(Paragraph(f"Domain: {standard.get('Domain', 'N/A')}", styles['BodyText']))
        story.append(Paragraph(f"Applies To: {standard.get('Applies To', 'N/A')}", styles['BodyText']))
        story.append(Paragraph(f"Why Required: {standard.get('Why Required', 'N/A')}", styles['BodyText']))
        story.append(Spacer(1, 6))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- Admin Functions ---
def show_admin_tab():
    """Show admin panel"""
    st.header("Admin Panel")
    st.info("This is the admin panel. Demo users can access this with admin credentials.")
    
    # Display usage statistics (mock data)
    st.subheader("Usage Statistics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Analyses", "47")
    col2.metric("Active Users", "12")
    col3.metric("Compliance Standards", "5")
    
    # Display demo credentials for convenience
    with st.expander("Demo Credentials"):
        st.write("**Admin Account:**")
        st.code("Username: admin\nPassword: admin123")
        st.write("**User Account:**")
        st.code("Username: user\nPassword: user123")
    
    # Mock system settings
    st.subheader("System Settings")
    st.checkbox("Enable email notifications", value=True)
    st.checkbox("Auto-update compliance standards", value=False)
    st.slider("Session timeout (minutes)", 10, 120, 30)

# --- Main App Components ---
def show_login():
    st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
    
    # Display demo credentials for easy access
    with st.expander("Demo Credentials", expanded=True):
        st.write("**Admin Account:**")
        st.code("Username: admin\nPassword: admin123")
        st.write("**User Account:**")
        st.code("Username: user\nPassword: user123")
    
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    with st.form("auth_form"):
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password", value="admin123")
        
        if st.form_submit_button("Login", use_container_width=True):
            if authenticate(username, password):
                st.rerun()
    
    if st.session_state.auth['login_attempts'] >= MAX_LOGIN_ATTEMPTS:
        elapsed = time.time() - st.session_state.auth['last_attempt']
        if elapsed < LOCKOUT_TIME:
            st.warning(f"Account locked. Try again in {int((LOCKOUT_TIME - elapsed) // 60) + 1} minutes.")
    
    st.markdown("</div>", unsafe_allow_html=True)

def show_main_app():
    # Check session timeout
    if time.time() - st.session_state.auth.get('last_activity', 0) > SESSION_TIMEOUT:
        st.session_state.auth['logged_in'] = False
        st.warning("Session timed out due to inactivity")
        st.rerun()
    
    # Update last activity time
    st.session_state.auth['last_activity'] = time.time()
    
    # Header
    st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        st.markdown(f"Welcome, **{st.session_state.auth['name']}**")
    with col2:
        st.markdown(f"*{st.session_state.auth.get('role', 'user').title()}*")
    with col3:
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
            # Display key metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Standards", len(compliance_df))
            col2.metric("Fully Implemented", len(compliance_df[compliance_df['Followed By Compunnel'] == 'Yes']))
            col3.metric("Partially Implemented", len(compliance_df[compliance_df['Followed By Compunnel'] == 'Partial']))
            
            # Display compliance standards by domain
            st.subheader("Compliance Standards by Domain")
            domain_counts = compliance_df['Domain'].value_counts()
            st.bar_chart(domain_counts)
            
            # Display data table
            st.subheader("Compliance Standards Details")
            st.dataframe(compliance_df, use_container_width=True, hide_index=True)
    
    with tab2:
        st.header("Project Compliance Analysis")
        
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        project_description = st.text_area(
            "Describe your project (include data types, industry, and regions):",
            height=150,
            placeholder="e.g., Healthcare app storing patient records in India with EU users...",
            help="Include keywords like 'healthcare', 'payment', 'EU', 'security', etc."
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            analyze_clicked = st.button("Analyze Compliance", type="primary", use_container_width=True)
        with col2:
            if st.session_state.get('analysis_results'):
                report_buffer = generate_pdf_report(
                    st.session_state.analysis_results, 
                    st.session_state.get('project_description', '')
                )
                st.download_button(
                    label="Download PDF Report",
                    data=report_buffer,
                    file_name="compliance_analysis_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        if analyze_clicked:
            if not project_description.strip():
                st.warning("Please enter a project description")
            else:
                with st.spinner("Analyzing compliance requirements..."):
                    # Store project description in session state
                    st.session_state.project_description = project_description
                    
                    # Perform analysis
                    results = analyze_project(project_description, compliance_df)
                    
                    # Store results in session state
                    st.session_state.analysis_results = results
                    
                    # Display results
                    display_results(results)
        
        # Show previous results if available
        elif st.session_state.get('analysis_results'):
            display_results(st.session_state.analysis_results)
    
    with tab3:
        if st.session_state.auth.get('role') == 'admin':
            show_admin_tab()
        else:
            st.error("Admin privileges required")
            st.info("Use admin credentials to access this section: username: 'admin', password: 'admin123'")

# --- Run Application ---
if __name__ == "__main__":
    initialize_auth()
    
    if st.session_state.auth['logged_in']:
        show_main_app()
    else:
        show_login()
    
    st.markdown("---")
    st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro | Demo Version</div>", unsafe_allow_html=True)
