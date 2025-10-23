import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from rapidfuzz import fuzz

# Page setup
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# CSS
st.markdown("""
<style>
.title { font-size: 2.5em; color: #003366; font-weight: bold; }
.badge { display: inline-block; padding: 0.25em 0.6em; font-size: 90%; font-weight: 600; border-radius: 0.25rem; }
.badge-blue { background-color: #d1ecf1; color: #0c5460; }
.dashboard-card { border-radius: 10px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.priority-high { border-left: 4px solid #dc3545; padding-left: 10px; margin: 8px 0; }
.priority-standard { border-left: 4px solid #fd7e14; padding-left: 10px; margin: 8px 0; }
.footer { text-align: center; font-size: 0.9em; color: gray; margin-top: 3rem; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
st.markdown("AI-powered compliance analysis for your exact requirements")

# Load data
@st.cache_data
def load_data():
    sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    df = pd.read_csv(sheet_url)
    return df

compliance_df = load_data()

# Project input
project_description = st.text_area(
    "Describe your project (include data types and regions):",
    height=150,
    placeholder="e.g., 'Healthcare app storing patient records in India with EU users...'"
)

# Fuzzy matching function
def match_category_fuzzy(text, categories, threshold=70):
    text = text.lower()
    scores = {k: 0 for k in categories}
    for category, keywords in categories.items():
        for kw in keywords:
            score = fuzz.partial_ratio(kw.lower(), text)
            if score >= threshold:
                scores[category] += score / 100  # scale 0-1
    max_score = max(scores.values())
    if max_score > 0:
        # return only highest scoring category
        return max(scores, key=scores.get)
    return "all"

# Analysis
def analyze_project(description):
    # Define matching categories
    domains = {
        "healthcare": ["healthcare", "hospital", "patient", "medical", "health", "phi"],
        "finance": ["bank", "finance", "payment", "financial", "pci", "credit card"],
        "ai solutions": ["ai", "artificial intelligence", "machine learning", "ml"],
        "govt/defense": ["government", "defense", "military", "public sector"],
        "cloud services": ["cloud", "saas", "iaas", "paas"],
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
        "USA": ["usa", "united states", "us", "california"],
        "EU": ["eu", "europe", "gdpr"],
        "Canada": ["canada"],
        "Brazil": ["brazil", "lgpd"],
        "global": ["global", "international", "worldwide"]
    }

    matched_domain = match_category_fuzzy(description, domains)
    matched_data_type = match_category_fuzzy(description, data_types)
    matched_region = match_category_fuzzy(description, regions)

    compliance_matches = []
    for _, row in compliance_df.iterrows():
        row_domains = [x.strip().lower() for x in str(row['Domain']).split(",")]
        domain_match = "all" in row_domains or matched_domain in row_domains

        applies_to = [x.strip().lower() for x in str(row['Applies To']).split(",")]
        applies_match = ("all" in applies_to or matched_region.lower() in applies_to or matched_data_type.lower() in applies_to)

        if domain_match and applies_match:
            checklist = [str(row.get(f"Checklist {i}", "")) for i in range(1,4) if pd.notna(row.get(f"Checklist {i}", None))]
            compliance_matches.append({
                "name": row['Compliance Name'],
                "followed": str(row['Followed By Compunnel']).strip().lower() == "yes",
                "priority": "High" if str(row.get('Priority','')).strip().lower() == "high" else "Standard",
                "why": row.get("Why Required", ""),
                "checklist": checklist
            })

    return {
        "domain": matched_domain,
        "data_type": matched_data_type,
        "region": matched_region,
        "compliance_matches": compliance_matches
    }

# PDF generation
def generate_pdf_report(project_info, compliance_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("Compliance Assessment Report", styles['Title']))
    story.append(Spacer(1,12))
    story.append(Paragraph(f"<b>Domain:</b> {project_info['domain']}<br/><b>Data Type:</b> {project_info['data_type']}<br/><b>Region:</b> {project_info['region']}", styles['BodyText']))
    story.append(Spacer(1,12))
    for item in compliance_data:
        status = "✅ Compliant" if item['followed'] else "❌ Pending"
        story.append(Paragraph(f"{status} {item['name']} - {item['why']}", styles['BodyText']))
        for point in item['checklist']:
            story.append(Paragraph(f"• {point}", styles['BodyText']))
    doc.build(story)
    buffer.seek(0)
    return buffer

# Main logic
if st.button("🔍 Analyze Compliance"):
    if not project_description.strip():
        st.warning("Please enter a project description")
        st.stop()

    results = analyze_project(project_description)
    st.session_state.results = results

    # Metrics
    met = [c for c in results['compliance_matches'] if c['followed']]
    pending = [c for c in results['compliance_matches'] if not c['followed']]
    score = int((len(met)/len(results['compliance_matches']))*100 if results['compliance_matches'] else 0)

    col1,col2,col3 = st.columns(3)
    col1.metric("Compliance Score", f"{score}%")
    col2.metric("Pending Requirements", len(pending))
    high_pri = len([c for c in pending if c['priority']=="High"])
    col3.metric("High Priority Items", high_pri)

    # Project Attributes
    st.markdown(f"**Domain:** <span class='badge badge-blue'>{results['domain']}</span>", unsafe_allow_html=True)
    st.markdown(f"**Data Type:** <span class='badge badge-blue'>{results['data_type']}</span>", unsafe_allow_html=True)
    st.markdown(f"**Region:** <span class='badge badge-blue'>{results['region']}</span>", unsafe_allow_html=True)

    # Priority Matrix & Compliance list
    for item in pending:
        div_class = "priority-high" if item['priority']=="High" else "priority-standard"
        st.markdown(f"<div class='{div_class}'><strong>{item['name']}</strong><br/>{item['why']}<br/>Checklist: {', '.join(item['checklist'])}</div>", unsafe_allow_html=True)

    # Save PDF & CSV in session_state
    st.session_state.pdf_buffer = generate_pdf_report(
        {"domain": results['domain'], "data_type": results['data_type'], "region": results['region']},
        results['compliance_matches']
    )

    action_items = []
    for item in results['compliance_matches']:
        if not item['followed']:
            action_items.append({
                "Requirement": item['name'],
                "Priority": item['priority'],
                "Deadline": "30 days" if item['priority']=="High" else "90 days",
                "Actions": "; ".join(item['checklist']),
                "Owner": "[Assign Owner]",
                "Status": "Not Started"
            })
    st.session_state.csv_data = pd.DataFrame(action_items).to_csv(index=False)

# Download buttons
if st.session_state.get('results'):
    st.markdown("### 📤 Download Reports")
    st.download_button("⬇️ Download PDF Report", st.session_state.pdf_buffer, "compliance_report.pdf", "application/pdf")
    st.download_button("⬇️ Download CSV Action Items", st.session_state.csv_data, "action_items.csv", "text/csv")

# Footer
st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", unsafe_allow_html=True)
