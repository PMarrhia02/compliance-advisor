import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import random

# =====================
# Page Setup
# =====================
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# =====================
# Digital Backgrounds
# =====================
backgrounds = [
    "https://images.unsplash.com/photo-1601933471450-5f96c130f7b0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80",
    "https://images.unsplash.com/photo-1591696205602-3cce77d57e5b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80",
    "https://images.unsplash.com/photo-1611095564989-8e14c1d898d5?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80",
    "https://images.unsplash.com/photo-1591696331114-f8bb2b0b86f6?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80",
    "https://images.unsplash.com/photo-1612831455540-501f36bcd64e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80"
]
bg_url = random.choice(backgrounds)

# =====================
# Custom CSS with semi-transparent content container
# =====================
st.markdown(f"""
<style>
.stApp {{
    background-image: url("{bg_url}");
    background-attachment: fixed;
    background-size: cover;
    background-repeat: no-repeat;
}}
.block-container {{
    background-color: rgba(255, 255, 255, 0.6) !important;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    backdrop-filter: blur(5px);
}}
.stButton>button {{
    background-color: #003366;
    color: white;
    border-radius: 8px;
    font-weight: bold;
    padding: 0.5em 1.5em;
    border: none;
}}
.stButton>button:hover {{
    background-color: #00509e;
}}
h1, h2, h3 {{ color: #002244; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); }}
.title {{ font-size: 2.5em; color: #003366; font-weight: bold; }}
.badge {{ display: inline-block; padding: 0.25em 0.6em; font-size: 90%; font-weight: 600; border-radius: 0.25rem; }}
.priority-high {{ border-left: 4px solid #dc3545; padding-left: 10px; margin: 8px 0; }}
.priority-standard {{ border-left: 4px solid #fd7e14; padding-left: 10px; margin: 8px 0; }}
.dashboard-card {{ border-radius: 10px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 6px rgba(0,0,0,0.15); }}
.footer {{ text-align: center; font-size: 0.9em; color: gray; margin-top: 3rem; }}
</style>
""", unsafe_allow_html=True)

# =====================
# Wrap content in container
# =====================
st.markdown("<div class='block-container'>", unsafe_allow_html=True)

# =====================
# Header
# =====================
st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
st.markdown("AI-powered compliance analysis for your exact requirements")

# =====================
# User Authentication
# =====================
if 'username' not in st.session_state:
    st.session_state.username = None

if st.session_state.username is None:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username == "admin" and password == "password":
            st.session_state.username = username
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password.")
else:
    st.success(f"Welcome, {st.session_state.username}!")

    # =====================
    # Load Google Sheet Data
    # =====================
    @st.cache_data
    def load_data():
        sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            df = pd.read_csv(sheet_url)
            required_cols = ['Compliance Name', 'Domain', 'Applies To','Checklist 1', 'Checklist 2', 'Checklist 3','Followed By Compunnel', 'Why Required']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                st.error(f"Missing required columns: {', '.join(missing_cols)}")
                st.stop()
            return df
        except Exception as e:
            st.error(f"Failed to load data: {str(e)}")
            st.stop()

    compliance_df = load_data()

    # =====================
    # Project Description Input
    # =====================
    project_description = st.text_area(
        "Describe your project (include data types and regions):",
        height=150,
        placeholder="e.g., 'Healthcare app storing patient records in India with EU users...'"
    )

    # =====================
    # Analysis functions (match_category & analyze_project)
    # =====================
    def match_category(text, categories):
        text = text.lower()
        scores = {k:0 for k in categories}
        for category, keywords in categories.items():
            for term in keywords:
                if term in text:
                    scores[category] += 2 if term == text.strip() else 1
        for category in scores:
            if categories[category]:
                scores[category] = scores[category]/len(categories[category])
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores, key=scores.get)
        else:
            for category in categories:
                if category in ["all", "global"]:
                    return category
            return list(categories.keys())[0]

    def analyze_project(description):
        domains = {"healthcare": ["healthcare","hospital","patient","medical","health","phi"],
                   "finance": ["bank","finance","payment","financial","pci","credit card"],
                   "ai solutions": ["ai","artificial intelligence","machine learning","ml"],
                   "govt/defense": ["government","defense","military","public sector"],
                   "all": []}
        data_types = {"PHI":["phi","health data","medical record","patient data"],
                      "PII":["pii","personal data","name","email","address","phone"],
                      "financial":["financial","credit card","transaction","bank account"],
                      "sensitive":["sensitive","confidential","proprietary"]}
        regions = {"India":["india","indian"], "USA":["usa","united states","us"], "EU":["eu","europe","gdpr"],
                   "Canada":["canada"], "Brazil":["brazil","lgpd"], "global":["global","international","worldwide"]}

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
                    "priority": "High" if str(row.get('Priority','')).strip().lower() == "high" else "Standard",
                    "alert": str(row.get('Trigger Alert','No')).strip().lower() == "yes",
                    "checklist": checklist,
                    "why": row.get("Why Required","")
                })
        return {"domain": matched_domain,"data_type": matched_data_type,"region": matched_region,"compliance_matches": compliance_matches}

# =====================
# Footer
# =====================
st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)  # Close block-container
