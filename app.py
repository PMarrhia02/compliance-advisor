import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

# Initialize session state
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
    st.session_state.results = None

# Page setup
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# Custom CSS
st.markdown("""
    <style>
        .title { font-size: 2.5em; color: #003366; font-weight: bold; }
        .badge { display: inline-block; padding: 0.25em 0.6em; font-size: 90%; font-weight: 600; border-radius: 0.25rem; }
        .badge-green { background-color: #d4edda; color: #155724; }
        .badge-red { background-color: #f8d7da; color: #721c24; }
        .badge-blue { background-color: #d1ecf1; color: #0c5460; }
        .priority-high { border-left: 4px solid #dc3545; padding-left: 10px; }
        .priority-standard { border-left: 4px solid #fd7e14; padding-left: 10px; }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)

# Load data with caching
@st.cache_data
def load_data():
    sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    return pd.read_csv(sheet_url)

compliance_df = load_data()

# Matching dictionaries
DOMAINS = {
    "healthcare": ["healthcare", "hospital", "patient", "medical"],
    "finance": ["bank", "finance", "payment", "transaction"],
    "ai solutions": ["ai", "machine learning", "llm"],
    "all": []
}

DATA_TYPES = {
    "PHI": ["phi", "health data", "medical record"],
    "PII": ["pii", "personal data", "name", "email"],
    "financial": ["financial", "credit card", "bank account"]
}

REGIONS = {
    "India": ["india", "indian"],
    "USA": ["usa", "united states"],
    "EU": ["eu", "europe"],
    "Canada": ["canada"],
    "Brazil": ["brazil"],
    "global": ["global", "international"]
}

def match_category(text, categories):
    text = text.lower()
    scores = {k: sum(term in text for term in v) for k, v in categories.items()}
    best_match = max(scores, key=scores.get)
    return best_match if scores[best_match] > 0 else "all"

def analyze_project(description):
    # Reset matches for fresh analysis
    compliance_matches = []
    text = description.lower()
    
    for _, row in compliance_df.iterrows():
        applies_to = [x.strip().lower() for x in str(row['Applies To']).split(",")]
        followed = str(row['Followed By Compunnel']).strip().lower() == "yes"
        
        compliance_matches.append({
            "name": row['Compliance Name'],
            "domain": str(row['Domain']).lower(),
            "applies_to": applies_to,
            "followed": followed,
            "priority": "High" if str(row.get('Priority', '')).strip().lower() == "high" else "Standard",
            "checklist": [
                str(item) for item in [
                    row['Checklist 1'], 
                    row['Checklist 2'], 
                    row['Checklist 3']
                ] if pd.notna(item)
            ],
            "why": row.get("Why Required", "")
        })
    
    matched_domain = match_category(text, DOMAINS)
    matched_data_type = match_category(text, DATA_TYPES)
    matched_region = match_category(text, REGIONS)
    
    # Filter matches based on project description
    filtered_matches = [
        m for m in compliance_matches
        if (matched_domain == m['domain'] or m['domain'] == "all")
        and any(
            term in applies_to 
            for term in [matched_data_type, matched_region, "all"]
            for applies_to in m['applies_to']
        )
    ]
    
    return {
        "domain": matched_domain,
        "data_type": matched_data_type,
        "region": matched_region,
        "compliance_matches": filtered_matches
    }

# Input
project_description = st.text_area(
    "Describe your project (include data types and regions):",
    height=150,
    key="project_input"  # Ensures fresh state
)

# Analysis trigger
if st.button("🔍 Analyze Compliance", type="primary"):
    if not project_description.strip():
        st.warning("Please enter a project description")
    else:
        with st.spinner("Analyzing..."):
            st.session_state.results = analyze_project(project_description)
            st.session_state.analysis_done = True
            st.success("Analysis complete!")

# Display results
if st.session_state.analysis_done:
    results = st.session_state.results
    met = [m for m in results['compliance_matches'] if m['followed']]
    pending = [m for m in results['compliance_matches'] if not m['followed']]
    score = int((len(met) / len(results['compliance_matches']) * 100) if results['compliance_matches'] else 0
    
    # Dashboard
    cols = st.columns(3)
    with cols[0]:
        st.metric("Compliance Score", f"{score}%")
    with cols[1]:
        st.metric("Pending Items", len(pending))
    with cols[2]:
        high_pri = len([p for p in pending if p['priority'] == "High"])
        st.metric("High Priority", high_pri)
    
    # Priority Matrix
    st.markdown("### 🚨 Priority Matrix")
    for priority, items in [("High", [p for p in pending if p['priority'] == "High"]),
                          ("Standard", [p for p in pending if p['priority'] == "Standard"])]:
        if items:
            st.markdown(f"#### {'🔴' if priority == 'High' else '🟠'} {priority} Priority")
            for item in items:
                st.markdown(f"""
                <div class='priority-{priority.lower()}'>
                    <strong>{item['name']}</strong><br/>
                    {item['why']}<br/>
                    <em>Checklist: {", ".join(item['checklist'])}</em>
                </div>
                """, unsafe_allow_html=True)

    # Debug view (optional)
    with st.expander("Debug Details"):
        st.json({
            "input": project_description,
            "matched_domain": results['domain'],
            "matched_data_type": results['data_type'],
            "matched_region": results['region'],
            "total_matches": len(results['compliance_matches'])
        })

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>© 2024 Compliance Advisor Pro</div>", 
            unsafe_allow_html=True)
