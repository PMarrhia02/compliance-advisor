import streamlit as st
import pandas as pd
from io import BytesIO
import logging
from functools import lru_cache
from typing import Dict, List, Tuple, Optional
import gspread
from google.oauth2.service_account import Credentials
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page setup
st.set_page_config(
    page_title="Compliance Advisor Pro", 
    layout="wide",
    menu_items={
        'Get Help': 'https://compunnel.com/support',
        'Report a bug': "https://compunnel.com/bug",
        'About': "### AI-Powered Compliance Advisor\nVersion 2.0"
    }
)

# Style and header
st.markdown("""
    <style>
        .title {
            font-size: 2.5em;
            color: #003366;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .subtitle {
            font-size: 1.1em;
            color: #555555;
            margin-bottom: 2rem;
        }
        .badge {
            display: inline-block;
            padding: 0.35em 0.65em;
            font-size: 0.9em;
            font-weight: 600;
            line-height: 1;
            text-align: center;
            white-space: nowrap;
            vertical-align: baseline;
            border-radius: 0.25rem;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .badge-green {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .badge-red {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .badge-blue {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .badge-orange {
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeeba;
        }
        .footer {
            text-align: center;
            font-size: 0.9em;
            color: gray;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #eeeeee;
        }
        .stProgress > div > div > div > div {
            background-color: #003366;
        }
        .stTextArea > div > div > textarea {
            min-height: 180px;
        }
        .st-expander > div {
            border: 1px solid #e0e0e0 !important;
            border-radius: 8px !important;
        }
        .st-expander > div > div {
            background-color: #f9f9f9 !important;
        }
    </style>
""", unsafe_allow_html=True)

# App header
st.markdown("<div class='title'>🔐 Compunnel AI-Powered Compliance Advisor Pro</div>", unsafe_allow_html=True)
st.markdown("""
    <div class='subtitle'>
        Enter your project details to analyze required cybersecurity and data protection compliances, 
        with automated gap analysis and actionable recommendations.
    </div>
""", unsafe_allow_html=True)

# Sidebar with enhanced features
with st.sidebar:
    st.image("https://compunnel.com/assets/img/logo.svg", width=180)
    st.markdown("### 🧠 How It Works")
    st.info("""
        1. Describe your project (industry, data types, regions)
        2. Specify compliance priorities
        3. Get automated analysis with:
           - Required compliances
           - Gap analysis
           - Implementation roadmap
    """)
    
    st.markdown("### ⚙️ Settings")
    analysis_depth = st.selectbox(
        "Analysis Depth", 
        ["Basic", "Detailed", "Comprehensive"],
        help="Choose the level of detail for compliance analysis"
    )
    
    show_technical = st.checkbox(
        "Show Technical Details", 
        value=True,
        help="Display technical implementation requirements"
    )

# Load configuration and secrets
@st.cache_data
def get_config():
    return {
        "sheet_id": st.secrets.get("sheet_id", "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"),
        "default_domains": {
            "healthcare": ["healthcare", "hospital", "patient", "medical", "clinic", "pharma", "health"],
            "finance": ["bank", "finance", "credit card", "payment", "fintech", "investment", "insurance"],
            "ecommerce": ["ecommerce", "shopping", "online store", "retail", "marketplace"],
            "ai solutions": ["ai", "artificial intelligence", "machine learning", "llm", "model", "data science"],
            "education": ["education", "school", "university", "learning", "edtech"],
            "government": ["government", "public sector", "defense", "military"]
        },
        "default_data_types": {
            "PHI": ["health data", "phi", "patient", "medical record", "clinical", "diagnosis"],
            "PII": ["personal data", "name", "address", "email", "aadhar", "pii", "dob", "ssn"],
            "financial": ["financial", "credit card", "bank account", "transaction", "upi", "fintech"],
            "biometric": ["fingerprint", "face recognition", "iris scan", "biometric"],
            "children": ["child", "minor", "student", "under 18"]
        },
        "default_regions": {
            "India": ["india", "indian", "bharat"],
            "USA": ["usa", "united states", "america", "us"],
            "EU": ["europe", "eu", "gdpr", "germany", "france", "spain", "italy"],
            "Canada": ["canada", "pipeda"],
            "Brazil": ["brazil", "lgpd"],
            "APAC": ["asia", "singapore", "australia", "japan", "korea"]
        }
    }

