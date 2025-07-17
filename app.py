import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

# Optional Plotly import with error handling
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Page setup
st.set_page_config(page_title="Compliance Advisor", layout="wide")

# Style and header
st.markdown("""
    <style>
        .title {
            font-size: 2.5em;
            color: #003366;
            font-weight: bold;
        }
        .badge {
            display: inline-block;
            padding: 0.25em 0.6em;
            font-size: 90%;
            font-weight: 600;
            border-radius: 0.25rem;
        }
        .badge-green {
            background-color: #d4edda;
            color: #155724;
        }
        .badge-red {
            background-color: #f8d7da;
            color: #721c24;
        }
        .badge-blue {
            background-color: #d1ecf1;
            color: #0c5460;
        }
        .footer {
            text-align: center;
            font-size: 0.9em;
            color: gray;
            margin-top: 3rem;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>🔐 Compunnel AI-Powered Compliance Advisor</div>", unsafe_allow_html=True)
st.markdown("Enter your project brief to see the cybersecurity and data protection compliances required, compared to what Compunnel already complies with.")

# Sidebar
with st.sidebar:
    st.image("https://compunnel.com/assets/img/logo.svg", width=180)
    st.markdown("### 🧠 How it Works")
    st.info("• Describe your project using natural language.\n\n• Mention data types (PHI, financial, personal) and regions (India, EU, USA).\n\n• Get matched compliance requirements instantly.")

# Load Google Sheet
sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

try:
    compliance_df = pd.read_csv(sheet_url)
    st.success("✅ Compliance database loaded successfully.")
except:
    st.error("❌ Failed to load compliance database.")
    st.stop()

# Input
st.markdown("### 📄 Project Description", unsafe_allow_html=True)
project_description = st.text_area("Enter your project brief below:", height=180)

def show_ai_tips(matched_domain, matched_data_type, matched_region):
    tips = []
    if "healthcare" in matched_domain.lower():
        tips.append("**🤖 AI Tip:** Implement HIPAA-compliant encryption for PHI data storage.")
    if "financial" in matched_data_type.lower():
        tips.append("**🤖 AI Tip:** Enable PCI-DSS compliant transaction logging.")
    if "eu" in matched_region.lower():
        tips.append("**🤖 AI Tip:** Review GDPR Article 30 for record-keeping requirements.")
    
    if tips:
        with st.expander("💡 AI-Powered Recommendations"):
            for tip in tips:
                st.markdown(f"- {tip}")

def generate_enhanced_pdf(report_text, matched_domain, matched_data_type, matched_region, compliance_matches):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("Compliance Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Project Info
    project_info = Paragraph(
        f"<b>Domain:</b> {matched_domain}<br/>"
        f"<b>Data Type:</b> {matched_data_type}<br/>"
        f"<b>Region:</b> {matched_region}",
        styles['BodyText']
    )
    story.append(project_info)
    story.append(Spacer(1, 12))
    
    # Compliance Table
    data = [["Compliance", "Status", "Checklist Items"]]
    for comp in compliance_matches:
        status = "✅ Met" if comp['followed'] else "❌ Pending"
        checklist = "<br/>".join([f"• {item}" for item in comp['checklist']])
        data.append([
            comp['name'], 
            status, 
            Paragraph(checklist, styles['BodyText'])
        ])
    
    table = Table(data, colWidths=[2*inch, 1*inch, 3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer

if st.button("🔍 Analyze Project"):
    if not project_description.strip():
        st.warning("Please enter a valid description.")
        st.stop()

    text = project_description.lower()

    # Matching logic
    domains = {
        "healthcare": ["healthcare", "hospital", "patient", "medical", "clinic"],
        "finance": ["bank", "finance", "credit card", "payment", "fintech", "investment"],
        "ecommerce": ["ecommerce", "shopping", "online store", "retail"],
        "ai solutions": ["ai", "artificial intelligence", "machine learning", "llm", "model", "data science"],
    }

    data_types = {
        "PHI": ["health data", "phi", "patient", "lab result", "medical", "clinical"],
        "PII": ["personal data", "name", "address", "email", "aadhar", "pii", "dob"],
        "financial": ["financial", "credit card", "bank", "transaction", "upi", "fintech"],
    }

    regions = {
        "India": ["india", "indian", "bharat"],
        "USA": ["usa", "united states", "america"],
        "EU": ["europe", "eu", "germany", "france", "european union"],
        "Canada": ["canada"],
        "Brazil": ["brazil"],
    }

    def match_category(rules, text):
        return max(rules.keys(), key=lambda key: sum(word in text for word in rules[key]), default="Unknown")

    matched_domain = match_category(domains, text)
    matched_data_type = match_category(data_types, text)
    matched_region = match_category(regions, text)

    # Initialize compliance_matches
    compliance_matches = []
    
    for _, row in compliance_df.iterrows():
        domain = str(row['Domain']).lower()
        applies_to = [x.strip().lower() for x in str(row['Applies To']).split(",")]
        followed = str(row['Followed By Compunnel']).strip().lower() == "yes"
        reason = row.get("Why Required", "")
        checklist = [item for item in row.iloc[3:6] if pd.notna(item)]

        if (matched_domain.lower() == domain or domain == "all") and (
            matched_data_type.lower() in applies_to
            or matched_region.lower() in applies_to
            or "all" in applies_to
        ):
            compliance_matches.append({
                "name": row['Compliance Name'],
                "followed": followed,
                "why": reason,
                "checklist": checklist
            })

    # Display info
    left, right = st.columns(2)
    with left:
        st.markdown("### 🧠 Detected Project Info")
        st.markdown(f"<span class='badge badge-blue'>Domain: {matched_domain}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='badge badge-blue'>Data Type: {matched_data_type}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='badge badge-blue'>Region: {matched_region}</span>", unsafe_allow_html=True)

    with right:
        st.markdown("### 📊 Compliance Summary")
        if not compliance_matches:
            st.warning("⚠️ No compliance matched.")
        else:
            already = [c for c in compliance_matches if c['followed']]
            missing = [c for c in compliance_matches if not c['followed']]

            st.markdown("✅ **Already Compliant With**")
            for comp in already:
                st.markdown(f"<span class='badge badge-green'>🛡️ {comp['name']}</span>", unsafe_allow_html=True)

            st.markdown("🚨 **To Be Implemented**")
            for comp in missing:
                st.markdown(f"<span class='badge badge-red'>❗ {comp['name']}</span>", unsafe_allow_html=True)
                if comp["why"]:
                    st.caption(f"💡 Why: {comp['why']}")

    # Visual Dashboard
    if compliance_matches and PLOTLY_AVAILABLE:
        met_count = len([c for c in compliance_matches if c['followed']])
        pending_count = len([c for c in compliance_matches if not c['followed']])
        
        fig = px.pie(
            names=["Met", "Pending"],
            values=[met_count, pending_count],
            title="Compliance Status",
            color_discrete_sequence=["#2ecc71", "#e74c3c"]
        )
        st.plotly_chart(fig, use_container_width=True)
    elif compliance_matches and not PLOTLY_AVAILABLE:
        st.info("✨ Install Plotly (`pip install plotly`) to enable visual charts")

    # AI Tips
    show_ai_tips(matched_domain, matched_data_type, matched_region)

    # Checklist and Report
    st.markdown("### 📋 Detailed Checklist")
    report_text = f"Project Domain: {matched_domain}\nData Type: {matched_data_type}\nRegion: {matched_region}\n\n"

    for comp in compliance_matches:
        with st.expander(f"{'🟢' if comp['followed'] else '🔴'} {comp['name']}"):
            for item in comp['checklist']:
                st.markdown(f"• {item}")
            if comp['why']:
                st.caption(f"💡 _Why Required_: {comp['why']}")
        report_text += f"\n{comp['name']}:\n"
        for item in comp['checklist']:
            report_text += f"  - {item}\n"
        if comp['why']:
            report_text += f"  Why Required: {comp['why']}\n"
        report_text += f"  Status: {'Followed ✅' if comp['followed'] else 'Not Followed ❌'}\n"

    # Store report text in session state
    st.session_state.report_text = report_text
    st.session_state.compliance_matches = compliance_matches
    st.session_state.matched_domain = matched_domain
    st.session_state.matched_data_type = matched_data_type
    st.session_state.matched_region = matched_region

# Download Options
if 'report_text' in st.session_state:
    st.markdown("### 📥 Download Compliance Summary")
    
    format_choice = st.radio(
        "Choose download format:", 
        ["Text", "Enhanced PDF"], 
        key="format_choice"
    )
    
    if format_choice == "Text":
        st.download_button(
            label="📄 Download as TXT",
            data=st.session_state.report_text,
            file_name="compliance_summary.txt",
            mime="text/plain",
            key="text_dl"
        )
    else:
        pdf_buffer = generate_enhanced_pdf(
            st.session_state.report_text,
            st.session_state.matched_domain,
            st.session_state.matched_data_type,
            st.session_state.matched_region,
            st.session_state.compliance_matches
        )
        st.download_button(
            label="📑 Download Enhanced PDF",
            data=pdf_buffer,
            file_name="compliance_report.pdf",
            mime="application/pdf",
            key="download_pdf"
        )

# Footer
st.markdown("<div class='footer'>© 2025 Compunnel Inc. | Built with ❤️ using Streamlit</div>", unsafe_allow_html=True)
