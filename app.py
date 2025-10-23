import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import difflib

# Page setup
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# Custom CSS
st.markdown("""
<style>
.title { font-size: 2.5em; color: #003366; font-weight: bold; }
.badge { display: inline-block; padding: 0.25em 0.6em; font-size: 90%; font-weight: 600; border-radius: 0.25rem; }
.badge-blue { background-color: #d1ecf1; color: #0c5460; }
.priority-high { border-left: 4px solid #dc3545; padding-left: 10px; margin: 8px 0; }
.priority-standard { border-left: 4px solid #fd7e14; padding-left: 10px; margin: 8px 0; }
.dashboard-card { border-radius: 10px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.footer { text-align: center; font-size: 0.9em; color: gray; margin-top: 3rem; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
st.markdown("AI-powered compliance analysis for your exact requirements")

# User Authentication (simple)
if 'username' not in st.session_state:
    st.session_state.username = None

if st.session_state.username is None:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username == "admin" and password == "password":  # replace with secure auth
            st.session_state.username = username
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password.")
else:
    st.success(f"Welcome, {st.session_state.username}!")

    # Load Excel data
    @st.cache_data
    def load_data():
        try:
            df = pd.read_excel("compliance_data.xlsx")  # your Excel file
            required_cols = ['Compliance Name', 'Domain', 'Applies To', 
                             'Checklist 1','Checklist 2','Checklist 3', 
                             'Followed By Compunnel','Why Required','Priority','Trigger Alert']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                st.error(f"Missing columns: {missing}")
                st.stop()
            return df
        except Exception as e:
            st.error(f"Failed to load data: {str(e)}")
            st.stop()
    
    compliance_df = load_data()

    # Project input
    project_description = st.text_area(
        "Describe your project (include data types and regions):",
        height=150,
        placeholder="e.g., 'Healthcare app storing patient records in India with EU users...'"
    )

    # Fuzzy matching function
    def match_category(text, categories, threshold=0.6):
        text = text.lower()
        scores = {}
        for category, keywords in categories.items():
            max_score = 0
            for kw in keywords:
                score = difflib.SequenceMatcher(None, text, kw.lower()).ratio()
                if score > max_score:
                    max_score = score
            scores[category] = max_score
        max_score_value = max(scores.values())
        if max_score_value >= threshold:
            for k, v in scores.items():
                if v == max_score_value:
                    return k
        return "all"

    # Analysis function
    def analyze_project(description):
        domains = {
            "healthcare": ["healthcare", "hospital", "patient", "medical", "phi"],
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
            "USA": ["usa", "united states", "us"],
            "EU": ["eu", "europe", "gdpr"],
            "Canada": ["canada"],
            "Brazil": ["brazil", "lgpd"],
            "global": ["global", "international", "worldwide"]
        }

        matched_domain = match_category(description, domains)
        matched_data_type = match_category(description, data_types)
        matched_region = match_category(description, regions)

        # Filter compliance items
        compliance_matches = []
        for _, row in compliance_df.iterrows():
            row_domains = [x.strip().lower() for x in str(row['Domain']).split(",")]
            domain_match = "all" in row_domains or matched_domain in row_domains

            applies_to = [x.strip().lower() for x in str(row['Applies To']).split(",")]
            applies_match = "all" in applies_to or matched_region.lower() in applies_to or matched_data_type.lower() in applies_to

            if domain_match and applies_match:
                checklist = [str(row[i]) for i in ['Checklist 1','Checklist 2','Checklist 3'] if pd.notna(row[i])]
                compliance_matches.append({
                    "name": row['Compliance Name'],
                    "followed": str(row['Followed By Compunnel']).strip().lower() == "yes",
                    "priority": "High" if str(row.get('Priority','')).strip().lower()=='high' else "Standard",
                    "alert": str(row.get('Trigger Alert','')).strip().lower()=='yes',
                    "why": row.get('Why Required',''),
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
        story.append(Paragraph("Project Details", styles['Heading2']))
        story.append(Paragraph(f"Domain: {project_info['domain']}<br/>Data Type: {project_info['data_type']}<br/>Region: {project_info['region']}", styles['BodyText']))
        story.append(Spacer(1,12))

        # Status table
        met = [c for c in compliance_data if c['followed']]
        pending = [c for c in compliance_data if not c['followed']]
        story.append(Paragraph("Compliance Status", styles['Heading2']))
        table = Table([
            ["Total Requirements", len(compliance_data)],
            ["Compliant", f"{len(met)}"],
            ["Pending", f"{len(pending)}"]
        ], colWidths=[2*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#003366")),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('BOX',(0,0),(-1,-1),0.5,colors.grey)
        ]))
        story.append(table)
        story.append(Spacer(1,12))

        # Detailed compliance
        story.append(Paragraph("Detailed Requirements", styles['Heading2']))
        for item in compliance_data:
            status = "Compliant" if item['followed'] else "Pending"
            story.append(Paragraph(f"{status} - {item['name']} ({', '.join(item['checklist'])})", styles['BodyText']))

        doc.build(story)
        buffer.seek(0)
        return buffer

    # Main Analysis Button
    if st.button("🔍 Analyze Compliance"):
        if not project_description.strip():
            st.warning("Please enter a project description")
            st.stop()
        
        results = analyze_project(project_description)
        st.session_state.results = results

        # Metrics
        met = [c for c in results['compliance_matches'] if c['followed']]
        pending = [c for c in results['compliance_matches'] if not c['followed']]
        score = int((len(met)/len(results['compliance_matches'])*100) if results['compliance_matches'] else 0)

        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Compliance Score", f"{score}%")
        with col2: st.metric("Pending Requirements", len(pending))
        with col3: st.metric("High Priority Items", len([c for c in pending if c['priority']=="High"]))

        # Project Attributes
        st.markdown(f"**Domain:** <span class='badge badge-blue'>{results['domain']}</span>", unsafe_allow_html=True)
        st.markdown(f"**Data Type:** <span class='badge badge-blue'>{results['data_type']}</span>", unsafe_allow_html=True)
        st.markdown(f"**Region:** <span class='badge badge-blue'>{results['region']}</span>", unsafe_allow_html=True)

        # Priority Matrix
        st.markdown("### 🚨 Priority Matrix")
        for item in pending:
            div_class = "priority-high" if item['priority']=="High" else "priority-standard"
            st.markdown(f"<div class='{div_class}'><strong>{item['name']}</strong><br/>{item['why']}<br/>Checklist: {', '.join(item['checklist'])}</div>", unsafe_allow_html=True)

        # Compliant list
        if met:
            st.markdown("### ✅ Compliant Requirements")
            for item in met:
                st.markdown(f"- {item['name']} ({', '.join(item['checklist'])})")

    # Download Reports
    if st.session_state.get('results'):
        results = st.session_state.results
        st.markdown("---")
        st.markdown("## 📤 Download Reports")
        format_choice = st.radio("Select report type:", ["PDF Report", "Action Plan (CSV)"], horizontal=True)

        if format_choice=="PDF Report":
            pdf_buffer = generate_pdf_report(
                {"domain": results['domain'], "data_type": results['data_type'], "region": results['region']},
                results['compliance_matches']
            )
            st.download_button("⬇️ Download PDF Report", pdf_buffer, "compliance_report.pdf", "application/pdf")
        else:
            # CSV
            action_items = []
            for item in results['compliance_matches']:
                if not item['followed']:
                    action_items.append({
                        "Requirement": item['name'],
                        "Priority": item['priority'],
                        "Actions": "; ".join(item['checklist']),
                        "Status": "Not Started",
                        "Owner": "[Assign Owner]"
                    })
            df = pd.DataFrame(action_items)
            csv = df.to_csv(index=False)
            st.download_button("⬇️ Download Action Plan", csv, "compliance_action_plan.csv", "text/csv")

    # Footer
    st.markdown("---")
    st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", unsafe_allow_html=True)
