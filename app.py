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
    compliance_suggestions = []
    for _, row in compliance_df.iterrows():
        domain = str(row['Domain']).lower()
        applies_to = str(row['Applies To']).lower()
        applies_to_list = [item.strip() for item in applies_to.split(",")]
        followed = str(row.get('Followed By Compunnel', '')).strip().lower() == "yes"
        reason = row.get("Why Required", "").strip()
        checklist = row.iloc[3:]

        if (
            matched_domain == domain or domain == "all"
        ) and (
            matched_data_type.lower() in applies_to_list
            or matched_region.lower() in applies_to_list
            or "all" in applies_to_list
        ):
            compliance_suggestions.append({
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

    # Show results
    st.subheader("✅ Required Compliances for this Project")

    if not compliance_suggestions:
        st.warning("⚠️ No compliance frameworks matched this project.")
    else:
        already_available = [c for c in compliance_suggestions if c["followed"]]
        missing_compliances = [c for c in compliance_suggestions if not c["followed"]]

        st.markdown("✅ **Already Compliant With:**")
        if already_available:
            for comp in already_available:
                st.success(comp["name"])
        else:
            st.warning("None of the matched compliances are currently covered.")

        st.markdown("❗ **Needs to be Implemented for this Project:**")
        if missing_compliances:
            for comp in missing_compliances:
                st.error(f"{comp['name']}")
                if comp["why"]:
                    st.info(f"💡 _Why Required_: {comp['why']}")
        else:
            st.info("All required compliances are already covered by Compunnel.")

        # Checklist Section with Icons
        st.subheader("📋 Checklist for Each Compliance")
        for c in compliance_suggestions:
            st.markdown(f"**🔒 {c['name']}**")
            checklist_items = [item for item in c["checklist"] if pd.notna(item) and item not in ["Yes", "No"]]
            status_icon = "✅" if c["followed"] else "⚠️"
            for item in checklist_items:
                st.write(f"{status_icon} {item}")
            if c["why"]:
                st.info(f"💡 _Why Required_: {c['why']}")
