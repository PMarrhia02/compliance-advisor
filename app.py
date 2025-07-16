import streamlit as st
import pandas as pd
from io import StringIO

# Set page config
st.set_page_config(page_title="Compliance Advisor", layout="wide")

# Header
st.markdown("""
    <style>
        .title {
            font-size: 2.5em;
            color: #003366;
            font-weight: bold;
        }
        .section {
            margin-top: 2rem;
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
except Exception as e:
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

    # Matching rules
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
        return max(
            rules.keys(),
            key=lambda label: sum(kw in text for kw in rules[label]),
            default="Unknown"
        )

    matched_domain = match_category(domains, text)
    matched_data_type = match_category(data_types, text)
    matched_region = match_category(regions, text)

    # Match compliances
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

    # Layout in columns
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
            if already:
                for comp in already:
                    st.markdown(f"<span class='badge badge-green'>🛡️ {comp['name']}</span>", unsafe_allow_html=True)
            else:
                st.info("None currently covered.")

            st.markdown("🚨 **To Be Implemented**")
            if missing:
                for comp in missing:
                    st.markdown(f"<span class='badge badge-red'>❗ {comp['name']}</span>", unsafe_allow_html=True)
                    if comp["why"]:
                        st.caption(f"💡 Why: {comp['why']}")

    # Detailed checklist
    st.markdown("### 📋 Detailed Checklist")
    for comp in compliance_matches:
        with st.expander(f"{'🟢' if comp['followed'] else '🔴'} {comp['name']}"):
            for item in comp['checklist']:
                st.markdown(f"• {item}")
            if comp['why']:
                st.caption(f"💡 _Why Required_: {comp['why']}")

    # 📥 Downloadable report
    st.markdown("### 📥 Download Compliance Summary")

    report_lines = [
        "Compunnel AI-Powered Compliance Advisor - Report",
        f"Project Description: {project_description}",
        f"Domain: {matched_domain}",
        f"Data Type: {matched_data_type}",
        f"Region: {matched_region}",
        "",
        "Required Compliances:"
    ]

    for comp in compliance_matches:
        status = "✅ Already Compliant" if comp["followed"] else "❗ Needs Implementation"
        report_lines.append(f"\n{comp['name']} - {status}")
        if comp["why"]:
            report_lines.append(f"Why Required: {comp['why']}")
        if comp["checklist"]:
            report_lines.append("Checklist:")
            for item in comp["checklist"]:
                report_lines.append(f"  - {item}")

    report_text = "\n".join(report_lines)
    buffer = StringIO()
    buffer.write(report_text)
    buffer.seek(0)

    st.download_button(
        label="📄 Download Compliance Report",
        data=buffer,
        file_name="compliance_summary.txt",
        mime="text/plain"
    )

# Footer
st.markdown("<div class='footer'>© 2025 Compunnel Inc. | Built with ❤️ using Streamlit</div>", unsafe_allow_html=True)
