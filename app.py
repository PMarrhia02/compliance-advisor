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

# Background image (digital/compliance themed)
bg_url = "https://images.unsplash.com/photo-1593642532973-d31b6557fa68?auto=format&fit=crop&w=1650&q=80"

# Custom CSS for background and text readability
st.markdown(f"""
<style>
/* Full page background */
.stApp {{
    background-image: url("{bg_url}");
    background-size: cover;
    background-attachment: fixed;
    background-repeat: no-repeat;
}}

/* Main content container */
.main-container {{
    background: rgba(255, 255, 255, 0.85);
    border-radius: 15px;
    padding: 2rem;
    backdrop-filter: blur(5px);
    color: #000 !important;
}}

/* Force readable text inside metric cards, expanders, badges */
.stMetricValue, .stMetricLabel, .stExpanderHeader, .stMarkdown, .stText, .stButton, .stNumberInput input {{
    color: #000 !important;
}}

/* Sidebar text */
.stSidebar, .stSidebar .stText, .stSidebar .stMarkdown {{
    color: #000 !important;
}}

/* Priority blocks and badges */
.priority-high, .priority-standard, .badge {{
    color: #000 !important;
}}

/* Tables (pandas/st.dataframe) */
div[data-testid="stDataFrameContainer"] {{
    color: #000 !important;
    background: rgba(255,255,255,0.85) !important;
}}
</style>
""", unsafe_allow_html=True)

