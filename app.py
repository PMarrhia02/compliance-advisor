import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import streamlit_authenticator as stauth
import matplotlib.pyplot as plt
import feedparser
from datetime import datetime
import json
from transformers import pipeline

# Page setup
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# Custom CSS
st.markdown("""
    <style>
        .timeline { margin-top: 2rem; border-left: 3px solid #003366; padding-left: 1rem; }
        .chatbot { background-color: #f8f9fa; padding: 1rem; border-radius: 10px; }
        .template-box { border: 1px dashed #6c757d; padding: 1rem; margin: 1rem 0; }
    </style>
""", unsafe_allow_html=True)

# --- USER AUTHENTICATION (Enhanced) ---
hashed_passwords = stauth.Hasher(['password', 'userpass']).generate()

config = {
    'credentials': {
        'usernames': {
            'admin': {
                'email': 'admin@example.com',
                'name': 'Admin',
                'password': hashed_passwords[0],
                'role': 'admin'
            },
            'user': {
                'email': 'user@example.com',
                'name': 'Standard User',
                'password': hashed_passwords[1],
                'role': 'user'
            }
        }
    },
    'cookie': {
        'name': 'compliance_cookie',
        'key': 'some_random_signature_key',
        'expiry_days': 30
    },
    'preauthorized': {
        'emails': ['admin@example.com']
    }
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    authenticator.logout('Logout', 'sidebar')
    role = config['credentials']['usernames'][username]['role']
    st.sidebar.title(f"Welcome {name} ({role.capitalize()})")
    
    # --- Load Data ---
    @st.cache_data
    def load_data():
        sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            df = pd.read_csv(sheet_url)
            required_cols = [
                'Compliance Name', 'Domain', 'Applies To', 'Checklist 1', 
                'Checklist 2', 'Checklist 3', 'Followed By Compunnel', 
                'Why Required', 'Priority', 'Trigger Alert'
            ]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                st.error(f"Missing required columns: {', '.join(missing_cols)}")
                st.stop()
            return df
        except Exception as e:
            st.error(f"Failed to load data: {str(e)}")
            st.stop()

    compliance_df = load_data()

    # --- Analysis Function ---
    def analyze_project(project_description):
        # Simple keyword-based analysis (replace with more sophisticated logic)
        results = {
            'project_description': project_description,
            'compliance_matches': [],
            'recommendations': []
        }
        
        # Convert to lowercase for case-insensitive matching
        desc_lower = project_description.lower()
        
        # Check for healthcare-related terms
        healthcare_terms = ['phi', 'health record', 'patient data', 'medical', 'treatment history']
        is_healthcare = any(term in desc_lower for term in healthcare_terms)
        
        # Check for India presence
        is_india = 'india' in desc_lower
        
        # Match compliance requirements
        for _, row in compliance_df.iterrows():
            match = False
            reason = []
            
            # Domain matching
            if is_healthcare and 'Healthcare' in row['Domain']:
                match = True
                reason.append("Healthcare data detected")
                
            # Regional requirements
            if is_india and 'India' in row['Applies To']:
                match = True
                reason.append("India operations detected")
                
            if match:
                results['compliance_matches'].append({
                    'name': row['Compliance Name'],
                    'domain': row['Domain'],
                    'applies_to': row['Applies To'],
                    'checklists': [row[f'Checklist {i}'] for i in range(1, 4) if pd.notna(row[f'Checklist {i}'])],
                    'followed': row['Followed By Compunnel'],
                    'why_required': row['Why Required'],
                    'priority': row['Priority'],
                    'trigger_alert': row['Trigger Alert'],
                    'match_reasons': reason
                })
        
        # Generate recommendations
        if is_healthcare and is_india:
            results['recommendations'].append("Implement HIPAA-like controls for PHI protection")
            results['recommendations'].append("Ensure data localization as per India's PDPB requirements")
        
        return results

    # --- Report Generation Functions ---
    def generate_markdown(results):
        markdown = f"# Compliance Report\n\n"
        markdown += f"**Project Description**: {results['project_description']}\n\n"
        
        markdown += "## Required Compliance Frameworks\n"
        for item in results['compliance_matches']:
            markdown += f"- **{item['name']}** (Priority: {item['priority']})\n"
            markdown += f"  - Applies to: {item['applies_to']}\n"
            markdown += f"  - Why required: {item['why_required']}\n"
            markdown += "  - Checklists:\n"
            for checklist in item['checklists']:
                markdown += f"    - {checklist}\n"
        
        markdown += "\n## Recommendations\n"
        for rec in results['recommendations']:
            markdown += f"- {rec}\n"
            
        return markdown

    def generate_policy_template(compliance_name):
        # Simple template generator
        templates = {
            "GDPR": """# GDPR Compliance Policy

1. Data Protection Principles
   - Lawfulness, fairness and transparency
   - Purpose limitation
   - Data minimization
   - Accuracy
   - Storage limitation
   - Integrity and confidentiality

2. Data Subject Rights
   - Right to access
   - Right to rectification
   - Right to erasure
   - Right to restrict processing
   - Right to data portability
   - Right to object""",
            
            "HIPAA": """# HIPAA Compliance Policy

1. Administrative Safeguards
   - Security management process
   - Assigned security responsibility
   - Workforce security

2. Physical Safeguards
   - Facility access controls
   - Workstation use and security

3. Technical Safeguards
   - Access control
   - Audit controls
   - Integrity controls
   - Transmission security"""
        }
        
        return templates.get(compliance_name, f"# {compliance_name} Compliance Policy\n\nCustom policy template goes here.")

    # --- Project Input ---
    project_description = st.text_area(
        "Describe your project (include data types and regions):",
        height=150,
        placeholder="e.g., 'Healthcare app storing patient records in India with EU users...'"
    )

    # --- Interactive Checklist ---
    def interactive_checklist(compliance_items):
        checklist_status = {}
        for item in compliance_items:
            with st.expander(f"{'✅' if item['followed'] else '❌'} {item['name']}"):
                status = st.radio(
                    f"Status for {item['name']}",
                    ['Not Started', 'In Progress', 'Completed'],
                    key=f"status_{item['name']}"
                )
                if status == 'Completed':
                    st.date_input("Completion Date", key=f"date_{item['name']}")
                    st.text_area("Notes", key=f"notes_{item['name']}")
                checklist_status[item['name']] = status
        return checklist_status

    # --- Timeline Visualization ---
    def show_timeline(compliance_data):
        deadlines = {
            'High': [item for item in compliance_data if item['priority'] == 'High'],
            'Standard': [item for item in compliance_data if item['priority'] == 'Standard']
        }
        
        fig, ax = plt.subplots(figsize=(10, 4))
        for i, (priority, items) in enumerate(deadlines.items()):
            dates = [datetime.now().date() for _ in items]
            ax.scatter(dates, [i]*len(items), label=f"{priority} Priority")
        
        ax.set_yticks([0, 1])
        ax.set_yticklabels(['High', 'Standard'])
        ax.set_title("Compliance Deadline Timeline")
        ax.legend()
        st.pyplot(fig)

    # --- Regulatory Updates (Handles missing RSS Feed) ---
    def get_regulatory_updates(df):
        updates = []
        if 'RSS Feed' not in df.columns:  # Skip if column doesn't exist
            return updates
        for _, row in df.dropna(subset=['RSS Feed']).iterrows():
            try:
                feed = feedparser.parse(row['RSS Feed'])
                updates.extend([(row['Compliance Name'], entry.title, entry.link) 
                             for entry in feed.entries[:2]])
            except Exception as e:
                st.error(f"Failed to parse RSS feed: {str(e)}")
                continue
        return updates

    # --- Chatbot Assistant ---
    @st.cache_resource
    def load_chatbot():
        return pipeline('text-generation', model='gpt2')

    def compliance_chatbot(question, compliance_data):
        chatbot = load_chatbot()
        context = "Compliance regulations: " + str(compliance_data[:500])  # Limit context
        prompt = f"Context: {context}\nQuestion: {question}\nAnswer:"
        return chatbot(prompt, max_length=150)[0]['generated_text']

    # --- Main Analysis ---
    if st.button("🔍 Analyze Compliance", type="primary"):
        if not project_description.strip():
            st.warning("Please enter a project description")
            st.stop()
        
        with st.spinner("Analyzing requirements..."):
            results = analyze_project(project_description)
            st.session_state.results = results
            st.success("Analysis complete!")
            
            # Display new features
            st.markdown("### 📅 Compliance Timeline")
            show_timeline(results['compliance_matches'])
            
            st.markdown("### 📝 Interactive Checklist")
            checklist_status = interactive_checklist(results['compliance_matches'])
            
            with st.sidebar.expander("💡 Compliance Assistant"):
                question = st.text_input("Ask about compliance")
                if question:
                    response = compliance_chatbot(question, results['compliance_matches'])
                    st.write(response.split("Answer:")[-1])
            
            with st.sidebar.expander("📰 Regulatory Updates"):
                updates = get_regulatory_updates(compliance_df)
                if not updates:
                    st.info("No RSS feeds configured.")
                for source, title, link in updates:
                    st.markdown(f"**{source}**: [{title}]({link})")

    # --- Report Generation (Enhanced) ---
    if st.session_state.get('results'):
        st.markdown("---")
        st.markdown("## 📤 Generate Reports")
        
        format_choice = st.radio(
            "Select report type:",
            ["PDF Report", "Action Plan (CSV)", "Markdown", "HTML"],
            horizontal=True
        )
        
        if format_choice == "Markdown":
            markdown_report = generate_markdown(st.session_state.results)
            st.download_button(
                "⬇️ Download Markdown",
                markdown_report,
                "compliance_report.md",
                "text/markdown"
            )
        
        # --- Policy Templates (Admin Only) ---
        if role == 'admin':
            with st.expander("🛠️ Policy Templates"):
                selected_compliance = st.selectbox(
                    "Select compliance for template",
                    compliance_df['Compliance Name'].unique()
                )
                if st.button("Generate Template"):
                    template = generate_policy_template(selected_compliance)
                    st.code(template)

    # --- Audit Logging ---
    def log_action(username, action):
        try:
            with open("audit_log.json", "a") as f:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'user': username,
                    'action': action
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            st.error(f"Failed to log action: {str(e)}")

    # Example logging
    log_action(username, "Accessed dashboard")

elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')
