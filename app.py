import streamlit as st
import pandas as pd
from io import StringIO

# Page Config
st.set_page_config(page_title="Compliance Advisor", layout="wide")
st.markdown("<h1 style='color:#003366;'>🔐 Compunnel AI-Powered Compliance Advisor</h1>", unsafe_allow_html=True)

# Sidebar Branding
with st.sidebar:
    st.markdown("## 🏢 Compunnel")
    st.markdown("AI-Powered Cybersecurity Compliance Advisor")
    st.markdown("___")
    st.markdown("**Need help?**")
    st.info("Use keywords like *healthcare*, *PHI*, *India*, *AI*, etc.")

# Load compliance database
sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

try:
    compliance_df = pd.read_csv(sheet_url)
    st.success("✅ Compliance database loaded successfully.")
except Exception as e:
    st.error("❌ Failed to load compliance database.")
    st.stop()

# Input area
st.markdown("### 📄 Describe Your Project")
project_description = st.text_area("What does the project do?", height=180)

if st.button("🔍 Analyze Project"):
    if project_description.strip() == "":
        st.warning("Please enter a valid project description.")
        st.stop()

    text = project_description.lower()

    # Matching rules
    domains = {
        "healthcare": ["healthcare", "hospital", "patient", "medical", "clinic"],
        "finance": ["bank", "finance", "credit card", "payment", "fintech", "investment", "lending"],
        "ecommerce": ["ecommerce", "shopping", "online store", "retail"],
        "ai solutions": ["ai", "artificial intelligence", "machine learning", "ml", "model", "llm", "b2b", "platform", "data science"],
    }

    data_types = {
        "PHI": ["health data", "patient", "medical record", "phi", "doctor", "lab result", "clinical", "hospital", "diagnosis"],
        "PII": ["personal data", "pii", "name", "address", "email", "phone", "aadhar", "dob", "identity"],
        "financial": ["financial", "credit card", "bank", "transaction", "upi", "investment"],
    }

    regions = {
        "USA": ["usa", "united states", "america", "us"],
        "EU": ["europe", "germany", "france", "eu", "european union"],
        "India": ["india", "indian", "bharat"],
        "Canada": ["canada", "canadian"],
        "Brazil": ["brazil", "brasil"],
    }

    def match_category(rules, text):
        match_scores = {label: sum(kw in text for kw in keywords) for label, keywords in rules.items()}
        return max(match_scores, key=match_scores.get) if match_scores else "Unknown"

    matched_domain = match_category(domains, text)
    matched_data_type = match_category(data_types, text)
    matched_region = match_category(regions, text)

    # Match compliances
    compliance_suggestions = []
    for _, row in compliance_df.iterrows():
        domain = str(row['Domain']).lower()
        applies_to = str(row['Applies To']).lower()
        applies_to_list = [item.strip().lower() for item in applies_to.split(",")]
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

    # Split into columns
    left, right = st.columns(2)

    with left:
        st.markdown("### 🧠 Detected Project Info")
        st.info(f"**Domain**: {matched_domain}")
        st.info(f"**Data Type**: {matched_data_type}")
        st.info(f"**Geography**: {matched_region}")

    with right:
        st.markdown("### 📊 Compliance Overview")

        if not compliance_suggestions:
            st.warning("⚠️ No compliance frameworks matched this project.")
        else:
            already = [c for c in compliance_suggestions if c["followed"]]
            missing = [c for c in compliance_suggestions if not c["followed"]]

            st.markdown("✅ **Already Compliant With:**")
            if already:
                for comp in already:
                    st.success(f"🛡️ {comp['name']}")
            else:
                st.warning("None are currently followed.")

            st.markdown("❗ **Needs to be Implemented:**")
            if missing:
                for comp in missing:
                    st.error(f"🚨 {comp['name']}")
                    if comp["why"]:
                        st.info(f"💡 _Why_: {comp['why']}")

    st.markdown("---")
    st.markdown("### 📋 Compliance Checklist")

    for c in compliance_suggestions:
        with st.expander(f"{'🟢' if c['followed'] else '🔴'} {c['name']} Checklist", expanded=False):
            for item in c["checklist"]:
                if pd.notna(item) and item not in ["Yes", "No"]:
                    icon = "✅" if c["followed"] else "⚠️"
                    st.markdown(f"{icon} {item}")
            if c["why"]:
                st.caption(f"**Why Required**: {c['why']}")
