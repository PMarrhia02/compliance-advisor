import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from streamlit_authenticator import Hasher
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------------------------
# Authentication Setup
# ---------------------------

# Create usernames and plain passwords
usernames = ['admin', 'viewer']
passwords = ['12345', '98765']

# ✅ Use the updated Hasher static method (for version >= 0.4.0)
hashed_pw = Hasher.generate(passwords)

# Create credentials dictionary
credentials = {
    "usernames": {
        "admin": {"name": "Admin", "password": hashed_pw[0]},
        "viewer": {"name": "Viewer", "password": hashed_pw[1]},
    }
}

# Initialize authenticator
authenticator = stauth.Authenticate(
    credentials,
    "compliance_advisor_cookie",
    "secret_key",
    cookie_expiry_days=30,
)

# Display login widget
name, authentication_status, username = authenticator.login("Login", "main")

# ---------------------------
# Streamlit App Logic
# ---------------------------

if authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.write(f"Welcome, {name}! 👋")

    st.title("Compliance Advisor Pro 🛡️")
    st.write("AI-powered compliance recommendation tool for Compunnel.")

    # Example app content
    project_description = st.text_area("Enter project description:")
    if project_description:
        st.write("Analyzing your project...")
        st.success("Recommended compliance frameworks will appear here.")

elif authentication_status is False:
    st.error("❌ Username/password is incorrect")
elif authentication_status is None:
    st.warning("⚠️ Please enter your username and password")
