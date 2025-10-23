import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

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

st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
st.markdown("AI-powered compliance analysis for your exact requirements")

# User Authentication
if 'username' not in st.session_state:
    st.session_state.username = None

if st.session_state.username is None:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "password":  # Replace with secure authentication
            st.session_state.username = username
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password.")
else:
    st.success(f"Welcome, {st.session_state.username}!")

    # Load data from Google Sheets
    @st.cache_data
    def load_data():
        sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"  # Replace with your sheet ID
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            df = pd.read_csv(sheet_url)
            required_cols = ['Compliance Name','Domain','Applies To','Checklist 1','Checklist 2','Checklist 3','Followed By Compunnel','Why Required','Priority','Trigger Alert']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                st.error(f"Missing required columns: {', '.join(missing_cols)}")
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

    # Category matching
    def match_category(text, categories):
        text = text.lower()
        scores = {k:0 for k in categories}
        for category, keywords in categories.items():
            for term in keywords:
                if term in text:
                    scores[category] += 2 if term==text.strip() else 1
        # Normalize by number of keywords
        for category in scores:
            if categories[category]:
                scores[category] /= len(categories[category])
        max_score = max(scores.values())
        if max_score > 0:
            return [k for k,v in scores.items() if v==max_score]
        else:
            return ["all"]

    def analyze_project(description):
        domains = {"healthcare":["healthcare","hospital","patient","medical","phi"],
                   "finance":["bank","finance","payment","financial","pci","credit card"],
                   "ai solutions":["ai","artificial intelligence","machine learning","ml"],
                   "govt/defense":["government","defense","military","public sector"],
                   "all":[]}
        data_types = {"PHI":["phi","health data","medical record","patient data"],
                      "PII":["pii","personal data","name","email","address","phone"],
                      "financial":["financial","credit card","transaction","bank account"],
                      "sensitive":["sensitive","confidential","proprietary"]}
        regions = {"India":["india","indian"],"USA":["usa","united states","us"],"EU":["eu","europe","gdpr"],
                   "Canada":["canada"],"Brazil":["brazil","lgpd"],"global":["global","international","worldwide"]}
        
        matched_domain = match_category(description, domains)
        matched_data_type = match_category(description, data_types)
        matched_region = match_category(description, regions)
        
        compliance_matches = []
        for _, row in compliance_df.iterrows():
            row_domains = [x.strip().lower() for x in str(row['Domain']).split(",")]
            domain_match = any(d in row_domains or "all" in row_domains for d in matched_domain)
            applies_to = [x.strip().lower() for x in str(row['Applies To']).split(",")]
            applies_match = any(r.lower() in applies_to or d.lower() in applies_to or "all" in applies_to for r in matched_region for d in matched_data_type)
            if domain_match and applies_match:
                checklist = [str(item) for item in [row['Checklist 1'],row['Checklist 2'],row['Checklist 3']] if pd.notna(item)]
                compliance_matches.append({
                    "name": row['Compliance Name'],
                    "followed": str(row['Followed By Compunnel']).strip().lower()=="yes",
                    "priority": "High" if str(row.get('Priority','')).strip().lower()=="high" else "Standard",
                    "alert": str(row.get('Trigger Alert','No')).strip().lower()=="yes",
                    "checklist": checklist,
                    "why": row.get("Why Required","")
                })
        return {"domain": matched_domain, "data_type": matched_data_type, "region": matched_region, "compliance_matches": compliance_matches}

    # Generate PDF
    def generate_pdf_report(project_info, compliance_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("Compliance Assessment Report", styles['Title']))
        story.append(Spacer(1,12))
        story.append(Paragraph(f"<b>Domain:</b> {', '.join(project_info['domain'])} | <b>Data Type:</b> {', '.join(project_info['data_type'])} | <b>Region:</b> {', '.join(project_info['region'])}", styles['BodyText']))
        story.append(Spacer(1,12))
        data=[["Requirement","Status","Checklist"]]
        for item in compliance_data:
            status="Compliant" if item['followed'] else "Pending"
            checklist="\n".join(item['checklist'])
            data.append([item['name'],status,checklist])
        table = Table(data,colWidths=[2.5*inch,1*inch,3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#003366")),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('ALIGN',(0,0),(-1,0),'CENTER'),
            ('VALIGN',(0,0),(-1,0),'MIDDLE'),
            ('INNERGRID',(0,0),(-1,-1),0.5,colors.lightgrey),
            ('BOX',(0,0),(-1,-1),0.5,colors.grey)
        ]))
        story.append(table)
        doc.build(story)
        buffer.seek(0)
        return buffer

    if st.button("🔍 Analyze Compliance"):
        if not project_description.strip():
            st.warning("Please enter a project description")
            st.stop()
        with st.spinner("Analyzing requirements..."):
            results = analyze_project(project_description)
            st.session_state.results = results
            # Prepare PDF and CSV for sticky download
            st.session_state.pdf_buffer = generate_pdf_report(
                {"domain": results['domain'],"data_type": results['data_type'],"region": results['region']},
                results['compliance_matches']
            )
            action_items=[]
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

    results = st.session_state.get('results')
    if results:
        met = [c for c in results['compliance_matches'] if c['followed']]
        pending = [c for c in results['compliance_matches'] if not c['followed']]
        score = int((len(met)/len(results['compliance_matches']))*100 if results['compliance_matches'] else 0)
        col1,col2,col3 = st.columns(3)
        col1.metric("Compliance Score", f"{score}%")
        col2.metric("Pending Requirements", len(pending))
        col3.metric("High Priority Items", len([c for c in pending if c['priority']=="High"]))
        st.markdown("### 📌 Detected Project Attributes")
        st.markdown(f"**Domain:** {', '.join(results['domain'])} | **Data Type:** {', '.join(results['data_type'])} | **Region:** {', '.join(results['region'])}")
        st.markdown("---")
        st.download_button("⬇️ Download PDF Report", st.session_state.pdf_buffer, "compliance_report.pdf","application/pdf")
        st.download_button("⬇️ Download Action Plan (CSV)", st.session_state.csv_data, "compliance_action_plan.csv","text/csv")
        st.markdown("### 🚨 Priority Matrix")
        for item in pending:
            cls='priority-high' if item['priority']=="High" else 'priority-standard'
            st.markdown(f"<div class='{cls}'><strong>{item['name']}</strong><br/>{item['why']}<br/>Checklist: {', '.join(item['checklist'])}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", unsafe_allow_html=True)
