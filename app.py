import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

# ---------------- Page setup ---------------- #
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# ---------------- Custom CSS ---------------- #
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
        if username == "admin" and password == "password":
            st.session_state.username = username
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password.")
else:
    st.success(f"Welcome, {st.session_state.username}!")

    # ---------------- Load Google Sheet ---------------- #
    @st.cache_data
    def load_data():
        sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            df = pd.read_csv(sheet_url)
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

    # ---------------- Project input ---------------- #
    project_description = st.text_area(
        "Describe your project (include data types and regions):",
        height=150,
        placeholder="e.g., 'Healthcare app storing patient records in India with EU users...'"
    )

    # ---------------- Matching functions ---------------- #
    def match_category(text, categories, threshold=0.2):
        text = text.lower()
        scores = {k: 0 for k in categories}
        for category, keywords in categories.items():
            for term in keywords:
                if term in text:
                    scores[category] += 1
        # Normalize scores
        for category in scores:
            if categories[category]:
                scores[category] = scores[category] / len(categories[category])
        # Filter by threshold
        filtered_scores = {k: v for k, v in scores.items() if v >= threshold}
        if not filtered_scores:
            return None
        return max(filtered_scores, key=filtered_scores.get)

    def analyze_project(description):
        domains = {
            "healthcare": ["healthcare", "hospital", "patient", "medical", "phi"],
            "finance": ["bank", "finance", "payment", "financial", "pci", "credit card"],
            "ai solutions": ["ai", "artificial intelligence", "machine learning", "ml"],
            "govt/defense": ["government", "defense", "military", "public sector"],
            "cloud services": ["cloud", "saas", "iaas", "paas"],
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
            "California": ["california"],
            "global": ["global", "international", "worldwide"]
        }

        matched_domain = match_category(description, domains)
        matched_data_type = match_category(description, data_types)
        matched_region = match_category(description, regions)

        if not matched_domain and not matched_data_type and not matched_region:
            return {
                "domain": None,
                "data_type": None,
                "region": None,
                "compliance_matches": []
            }

        compliance_matches = []
        for _, row in compliance_df.iterrows():
            row_domains = [x.strip().lower() for x in str(row['Domain']).split(",")]
            row_applies = [x.strip().lower() for x in str(row['Applies To']).split(",")]
            domain_match = matched_domain in row_domains or ("all" in row_domains and matched_domain)
            applies_match = (matched_region and matched_region.lower() in row_applies) or \
                            (matched_data_type and matched_data_type.lower() in row_applies) or \
                            "all" in row_applies or "global" in row_applies
            if domain_match and applies_match:
                checklist = [str(item) for item in [row['Checklist 1'], row['Checklist 2'], row['Checklist 3']] if pd.notna(item)]
                compliance_matches.append({
                    "name": row['Compliance Name'],
                    "domain": row['Domain'],
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

    # ---------------- PDF Report ---------------- #
    def generate_pdf_report(project_info, compliance_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("Compliance Assessment Report", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Domain:</b> {project_info['domain']}<br/><b>Data Type:</b> {project_info['data_type']}<br/><b>Region:</b> {project_info['region']}", styles['BodyText']))
        story.append(Spacer(1, 12))
        met = [c for c in compliance_data if c['followed']]
        pending = [c for c in compliance_data if not c['followed']]
        story.append(Paragraph(f"Total Requirements: {len(compliance_data)}<br/>Compliant: {len(met)}<br/>Pending: {len(pending)}", styles['BodyText']))
        story.append(Spacer(1, 12))
        for item in compliance_data:
            status = "Compliant" if item['followed'] else "Pending"
            checklist_text = ", ".join(item['checklist'])
            story.append(Paragraph(f"{item['name']} - {status} - Checklist: {checklist_text}", styles['BodyText']))
        doc.build(story)
        buffer.seek(0)
        return buffer

    # ---------------- Main Analysis ---------------- #
    if st.button("🔍 Analyze Compliance", type="primary"):
        if not project_description.strip():
            st.warning("Please enter a project description")
            st.stop()
        with st.spinner("Analyzing requirements..."):
            results = analyze_project(project_description)
            st.session_state.results = results
            st.success("Analysis complete!")

            if not results['compliance_matches']:
                st.info("No compliance requirements detected for this project description.")
            else:
                # Summary Metrics
                met = [c for c in results['compliance_matches'] if c['followed']]
                pending = [c for c in results['compliance_matches'] if not c['followed']]
                score = int((len(met)/len(results['compliance_matches']))*100)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Compliance Score", f"{score}%")
                with col2:
                    st.metric("Pending Requirements", len(pending))
                with col3:
                    high_pri = len([c for c in pending if c['priority'] == "High"])
                    st.metric("High Priority Items", high_pri)

                # Project Attributes
                st.markdown("### 📌 Detected Project Attributes")
                att_col1, att_col2, att_col3 = st.columns(3)
                att_col1.markdown(f"**Domain:** <span class='badge badge-blue'>{results['domain']}</span>", unsafe_allow_html=True)
                att_col2.markdown(f"**Data Type:** <span class='badge badge-blue'>{results['data_type']}</span>", unsafe_allow_html=True)
                att_col3.markdown(f"**Region:** <span class='badge badge-blue'>{results['region']}</span>", unsafe_allow_html=True)

                # Priority Matrix
                st.markdown("### 🚨 Priority Matrix")
                high_priority = [c for c in pending if c['priority']=="High"]
                standard_priority = [c for c in pending if c['priority']=="Standard"]
                for item in high_priority:
                    st.markdown(f"<div class='priority-high'><strong>{item['name']}</strong><br/>{item['why']}<br/><em>Checklist: {', '.join(item['checklist'])}</em></div>", unsafe_allow_html=True)
                for item in standard_priority:
                    st.markdown(f"<div class='priority-standard'><strong>{item['name']}</strong><br/>{item['why']}</div>", unsafe_allow_html=True)

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

                # ---------------- Download Section ---------------- #
                st.markdown("---")
                st.markdown("## 📤 Generate Reports")
                format_choice = st.radio("Select report type:", ["PDF Report", "Action Plan (CSV)"], horizontal=True)
                if format_choice == "PDF Report":
                    pdf_buffer = generate_pdf_report(
                        {"domain": results['domain'], "data_type": results['data_type'], "region": results['region']},
                        results['compliance_matches']
                    )
                    st.download_button("⬇️ Download PDF Report", pdf_buffer, "compliance_report.pdf", "application/pdf")
                else:
                    # Action Plan CSV
                    action_items = []
                    for item in pending:
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

    # ---------------- Footer ---------------- #
    st.markdown("---")
    st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", unsafe_allow_html=True)
