import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

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
        return max(rules, key=lambda key: sum(word in text for word in rules[key]), default="Unknown")

    matched_domain = match_category(domains, text)
    matched_data_type = match_category(data_types, text)
    matched_region = match_category(regions, text)

    # Match compliance
    compliance_matches = []
    for _, row in compliance_df.iterrows():
        domain = str(row['Domain']).lower()
        applies_to = [x.strip().lower() for x in str(row['Applies To']).split(",")]
        followed = str(row['Followed By Compunnel']).strip().lower() == "yes"
        reason = row.get("Why Required", "")
        checklist = [item for item in row.iloc[3:6] if pd.notna(item)]

        if (
            matched_domain == domain or domain == "all"
        ) and (
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

    # Download Options
    st.markdown("### 📥 Download Compliance Summary")
    option = st.radio("Choose download format:", ["Text", "PDF"], key="format_choice")

    if option == "Text":
        st.download_button(
            label="📄 Download as TXT",
            data=report_text,
            file_name="compliance_summary.txt",
            mime="text/plain",
            key="text_dl"
        )
    else:
        if "pdf_ready" not in st.session_state:
            st.session_state["pdf_ready"] = False

        if st.button("🧾 Generate PDF", key="generate_pdf"):
            buffer = BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)
            text_obj = pdf.beginText(40, 800)
            for line in report_text.split("\n"):
                text_obj.textLine(line)
            pdf.drawText(text_obj)
            pdf.save()
            buffer.seek(0)
            st.session_state["pdf_data"] = buffer.read()
            st.session_state["pdf_ready"] = True
            st.success("✅ PDF generated! Now click download below.")

        if st.session_state.get("pdf_ready"):
            st.download_button(
                label="⬇️ Download PDF",
                data=st.session_state["pdf_data"],
                file_name="compliance_summary.pdf",
                mime="application/pdf",
                key="download_pdf"
            )

# Footer
st.markdown("<div class='footer'>© 2025 Compunnel Inc. | Built with ❤️ using Streamlit</div>", unsafe_allow_html=True)
