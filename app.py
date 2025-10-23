import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import re

# ---------------- Page Setup ---------------- #
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")
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

# ---------------- Authentication ---------------- #
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

    # ---------------- Load Compliance Data ---------------- #
    @st.cache_data
    def load_data():
        # replace with your CSV / Google Sheet path
        df = pd.read_csv("compliance_data.csv")  # your CSV
        required_cols = [
            'Compliance Name','Domain','Applies To',
            'Checklist 1','Checklist 2','Checklist 3',
            'Followed By Compunnel','Why Required','Priority','Trigger Alert'
        ]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            st.error(f"Missing columns: {', '.join(missing)}")
            st.stop()
        return df

    compliance_df = load_data()

    # ---------------- Project Input ---------------- #
    project_description = st.text_area(
        "Describe your project (include data types and regions):",
        height=150,
        placeholder="e.g., 'Healthcare app storing patient records in India with EU users...'"
    )

    # ---------------- Matching Logic ---------------- #
    def match_category(description, categories, threshold=0.3):
        description = description.lower()
        words = re.findall(r'\b\w+\b', description)
        matched = []
        for category, keywords in categories.items():
            if not keywords:
                continue
            matches = sum(1 for kw in keywords if kw.lower() in description)
            if matches / len(keywords) >= threshold:
                matched.append(category)
        return matched if matched else ["No clear match"]

    def analyze_project(description):
        domains = {
            "healthcare": ["healthcare","hospital","patient","medical","phi"],
            "finance": ["bank","finance","payment","financial","pci","credit card"],
            "ai solutions": ["ai","artificial intelligence","machine learning","ml"],
            "govt/defense": ["government","defense","military","public sector"],
            "all": []
        }
        data_types = {
            "PHI":["phi","health data","medical record","patient data"],
            "PII":["pii","personal data","name","email","address","phone"],
            "financial":["financial","credit card","transaction","bank account"],
            "sensitive":["sensitive","confidential","proprietary"]
        }
        regions = {
            "India":["india","indian"], "USA":["usa","united states","us"],
            "EU":["eu","europe","gdpr"], "Canada":["canada"],
            "Brazil":["brazil","lgpd"], "global":["global","international","worldwide"]
        }

        matched_domains = match_category(description, domains)
        matched_data_types = match_category(description, data_types)
        matched_regions = match_category(description, regions)

        compliance_matches=[]
        for _, row in compliance_df.iterrows():
            row_domains = [x.strip().lower() for x in str(row['Domain']).split(",")]
            row_applies = [x.strip().lower() for x in str(row['Applies To']).split(",")]
            domain_match = any(d.lower() in row_domains or "all" in row_domains for d in matched_domains)
            applies_match = any(a.lower() in row_applies or "all" in row_applies for a in matched_data_types + matched_regions)
            if domain_match and applies_match:
                checklist = [str(i) for i in [row['Checklist 1'],row['Checklist 2'],row['Checklist 3']] if pd.notna(i)]
                compliance_matches.append({
                    "name": row['Compliance Name'],
                    "domain": row_domains,
                    "applies_to": row_applies,
                    "followed": str(row['Followed By Compunnel']).strip().lower()=="yes",
                    "priority":"High" if str(row.get('Priority',"")).strip().lower()=="high" else "Standard",
                    "alert": str(row.get("Trigger Alert","No")).strip().lower()=="yes",
                    "checklist": checklist,
                    "why": row.get("Why Required","")
                })
        return {
            "domain": matched_domains,
            "data_type": matched_data_types,
            "region": matched_regions,
            "compliance_matches": compliance_matches
        }

    # ---------------- PDF Generation ---------------- #
    def generate_pdf_report(project_info, compliance_data):
        buffer=BytesIO()
        doc=SimpleDocTemplate(buffer,pagesize=A4)
        styles=getSampleStyleSheet()
        story=[]
        story.append(Paragraph("Compliance Assessment Report",styles['Title']))
        story.append(Spacer(1,12))
        story.append(Paragraph("Project Details",styles['Heading2']))
        story.append(Paragraph(f"<b>Domain:</b> {project_info['domain']}<br/><b>Data Type:</b> {project_info['data_type']}<br/><b>Region:</b> {project_info['region']}",styles['BodyText']))
        story.append(Spacer(1,12))
        met = [c for c in compliance_data if c['followed']]
        pending = [c for c in compliance_data if not c['followed']]
        story.append(Paragraph("Compliance Status",styles['Heading2']))
        status_table = Table([
            ["Total Requirements", len(compliance_data)],
            ["Compliant", f"{len(met)} ({len(met)/len(compliance_data):.0%})"],
            ["Pending", f"{len(pending)} ({len(pending)/len(compliance_data):.0%})"]
        ], colWidths=[2*inch,1.5*inch])
        status_table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#003366")),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('BOX',(0,0),(-1,-1),0.5,colors.grey)
        ]))
        story.append(status_table)
        story.append(Spacer(1,12))
        story.append(Paragraph("Detailed Requirements",styles['Heading2']))
        data=[["Requirement","Status","Checklist"]]
        for item in compliance_data:
            status="Compliant" if item['followed'] else "Pending"
            color = colors.green if item['followed'] else colors.red
            checklist="<br/>".join([f"• {p}" for p in item['checklist']])
            data.append([Paragraph(item['name'],styles['BodyText']),
                         Paragraph(f"<font color='{color.hexval()}'>{status}</font>",styles['BodyText']),
                         Paragraph(checklist,styles['BodyText'])])
        table=Table(data,colWidths=[2.5*inch,1*inch,2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#003366")),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('INNERGRID',(0,0),(-1,-1),0.5,colors.lightgrey),
            ('BOX',(0,0),(-1,-1),0.5,colors.grey)
        ]))
        story.append(table)
        doc.build(story)
        buffer.seek(0)
        return buffer

    # ---------------- Main Logic with Sticky Downloads ---------------- #
    analyze_button = st.button("🔍 Analyze Compliance", type="primary")
    if analyze_button or 'results' not in st.session_state:
        if not project_description.strip():
            st.warning("Please enter project description")
            st.stop()
        with st.spinner("Analyzing..."):
            results = analyze_project(project_description)
            st.session_state.results = results
            st.session_state.pdf_buffer = generate_pdf_report(
                {"domain":results['domain'], "data_type":results['data_type'], "region":results['region']},
                results['compliance_matches']
            )
            pending = [c for c in results['compliance_matches'] if not c['followed']]
            action_items=[]
            for item in pending:
                action_items.append({
                    "Requirement": item['name'],
                    "Priority": item['priority'],
                    "Deadline": "30 days" if item['priority']=="High" else "90 days",
                    "Actions": "; ".join(item['checklist']),
                    "Owner":"[Assign Owner]",
                    "Status":"Not Started"
                })
            st.session_state.csv_data = pd.DataFrame(action_items).to_csv(index=False)

    results = st.session_state.get('results')
    if results:
        # Metrics
        met = [c for c in results['compliance_matches'] if c['followed']]
        pending = [c for c in results['compliance_matches'] if not c['followed']]
        score = int((len(met)/len(results['compliance_matches']))*100 if results['compliance_matches'] else 0)
        col1,col2,col3 = st.columns(3)
        col1.metric("Compliance Score", f"{score}%")
        col2.metric("Pending Requirements", len(pending))
        col3.metric("High Priority Items", len([c for c in pending if c['priority']=="High"]))

        st.markdown("### 📌 Detected Project Attributes")
        st.markdown(f"**Domain:** {', '.join(results['domain'])} | **Data Type:** {', '.join(results['data_type'])} | **Region:** {', '.join(results['region'])}")

        # Download buttons (sticky)
        st.markdown("---")
        st.download_button("⬇️ Download PDF Report", st.session_state.pdf_buffer, "compliance_report.pdf", "application/pdf")
        st.download_button("⬇️ Download Action Plan (CSV)", st.session_state.csv_data, "compliance_action_plan.csv", "text/csv")

        # Priority display
        st.markdown("### 🚨 Priority Matrix")
        for item in pending:
            cls = 'priority-high' if item['priority']=="High" else 'priority-standard'
            st.markdown(f"<div class='{cls}'><strong>{item['name']}</strong><br/>{item['why']}<br/>Checklist: {', '.join(item['checklist'])}</div>", unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", unsafe_allow_html=True)
