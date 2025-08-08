import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import streamlit_authenticator as stauth
import bcrypt

# Page setup
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None

# Custom CSS
st.markdown("""
    <style>
        .title { font-size: 2.5em; color: #003366; font-weight: bold; }
        .badge { display: inline-block; padding: 0.25em 0.6em; font-size: 90%; font-weight: 600; border-radius: 0.25rem; }
        .badge-green { background-color: #d4edda; color: #155724; }
        .badge-red { background-color: #f8d7da; color: #721c24; }
        .badge-blue { background-color: #d1ecf1; color: #0c5460; }
        .badge-gold { background-color: #fff3cd; color: #856404; }
        .priority-high { border-left: 4px solid #dc3545; padding-left: 10px; margin: 8px 0; }
        .priority-standard { border-left: 4px solid #fd7e14; padding-left: 10px; margin: 8px 0; }
        .dashboard-card { border-radius: 10px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .footer { text-align: center; font-size: 0.9em; color: gray; margin-top: 3rem; }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("<div class='title'>🔐 Compliance Advisor Pro</div>", unsafe_allow_html=True)
st.markdown("AI-powered compliance analysis for your exact requirements")

# User Authentication
# Define user credentials (hashed passwords)
names = ['Admin']
usernames = ['admin']

# Create a simple hash for the password (you should use a proper secret in production)
hashed_password = bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
passwords = [hashed_password]

# Create credentials dictionary for streamlit-authenticator
credentials = {
    'usernames': {
        'admin': {
            'name': 'Admin',
            'password': hashed_password
        }
    }
}

# Create an authenticator object
authenticator = stauth.Authenticate(
    credentials,
    'some_cookie_name',
    'some_signature_key',
    cookie_expiry_days=30
)

# Login
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
elif authentication_status:
    st.success(f'Welcome {name}')
    
    # Add logout button to sidebar
    authenticator.logout('Logout', 'sidebar')

    # Load data from Google Sheets
    @st.cache_data
    def load_data():
        sheet_id = "1kTLUwg_4-PDY-CsUvTpPv1RIJ59BztKI_qnVOLyF12I"
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            df = pd.read_csv(sheet_url)
            
            # Validate columns
            required_cols = [
                'Compliance Name', 'Domain', 'Applies To',
                'Checklist 1', 'Checklist 2', 'Checklist 3',
                'Followed By Compunnel', 'Why Required'
            ]
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                st.error(f"Missing required columns: {', '.join(missing_cols)}")
                st.error("Available columns: " + str(list(df.columns)))
                st.stop()
                
            return df
        except Exception as e:
            st.error(f"Failed to load data: {str(e)}")
            # Create a sample dataframe for testing
            sample_data = {
                'Compliance Name': ['GDPR', 'HIPAA', 'SOX'],
                'Domain': ['all', 'healthcare', 'finance'],
                'Applies To': ['EU', 'PHI', 'financial'],
                'Checklist 1': ['Data mapping', 'Risk assessment', 'Internal controls'],
                'Checklist 2': ['Privacy policy', 'Security measures', 'Financial reporting'],
                'Checklist 3': ['Consent management', 'Access controls', 'Audit trails'],
                'Followed By Compunnel': ['yes', 'no', 'yes'],
                'Why Required': ['EU data protection', 'Healthcare data security', 'Financial transparency']
            }
            st.warning("Using sample data for demonstration")
            return pd.DataFrame(sample_data)

    try:
        compliance_df = load_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

    # Project input
    project_description = st.text_area(
        "Describe your project (include data types and regions):",
        height=150,
        placeholder="e.g., 'Healthcare app storing patient records in India with EU users...'"
    )

    # Analysis functions
    def match_category(text, categories):
        if not text or pd.isna(text):
            return list(categories.keys())[0] if categories else "unknown"
            
        text = text.lower()
        scores = {k: 0 for k in categories}
        
        # Calculate scores based on keyword matches
        for category, keywords in categories.items():
            for term in keywords:
                # Assign higher weight to exact matches, lower for partial
                if term in text:
                    scores[category] += 2 if term == text.strip() else 1
        
        # Normalize scores by number of keywords to avoid bias toward categories with more keywords
        for category in scores:
            if categories[category]:  # Avoid division by zero
                scores[category] = scores[category] / len(categories[category]) if len(categories[category]) > 0 else 0
        
        # Find the category with the highest score
        max_score = max(scores.values()) if scores else 0
        if max_score > 0:
            return max(scores, key=scores.get)
        else:
            # Fallback: If no keywords match, use the first non-empty category or "all"/"global"
            for category in categories:
                if category in ["all", "global"]:
                    return category
            return list(categories.keys())[0] if categories else "unknown"

    def analyze_project(description):
        # Define matching categories
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
        
        # Match project to categories
        matched_domain = match_category(description, domains)
        matched_data_type = match_category(description, data_types)
        matched_region = match_category(description, regions)
        
        # Filter compliance items based on matched categories
        compliance_matches = []
        for _, row in compliance_df.iterrows():
            try:
                # Check if this compliance applies to our matched domain
                domain_str = str(row['Domain']) if pd.notna(row['Domain']) else ""
                row_domains = [x.strip().lower() for x in domain_str.split(",")]
                domain_match = "all" in row_domains or matched_domain.lower() in row_domains
                
                # Check if this compliance applies to our matched region/data type
                applies_to_str = str(row['Applies To']) if pd.notna(row['Applies To']) else ""
                applies_to = [x.strip().lower() for x in applies_to_str.split(",")]
                applies_match = (
                    "all" in applies_to or 
                    matched_region.lower() in applies_to or 
                    matched_data_type.lower() in applies_to
                )
                
                # Only include if matches domain AND applies_to criteria
                if domain_match and applies_match:
                    checklist = []
                    for col in ['Checklist 1', 'Checklist 2', 'Checklist 3']:
                        if col in row and pd.notna(row[col]):
                            checklist.append(str(row[col]))
                    
                    followed_val = str(row.get('Followed By Compunnel', 'no')).strip().lower()
                    followed = followed_val == "yes"
                    
                    compliance_matches.append({
                        "name": str(row.get('Compliance Name', 'Unknown')),
                        "domain": domain_str.lower(),
                        "applies_to": applies_to,
                        "followed": followed,
                        "priority": "High" if str(row.get('Priority', '')).strip().lower() == "high" else "Standard",
                        "alert": str(row.get('Trigger Alert', 'No')).strip().lower() == "yes",
                        "checklist": checklist,
                        "why": str(row.get("Why Required", ""))
                    })
            except Exception as e:
                st.error(f"Error processing row: {e}")
                continue
        
        return {
            "domain": matched_domain,
            "data_type": matched_data_type,
            "region": matched_region,
            "compliance_matches": compliance_matches
        }

    # Generate PDF Report
    def generate_pdf_report(project_info, compliance_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        story.append(Paragraph("Compliance Assessment Report", styles['Title']))
        story.append(Spacer(1, 12))
        
        # Project Info
        story.append(Paragraph("Project Details", styles['Heading2']))
        story.append(Paragraph(f"""
            <b>Domain:</b> {project_info['domain']}<br/>
            <b>Data Type:</b> {project_info['data_type']}<br/>
            <b>Region:</b> {project_info['region']}
        """, styles['BodyText']))
        story.append(Spacer(1, 24))
        
        # Compliance Status
        if compliance_data:
            met = [c for c in compliance_data if c['followed']]
            pending = [c for c in compliance_data if not c['followed']]
            
            story.append(Paragraph("Compliance Status", styles['Heading2']))
            status_table = Table([
                ["Total Requirements", len(compliance_data)],
                ["Compliant", f"{len(met)} ({len(met)/len(compliance_data)*100:.0f}%)"],
                ["Pending", f"{len(pending)} ({len(pending)/len(compliance_data)*100:.0f}%)"]
            ], colWidths=[2*inch, 1.5*inch])
            
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOX', (0,0), (-1,-1), 0.5, colors.grey)
            ]))
            story.append(status_table)
            story.append(Spacer(1, 24))
            
            # Detailed Requirements
            story.append(Paragraph("Detailed Requirements", styles['Heading2']))
            data = [["Requirement", "Status", "Checklist"]]
            for item in compliance_data:
                status = "Compliant" if item['followed'] else "Pending"
                color = colors.green if item['followed'] else colors.red
                checklist = "<br/>".join([f"• {point}" for point in item['checklist']])
                
                data.append([
                    Paragraph(item['name'], styles['BodyText']),
                    Paragraph(f"<font color='{color.hexval()}'>{status}</font>", styles['BodyText']),
                    Paragraph(checklist, styles['BodyText'])
                ])
            
            table = Table(data, colWidths=[2.5*inch, 1*inch, 2.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 10),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('VALIGN', (0,0), (-1,0), 'MIDDLE'),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
            ]))
            story.append(table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer

    # Main analysis
    if st.button("🔍 Analyze Compliance", type="primary"):
        if not project_description.strip():
            st.warning("Please enter a project description")
            st.stop()
        
        with st.spinner("Analyzing requirements..."):
            try:
                results = analyze_project(project_description)
                st.session_state.results = results
                st.success("Analysis complete!")
                
                if results['compliance_matches']:
                    # Show summary metrics
                    met = [c for c in results['compliance_matches'] if c['followed']]
                    pending = [c for c in results['compliance_matches'] if not c['followed']]
                    score = int((len(met) / len(results['compliance_matches'])) * 100)
                    
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
                        high_pri = len([c for c in pending if c['priority'] == "High"])
                        st.metric("High Priority Items", high_pri)
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Show matched categories
                    st.markdown("### 📌 Detected Project Attributes")
                    att_col1, att_col2, att_col3 = st.columns(3)
                    with att_col1:
                        st.markdown(f"**Domain:** <span class='badge badge-blue'>{results['domain'].title()}</span>", unsafe_allow_html=True)
                    with att_col2:
                        st.markdown(f"**Data Type:** <span class='badge badge-blue'>{results['data_type']}</span>", unsafe_allow_html=True)
                    with att_col3:
                        st.markdown(f"**Region:** <span class='badge badge-blue'>{results['region'].title()}</span>", unsafe_allow_html=True)
                    
                    # Priority Matrix
                    st.markdown("### 🚨 Priority Matrix")
                    high_priority = [c for c in pending if c['priority'] == "High"]
                    standard_priority = [c for c in pending if c['priority'] == "Standard"]
                    
                    if high_priority:
                        st.markdown("#### 🔴 High Priority (Urgent)")
                        for item in high_priority:
                            st.markdown(f"""
                            <div class='priority-high'>
                                <strong>{item['name']}</strong><br/>
                                {item['why']}<br/>
                                <em>Checklist: {", ".join(item['checklist'])}</em>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    if standard_priority:
                        st.markdown("#### 🟠 Standard Priority")
                        for item in standard_priority:
                            st.markdown(f"""
                            <div class='priority-standard'>
                                <strong>{item['name']}</strong><br/>
                                {item['why']}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Full Checklist
                    st.markdown("### 📋 Detailed Checklist")
                    for item in results['compliance_matches']:
                        with st.expander(f"{'✅' if item['followed'] else '❌'} {item['name']}"):
                            st.markdown(f"**Priority:** {item['priority']}")
                            if item['alert']:
                                st.warning("⚠️ Alert: This regulation has recent updates")
                            st.markdown("**Requirements:**")
                            for point in item['checklist']:
                                st.markdown(f"- {point}")
                            st.markdown(f"*{item['why']}*")
                else:
                    st.info("No matching compliance requirements found for your project description.")
                    
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")

    # Report generation
    if st.session_state.get('results') and st.session_state.results.get('compliance_matches'):
        st.markdown("---")
        st.markdown("## 📤 Generate Reports")
        
        format_choice = st.radio(
            "Select report type:",
            ["PDF Report", "Action Plan (CSV)"],
            horizontal=True
        )
        
        if format_choice == "PDF Report":
            try:
                pdf_buffer = generate_pdf_report(
                    {
                        "domain": st.session_state.results['domain'],
                        "data_type": st.session_state.results['data_type'],
                        "region": st.session_state.results['region']
                    },
                    st.session_state.results['compliance_matches']
                )
                st.download_button(
                    "⬇️ Download PDF Report",
                    pdf_buffer,
                    "compliance_report.pdf",
                    "application/pdf"
                )
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
        else:
            try:
                # Generate CSV action plan
                action_items = []
                for item in st.session_state.results['compliance_matches']:
                    if not item['followed']:
                        action_items.append({
                            "Requirement": item['name'],
                            "Priority": item['priority'],
                            "Deadline": "30 days" if item['priority'] == "High" else "90 days",
                            "Actions": "; ".join(item['checklist']),
                            "Owner": "[Assign Owner]",
                            "Status": "Not Started"
                        })
                
                if action_items:
                    df = pd.DataFrame(action_items)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "⬇️ Download Action Plan",
                        csv,
                        "compliance_action_plan.csv",
                        "text/csv"
                    )
                else:
                    st.info("No pending compliance items to include in action plan.")
            except Exception as e:
                st.error(f"Error generating CSV: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown("<div class='footer'>© 2025 Compliance Advisor Pro</div>", unsafe_allow_html=True)
