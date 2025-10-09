import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from streamlit_authenticator import Authenticate
from streamlit_authenticator.utilities.hasher import Hasher  # ✅ updated import

# ==============================
# 🔐 AUTHENTICATION SETUP
# ==============================
names = ['Admin', 'Viewer']
usernames = ['admin', 'viewer']
passwords = ['12345', '98765']  # Plain text for demo; use strong passwords in production!

# ✅ Updated password hashing for streamlit-authenticator >= 0.4.2
try:
    hashed_pw = Hasher.hash_list(passwords)
except Exception:
    # Fallback for possible version differences
    h = Hasher(passwords)
    hashed_pw = h.hash_list()

credentials = {
    "usernames": {
        "admin": {"name": "Admin", "password": hashed_pw[0]},
        "viewer": {"name": "Viewer", "password": hashed_pw[1]},
    }
}

authenticator = Authenticate(
    credentials=credentials,
    cookie_name="complianceadvisor",
    key="abcdef",
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login("main")

if authentication_status is False:
    st.error("Invalid username or password")
    st.stop()
elif authentication_status is None:
    st.warning("Please enter your credentials")
    st.stop()

# ==============================
# 🎨 PAGE SETUP AND STYLES
# ==============================
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

st.markdown("""
<style>
    .title { font-size: 2.5em; color: #003366; font-weight: bold; }
    .dashboard-card { border-radius: 10px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .footer { text-align: center; font-size: 0.9em; color: gray; margin-top: 3rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
st.markdown("AI-powered compliance analysis and tracking for your requirements")

# ==============================
# 📄 LOAD DATA FROM GOOGLE SHEETS
# ==============================
@st.cache_data
def load_data(sheet_id, gid=None):
    base_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    url = base_url if not gid else f"{base_url}&gid={gid}"
    return pd.read_csv(url)

SHEET_ID = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"  # ✅ replace with your actual Sheet ID

try:
    compliance_df = load_data(SHEET_ID)
except Exception as e:
    st.error(f"Error loading compliance data: {e}")
    st.stop()

try:
    breach_log = load_data(SHEET_ID, gid="YOUR_BREACH_LOG_GID")
except Exception:
    breach_log = pd.DataFrame(columns=["Date", "Project", "Compliance Name", "Description", "Status", "Owner"])

# ==============================
# 🧠 COMPLIANCE ANALYSIS
# ==============================
def match_category(text, categories):
    text = text.lower()
    scores = {k: 0 for k in categories}
    for category, keywords in categories.items():
        for term in keywords:
            if term in text:
                scores[category] += 2 if term == text.strip() else 1
    for category in scores:
        if categories[category]:
            scores[category] = scores[category] / len(categories[category])
    max_score = max(scores.values())
    if max_score > 0:
        return max(scores, key=scores.get)
    return list(categories.keys())[0]

def analyze_project(description):
    domains = {
        "healthcare": ["healthcare", "hospital", "patient", "medical", "health", "phi"],
        "finance": ["bank", "finance", "payment", "pci", "credit card"],
        "ai solutions": ["ai", "artificial intelligence", "ml"],
        "govt/defense": ["government", "defense", "public sector"],
        "all": []
    }
    data_types = {
        "PHI": ["phi", "health data", "medical record", "patient data"],
        "PII": ["pii", "personal data", "name", "email", "address"],
        "financial": ["financial", "credit card", "bank account"],
        "sensitive": ["sensitive", "confidential"]
    }
    regions = {
        "India": ["india", "indian"],
        "USA": ["usa", "us", "united states"],
        "EU": ["eu", "europe", "gdpr"],
        "Canada": ["canada"],
        "Brazil": ["brazil", "lgpd"],
        "global": ["global"]
    }

    matched_domain = match_category(description, domains)
    matched_data_type = match_category(description, data_types)
    matched_region = match_category(description, regions)

    compliance_matches = []
    for _, row in compliance_df.iterrows():
        row_domains = [x.strip().lower() for x in str(row["Domain"]).split(",")]
        applies_to = [x.strip().lower() for x in str(row["Applies To"]).split(",")]

        domain_match = "all" in row_domains or matched_domain in row_domains
        applies_match = (
            "all" in applies_to or matched_region.lower() in applies_to or matched_data_type.lower() in applies_to
        )

        if domain_match and applies_match:
            checklist = [str(item) for item in [row.get("Checklist 1"), row.get("Checklist 2"), row.get("Checklist 3")] if pd.notna(item)]
            compliance_matches.append({
                "name": row["Compliance Name"],
                "domain": str(row["Domain"]).lower(),
                "applies_to": applies_to,
                "followed": str(row["Followed By Compunnel"]).strip().lower() == "yes",
                "priority": "High" if str(row.get("Priority", "")).strip().lower() == "high" else "Standard",
                "alert": str(row.get("Trigger Alert", "No")).strip().lower() == "yes",
                "checklist": checklist,
                "why": row.get("Why Required", "")
            })

    return {
        "domain": matched_domain,
        "data_type": matched_data_type,
        "region": matched_region,
        "compliance_matches": compliance_matches
    }

# ==============================
# 🚀 MAIN INTERFACE
# ==============================
project_description = st.text_area(
    "Describe your project (include data types and regions):",
    height=120,
    placeholder="e.g., Healthcare app storing patient records in India with EU users...",
    help="This helps match your project to compliance requirements."
)

if st.button("🔍 Analyze Compliance", type="primary"):
    if not project_description.strip():
        st.warning("Please enter a project description")
        st.stop()

    with st.spinner("Analyzing requirements..."):
        results = analyze_project(project_description)
        st.session_state["results"] = results

        met = [c for c in results["compliance_matches"] if c["followed"]]
        pending = [c for c in results["compliance_matches"] if not c["followed"]]
        score = int((len(met) / len(results["compliance_matches"])) * 100 if results["compliance_matches"] else 0)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
            st.metric("Compliance Score", f"{score}%")
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
            st.metric("Pending Requirements", len(pending))
            st.markdown("</div>", unsafe_allow_html=True)
        with col3:
            st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
            st.metric("High Priority Items", len([c for c in pending if c["priority"] == "High"]))
            st.markdown("</div>", unsafe_allow_html=True)

        st.write("#### Compliance Progress Chart")
        plt.bar(["Compliant", "Pending"], [len(met), len(pending)], color=["green", "orange"])
        st.pyplot(plt)

        st.write("#### 📌 Detected Project Attributes")
        st.write(f"- **Domain:** {results['domain']}")
        st.write(f"- **Data Type:** {results['data_type']}")
        st.write(f"- **Region:** {results['region']}")

        st.write("#### 📝 Requirements Matrix")
        for req in results["compliance_matches"]:
            st.markdown(f"- {'✅' if req['followed'] else '❌'} **{req['name']}** ({req['priority']}): {', '.join(req['checklist'])}")

# ==============================
# 🧾 BREACH LOG SECTION
# ==============================
st.markdown("---")
st.markdown("### Compliance Breach & Audit Log")

with st.expander("Log a New Compliance Breach"):
    with st.form("log_breach"):
        breach_proj = st.text_input("Project")
        breach_name = st.text_input("Compliance Name")
        desc = st.text_area("Description")
        status = st.selectbox("Status", ["Open", "Investigating", "Closed"])
        owner = st.text_input("Owner")
        submit = st.form_submit_button("Submit Breach")

        if submit and breach_proj and breach_name and desc:
            new_row = {
                "Date": datetime.date.today().isoformat(),
                "Project": breach_proj,
                "Compliance Name": breach_name,
                "Description": desc,
                "Status": status,
                "Owner": owner
            }
            breach_log = pd.concat([breach_log, pd.DataFrame([new_row])], ignore_index=True)
            st.success("✅ Breach logged (demo mode — not saved to Google Sheet).")

st.write("#### All Breach Records")
st.dataframe(breach_log)

st.markdown("---")
st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", unsafe_allow_html=True)
