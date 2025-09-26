import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import re

# Page setup
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# Background image + overlay
bg_url = "https://images.unsplash.com/photo-1677165605399-9e2f1e9a6e3e?crop=entropy&cs=tinysrgb&fit=max&ixid=MnwzNjUyOXwwfDF8c2VhcmNofDkxfHxmb2xkZXJzfGVufDB8fHx8fDE2NzYxNzYwMjA&ixlib=rb-1.2.1&q=80&w=1080"

st.markdown(f"""
<style>
.stApp {{
    background: linear-gradient(rgba(255,255,255,0.1), rgba(255,255,255,0.1)), url("{bg_url}");
    background-size: cover;
    background-attachment: fixed;
    background-repeat: no-repeat;
}}
.stContainer, .stExpander {{
    background: rgba(255, 255, 255, 0.85);
    border-radius: 15px;
    padding: 1rem;
    backdrop-filter: blur(6px);
    color: #000 !important;
}}
div[data-testid="stDataFrameContainer"], .stMetricValue, .stMetricLabel, .stExpanderHeader, .stText, .stMarkdown {{
    color: #000 !important;
}}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<div style='font-size:2.5em; font-weight:bold; color:#003366;'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
st.markdown("AI-powered compliance analysis for your exact requirements")

# -----------------------------
# LOGIN FUNCTIONALITY
# -----------------------------
if 'username' not in st.session_state:
    st.session_state.username = None

if st.session_state.username is None:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username == "admin" and password == "password":  # Replace with secure auth
            st.session_state.username = username
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password.")
else:
    st.success(f"Welcome, {st.session_state.username}!")

    # -----------------------------
    # Load data from Google Sheets
    # -----------------------------
    @st.cache_data
    def load_data():
        sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            df = pd.read_csv(sheet_url)
            required_cols = [
                'Compliance Name', 'Domain', 'Applies To',
                'Checklist 1', 'Checklist 2', 'Checklist 3',
                'Followed By Compunnel', 'Why Required'
            ]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                st.error(f"Missing required columns: {', '.join(missing_cols)}")
                st.stop()
            return df
        except Exception as e:
            st.error(f"Failed to load data: {str(e)}")
            st.stop()

    compliance_df = load_data()

    # -----------------------------
    # Project input
    # -----------------------------
    project_description = st.text_area(
        "Describe your project (include data types and regions):",
        height=150,
        placeholder="e.g., 'Healthcare app storing patient records in India with EU users...'"
    )

    # -----------------------------
    # STRICT MATCH CATEGORY FUNCTION
    # -----------------------------
    def match_category(text, categories):
        text = text.lower()
        scores = {k: 0 for k in categories}
        words = re.findall(r'\b\w+\b', text)  # split text into words
        for category, keywords in categories.items():
            for term in keywords:
                term_lower = term.lower()
                if term_lower in text:
                    if term_lower in words:
                        scores[category] += 2  # exact word match
                    else:
                        scores[category] += 1  # partial substring match
        # Normalize scores
        for category in scores:
            if categories[category]:
                scores[category] = scores[category] / len(categories[category])
        max_score = max(scores.values())
        if max_score >= 0.5:
            return max(scores, key=scores.get)
        else:
            return "all"  # fallback

    # -----------------------------
    # ANALYZE PROJECT FUNCTION
    # -----------------------------
    def analyze_project(description):
        domains = {
            "healthcare": ["healthcare", "hospital", "patient", "medical", "health", "phi"],
            "finance": ["bank", "finance", "payment", "financial", "pci", "credit card"],
            "ai solutions": ["ai", "artificial intelligence", "machine learning", "ml"],
            "govt/defense": ["government", "defense", "military", "public sector"],
            "all": []
        }
        data_types = {
            "PHI": ["phi", "health data", "medical record", "patient data"],
            "PII": ["pii", "personal data", "name", "email", "address", "phone"],
            "financial": ["financial", "credit card", "transaction", "bank account"],
            "sensitive": ["sensitive", "confidential", "proprietary"]
        }
        regions = {
            "India": ["india", "indian"],
            "USA": ["usa", "united states", "us"],
            "EU": ["eu", "europe", "gdpr"],
            "Canada": ["canada"],
            "Brazil": ["brazil", "lgpd"],
            "global": ["global", "international", "worldwide"]
        }
        matched_domain = match_category(description, domains)
        matched_data_type = match_category(description, data_types)
        matched_region = match_category(description, regions)
        compliance_matches = []
        for _, row in compliance_df.iterrows():
            row_domains = [x.strip().lower() for x in str(row['Domain']).split(",")]
            domain_match = "all" in row_domains or matched_domain in row_domains
            applies_to = [x.strip().lower() for x in str(row['Applies To']).split(",")]
            applies_match = ("all" in applies_to or matched_region.lower() in applies_to or matched_data_type.lower() in applies_to)
            if domain_match and applies_match:
                checklist = [str(item) for item in [row['Checklist 1'], row['Checklist 2'], row['Checklist 3']] if pd.notna(item)]
                compliance_matches.append({
                    "name": row['Compliance Name'],
                    "domain": str(row['Domain']).lower(),
                    "applies_to": applies_to,
                    "followed": str(row['Followed By Compunnel']).strip().lower() == "yes",
                    "priority": "High" if str(row.get('Priority', '')).strip().lower() == "high" else "Standard",
                    "alert": str(row.get('Trigger Alert', 'No')).strip().lower() == "yes",
                    "checklist": checklist,
                    "why": row.get("Why Required", "")
                })
        return {"domain": matched_domain, "data_type": matched_data_type, "region": matched_region, "compliance_matches": compliance_matches}

    # -----------------------------
    # Rest of your code remains unchanged
    # (PDF generation, metrics, priority matrix, report download)
    # -----------------------------
    # Just replace the old match_category with this stricter one
    # All functionality like PDF/CSV, login, background stays