# Load compliance data with caching and error handling
@st.cache_data(ttl=3600, show_spinner="Loading compliance database...")
def load_compliance_data():
    """Load compliance data from Google Sheets with proper authentication."""
    try:
        config = get_config()
        
        # Use service account credentials from secrets
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # Open the spreadsheet
        sheet = client.open_by_key(config["sheet_id"])
        worksheet = sheet.get_worksheet(0)
        
        # Get all records and convert to DataFrame
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        
        # Data validation
        required_columns = ['Compliance Name', 'Domain', 'Applies To', 'Followed By Compunnel']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Missing required columns in the spreadsheet")
            
        logger.info("Successfully loaded compliance data")
        return df
    
    except Exception as e:
        logger.error(f"Failed to load compliance data: {str(e)}")
        st.error(f"❌ Failed to load compliance database: {str(e)}")
        st.stop()

# Enhanced matching function with caching
@lru_cache(maxsize=1024)
def match_category(text: str, rules: Dict[str, List[str]]) -> str:
    """
    Match text against categories with weighted scoring.
    
    Args:
        text: Input text to analyze
        rules: Dictionary of categories and their keywords
        
    Returns:
        Best matching category or "Unknown"
    """
    text = text.lower()
    scores = {}
    
    for category, keywords in rules.items():
        score = 0
        for keyword in keywords:
            keyword = keyword.lower()
            if keyword in text:
                # Weight by term length (multi-word terms get higher scores)
                term_weight = 1 + (len(keyword.split()) * 0.3)
                # Position bonus (terms earlier in list are more important)
                position_bonus = 1 + (0.1 * (len(keywords) - keywords.index(keyword)) / len(keywords)
                score += term_weight * position_bonus
        
        if score > 0:
            scores[category] = score
    
    return max(scores.items(), key=lambda x: x[1])[0] if scores else "Unknown"
    """
    text = text.lower()
    scores = {}
    
    for category, keywords in rules.items():
        score = 0
        for keyword in keywords:
            keyword = keyword.lower()
            if keyword in text:
                # Weight by term length (multi-word terms get higher scores)
                term_weight = 1 + (len(keyword.split()) * 0.3)
                # Position bonus (terms earlier in list are more important)
                position_bonus = 1 + (0.1 * (len(keywords) - keywords.index(keyword)) / len(keywords)
                score += term_weight * position_bonus
        
        if score > 0:
            scores[category] = score
    
    return max(scores.items(), key=lambda x: x[1])[0] if scores else "Unknown"

# Generate PDF report with professional formatting
def generate_pdf_report(content: str, project_info: Dict) -> bytes:
    """
    Generate a professional PDF compliance report.
    
    Args:
        content: The compliance content to include
        project_info: Dictionary with project details
        
    Returns:
        Bytes of the PDF file
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=40, leftMargin=40,
                          topMargin=60, bottomMargin=60)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_LEFT, fontSize=12, leading=14))
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        spaceAfter=20,
        textColor=colors.HexColor('#003366')
    
    heading_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        spaceAfter=12,
        textColor=colors.HexColor('#555555'))
    
    normal_style = styles['Justify']
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['BodyText'],
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=8)
    
    # Build the story (content)
    story = []
    
    # Title
    story.append(Paragraph("Compliance Assessment Report", title_style))
    
    # Project info
    story.append(Paragraph("<b>Project Information</b>", heading_style))
    story.append(Paragraph(f"<b>Domain:</b> {project_info.get('domain', 'Not specified')}", normal_style))
    story.append(Paragraph(f"<b>Data Types:</b> {project_info.get('data_types', 'Not specified')}", normal_style))
    story.append(Paragraph(f"<b>Regions:</b> {project_info.get('regions', 'Not specified')}", normal_style))
    story.append(Spacer(1, 20))
    
    # Compliance content
    story.append(Paragraph("<b>Compliance Analysis</b>", heading_style))
    
    for line in content.split('\n'):
        if line.strip() == "":
            continue
        if line.endswith(':'):  # Section header
            story.append(Paragraph(f"<b>{line}</b>", heading_style))
        elif line.startswith('•'):  # Bullet point
            story.append(Paragraph(line, bullet_style))
        else:
            story.append(Paragraph(line, normal_style))
    
    # Footer
    story.append(Spacer(1, 40))
    story.append(Paragraph("<i>Generated by Compunnel Compliance Advisor Pro</i>", 
                         ParagraphStyle(name='Footer', fontSize=9, textColor=colors.gray)))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Main analysis function
