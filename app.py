import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import streamlit_authenticator as stauth
import bcrypt
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
        .timeline { margin-top: 2rem; border-left: 3px solid #003366; padding-left: 1rem; }
        .chatbot { background-color: #f8f9fa; padding: 1rem; border-radius: 10px; }
        .template-box { border: 1px dashed #6c757d; padding: 1rem; margin: 1rem 0; }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
st.markdown("AI-powered compliance analysis for your exact requirements")

# --- CORE APP FUNCTIONS (Moved to global scope) ---

def analyze_project(project_description):
    results = {
        'project_description': project_description,
        'compliance_matches': [],
        'recommendations': []
    }
    desc_lower = project_description.lower()
    
    healthcare_terms = ['phi', 'health record', 'patient data', 'medical', 'treatment history']
    is_healthcare = any(term in desc_lower for term in healthcare_terms)
    
    is_india = 'india' in desc_lower
    
    results['compliance_matches'] = [
        {
            'name': 'HIPAA',
            'domain': 'Healthcare',
            'applies_to': 'US',
            'checklists': ['Encrypt PHI', 'Access controls', 'Audit logs'],
            'followed': False,
            'why_required': 'Handles patient health information',
            'priority': 'High',
            'trigger_alert': True,
            'match_reasons': ['Healthcare data detected']
        },
        {
            'name': 'GDPR',
            'domain': 'Data Privacy',
            'applies_to': 'EU',
            'checklists': ['Data protection impact assessment', 'Appoint DPO', 'User consent mechanisms'],
            'followed': True,
            'why_required': 'May process EU citizen data',
            'priority': 'Standard',
            'trigger_alert': False,
            'match_reasons': ['International operations']
        }
    ]
    
    results['recommendations'] = [
        "Implement data encryption for sensitive information",
        "Create a data retention policy",
        "Establish access control procedures"
    ]
    
    return results

@st.cache_data
def load_data():
    try:
        data = {
            'Compliance Name': ['HIPAA', 'GDPR', 'PDPB'],
            'Domain': ['Healthcare', 'Data Privacy', 'Data Privacy'],
            'Applies To': ['US', 'EU', 'India'],
            'Checklist 1': ['Encrypt PHI', 'DPIA', 'Data Localization'],
            'Checklist 2': ['Access controls', 'Appoint DPO', 'Consent Mechanisms'],
            'Checklist 3': ['Audit logs', 'User rights', 'Data Protection Officer'],
            'Followed By Compunnel': [False, True, False],
            'Why Required': ['Patient data', 'EU citizens', 'Indian law'],
            'Priority': ['High', 'Standard', 'High'],
            'Trigger Alert': [True, False, True]
        }
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        st.stop()

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

@st.cache_resource
def load_chatbot():
    return pipeline('text-generation', model='gpt2')

def compliance_chatbot(question, compliance_data):
    chatbot = load_chatbot()
    context = "Compliance regulations: " + str(compliance_data[:500])
    prompt = f"Context: {context}\nQuestion: {question}\nAnswer:"
    return chatbot(prompt, max_length=150)[0]['generated_text']

# --- USER AUTHENTICATION ---
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

# --- MAIN APP LOGIC ---

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    authenticator.logout('Logout', 'sidebar')
    role = config['credentials']['usernames'][username]['role']
    st.sidebar.title(f"Welcome {name} ({role.capitalize()})")
    
    compliance_df = load_data()

    project_description = st.text_area(
        "Describe your project (include data types and regions):",
        height=150,
        placeholder="e.g., 'Healthcare app storing patient records in India with EU users...'"
    )

    if st.button("🔍 Analyze Compliance", type="primary"):
        if not project_description.strip():
            st.warning("Please enter a project description")
            st.stop()
        
        with st.spinner("Analyzing requirements..."):
            results = analyze_project(project_description)
            st.session_state.results = results
            st.success("Analysis complete!")
            
            st.markdown("### 📅 Compliance Timeline")
            show_timeline(results['compliance_matches'])
            
            st.markdown("### 📝 Interactive Checklist")
            interactive_checklist(results['compliance_matches'])
            
            with st.sidebar.expander("💡 Compliance Assistant"):
                question = st.text_input("Ask about compliance")
                if question:
                    response = compliance_chatbot(question, results['compliance_matches'])
                    st.write(response.split("Answer:")[-1])

elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')

# Footer
st.markdown("---")
st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", unsafe_allow_html=True)
