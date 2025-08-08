# app.py
import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import bcrypt
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

# ------------------------
# Page setup & CSS
# ------------------------
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide", page_icon="🛡️")

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

# ------------------------
# Initialize session state
# ------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'results' not in st.session_state:
    st.session_state.results = None

# ------------------------
# Analysis function
# ------------------------
def analyze_project(project_description):
    """Analyze project description and return compliance requirements"""
    try:
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

        # Financial compliance (added for fintech example)
        financial_terms = ['payment', 'credit card', 'bank account', 'fintech']
        if any(term in desc_lower for term in financial_terms):
            results['compliance_matches'].append({
                'name': 'PCI DSS',
                'domain': 'Financial',
                'applies_to': 'Global',
                'checklists': [
                    'Encrypt cardholder data',
                    'Implement strong access control measures',
                    'Regularly test security systems'
                ],
                'followed': False,
                'why_required': 'Handles payment card information',
                'priority': 'High',
                'trigger_alert': True,
                'deadline': datetime.now() + timedelta(days=45)
            })
            results['recommendations'].append("Implement PCI DSS compliance measures")
            results['timeline'].append({
                'task': 'PCI DSS Compliance',
                'start': datetime.now().date(),
                'end': (datetime.now() + timedelta(days=45)).date(),
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

    except Exception as e:
        st.error(f"Error in analysis: {str(e)}")
        return {
            'project_description': project_description,
            'compliance_matches': [],
            'recommendations': [],
            'timeline': []
        }

# ------------------------
# Visualization helpers
# ------------------------
def show_gantt_chart(timeline_data):
    if not timeline_data:
        st.info("No timeline data to show")
        return
    
    try:
        df = pd.DataFrame(timeline_data)
        # ensure date columns are in datetime
        df['start'] = pd.to_datetime(df['start'])
        df['end'] = pd.to_datetime(df['end'])
        fig = px.timeline(df, 
                          x_start="start", 
                          x_end="end", 
                          y="task",
                          color="priority",
                          title="Compliance Timeline")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error showing timeline: {str(e)}")

def show_compliance_matrix(compliance_data):
    if not compliance_data:
        st.info("No compliance matches to show")
        return
    
    try:
        df = pd.DataFrame(compliance_data)
        # For plotting convenience convert priority to ordinal by mapping
        priority_map = {'Low': 1, 'Medium': 2, 'High': 3}
        if 'priority' in df.columns:
            df['priority_val'] = df['priority'].map(priority_map).fillna(1)
        fig = px.bar(df, 
                     x='name', 
                     y='priority_val',
                     color='domain',
                     title="Compliance Priority Matrix",
                     labels={'priority_val': 'Priority (1=Low, 3=High)'})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error showing compliance matrix: {str(e)}")

# ------------------------
# Authentication
# ------------------------
_precreated_users_plain = {
    "admin": "admin123",
    "user": "userpass"
}

# Create hashed passwords
users = {}
for uname, pwd in _precreated_users_plain.items():
    users[uname] = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())

def do_login_block():
    st.sidebar.title("🔐 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    login_btn = st.sidebar.button("Login")

    if login_btn:
        if username in users and bcrypt.checkpw(password.encode(), users[username]):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.results = None  # Clear previous results
            st.sidebar.success(f"Welcome, {username}!")
            st.experimental_rerun()
        else:
            st.sidebar.error("Invalid username or password")

def do_logout():
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.results = None
        st.experimental_rerun()

# ------------------------
# Main App UI
# ------------------------
if not st.session_state.logged_in:
    # Show login block
    do_login_block()
    st.title("Compliance Advisor Pro - Login required")
    st.write("Please login from the sidebar to access the Compliance Advisor.")
else:
    # Logged in - show app
    do_logout()
    st.sidebar.write(f"👤 Logged in as **{st.session_state.username}**")
    role = "admin" if st.session_state.username == "admin" else "user"
    st.sidebar.write(f"**Role:** {role}")

    st.header("Project Compliance Assessment")
    project_description = st.text_area(
        "Describe your project (include data types, regions, and industry):",
        height=150,
        placeholder="e.g., 'Healthcare app storing patient records in India with EU users...'"
    )

    if st.button("🔍 Analyze Compliance"):
        if not project_description.strip():
            st.warning("Please enter a project description")
        else:
            with st.spinner("Analyzing compliance requirements..."):
                st.session_state.results = analyze_project(project_description)

            st.success("Analysis complete!")
            st.balloons()

    # Show results if available
    if st.session_state.results:
        results = st.session_state.results
        
        # Results Overview
        st.subheader("Compliance Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Requirements", len(results['compliance_matches']))
        col2.metric("High Priority",
                    len([x for x in results['compliance_matches'] if x['priority'] == 'High']))
        col3.metric("Recommended Actions", len(results['recommendations']))

        # Visualizations
        st.subheader("Compliance Timeline")
        show_gantt_chart(results['timeline'])

        st.subheader("Priority Matrix")
        show_compliance_matrix(results['compliance_matches'])

        # Detailed Requirements
        st.subheader("Detailed Requirements")
        for item in results['compliance_matches']:
            with st.expander(f"{item['name']} ({item['domain']})", expanded=True):
                st.markdown(f"**Applies to**: {item['applies_to']}")
                st.markdown(f"**Priority**: <span class='priority-{item['priority'].lower()}'>{item['priority']}</span>",
                            unsafe_allow_html=True)
                st.markdown(f"**Why Required**: {item['why_required']}")
                st.markdown("**Checklist**:")
                for i, checklist in enumerate(item['checklists'], 1):
                    st.checkbox(f"{i}. {checklist}", key=f"{item['name']}_check_{i}")

                due_date = item['deadline'].date()
                days_remaining = max(0, (item['deadline'] - datetime.now()).days)
                st.markdown(f"**Deadline**: {due_date}  —  **Days remaining**: {days_remaining}")

                # Progress indicator
                cap_days = 60
                pct_done = max(0, min(100, int((1 - days_remaining / cap_days) * 100)))
                st.progress(pct_done)

    # Report Generation Section (sidebar)
    if st.session_state.results:
        st.sidebar.header("Report Generation")
        report_type = st.sidebar.selectbox("Select report format", ["PDF", "CSV", "Markdown"])
        if st.sidebar.button("Generate Report"):
            with st.spinner(f"Generating {report_type} report..."):
                results = st.session_state.results

                if report_type == "CSV":
                    rows = []
                    for item in results['compliance_matches']:
                        rows.append({
                            "name": item['name'],
                            "domain": item['domain'],
                            "applies_to": item['applies_to'],
                            "priority": item['priority'],
                            "why_required": item['why_required'],
                            "deadline": item['deadline'].strftime("%Y-%m-%d")
                        })
                    df_report = pd.DataFrame(rows)
                    csv_bytes = df_report.to_csv(index=False).encode('utf-8')
                    st.sidebar.success("CSV ready")
                    st.sidebar.download_button("Download CSV", data=csv_bytes, file_name="compliance_report.csv", mime="text/csv")

                elif report_type == "Markdown":
                    md = f"# Compliance Report\n\n**Project:** {results['project_description']}\n\n"
                    for item in results['compliance_matches']:
                        md += f"## {item['name']} ({item['domain']})\n"
                        md += f"- Applies to: {item['applies_to']}\n"
                        md += f"- Priority: {item['priority']}\n"
                        md += f"- Why: {item['why_required']}\n"
                        md += f"- Deadline: {item['deadline'].strftime('%Y-%m-%d')}\n\n"
                    md_bytes = md.encode('utf-8')
                    st.sidebar.success("Markdown ready")
                    st.sidebar.download_button("Download Markdown", data=md_bytes, file_name="compliance_report.md", mime="text/markdown")

                else:  # PDF
                    buffer = BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=A4)
                    styles = getSampleStyleSheet()
                    story = []
                    story.append(Paragraph("Compliance Report", styles['Title']))
                    story.append(Spacer(1, 12))
                    story.append(Paragraph(f"Project: {results['project_description']}", styles['Normal']))
                    story.append(Spacer(1, 12))
                    for item in results['compliance_matches']:
                        story.append(Paragraph(f"{item['name']} ({item['domain']})", styles['Heading2']))
                        story.append(Paragraph(f"Applies to: {item['applies_to']}", styles['Normal']))
                        story.append(Paragraph(f"Priority: {item['priority']}", styles['Normal']))
                        story.append(Paragraph(f"Why: {item['why_required']}", styles['Normal']))
                        story.append(Paragraph(f"Deadline: {item['deadline'].strftime('%Y-%m-%d')}", styles['Normal']))
                        story.append(Spacer(1, 12))
                    doc.build(story)
                    buffer.seek(0)
                    st.sidebar.success("PDF ready")
                    st.sidebar.download_button("Download PDF", data=buffer, file_name="compliance_report.pdf", mime="application/pdf")

    # Initial hint if no analysis done yet
    if not st.session_state.results:
        st.info("Enter a project description and click 'Analyze Compliance' to get recommendations and reports.")
