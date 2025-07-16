import streamlit as st
import pandas as pd
from io import StringIO

# Page config
st.set_page_config(page_title="Compliance Advisor", layout="wide")
st.title("🔐 Compunnel AI-Powered Compliance Advisor")
st.write("Enter your project brief to get a list of required compliances, matched against Compunnel's existing certifications.")

# Load from Google Sheet
sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

try:
    compliance_df = pd.read_csv(sheet_url)
    st.success("✅ Compliance database loaded successfully.")
except Exception as e:
    st.error("❌ Failed to load compliance database. Please check the sheet ID and sharing permissions.")
    st.stop()

# Input
project_description = st.text_area("📄 Project Description", height=200)

if st.button("Analyze Project"):
    if project_description.strip() == "":
        st.warning("Please enter a valid project description.")
        st.stop()

    text = project_description.lower()

    # Keyword match rules
    domains = {
        "healthcare": ["healthcare", "hospital", "patient", "medical", "clinic"],
        "finance": ["bank", "finance", "credit card", "payment", "fintech", "investment", "lending"],
        "ecommerce": ["ecommerce", "shopping", "online store", "retail"],
        "ai solutions": ["ai", "artificial intelligence", "machine learning", "ml", "model", "llm", "b2b", "platform", "data science"],
    }

    data_types = {
        "PHI": ["health data", "patient", "medical record", "phi", "doctor", "lab result", "clinical", "hospital", "diagnosis"],
        "PII": ["personal data", "sensitive personal data", "pii", "name", "address", "email", "phone", "aadhar", "dob", "identity"],
        "financial": ["financial", "financial data", "bank account", "credit card", "payment", "transaction", "upi", "investment", "fintech"],
    }

    regions = {
        "USA": ["united states", "us", "usa", "america"],
        "EU": ["europe", "germany", "france", "eu", "european union"],
        "India": ["india", "indian", "bharat"],
        "Canada": ["canada", "canadian"],
        "Brazil": ["brazil", "brasil"],
    }

    def match_category(rules, text):
        match_scores = {}
        for label, keywords in rules.items():
            score = sum(kw in text for kw in keywords)
            if score > 0:
                match_scores[label] = score
        return max(match_scores, key=match_scores.get) if match_scores else "Unknown"

    matched_domain = match_category(domains, text)
    matched_data_type = match_category(data_types, text)
    matched_region = match_category(regions, text)

    # Match compliances
    compliance_matches = []
    for _, row in compliance_df.iterrows():
        domain = str(row['Domain']).lower()
        applies_to = str(row['Applies To']).lower()
        applies_to_list = [item.strip().lower() for item in applies_to.split(",")]
        followed = str(row.get('Followed By Compunnel', '')).strip().lower() == "yes"
        reason = row.get("Why Required", "").strip()
        checklist = [item for item in row.iloc[3:6] if pd.notna(item)]

        if (
            matched_domain == domain or domain == "all"
        ) and (
            matched_data_type.lower() in applies_to_list
            or matched_region.lower() in applies_to_list
            or "all" in applies_to_list
        ):
            compliance_matches.append({
                "name": row['Compliance Name'],
                "followed": followed,
                "why": reason,
                "checklist": checklist
            })

    # Display project info
    st.subheader("🔍 Detected Project Info")
    st.write(f"**Domain**: {matched_domain}")
    st.write(f"**Data Type**: {matched_data_type}")
    st.write(f"**Geography**: {matched_region}")

    # Show compliance suggestions
    st.subheader("✅ Required Compliances for this Project")

    if not compliance_matches:
        st.warning("⚠️ No compliance frameworks matched this project.")
    else:
        already = [c for c in compliance_matches if c["followed"]]
        missing = [c for c in compliance_matches if not c["followed"]]

        st.markdown("✅ **Already Compliant With:**")
        if already:
            for comp in already:
                st.success(comp["name"])
        else:
            st.warning("None of the matched compliances are currently covered.")

        st.markdown("❗ **Needs to be Implemented for this Project:**")
        if missing:
            for comp in missing:
                st.error(f"{comp['name']}")
                if comp["why"]:
                    st.info(f"💡 _Why Required_: {comp['why']}")
        else:
            st.info("All required compliances are already covered by Compunnel.")

        # Checklist
        st.subheader("📋 Checklist for Each Compliance")
        for comp in compliance_matches:
            with st.expander(f"{'🟢' if comp['followed'] else '🔴'} {comp['name']}"):
                for item in comp["checklist"]:
                    st.write(f"- {item}")
                if comp["why"]:
                    st.markdown(f"**Why Required**: _{comp['why']}_")

        # Downloadable report
        report_lines = []
        report_lines.append("🔐 Compunnel AI-Powered Compliance Advisor Report")
        report_lines.append("=" * 50)
        report_lines.append(f"\n📄 Project Description:\n{project_description}")
        report_lines.append(f"\n🧠 Detected Domain: {matched_domain}")
        report_lines.append(f"🧠 Data Type: {matched_data_type}")
        report_lines.append(f"🧠 Region: {matched_region}\n")

        report_lines.append("✅ Already Compliant With:")
        if already:
            for comp in already:
                report_lines.append(f" - {comp['name']}")
        else:
            report_lines.append(" - None")

        report_lines.append("\n❗ Needs to be Implemented:")
        if missing:
            for comp in missing:
                report_lines.append(f" - {comp['name']}")
                if comp['why']:
                    report_lines.append(f"   Why Required: {comp['why']}")
        else:
            report_lines.append(" - All required compliances are covered.")

        report_lines.append("\n📋 Checklist for Each Compliance:")
        for comp in compliance_matches:
            report_lines.append(f"\n🔹 {comp['name']}:")
            for item in comp['checklist']:
                report_lines.append(f"   - {item}")
            if comp['why']:
                report_lines.append(f"   💡 Why: {comp['why']}")

        report_text = "\n".join(report_lines)

        st.download_button(
            label="📥 Download Report as Text",
            data=report_text,
            file_name="compliance_report.txt",
            mime="text/plain"
        )
