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

# Custom CSS
st.markdown("""
    <style>
        .title { font-size: 2.5em; color: #003366; font-weight: bold; }
        .badge { display: inline-block; padding: 0.25em 0.6em; font-size: 90%; font-weight: 600; border-radius: 0.25rem; }
        .badge-green { background-color: #d4edda; color: #155724; }
        .badge-red { background-color: #f8d7da; color: #721c24; }
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
        sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            df = pd.read_csv(sheet_url)
            
            # Validate columns
            required_cols = [
                'Compliance Name', 'Domain', 'Applies To',
                'Checklist 1', 'Checklist 2', 'Checklist 3',
                'Followed By Compunnel', 'Why Required', 'Priority', 'Trigger Alert'
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

    # Project input
    project_description = st.text_area(
        "Describe your project (include data types and regions):",
        height=150,
        placeholder="e.g., 'Healthcare app storing patient records in India with EU users...'"
    )

    # Matching function using RapidFuzz
    def match_category(text, categories, min_score=40):
        text = text.lower()
        scores = {}
        for category, keywords in categories.items():
            max_score = 0
            for kw in keywords:
                score = fuzz.partial_ratio(kw.lower(), text)
                if score > max_score:
                    max_score = score
            scores[category] = max_score
        best_category = max(scores, key=scores.get)
        if scores[best_category] >= min_score:
            return best_category
        return "unknown"

    def analyze_project(description):
        domains = {
            "healthcare": ["healthcare", "hospital", "patient", "medical", "health", "phi"],
            "finance": ["bank", "finance", "payment", "financial", "pci", "credit card"],
            "ai solutions": ["ai", "artificial intelligence", "machine learning", "ml"],
            "govt/defense": ["government", "defense", "military", "public sector"],
            "cloud services": ["cloud", "saas", "iaas", "paas", "aws", "azure", "gcp"],
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
            row_applies = [x.strip().lower() for x in str(row['Applies To']).split(",")]
            domain_match = "all" in row_domains or matched_domain in row_domains
            applies_match = "all" in row_applies or matched_region.lower() in row_applies or matched_data_type.lower() in row_applies
            
            if domain_match and applies_match:
                checklist = [str(item) for item in [row['Checklist 1'], row['Checklist 2'], row['Checklist 3']] if pd.notna(item)]
                compliance_matches.append({
                    "name": row['Compliance Name'],
                    "domain": str(row['Domain']).lower(),
                    "applies_to": row_applies,
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

    # Display compliance matches inline
    def display_compliance(compliance_matches):
        for item in compliance_matches:
            status = "✅ Followed" if item['followed'] else "❌ Pending"
            color = "#d4edda" if item['followed'] else "#f8d7da"
            st.markdown(f"""
            <div style='background-color:{color}; padding:10px; margin-bottom:5px; border-radius:5px;'>
                <strong>{item['name']}</strong> - {status}<br/>
                Priority: {item['priority']}<br/>
                Checklist: {', '.join(item['checklist'])}<br/>
                Why Required: {item['why']}
            </div>
            """, unsafe_allow_html=True)

    # Generate PDF
    def generate_pdf_report(project_info, compliance_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("Compliance Assessment Report", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Project Details", styles['Heading2']))
        story.append(Paragraph(f"<b>Domain:</b> {project_info['domain']}<br/><b>Data Type:</b> {project_info['data_type']}<br/><b>Region:</b> {project_info['region']}", styles['BodyText']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Compliance Status", styles['Heading2']))
        data = [["Requirement", "Status", "Priority", "Checklist"]]
        for item in compliance_data:
            status = "Followed" if item['followed'] else "Pending"
            checklist = ", ".join(item['checklist'])
            data.append([item['name'], status, item['priority'], checklist])
        table = Table(data, colWidths=[2*inch, 1*inch, 1*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BOX', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        story.append(table)
        doc.build(story)
        buffer.seek(0)
        return buffer

    if st.button("🔍 Analyze Compliance", type="primary"):
        if not project_description.strip():
            st.warning("Please enter a project description")
            st.stop()
        with st.spinner("Analyzing requirements..."):
            results = analyze_project(project_description)
            st.session_state.results = results
            st.success("Analysis complete!")

            compliance_matches = results['compliance_matches']
            total = len(compliance_matches)
            followed = len([c for c in compliance_matches if c['followed']])
            pending = total - followed
            score = int((followed / total)*100) if total else 0
            high_priority_pending = len([c for c in compliance_matches if not c['followed'] and c['priority']=="High"])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Compliance Score", f"{score}%")
            with col2:
                st.metric("Pending Requirements", pending)
            with col3:
                st.metric("High Priority Items", high_priority_pending)

            st.markdown("### 📌 Detected Project Attributes")
            att_col1, att_col2, att_col3 = st.columns(3)
            with att_col1:
                st.markdown(f"**Domain:** {results['domain']}")
            with att_col2:
                st.markdown(f"**Data Type:** {results['data_type']}")
            with att_col3:
                st.markdown(f"**Region:** {results['region']}")

            st.markdown("### 📋 Compliance Details")
            display_compliance(compliance_matches)

    # Generate Reports
    if st.session_state.get('results'):
        st.markdown("---")
        st.markdown("## 📤 Generate Reports")
        format_choice = st.radio("Select report type:", ["PDF Report", "Action Plan (CSV)"], horizontal=True)
        results = st.session_state.results
        compliance_matches = results['compliance_matches']
        project_info = {
            "domain": results['domain'],
            "data_type": results['data_type'],
            "region": results['region']
        }

        if format_choice == "PDF Report":
            pdf_buffer = generate_pdf_report(project_info, compliance_matches)
            st.download_button("⬇️ Download PDF Report", pdf_buffer, "compliance_report.pdf", "application/pdf")
        else:
            action_items = []
            for item in compliance_matches:
                if not item['followed']:
                    action_items.append({
                        "Requirement": item['name'],
                        "Priority": item['priority'],
                        "Deadline": "30 days" if item['priority']=="High" else "90 days",
                        "Actions": "; ".join(item['checklist']),
                        "Owner": "[Assign Owner]",
                        "Status": "Not Started"
                    })
            df = pd.DataFrame(action_items)
            csv = df.to_csv(index=False)
            st.download_button("⬇️ Download Action Plan", csv, "compliance_action_plan.csv", "text/csv")

    st.markdown("---")
    st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", unsafe_allow_html=True)
