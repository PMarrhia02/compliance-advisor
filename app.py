import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import plotly.express as px

# Page setup (unchanged)
st.set_page_config(page_title="Compliance Advisor", layout="wide")

# Style and header (unchanged)
st.markdown("""
    <style>
        .title { font-size: 2.5em; color: #003366; font-weight: bold; }
        .badge { display: inline-block; padding: 0.25em 0.6em; font-size: 90%; font-weight: 600; border-radius: 0.25rem; }
        .badge-green { background-color: #d4edda; color: #155724; }
        .badge-red { background-color: #f8d7da; color: #721c24; }
        .badge-blue { background-color: #d1ecf1; color: #0c5460; }
        .footer { text-align: center; font-size: 0.9em; color: gray; margin-top: 3rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>🔐 Compunnel AI-Powered Compliance Advisor</div>", unsafe_allow_html=True)
st.markdown("Enter your project brief to see the cybersecurity and data protection compliances required, compared to what Compunnel already complies with.")

# --- New AI Tip Function (Free) ---
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

# --- Enhanced PDF Generator (Free) ---
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

# --- Original Code Continues (Unchanged until analysis section) ---
with st.sidebar:
    st.image("https://compunnel.com/assets/img/logo.svg", width=180)
    st.markdown("### 🧠 How it Works")
    st.info("• Describe your project using natural language.\n\n• Mention data types (PHI, financial, personal) and regions (India, EU, USA).\n\n• Get matched compliance requirements instantly.")

# Load Google Sheet (unchanged)
sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

try:
    compliance_df = pd.read_csv(sheet_url)
    st.success("✅ Compliance database loaded successfully.")
except:
    st.error("❌ Failed to load compliance database.")
    st.stop()

# Input (unchanged)
project_description = st.text_area("Enter your project brief below:", height=180)

if st.button("🔍 Analyze Project"):
    if not project_description.strip():
        st.warning("Please enter a valid description.")
        st.stop()

    # ... (original matching logic remains identical until compliance_matches is created)

    # --- New Visual Dashboard (Free) ---
    if compliance_matches:
        met_count = len([c for c in compliance_matches if c['followed']])
        pending_count = len([c for c in compliance_matches if not c['followed']])
        
        fig = px.pie(
            names=["Met", "Pending"],
            values=[met_count, pending_count],
            title="Compliance Status",
            color_discrete_sequence=["#2ecc71", "#e74c3c"]
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # --- New AI Tips Section (Free) ---
    show_ai_tips(matched_domain, matched_data_type, matched_region)

    # --- Modified Download Section (Enhanced PDF) ---
    st.markdown("### 📥 Download Compliance Summary")
    format_choice = st.radio("Choose format:", ["Text", "Enhanced PDF"])
    
    if format_choice == "Text":
        st.download_button(
            label="📄 Download as TXT",
            data=report_text,
            file_name="compliance_summary.txt",
            mime="text/plain"
        )
    else:
        pdf_buffer = generate_enhanced_pdf(
            report_text, 
            matched_domain, 
            matched_data_type, 
            matched_region,
            compliance_matches
        )
        st.download_button(
            label="📑 Download Enhanced PDF",
            data=pdf_buffer,
            file_name="compliance_report.pdf",
            mime="application/pdf"
        )

# Footer (unchanged)
st.markdown("<div class='footer'>© 2025 Compunnel Inc. | Built with ❤️ using Streamlit</div>", unsafe_allow_html=True)
