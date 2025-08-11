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
import bcrypt
import time

# --- Initialization ---
load_dotenv()
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
        .badge-blue { background-color: #d1ecf1; color: #0c5460; }
        .badge-gold { background-color: #fff3cd; color: #856404; }
        .priority-high { border-left: 4px solid #dc3545; padding-left: 10px; margin: 8px 0; }
        .priority-standard { border-left: 4px solid #fd7e14; padding-left: 10px; margin: 8px 0; }
        .dashboard-card { border-radius: 10px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .footer { text-align: center; font-size: 0.9em; color: gray; margin-top: 3rem; }
    </style>
""", unsafe_allow_html=True)

# --- Authentication ---
def initialize_session():
    if 'auth' not in st.session_state:
        st.session_state.auth = {
            'logged_in': False,
            'username': None,
            'login_attempts': 0,
            'last_attempt': 0,
            'last_activity': time.time()
        }

def check_session_timeout():
    if st.session_state.auth['logged_in']:
        elapsed = time.time() - st.session_state.auth['last_activity']
        if elapsed > SESSION_TIMEOUT:
            st.session_state.auth['logged_in'] = False
            st.warning("Session timed out. Please log in again.")
            return False
        st.session_state.auth['last_activity'] = time.time()
    return True

def authenticate(username, password):
    # Check if locked out
    if st.session_state.auth['login_attempts'] >= MAX_LOGIN_ATTEMPTS:
        if time.time() - st.session_state.auth['last_attempt'] < LOCKOUT_TIME:
            remaining = int((LOCKOUT_TIME - (time.time() - st.session_state.auth['last_attempt'])) // 60
            st.error(f"Too many attempts. Try again in {remaining} minutes.")
            return False
        else:
            st.session_state.auth['login_attempts'] = 0

    # Check credentials
    env_user = os.getenv("ADMIN_USER")
    env_pass = os.getenv("ADMIN_PASS")
    
    if username == env_user and bcrypt.checkpw(password.encode(), env_pass.encode()):
        st.session_state.auth.update({
            'logged_in': True,
            'username': username,
            'login_attempts': 0
        })
        return True
    
    # Demo credentials (remove in production)
    demo_user = "demo_admin"
    demo_pass = "Demo@123"
    if username == demo_user and password == demo_pass:
        st.warning("Using demo credentials - configure .env for production")
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

# --- GitHub Integration ---
@st.cache_resource
def get_github_client():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        st.error("GitHub token not configured")
        return None
    return Github(token)

def load_compliance_data():
    """Load data from GitHub or fallback to Google Sheets"""
    try:
        # Try GitHub first
        repo = os.getenv("COMPLIANCE_DATA_REPO")
        if repo and get_github_client():
            contents = get_github_client().get_repo(repo).get_contents("compliance_standards.csv")
            df = pd.read_csv(BytesIO(contents.decoded_content))
            return df
    except Exception as e:
        st.warning(f"GitHub load failed: {str(e)}")
    
    # Fallback to Google Sheets
    sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        df = pd.read_csv(sheet_url)
        required_cols = ['Compliance Name', 'Domain', 'Applies To', 'Checklist 1', 
                        'Checklist 2', 'Checklist 3', 'Followed By Compunnel', 'Why Required']
        
        if all(col in df.columns for col in required_cols):
            return df
        st.error("Missing required columns in data")
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
    
    return pd.DataFrame()

# --- Analysis Functions ---
def match_category(text, categories):
    text = text.lower()
    scores = {k: 0 for k in categories}
    
    for category, keywords in categories.items():
        for term in keywords:
            if term in text:
                scores[category] += 2 if term == text.strip() else 1
    
    for category in scores:
        if categories[category]:
            scores[category] = scores[category] / len(categories[category])
    
    max_score = max(scores.values())
    if max_score > 0:
        return max(scores, key=scores.get)
    return next((cat for cat in categories if cat in ["all", "global"]), list(categories.keys())[0])

def analyze_project(description, compliance_df):
    domains = {
        "healthcare": ["healthcare", "hospital", "patient", "medical", "health", "phi"],
        "finance": ["bank", "finance", "payment", "financial", "pci", "credit card"],
        "ai solutions": ["ai", "artificial intelligence", "machine learning", "ml"],
        "govt/defense": ["government", "defense", "military", "public sector"],
        "all": []
    }
    
    data_types = {
        "PHI": ["phi", "health data", "medical record", "patient data"],
        "PII": ["pii", "personal data", "name", "email", "address", "phone"],
        "financial": ["financial", "credit card", "transaction", "bank account"],
        "sensitive": ["sensitive", "confidential", "proprietary"]
    }
    
    regions = {
        "India": ["india", "indian"],
        "USA": ["usa", "united states", "us"],
        "EU": ["eu", "europe", "gdpr"],
        "Canada": ["canada"],
        "Brazil": ["brazil", "lgpd"],
        "global": ["global", "international", "worldwide"]
    }
    
    matched_domain = match_category(description, domains)
    matched_data_type = match_category(description, data_types)
    matched_region = match_category(description, regions)
    
    compliance_matches = []
    for _, row in compliance_df.iterrows():
        row_domains = [x.strip().lower() for x in str(row['Domain']).split(",")]
        domain_match = "all" in row_domains or matched_domain in row_domains
        
        applies_to = [x.strip().lower() for x in str(row['Applies To']).split(",")]
        applies_match = ("all" in applies_to or 
                        matched_region.lower() in applies_to or 
                        matched_data_type.lower() in applies_to)
        
        if domain_match and applies_match:
            checklist = [str(item) for item in [
                row['Checklist 1'], row['Checklist 2'], row['Checklist 3']
            ] if pd.notna(item)]
            
            compliance_matches.append({
                "name": row['Compliance Name'],
                "domain": str(row['Domain']).lower(),
                "applies_to": applies_to,
                "followed": str(row['Followed By Compunnel']).strip().lower() == "yes",
                "priority": "High" if str(row.get('Priority', '')).strip().lower() == "high" else "Standard",
                "alert": str(row.get('Trigger Alert', 'No')).strip().lower() == "yes",
                "checklist": checklist,
                "why": row.get("Why Required", "")
            })
    
    return {
        "domain": matched_domain,
        "data_type": matched_data_type,
        "region": matched_region,
        "compliance_matches": compliance_matches
    }

# --- Report Generation ---
def generate_pdf_report(project_info, compliance_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph("Compliance Assessment Report", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Project Info
    story.append(Paragraph("Project Details", styles['Heading2']))
    story.append(Paragraph(f"""
        <b>Domain:</b> {project_info['domain']}<br/>
        <b>Data Type:</b> {project_info['data_type']}<br/>
        <b>Region:</b> {project_info['region']}
    """, styles['BodyText']))
    story.append(Spacer(1, 24))
    
    # Compliance Status
    met = [c for c in compliance_data if c['followed']]
    pending = [c for c in compliance_data if not c['followed']]
    
    story.append(Paragraph("Compliance Status", styles['Heading2']))
    status_table = Table([
        ["Total Requirements", len(compliance_data)],
        ["Compliant", f"{len(met)} ({len(met)/len(compliance_data):.0%})"],
        ["Pending", f"{len(pending)} ({len(pending)/len(compliance_data):.0%})"]
    ], colWidths=[2*inch, 1.5*inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    story.append(status_table)
    story.append(Spacer(1, 24))
    
    # Detailed Requirements
    story.append(Paragraph("Detailed Requirements", styles['Heading2']))
    data = [["Requirement", "Status", "Checklist"]]
    for item in compliance_data:
        status = "Compliant" if item['followed'] else "Pending"
        color = colors.green if item['followed'] else colors.red
        checklist = "<br/>".join([f"• {point}" for point in item['checklist']])
        
        data.append([
            Paragraph(item['name'], styles['BodyText']),
            Paragraph(f"<font color='{color.hexval()}'>{status}</font>", styles['BodyText']),
            Paragraph(checklist, styles['BodyText'])
        ])
    
    table = Table(data, colWidths=[2.5*inch, 1*inch, 2.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,0), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- Main App ---
def show_login():
    st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
    st.markdown("AI-powered compliance analysis for your exact requirements")
    
    with st.form("auth_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            if authenticate(username, password):
                st.rerun()
    
    if st.session_state.auth['login_attempts'] >= MAX_LOGIN_ATTEMPTS:
        remaining = int((LOCKOUT_TIME - (time.time() - st.session_state.auth['last_attempt'])) // 60)
        st.warning(f"Account locked. Try again in {remaining} minutes.")

def show_main_app():
    # Header
    st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
    st.markdown(f"Welcome, **{st.session_state.auth['username']}**")
    
    if st.button("Logout", key="logout_btn"):
        st.session_state.auth['logged_in'] = False
        st.rerun()
    
    # Load data
    compliance_df = load_compliance_data()
    
    if compliance_df.empty:
        st.error("Failed to load compliance data")
        return
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Analysis", "⚙️ Admin"])
    
    with tab1:
        st.header("Compliance Overview")
        st.dataframe(compliance_df, use_container_width=True)
    
    with tab2:
        st.header("Project Compliance Analysis")
        project_description = st.text_area(
            "Describe your project (include data types and regions):",
            height=150,
            key="project_desc",
            placeholder="e.g., Healthcare app storing patient records in India with EU users..."
        )
        
        if st.button("Analyze Compliance", type="primary"):
            if not project_description.strip():
                st.warning("Please enter a project description")
            else:
                with st.spinner("Analyzing requirements..."):
                    results = analyze_project(project_description, compliance_df)
                    st.session_state.results = results
                    display_results(results)
    
    with tab3:
        if st.session_state.auth['username'] == os.getenv("ADMIN_USER", "admin"):
            show_admin_tab()
        else:
            st.error("Admin privileges required")

def display_results(results):
    st.success("Analysis complete!")
    
    # Metrics
    met = [c for c in results['compliance_matches'] if c['followed']]
    pending = [c for c in results['compliance_matches'] if not c['followed']]
    score = int((len(met) / len(results['compliance_matches'])) * 100) if results['compliance_matches'] else 0
    
    cols = st.columns(3)
    with cols[0]:
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        st.metric("Compliance Score", f"{score}%")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        st.metric("Pending Requirements", len(pending))
        st.markdown("</div>", unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        high_pri = len([c for c in pending if c['priority'] == "High"])
        st.metric("High Priority Items", high_pri)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Details
    with st.expander("📋 Detailed Compliance Checklist"):
        for item in results['compliance_matches']:
            st.markdown(f"#### {'✅' if item['followed'] else '❌'} {item['name']}")
            st.markdown(f"**Priority:** `{item['priority']}`")
            if item['alert']:
                st.warning("⚠️ Alert: This regulation has recent updates")
            st.markdown("**Requirements:**")
            for point in item['checklist']:
                st.markdown(f"- {point}")
            st.markdown(f"*{item['why']}*")
            st.divider()
    
    # Report generation
    st.markdown("---")
    st.markdown("## 📤 Generate Reports")
    
    if st.button("Download PDF Report"):
        pdf_buffer = generate_pdf_report(
            {
                "domain": results['domain'],
                "data_type": results['data_type'],
                "region": results['region']
            },
            results['compliance_matches']
        )
        st.download_button(
            "⬇️ Save PDF",
            pdf_buffer,
            "compliance_report.pdf",
            "application/pdf"
        )
    
    if st.button("Download Action Plan (CSV)"):
        action_items = []
        for item in results['compliance_matches']:
            if not item['followed']:
                action_items.append({
                    "Requirement": item['name'],
                    "Priority": item['priority'],
                    "Deadline": "30 days" if item['priority'] == "High" else "90 days",
                    "Actions": "; ".join(item['checklist']),
                    "Owner": "[Assign Owner]",
                    "Status": "Not Started"
                })
        
        df = pd.DataFrame(action_items)
        st.download_button(
            "⬇️ Save CSV",
            df.to_csv(index=False),
            "compliance_action_plan.csv",
            "text/csv"
        )

def show_admin_tab():
    st.header("Administration Panel")
    
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

# --- App Entry Point ---
def main():
    initialize_session()
    
    if not check_session_timeout():
        return
    
    if st.session_state.auth['logged_in']:
        show_main_app()
    else:
        show_login()
    
    # Footer
    st.markdown("---")
    st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
