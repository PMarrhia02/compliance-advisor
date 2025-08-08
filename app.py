import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import streamlit_authenticator as stauth
import matplotlib.pyplot as plt
import feedparser
from datetime import datetime
import json
from transformers import pipeline  # For the chatbot feature

# Page setup
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# Custom CSS
st.markdown("""
    <style>
        .timeline { margin-top: 2rem; border-left: 3px solid #003366; padding-left: 1rem; }
        .chatbot { background-color: #f8f9fa; padding: 1rem; border-radius: 10px; }
        .template-box { border: 1px dashed #6c757d; padding: 1rem; margin: 1rem 0; }
    </style>
""", unsafe_allow_html=True)

# --- USER AUTHENTICATION (Enhanced) ---
hashed_passwords = stauth.Hasher(['password', 'userpass']).generate()

config = {
    'credentials': {
        'usernames': {
            'admin': {
                'email': 'admin@example.com',
                'name': 'Admin',
                'password': hashed_passwords[0],
                'role': 'admin'
            },
            'user': {
                'email': 'user@example.com',
                'name': 'Standard User',
                'password': hashed_passwords[1],
                'role': 'user'
            }
        }
    },
    'cookie': {
        'name': 'compliance_cookie',
        'key': 'some_random_signature_key',
        'expiry_days': 30
    },
    'preauthorized': {
        'emails': ['admin@example.com']
    }
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    authenticator.logout('Logout', 'sidebar')
    role = config['credentials']['usernames'][username]['role']
    st.sidebar.title(f"Welcome {name} ({role.capitalize()})")
    
    # --- Load Data ---
    @st.cache_data
    def load_data():
        sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            df = pd.read_csv(sheet_url)
            required_cols = [
                'Compliance Name', 'Domain', 'Applies To', 'Checklist 1', 
                'Checklist 2', 'Checklist 3', 'Followed By Compunnel', 
                'Why Required', 'Priority', 'Trigger Alert', 'RSS Feed'
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

    # --- Project Input ---
    project_description = st.text_area(
        "Describe your project (include data types and regions):",
        height=150,
        placeholder="e.g., 'Healthcare app storing patient records in India with EU users...'"
    )

    # --- NEW FEATURE 2: Interactive Checklist ---
    def interactive_checklist(compliance_items):
        checklist_status = {}
        for item in compliance_items:
            with st.expander(f"{'✅' if item['followed'] else '❌'} {item['name']}"):
                status = st.radio(
                    f"Status for {item['name']}",
                    ['Not Started', 'In Progress', 'Completed'],
                    key=f"status_{item['name']}"
                )
                if status == 'Completed':
                    st.date_input("Completion Date", key=f"date_{item['name']}")
                    st.text_area("Notes", key=f"notes_{item['name']}")
                checklist_status[item['name']] = status
        return checklist_status

    # --- NEW FEATURE 3: Timeline Visualization ---
    def show_timeline(compliance_data):
        deadlines = {
            'High': [item for item in compliance_data if item['priority'] == 'High'],
            'Standard': [item for item in compliance_data if item['priority'] == 'Standard']
        }
        
        fig, ax = plt.subplots(figsize=(10, 4))
        for i, (priority, items) in enumerate(deadlines.items()):
            dates = [datetime.now().date() for _ in items]
            ax.scatter(dates, [i]*len(items), label=f"{priority} Priority")
        
        ax.set_yticks([0, 1])
        ax.set_yticklabels(['High', 'Standard'])
        ax.set_title("Compliance Deadline Timeline")
        ax.legend()
        st.pyplot(fig)

    # --- NEW FEATURE 4: Regulatory Updates ---
    def get_regulatory_updates(df):
        updates = []
        for _, row in df.dropna(subset=['RSS Feed']).iterrows():
            try:
                feed = feedparser.parse(row['RSS Feed'])
                updates.extend([(row['Compliance Name'], entry.title, entry.link) 
                             for entry in feed.entries[:2]])
            except Exception as e:
                st.error(f"Failed to parse RSS feed: {str(e)}")
                continue
        return updates

    # --- NEW FEATURE 5: Chatbot Assistant ---
    @st.cache_resource
    def load_chatbot():
        return pipeline('text-generation', model='gpt2')

    def compliance_chatbot(question, compliance_data):
        chatbot = load_chatbot()
        context = "Compliance regulations: " + str(compliance_data[:500])  # Limit context
        prompt = f"Context: {context}\nQuestion: {question}\nAnswer:"
        return chatbot(prompt, max_length=150)[0]['generated_text']

    # --- Main Analysis ---
    if st.button("🔍 Analyze Compliance", type="primary"):
        if not project_description.strip():
            st.warning("Please enter a project description")
            st.stop()
        
        with st.spinner("Analyzing requirements..."):
            results = analyze_project(project_description)
            st.session_state.results = results
            st.success("Analysis complete!")
            
            # Display new features
            st.markdown("### 📅 Compliance Timeline")
            show_timeline(results['compliance_matches'])
            
            st.markdown("### 📝 Interactive Checklist")
            checklist_status = interactive_checklist(results['compliance_matches'])
            
            with st.sidebar.expander("💡 Compliance Assistant"):
                question = st.text_input("Ask about compliance")
                if question:
                    response = compliance_chatbot(question, results['compliance_matches'])
                    st.write(response.split("Answer:")[-1])
            
            with st.sidebar.expander("📰 Regulatory Updates"):
                for source, title, link in get_regulatory_updates(compliance_df):
                    st.markdown(f"**{source}**: [{title}]({link})")

    # --- Report Generation (Enhanced) ---
    if st.session_state.get('results'):
        st.markdown("---")
        st.markdown("## 📤 Generate Reports")
        
        format_choice = st.radio(
            "Select report type:",
            ["PDF Report", "Action Plan (CSV)", "Markdown", "HTML"],
            horizontal=True
        )
        
        if format_choice == "Markdown":
            markdown_report = generate_markdown(st.session_state.results)
            st.download_button(
                "⬇️ Download Markdown",
                markdown_report,
                "compliance_report.md",
                "text/markdown"
            )
        
        # --- NEW FEATURE 6: Policy Templates ---
        if role == 'admin':
            with st.expander("🛠️ Policy Templates"):
                selected_compliance = st.selectbox(
                    "Select compliance for template",
                    compliance_df['Compliance Name'].unique()
                )
                if st.button("Generate Template"):
                    template = generate_policy_template(selected_compliance)
                    st.code(template)

    # --- NEW FEATURE 7: Audit Logging ---
    def log_action(username, action):
        try:
            with open("audit_log.json", "a") as f:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'user': username,
                    'action': action
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            st.error(f"Failed to log action: {str(e)}")

    # Example logging
    log_action(username, "Accessed dashboard")

elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')