def analyze_compliance(project_description: str, compliance_df: pd.DataFrame) -> Tuple[Dict, List[Dict]]:
    """
    Analyze project description against compliance requirements.
    
    Args:
        project_description: The project description text
        compliance_df: DataFrame with compliance data
        
    Returns:
        Tuple of (project_info, compliance_matches)
    """
    config = get_config()
    text = project_description.lower()
    
    # Match project characteristics
    matched_domain = match_category(text, config["default_domains"])
    matched_data_type = match_category(text, config["default_data_types"])
    matched_region = match_category(text, config["default_regions"])
    
    # Prepare project info
    project_info = {
        "domain": matched_domain,
        "data_type": matched_data_type,
        "region": matched_region,
        "text": project_description
    }
    
    # Match compliance requirements
    compliance_matches = []
    for _, row in compliance_df.iterrows():
        domain = str(row['Domain']).lower()
        applies_to = [x.strip().lower() for x in str(row.get('Applies To', '')).split(",")]
        followed = str(row.get('Followed By Compunnel', '')).strip().lower() == "yes"
        criticality = str(row.get('Criticality', 'Medium')).strip()
        
        # Get checklist items (handle missing columns)
        checklist = []
        for col in ['Technical Requirements', 'Process Requirements', 'Documentation Requirements']:
            if col in row and pd.notna(row[col]):
                checklist.append(row[col])
        
        # Matching logic
        domain_match = (matched_domain.lower() == domain or domain == "all")
        data_type_match = (matched_data_type.lower() in applies_to or "all" in applies_to)
        region_match = (matched_region.lower() in applies_to or "all" in applies_to)
        
        if domain_match and (data_type_match or region_match):
            compliance_matches.append({
                "name": row['Compliance Name'],
                "followed": followed,
                "criticality": criticality,
                "why": row.get("Why Required", ""),
                "implementation": row.get("Implementation Guidance", ""),
                "checklist": checklist,
                "references": [x.strip() for x in str(row.get('References', '')).split(";") if x.strip()]
            })
    
    return project_info, compliance_matches

