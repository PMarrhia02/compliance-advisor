import streamlit as st
import pandas as pd

st.set_page_config(page_title="Compliance Advisor", layout="wide")

st.title("🔐 Compunnel AI-Powered Compliance Advisor")
st.write("Enter your project brief to get a list of required compliances, matched against Compunnel's existing certifications.")

# Step 1: Load compliance data from Google Sheets
sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"  # 👈 Replace this with your actual sheet ID
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

try:
    compliance_df = pd.read_csv(sheet_url)
    st.success("✅ Compliance database loaded successfully.")
except Exception as e:
    st.error("❌ Failed to load compliance database. Please check the sheet ID and sharing permissions.")
    st.stop()

# Step 2: Project Description Input
project_description = st.text_area("📄 Project Description", height=200)

if st.button("Analyze Project"):
    if project_description.strip() == "":
        st.warning("Please enter a valid project description.")
        st.stop()

    text = project_description.lower()

    # Step 3: Match Categories
    domains = {
        "healthcare": ["healthcare", "hospital", "patient", "medical", "clinic"],
        "finance": ["bank", "finance", "credit card", "payment", "fintech"],
        "ecommerce": ["ecommerce", "shopping", "online store", "retail"],
        "ai solutions": ["ai", "artificial intelligence", "machine learning", "model"],
    }

    data_types = {
        "PHI": ["health data", "patient", "medical record", "PHI"],
        "PII": ["personal data", "name", "address", "email", "phone"],
        "financial": ["credit card", "bank account", "payment", "transaction"],
    }

    regions = {
        "USA": ["united states", "us", "usa", "america"],
        "EU": ["europe", "germany", "france", "eu", "european union"],
        "India": ["india", "indian"],
    }

    def match_category(rules, text):
        for label, keywords in rules.items():
            for word in keywords:
                if word in text:
                    return label
        return "Unknown"

    matched_domain = match_category(domains, text)
    matched_data_type = match_category(data_types, text)
    matched_region = match_category(regions, text)

    # Step 4: Match Compliance from Google Sheet
    compliance_suggestions = []

    for _, row in compliance_df.iterrows():
        domain = str(row['Domain']).lower()
        applies_to = str(row['Applies To']).lower()

        if (
            matched_domain in domain or domain == "all"
        ) and (
            matched_data_type in applies_to
            or matched_region in applies_to
            or applies_to == "all"
        ):
            compliance_suggestions.append(row['Compliance Name'])

    compliance_suggestions = list(set(compliance_suggestions))

    # Step 5: Compunnel Existing Compliances
    compunnel_compliances = ["ISO 27001", "SOC 2", "GDPR", "CCPA or State-level Privacy Laws"]

    already_available = [c for c in compliance_suggestions if c in compunnel_compliances]
    missing_compliances = [c for c in compliance_suggestions if c not in compunnel_compliances]

    # Step 6: Display Results
    st.subheader("🔍 Detected Project Info")
    st.write(f"**Domain**: {matched_domain}")
    st.write(f"**Data Type**: {matched_data_type}")
    st.write(f"**Geography**: {matched_region}")

    st.subheader("✅ Required Compliances for this Project")
    for c in compliance_suggestions:
        st.write(f"• {c}")

    st.subheader("🏢 Compunnel Compliance Coverage")

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
        st.info("All suggested compliances are already covered by Compunnel.")

    st.subheader("📋 Checklist for Each Compliance")
    for compliance in compliance_suggestions:
        st.markdown(f"**{compliance}**")
        checklist_items = compliance_df[compliance_df["Compliance Name"] == compliance].iloc[0, 3:]
        for item in checklist_items:
            if pd.notna(item):
                st.write(f"- {item}")
