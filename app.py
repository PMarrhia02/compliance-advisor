import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Compliance Advisor", layout="wide")
st.title("🔐 Compunnel AI-Powered Compliance Advisor")
st.write("Enter your project brief to get a list of required compliances, matched against Compunnel's existing certifications.")

# Load compliance data from Google Sheets
sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

try:
    compliance_df = pd.read_csv(sheet_url)
    st.success("✅ Compliance database loaded successfully.")
except Exception as e:
    st.error("❌ Failed to load compliance database. Please check the sheet ID and sharing permissions.")
    st.stop()

# Project Description Input
project_description = st.text_area("📄 Project Description", height=200)

if st.button("Analyze Project"):
    if project_description.strip() == "":
        st.warning("Please enter a valid project description.")
        st.stop()

    text = project_description.lower()

    # Keyword rules
    domains = {
    "healthcare": ["healthcare", "hospital", "patient", "medical", "clinic"],
    "finance": ["bank", "finance", "credit card", "payment", "fintech"],
    "ecommerce": ["ecommerce", "shopping", "online store", "retail"],
    "ai solutions": ["ai", "artificial intelligence", "machine learning", "ml", "model", "llm", "b2b", "platform"],
}
,

    data_types = {
        "PHI": ["health data", "patient", "medical record", "phi", "doctor", "lab result"],
        "PII": ["personal data", "name", "address", "email", "phone", "aadhar", "dob"],
        "financial": ["credit card", "bank account", "payment", "transaction", "upi"],
    }

    regions = {
        "USA": ["united states", "us", "usa", "america"],
        "EU": ["europe", "germany", "france", "eu", "european union"],
        "India": ["india", "indian", "bharat"],
    }

    # Match based on most keyword hits
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

    # Match Compliance from Sheet
    compliance_suggestions = []
    for _, row in compliance_df.iterrows():
        domain = str(row['Domain']).lower()
        applies_to = str(row['Applies To']).lower()
        applies_to_list = [item.strip() for item in applies_to.split(",")]

        if (
            matched_domain == domain or domain == "all"
        ) and (
            matched_data_type.lower() in applies_to_list
            or matched_region.lower() in applies_to_list
            or "all" in applies_to_list
        ):
            compliance_name = row['Compliance Name']
            is_followed = str(row.get('Followed By Compunnel', '')).strip().lower() == "yes"
            checklist_items = row.iloc[3:]
            compliance_suggestions.append({
                "name": compliance_name,
                "followed": is_followed,
                "checklist": checklist_items
            })

    # Display Project Info
    st.subheader("🔍 Detected Project Info")
    st.write(f"**Domain**: {matched_domain}")
    st.write(f"**Data Type**: {matched_data_type}")
    st.write(f"**Geography**: {matched_region}")

    # Display Compliance Recommendations
    st.subheader("✅ Required Compliances for this Project")
    if not compliance_suggestions:
        st.warning("⚠️ No compliance frameworks matched this project. Try using more detailed keywords.")
    else:
        already_available = [c["name"] for c in compliance_suggestions if c["followed"]]
        missing_compliances = [c["name"] for c in compliance_suggestions if not c["followed"]]

        st.markdown("✅ **Already Compliant With:**")
        if already_available:
            for comp in already_available:
                st.success(comp)
        else:
            st.warning("None of the matched compliances are currently covered.")

        st.markdown("❗ **Needs to be Implemented for this Project:**")
        if missing_compliances:
            for comp in missing_compliances:
                st.error(comp)
        else:
            st.info("All required compliances are already covered by Compunnel.")

        # Checklist display
        st.subheader("📋 Checklist for Each Compliance")
        for c in compliance_suggestions:
            st.markdown(f"**{c['name']}**")
            for item in c["checklist"]:
                if pd.notna(item):
                    st.write(f"- {item}")

        # Downloadable report
        report = StringIO()
        report.write("🔐 Compunnel Compliance Report\n\n")
        report.write(f"📄 Project: {project_description[:100]}...\n")
        report.write(f"Domain: {matched_domain}\n")
        report.write(f"Data Type: {matched_data_type}\n")
        report.write(f"Region: {matched_region}\n\n")
        report.write("Compliances:\n")
        for c in compliance_suggestions:
            status = "✅ Already Compliant" if c["followed"] else "❗ Needs Implementation"
            report.write(f"- {c['name']} [{status}]\n")
        report.write("\nChecklist:\n")
        for c in compliance_suggestions:
            report.write(f"\n{c['name']} Checklist:\n")
            for item in c["checklist"]:
                if pd.notna(item):
                    report.write(f"  - {item}\n")

        st.download_button(
            label="📥 Download Compliance Report",
            data=report.getvalue(),
            file_name="compliance_report.txt",
            mime="text/plain"
        )