# Wrap the main content inside a container
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

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
                'Followed By Compunnel', 'Why Required'
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

    # Analysis functions
    def match_category(text, categories):
        text = text.lower()
        scores = {k: 0 for k in categories}
        for category, keywords in categories.items():
            for term in keywords:
                if term in text:
                    scores[category] += 2 if term == text.strip() else 1
        for category in scores:
            if categories[category]:
                scores[category] = scores[category] / len(categories[category])
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores, key=scores.get)
        else:
            for category in categories:
                if category in ["all", "global"]:
                    return category
            return list(categories.keys())[0]

    def analyze_project(description):
        domains = {
            "healthcare": ["healthcare", "hospital", "patient", "medical", "health", "phi"],
            "finance": ["bank", "finance", "payment", "financial", "pci", "credit card"],
            "ai solutions": ["ai", "artificial intelligence", "machine learning", "ml"],
            "govt/defense": ["government", "defense", "military", "public sector"],
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
            domain_match = "all" in row_domains or matched_domain in row_domains
            applies_to = [x.strip().lower() for x in str(row['Applies To']).split(",")]
            applies_match = (
                "all" in applies_to or 
                matched_region.lower() in applies_to or 
                matched_data_type.lower() in applies_to
            )
            if domain_match and applies_match:
                checklist = [str(item) for item in [
                    row['Checklist 1'], row['Checklist 2'], row['Checklist 3']
                ] if pd.notna(item)]
                compliance_matches.append({
                    "name": row['Compliance Name'],
                    "domain": str(row['Domain']).lower(),
                    "applies_to": applies_to,
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

    # PDF generation (unchanged)
    def generate_pdf_report(project_info, compliance_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("Compliance Assessment Report", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Project Details", styles['Heading2']))
        story.append(Paragraph(f"""
            <b>Domain:</b> {project_info['domain']}<br/>
            <b>Data Type:</b> {project_info['data_type']}<br/>
            <b>Region:</b> {project_info['region']}
        """, styles['BodyText']))
        story.append(Spacer(1, 24))
        met = [c for c in compliance_data if c['followed']]
        pending = [c for c in compliance_data if not c['followed']]
        story.append(Paragraph("Compliance Status", styles['Heading2']))
        status_table = Table([
            ["Total Requirements", len(compliance_data)],
            ["Compliant", f"{len(met)} ({len(met)/len(compliance_data):.0%})"],
            ["Pending", f"{len(pending)} ({len(pending)/len(compliance_data):.0%})"]
        ], colWidths=[2*inch, 1.5*inch])
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOX', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        story.append(status_table)
        story.append(Spacer(1, 24))
        story.append(Paragraph("Detailed Requirements", styles['Heading2']))
        data = [["Requirement", "Status", "Checklist"]]
        for item in compliance_data:
            status = "Compliant" if item['followed'] else "Pending"
            color = colors.green if item['followed'] else colors.red
            checklist = "<br/>".join([f"• {point}" for point in item['checklist']])
            data.append([
                Paragraph(item['name'], styles['BodyText']),
                Paragraph(f"<font color='{color.hexval()}'>{status}</font>", styles['BodyText']),
                Paragraph(checklist, styles['BodyText'])
            ])
        table = Table(data, colWidths=[2.5*inch, 1*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('VALIGN', (0,0), (-1,0), 'MIDDLE'),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        story.append(table)
        doc.build(story)
        buffer.seek(0)
        return buffer

    # Main Analysis
    if st.button("🔍 Analyze Compliance", type="primary"):
        if not project_description.strip():
            st.warning("Please enter a project description")
            st.stop()
        
        with st.spinner("Analyzing requirements..."):
            results = analyze_project(project_description)
            st.session_state.results = results
            st.success("Analysis complete!")
            met = [c for c in results['compliance_matches'] if c['followed']]
            pending = [c for c in results['compliance_matches'] if not c['followed']]
            score = int((len(met) / len(results['compliance_matches'])) * 100 if results['compliance_matches'] else 0)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
                st.metric("Compliance Score", f"{score}%")
                st.markdown("</div>", unsafe_allow_html=True)
            with col2:
                st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
                st.metric("Pending Requirements", len(pending))
                st.markdown("</div>", unsafe_allow_html=True)
            with col3:
                st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
                high_pri = len([c for c in pending if c['priority'] == "High"])
                st.metric("High Priority Items", high_pri)
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Detected attributes
            st.markdown("### 📌 Detected Project Attributes")
            att_col1, att_col2, att_col3 = st.columns(3)
            with att_col1:
                st.markdown(f"**Domain:** <span class='badge badge-blue'>{results['domain'].title()}</span>", unsafe_allow_html=True)
            with att_col2:
                st.markdown(f"**Data Type:** <span class='badge badge-blue'>{results['data_type']}</span>", unsafe_allow_html=True)
            with att_col3:
                st.markdown(f"**Region:** <span class='badge badge-blue'>{results['region'].title()}</span>", unsafe_allow_html=True)
            
            # Priority Matrix
            st.markdown("### 🚨 Priority Matrix")
            high_priority = [c for c in pending if c['priority'] == "High"]
            standard_priority = [c for c in pending if c['priority'] == "Standard"]
            if high_priority:
                st.markdown("#### 🔴 High Priority (Urgent)")
                for item in high_priority:
                    st.markdown(f"""
                    <div class='priority-high'>
                        <strong>{item['name']}</strong><br/>
                        {item['why']}<br/>
                        <em>Checklist: {", ".join(item['checklist'])}</em>
                    </div>
                    """, unsafe_allow_html=True)
            if standard_priority:
                st.markdown("#### 🟠 Standard Priority")
                for item in standard_priority:
                    st.markdown(f"""
                    <div class='priority-standard'>
                        <strong>{item['name']}</strong><br/>
                        {item['why']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Full Checklist
            st.markdown("### 📋 Detailed Checklist")
            for item in results['compliance_matches']:
                with st.expander(f"{'✅' if item['followed'] else '❌'} {item['name']}"):
                    st.markdown(f"**Priority:** {item['priority']}")
                    if item['alert']:
                        st.warning("⚠️ Alert: This regulation has recent updates")
                    st.markdown("**Requirements:**")
                    for point in item['checklist']:
                        st.markdown(f"- {point}")
                    st.markdown(f"*{item['why']}*")

    # Report Generation
    if st.session_state.get('results'):
        st.markdown("---")
        st.markdown("## 📤 Generate Reports")
        format_choice = st.radio(
            "Select report type:",
            ["PDF Report", "Action Plan (CSV)"],
            horizontal=True
        )
        if format_choice == "PDF Report":
            pdf_buffer = generate_pdf_report(
                {
                    "domain": st.session_state.results['domain'],
                    "data_type": st.session_state.results['data_type'],
                    "region": st.session_state.results['region']
                },
                st.session_state.results['compliance_matches']
            )
            st.download_button(
                "⬇️ Download PDF Report",
                pdf_buffer,
                "compliance_report.pdf",
                "application/pdf"
            )
        else:
            action_items = []
            for item in st.session_state.results['compliance_matches']:
                if not item['followed']:
                    action_items.append({
                        "Requirement": item['name'],
                        "Priority": item['priority'],
                        "Deadline": "30 days" if item['priority'] == "High" else "90 days",
                        "Actions": "; ".join(item['checklist']),
                        "Owner": "[Assign Owner]",
                        "Status": "Not Started"
                    })
            df = pd.DataFrame(action_items)
            csv = df.to_csv(index=False)
            st.download_button(
                "⬇️ Download Action Plan",
                csv,
                "compliance_action_plan.csv",
                "text/csv"
            )

# Footer
st.markdown("---")
st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)  # Close main-container
