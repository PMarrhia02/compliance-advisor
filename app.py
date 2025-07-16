import streamlit as st
import pandas as pd
from io import StringIO

# Page config
st.set_page_config(page_title="Compliance Advisor", layout="wide")
st.title("🔐 Compunnel AI-Powered Compliance Advisor")
st.write("Enter your project brief to get a list of required compliances, matched against Compunnel's existing certifications.")

# Load from Google Sheet
# ---- Load Compliance Data from Google Sheets ----
sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

@@ -18,89 +16,111 @@
    st.error("❌ Failed to load compliance database. Please check the sheet ID and sharing permissions.")
    st.stop()

# Input
project_description = st.text_area("📄 Project Description", height=200)
# ---- Project Prompt Memory (Option 3: Save & Reuse Prompts) ----
st.subheader("📁 Saved Project Prompts")

if "saved_prompts" not in st.session_state:
    st.session_state["saved_prompts"] = {}

selected_prompt = st.selectbox("Select a saved project", [""] + list(st.session_state["saved_prompts"].keys()))

if selected_prompt:
    project_description = st.session_state["saved_prompts"][selected_prompt]
else:
    project_description = ""

project_description = st.text_area("📄 Project Description", value=project_description, height=200)

# Save new prompt
new_name = st.text_input("💾 Save this prompt as (give project name):")
if st.button("Save Project Prompt"):
    if new_name and project_description.strip():
        st.session_state["saved_prompts"][new_name] = project_description
        st.success(f"✅ Saved project: {new_name}")

# ---- Analyze Project ----
if st.button("Analyze Project"):
    if project_description.strip() == "":
        st.warning("Please enter a valid project description.")
        st.stop()

    text = project_description.lower()

    # Keyword match rules
    domains = {
        "healthcare": ["healthcare", "hospital", "patient", "medical", "clinic"],
        "finance": ["bank", "finance", "credit card", "payment", "fintech", "investment", "lending"],
        "finance": ["bank", "finance", "credit card", "payment", "fintech"],
        "ecommerce": ["ecommerce", "shopping", "online store", "retail"],
        "ai solutions": ["ai", "artificial intelligence", "machine learning", "ml", "model", "llm", "b2b", "platform", "data science"],
        "ai solutions": ["ai", "artificial intelligence", "machine learning", "model"],
    }

    data_types = {
        "PHI": ["health data", "patient", "medical record", "phi", "doctor", "lab result", "clinical", "hospital", "diagnosis"],
        "PII": ["personal data", "sensitive personal data", "pii", "name", "address", "email", "phone", "aadhar", "dob", "identity"],
        "financial": ["financial", "financial data", "bank account", "credit card", "payment", "transaction", "upi", "investment", "fintech"],
        "PHI": ["health data", "patient", "medical record", "phi", "doctor", "lab result"],
        "PII": ["personal data", "name", "address", "email", "phone", "aadhar", "dob"],
        "financial": ["credit card", "bank account", "payment", "transaction", "upi"],
    }

    regions = {
        "USA": ["united states", "us", "usa", "america"],
        "EU": ["europe", "germany", "france", "eu", "european union"],
        "India": ["india", "indian", "bharat"],
        "Canada": ["canada", "canadian"],
        "Brazil": ["brazil", "brasil"],
        "Canada": ["canada", "canadian"]
    }

    def match_category(rules, text):
        match_scores = {}
        for label, keywords in rules.items():
            score = sum(kw in text for kw in keywords)
            if score > 0:
                match_scores[label] = score
        return max(match_scores, key=match_scores.get) if match_scores else "Unknown"
            for word in keywords:
                if word in text:
                    return label
        return "Unknown"

    matched_domain = match_category(domains, text)
    matched_data_type = match_category(data_types, text)
    matched_region = match_category(regions, text)

    # Match compliances
    # Match Compliance from Sheet
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
            matched_domain in domain or domain == "all"
        ) and (
            matched_data_type.lower() in applies_to_list
            or matched_region.lower() in applies_to_list
            or "all" in applies_to_list
            matched_data_type in applies_to
            or matched_region in applies_to
            or applies_to == "all"
        ):
            compliance_suggestions.append({
                "name": row['Compliance Name'],
                "followed": followed,
                "why": reason,
                "checklist": checklist
                "checklist": row[3:6],  # You can adjust if more columns are added
                "compunnel": row.get('Followed By Compunnel', 'No'),
                "why": row.get("Why Required", "")
            })

    # Display project info
    compunnel_compliances = [row['Compliance Name'] for _, row in compliance_df[compliance_df['Followed By Compunnel'].str.lower() == "yes"].iterrows()]

    already_available = [c for c in compliance_suggestions if c["name"] in compunnel_compliances]
    missing_compliances = [c for c in compliance_suggestions if c["name"] not in compunnel_compliances]

    # Display Results
    st.subheader("🔍 Detected Project Info")
    st.write(f"**Domain**: {matched_domain}")
    st.write(f"**Data Type**: {matched_data_type}")
    st.write(f"**Geography**: {matched_region}")

    # Show results
    st.subheader("✅ Required Compliances for this Project")

    if not compliance_suggestions:
        st.warning("⚠️ No compliance frameworks matched this project.")
    if compliance_suggestions:
        for c in compliance_suggestions:
            st.write(f"• {c['name']}")
    else:
        already_available = [c for c in compliance_suggestions if c["followed"]]
        missing_compliances = [c for c in compliance_suggestions if not c["followed"]]
        st.warning("⚠️ No compliance frameworks matched this project. Try using more detailed keywords.")

    st.subheader("🏢 Compunnel Compliance Coverage")

    if compliance_suggestions:
        st.markdown("✅ **Already Compliant With:**")
        if already_available:
            for comp in already_available:
@@ -111,15 +131,20 @@ def match_category(rules, text):
        st.markdown("❗ **Needs to be Implemented for this Project:**")
        if missing_compliances:
            for comp in missing_compliances:
                st.error(f"{comp['name']}")
                if comp["why"]:
                    st.info(f"💡 _Why Required_: {comp['why']}")
                with st.container():
                    st.error(f"🔸 {comp['name']}")
                    if comp["why"]:
                        st.markdown(f"📝 **Why Required**: {comp['why']}")
        else:
            st.info("All required compliances are already covered by Compunnel.")

    # Checklist Section
    if compliance_suggestions:
        st.subheader("📋 Checklist for Each Compliance")
        for c in compliance_suggestions:
            st.markdown(f"**{c['name']}**")
            for item in c["checklist"]:
                if pd.notna(item):
        for comp in compliance_suggestions:
            st.markdown(f"**{comp['name']}**")
            for item in comp["checklist"]:
                if pd.notna(item) and item.strip().lower() not in ['yes', 'no']:
                    st.write(f"- {item}")
            if comp["why"]:
                st.markdown(f"📝 **Why Required**: {comp['why']}")
