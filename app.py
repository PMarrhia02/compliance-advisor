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
from datetime import datetime, timedelta
import json
from transformers import pipeline
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image
import base64

# ---------------------------------------------------------
#  Page setup
# ---------------------------------------------------------
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide", page_icon="🛡️")

# Custom CSS
st.markdown("""
    <style>
        .timeline { margin-top: 2rem; border-left: 3px solid #003366; padding-left: 1rem; }
        .chatbot { background-color: #f8f9fa; padding: 1rem; border-radius: 10px; }
        .template-box { border: 1px dashed #6c757d; padding: 1rem; margin: 1rem 0; }
        .priority-high { color: #dc3545; font-weight: bold; }
        .priority-medium { color: #fd7e14; font-weight: bold; }
        .priority-low { color: #28a745; font-weight: bold; }
        .stProgress > div > div > div > div { background-color: #003366; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
#  Analysis Function (moved up so it’s always available)
# ---------------------------------------------------------
def analyze_project(project_description):
    """Analyze project description and return compliance requirements"""
    results = {
        'project_description': project_description,
        'compliance_matches': [],
        'recommendations': [],
        'timeline': []
    }
    
    desc_lower = project_description.lower()

    # Healthcare compliance
    healthcare_terms = ['phi', 'health record', 'patient data', 'medical', 'hipaa']
    if any(term in desc_lower for term in healthcare_terms):
        results['compliance_matches'].append({
            'name': 'HIPAA',
            'domain': 'Healthcare',
            'applies_to': 'US',
            'checklists': ['Encrypt PHI at rest and in transit', 
                           'Implement access controls', 
                           'Maintain audit logs'],
            'followed': False,
            'why_required': 'Handles protected health information',
            'priority': 'High',
            'trigger_alert': True,
            'deadline': datetime.now() + timedelta(days=30)
        })
        results['recommendations'].append("Implement HIPAA-compliant security measures")
        results['timeline'].append({
            'task': 'HIPAA Compliance',
            'start': datetime.now().date(),
            'end': (datetime.now() + timedelta(days=30)).date(),
            'priority': 'High'
        })

    # India compliance
    if 'india' in desc_lower:
        results['compliance_matches'].append({
            'name': 'India PDPB',
            'domain': 'Data Privacy',
            'applies_to': 'India',
            'checklists': ['Data localization', 
                           'Appoint Data Protection Officer',
                           'Implement consent mechanisms'],
            'followed': False,
            'why_required': 'Processing data of Indian residents',
            'priority': 'High',
            'trigger_alert': True,
            'deadline': datetime.now() + timedelta(days=45)
        })
        results['recommendations'].append("Prepare for India's Personal Data Protection Bill")
        results['timeline'].append({
            'task': 'India PDPB Compliance',
            'start': datetime.now().date(),
            'end': (datetime.now() + timedelta(days=45)).date(),
            'priority': 'High'
        })

    # GDPR compliance
    if any(term in desc_lower for term in ['eu', 'europe', 'gdpr']):
        results['compliance_matches'].append({
            'name': 'GDPR',
            'domain': 'Data Privacy',
            'applies_to': 'EU',
            'checklists': ['Data Protection Impact Assessment',
                           'Appoint EU Representative',
                           'Implement user rights mechanisms'],
            'followed': False,
            'why_required': 'Processing data of EU residents',
            'priority': 'High',
            'trigger_alert': True,
            'deadline': datetime.now() + timedelta(days=60)
        })
        results['recommendations'].append("Implement GDPR compliance program")
        results['timeline'].append({
            'task': 'GDPR Compliance',
            'start': datetime.now().date(),
            'end': (datetime.now() + timedelta(days=60)).date(),
            'priority': 'High'
        })

    return results

# ---------------------------------------------------------
#  Visualization Functions
# ---------------------------------------------------------
def show_gantt_chart(timeline_data):
    df = pd.DataFrame(timeline_data)
    fig = px.timeline(df, 
                      x_start="start", 
                      x_end="end", 
                      y="task",
                      color="priority",
                      title="Compliance Timeline")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

def show_compliance_matrix(compliance_data):
    df = pd.DataFrame(compliance_data)
    fig = px.bar(df, 
                 x='name', 
                 y='priority',
                 color='domain',
                 title="Compliance Priority Matrix")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
#  Authentication Setup
# ---------------------------------------------------------
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

# ---------------------------------------------------------
#  Main App Logic
# ---------------------------------------------------------
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    authenticator.logout('Logout', 'sidebar')
    role = config['credentials']['usernames'][username]['role']
    st.sidebar.title(f"Welcome {name} ({role.capitalize()})")
    
    st.header("Project Compliance Assessment")
    project_description = st.text_area(
        "Describe your project (include data types, regions, and industry):",
        height=150,
        placeholder="e.g., 'Healthcare app storing patient records in India with EU users...'"
    )
    
    if st.button("🔍 Analyze Compliance", type="primary"):
        if not project_description.strip():
            st.warning("Please enter a project description")
        else:
            with st.spinner("Analyzing compliance requirements..."):
                results = analyze_project(project_description)
                st.session_state.results = results
                
                st.success("Analysis complete!")
                st.balloons()
                
                # Overview
                st.subheader("Compliance Overview")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Requirements", len(results['compliance_matches']))
                col2.metric("High Priority", len([x for x in results['compliance_matches'] if x['priority'] == 'High']))
                col3.metric("Recommended Actions", len(results['recommendations']))
                
                # Charts
                st.subheader("Compliance Timeline")
                show_gantt_chart(results['timeline'])
                
                st.subheader("Priority Matrix")
                show_compliance_matrix(results['compliance_matches'])
                
                # Detailed
                st.subheader("Detailed Requirements")
                for item in results['compliance_matches']:
                    with st.expander(f"{item['name']} ({item['domain']})", expanded=True):
                        st.markdown(f"**Applies to**: {item['applies_to']}")
                        st.markdown(f"**Priority**: <span class='priority-{item['priority'].lower()}'>{item['priority']}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Why Required**: {item['why_required']}")
                        st.markdown("**Checklist**:")
                        for i, checklist in enumerate(item['checklists'], 1):
                            st.checkbox(f"{i}. {checklist}", key=f"{item['name']}_check_{i}")
                        due_date = item['deadline'].strftime("%Y-%m-%d")
                        st.markdown(f"**Deadline**: {due_date}")
                        st.progress(min(100, int((item['deadline'] - datetime.now()).days)))

    # Report generation
    if 'results' in st.session_state:
        st.sidebar.header("Report Generation")
        report_type = st.sidebar.selectbox("Select report format", ["PDF", "CSV", "Markdown"])
        
        if st.sidebar.button("Generate Report"):
            with st.spinner(f"Generating {report_type} report..."):
                st.success(f"{report_type} report generated successfully!")
                st.sidebar.download_button(
                    label="Download Report",
                    data="Sample report content",  
                    file_name=f"compliance_report.{report_type.lower()}",
                    mime="application/pdf" if report_type == "PDF" else "text/csv"
                )

elif authentication_status is False:
    st.error('Username/password is incorrect')

elif authentication_status is None:
    st.warning('Please enter your username and password')