# Main app logic
def main():
    # Load data
    with st.spinner("Loading compliance database..."):
        compliance_df = load_compliance_data()
    
    # Input section with enhanced features
    st.markdown("### 📄 Project Details", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("Project Name", help="Enter a name for your project")
    with col2:
        project_priority = st.selectbox(
            "Compliance Priority", 
            ["Standard", "Enhanced", "Strict"],
            help="Select how strict compliance requirements should be"
        )
    
    project_description = st.text_area(
        "Project Description", 
        height=200,
        help="Describe your project including data types, industry, and regions involved"
    )
    
    # Manual override options
    with st.expander("⚙️ Advanced Options"):
        col1, col2, col3 = st.columns(3)
        with col1:
            manual_domain = st.selectbox(
                "Override Domain", 
                ["Auto-detect"] + list(get_config()["default_domains"].keys()),
                index=0
            )
        with col2:
            manual_data_type = st.selectbox(
                "Override Data Type", 
                ["Auto-detect"] + list(get_config()["default_data_types"].keys()),
                index=0
            )
        with col3:
            manual_region = st.selectbox(
                "Override Region", 
                ["Auto-detect"] + list(get_config()["default_regions"].keys()),
                index=0
            )
    
    if st.button("🔍 Analyze Compliance", type="primary"):
        if not project_description.strip():
            st.warning("Please enter a project description")
            return
        
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Perform analysis
        status_text.text("Analyzing project details...")
        progress_bar.progress(20)
        
        project_info, compliance_matches = analyze_compliance(project_description, compliance_df)
        
        # Apply manual overrides if specified
        if manual_domain != "Auto-detect":
            project_info["domain"] = manual_domain
        if manual_data_type != "Auto-detect":
            project_info["data_type"] = manual_data_type
        if manual_region != "Auto-detect":
            project_info["region"] = manual_region
        
        status_text.text("Preparing results...")
        progress_bar.progress(60)
        
        # Display results
        st.success("Analysis complete!")
        progress_bar.progress(80)
        
        # Show project info
        st.markdown("### 🧠 Detected Project Characteristics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Domain**\n\n<span class='badge badge-blue'>{project_info['domain']}</span>", 
                       unsafe_allow_html=True)
        with col2:
            st.markdown(f"**Data Type**\n\n<span class='badge badge-blue'>{project_info['data_type']}</span>", 
                       unsafe_allow_html=True)
        with col3:
            st.markdown(f"**Region**\n\n<span class='badge badge-blue'>{project_info['region']}</span>", 
                       unsafe_allow_html=True)
        
        # Compliance summary
        st.markdown("### 📊 Compliance Summary")
        
        if not compliance_matches:
            st.warning("No compliance requirements matched your project criteria")
        else:
            # Categorize compliances
            already_compliant = [c for c in compliance_matches if c['followed']]
            not_compliant = [c for c in compliance_matches if not c['followed']]
            high_priority = [c for c in not_compliant if c['criticality'].lower() == 'high']
            medium_priority = [c for c in not_compliant if c['criticality'].lower() == 'medium']
            low_priority = [c for c in not_compliant if c['criticality'].lower() == 'low']
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Requirements", len(compliance_matches))
            col2.metric("Already Compliant", len(already_compliant), 
                       f"{len(already_compliant)/len(compliance_matches):.0%}")
            col3.metric("Gaps Identified", len(not_compliant), 
                       f"{len(not_compliant)/len(compliance_matches):.0%}")
            
            # Display compliant items
            if already_compliant:
                with st.expander(f"✅ Already Compliant ({len(already_compliant)})", expanded=True):
                    for comp in already_compliant:
                        st.markdown(f"#### 🛡️ {comp['name']}")
                        if comp['why']:
                            st.info(f"**Why required:** {comp['why']}")
                        if show_technical and comp['checklist']:
                            st.markdown("**Requirements met:**")
                            for item in comp['checklist']:
                                st.markdown(f"- {item}")
            
            # Display high priority gaps
            if high_priority:
                with st.expander(f"🚨 High Priority Gaps ({len(high_priority)})", expanded=True):
                    for comp in high_priority:
                        st.markdown(f"#### ❗ {comp['name']}")
                        if comp['why']:
                            st.error(f"**Why required:** {comp['why']}")
                        if show_technical and comp['implementation']:
                            st.markdown("**Implementation Guidance:**")
                            st.info(comp['implementation'])
                        if comp['checklist']:
                            st.markdown("**Requirements:**")
                            for item in comp['checklist']:
                                st.markdown(f"- {item}")
                        if comp['references']:
                            st.markdown("**References:**")
                            for ref in comp['references']:
                                st.markdown(f"- [{ref}]({ref})")
            
            # Display medium priority gaps
            if medium_priority:
                with st.expander(f"⚠️ Medium Priority Gaps ({len(medium_priority)})", expanded=False):
                    for comp in medium_priority:
                        st.markdown(f"#### 🔸 {comp['name']}")
                        if comp['why']:
                            st.warning(f"**Why required:** {comp['why']}")
                        if show_technical and comp['checklist']:
                            st.markdown("**Requirements:**")
                            for item in comp['checklist']:
                                st.markdown(f"- {item}")
            
            # Display low priority gaps
            if low_priority:
                with st.expander(f"ℹ️ Low Priority Gaps ({len(low_priority)})", expanded=False):
                    for comp in low_priority:
                        st.markdown(f"#### 🔹 {comp['name']")
                        if comp['why']:
                            st.info(f"**Why required:** {comp['why']}")
                        if show_technical and comp['checklist']:
                            st.markdown("**Requirements:**")
                            for item in comp['checklist']:
                                st.markdown(f"- {item}")
        
        # Generate report content
        report_content = f"Compliance Analysis Report\n{'='*30}\n\n"
        report_content += f"Project: {project_name or 'Unnamed Project'}\n"
        report_content += f"Domain: {project_info['domain']}\n"
        report_content += f"Data Type: {project_info['data_type']}\n"
        report_content += f"Region: {project_info['region']}\n"
        report_content += f"Priority Level: {project_priority}\n\n"
        
        report_content += "Summary:\n"
        report_content += f"- Total Requirements: {len(compliance_matches)}\n"
        report_content += f"- Already Compliant: {len(already_compliant)} ({len(already_compliant)/len(compliance_matches):.0%})\n"
        report_content += f"- Gaps Identified: {len(not_compliant)} ({len(not_compliant)/len(compliance_matches):.0%})\n\n"
        
        if already_compliant:
            report_content += "Already Compliant:\n"
            for comp in already_compliant:
                report_content += f"- {comp['name']}\n"
                if comp['why']:
                    report_content += f"  Reason: {comp['why']}\n"
                if comp['checklist']:
                    report_content += "  Requirements Met:\n"
                    for item in comp['checklist']:
                        report_content += f"    • {item}\n"
            report_content += "\n"
        
        if not_compliant:
            report_content += "Compliance Gaps:\n"
            for comp in not_compliant:
                report_content += f"- {comp['name']} ({comp['criticality']} priority)\n"
                if comp['why']:
                    report_content += f"  Reason: {comp['why']}\n"
                if comp['implementation']:
                    report_content += f"  Implementation: {comp['implementation']}\n"
                if comp['checklist']:
                    report_content += "  Requirements:\n"
                    for item in comp['checklist']:
                        report_content += f"    • {item}\n"
                if comp['references']:
                    report_content += "  References:\n"
                    for ref in comp['references']:
                        report_content += f"    • {ref}\n"
        
        # Download options
        st.markdown("### 📥 Download Report")
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📄 Download as Text",
                data=report_content,
                file_name="compliance_report.txt",
                mime="text/plain"
            )
        
        with col2:
            if st.button("🧾 Generate PDF Report"):
                with st.spinner("Generating professional PDF report..."):
                    pdf_data = generate_pdf_report(report_content, {
                        "domain": project_info['domain'],
                        "data_types": project_info['data_type'],
                        "regions": project_info['region'],
                        "priority": project_priority
                    })
                    
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_data,
                        file_name="compliance_report.pdf",
                        mime="application/pdf"
                    )
        
        progress_bar.progress(100)
        status_text.text("Analysis complete!")
        st.balloons()

# Footer
st.markdown("""
    <div class='footer'>
        <p>&copy; 2025 Compunnel Digital | Compliance Advisor Pro v2.0</p>
        <p>This tool provides general guidance only and does not constitute legal advice.</p>
    </div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
