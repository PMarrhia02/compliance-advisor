import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import datetime
from streamlit_authenticator import Authenticate
from streamlit_authenticator.utilities.hasher import Hasher

# ==============================================
# APP CONFIG
# ==============================================
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

st.title("🧠 Compunnel | AI-Powered Compliance Advisor Pro")
st.markdown("### Smart Compliance Recommendations from Live Google Sheets")

# ==============================================
# AUTHENTICATION SETUP
# ==============================================
names = ["Admin", "Viewer"]
usernames = ["admin", "viewer"]
passwords = ["12345", "98765"]

# ✅ Correct password hashing for v0.4.2+
hashed_pw = Hasher.generate(passwords)

credentials = {
    "usernames": {
        usernames[0]: {"name": names[0], "password": hashed_pw[0]},
        usernames[1]: {"name": names[1], "password": hashed_pw[1]},
    }
}

authenticator = Authenticate(
    credentials=credentials,
    cookie_name="complianceadvisor_cookie",
    key="abcdef",
    cookie_expiry_days=30,
)

# ✅ Updated login call (new API for v0.4.2+)
name, authentication_status, username = authenticator.login(
    location="main",
    fields={
        "Form name": "Login",
        "Username": "Username",
        "Password": "Password",
        "Login": "Login",
    },
)

if authentication_status is False:
    st.error("❌ Invalid username or password.")
    st.stop()
elif authentication_status is None:
    st.warning("🔐 Please enter your credentials.")
    st.stop()
else:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"✅ Logged in as: {name}")

# ==============================================
# GOOGLE SHEETS CONNECTION
# ==============================================
@st.cache_data(ttl=600)
def load_compliance_data():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials.json", scope
        )
        client = gspread.authorize(creds)
        sheet = client.open("Compunnel_Compliance_DB").sheet1
        data = pd.DataFrame(sheet.get_all_records())
        return data
    except Exception as e:
        st.error("⚠️ Failed to load Google Sheet. Please check credentials or permissions.")
        st.stop()

compliance_df = load_compliance_data()

# ==============================================
# USER INPUT
# ==============================================
st.subheader("📝 Describe your project")
project_description = st.text_area(
    "Enter project details (domain, data type, region, etc.)",
    placeholder="Example: Healthcare project for US clients storing patient data in the cloud...",
)

# ==============================================
# COMPLIANCE RECOMMENDATION LOGIC
# ==============================================
def get_compliance_recommendations(description, df):
    if not description:
        return pd.DataFrame()

    desc = description.lower()
    matched_rows = []

    for _, row in df.iterrows():
        domain = str(row.get("Domain", "")).lower()
        applies_to = str(row.get("Applies To", "")).lower()
        checklist = str(row.get("Checklist items", "")).lower()

        if any(keyword in desc for keyword in [domain, applies_to, checklist]):
            matched_rows.append(row)

    return pd.DataFrame(matched_rows)

# ==============================================
# RUN ANALYSIS
# ==============================================
if st.button("🔍 Analyze Project"):
    if not project_description.strip():
        st.warning("Please enter a project description first.")
    else:
        st.info("Analyzing project description... ⏳")
        results_df = get_compliance_recommendations(project_description, compliance_df)

        if not results_df.empty:
            st.success(f"✅ Found {len(results_df)} relevant compliance frameworks!")
            st.dataframe(results_df)
        else:
            st.warning("No direct compliance matches found for your description.")

# ==============================================
# DOWNLOAD REPORTS
# ==============================================
def generate_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Compunnel | Compliance Advisor Pro Report", styles["Heading1"]))
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 12))

    for _, row in data.iterrows():
        story.append(Paragraph(f"<b>Compliance Name:</b> {row['Compliance Name']}", styles["Heading3"]))
        story.append(Paragraph(f"Domain: {row['Domain']}", styles["Normal"]))
        story.append(Paragraph(f"Applies To: {row['Applies To']}", styles["Normal"]))
        story.append(Paragraph(f"Checklist: {row['Checklist items']}", styles["Normal"]))
        story.append(Paragraph(f"Followed By Compunnel: {row['Followed By Compunnel']}", styles["Normal"]))
        story.append(Paragraph(f"Why Required: {row['Why Required']}", styles["Normal"]))
        story.append(Spacer(1, 12))

    doc.build(story)
    buffer.seek(0)
    return buffer

if st.button("📄 Download PDF Report"):
    if "results_df" in locals() and not results_df.empty:
        pdf_buffer = generate_pdf(results_df)
        st.download_button(
            label="⬇️ Download Report as PDF",
            data=pdf_buffer,
            file_name="Compliance_Report.pdf",
            mime="application/pdf",
        )
    else:
        st.warning("No analysis results found. Please run the analysis first.")

if st.button("📊 Download CSV Report"):
    if "results_df" in locals() and not results_df.empty:
        csv_data = results_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Report as CSV",
            data=csv_data,
            file_name="Compliance_Report.csv",
            mime="text/csv",
        )
    else:
        st.warning("No analysis results found. Please run the analysis first.")
