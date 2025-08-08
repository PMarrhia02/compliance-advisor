# app.py
import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import bcrypt
import plotly.express as px
from datetime import datetime, timedelta

# ------------------------
# Page setup & CSS
# ------------------------
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
        .priority-high { color: #dc3545; font-weight: bold; }
        .priority-medium { color: #fd7e14; font-weight: bold; }
        .priority-low { color: #28a745; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ------------------------
# Simplified Analysis function
# ------------------------
def analyze_project(project_description):
    """Simplified analysis without complex date handling"""
    results = {
        'project_description': project_description,
        'compliance_matches': [],
        'recommendations': []
    }
    
    desc_lower = project_description.lower()

    # Healthcare compliance (simplified)
    healthcare_terms = ['phi', 'health record', 'patient data', 'medical', 'hipaa']
    if any(term in desc_lower for term in healthcare_terms):
        results['compliance_matches'].append({
            'name': 'HIPAA',
            'domain': 'Healthcare',
            'applies_to': 'US',
            'checklists': ['Encrypt PHI at rest and in transit', 
                           'Implement access controls'],
            'priority': 'High'
        })
        results['recommendations'].append("Implement HIPAA-compliant security measures")

    # Financial compliance (simplified)
    financial_terms = ['payment', 'credit card', 'bank account', 'fintech']
    if any(term in desc_lower for term in financial_terms):
        results['compliance_matches'].append({
            'name': 'PCI DSS',
            'domain': 'Financial',
            'applies_to': 'Global',
            'checklists': ['Encrypt cardholder data',
                           'Implement access controls'],
            'priority': 'High'
        })
        results['recommendations'].append("Implement PCI DSS compliance measures")

    return results

# ------------------------
# Visualization helpers (simplified)
# ------------------------
def show_compliance_matrix(compliance_data):
    if not compliance_data:
        return
    try:
        df = pd.DataFrame(compliance_data)
        priority_map = {'Low': 1, 'Medium': 2, 'High': 3}
        df['priority_val'] = df['priority'].map(priority_map).fillna(1)
        fig = px.bar(df, 
                    x='name', 
                    y='priority_val',
                    color='domain',
                    title="Compliance Priority Matrix")
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        pass

# ------------------------
# Authentication (simplified)
# ------------------------
users = {
    "admin": bcrypt.hashpw(b"admin123", bcrypt.gensalt()),
    "user": bcrypt.hashpw(b"userpass", bcrypt.gensalt())
}

def login():
    st.sidebar.title("🔐 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if username in users and bcrypt.checkpw(password.encode(), users[username]):
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.experimental_rerun()

# ------------------------
# Main App
# ------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login()
    st.title("Please login")
else:
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.experimental_rerun()
    
    st.header("Project Compliance Assessment")
    project_description = st.text_area("Describe your project:", height=150)

    if st.button("Analyze"):
        if project_description.strip():
            st.session_state['results'] = analyze_project(project_description)
    
    if 'results' in st.session_state and st.session_state['results']:
        results = st.session_state['results']
        
        st.subheader("Compliance Overview")
        st.write(f"Found {len(results['compliance_matches'])} requirements")
        
        st.subheader("Priority Matrix")
        show_compliance_matrix(results['compliance_matches'])

        st.subheader("Recommendations")
        for rec in results['recommendations']:
            st.write(f"- {rec}")
