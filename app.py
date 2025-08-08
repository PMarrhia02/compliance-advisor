import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import streamlit_authenticator as stauth

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None

# Analysis functions - MOVED TO THE TOP
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
    else:
        for category in categories:
            if category in ["all", "global"]:
                return category
        return list(categories.keys())[0]

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
        applies_match = (
            "all" in applies_to or 
            matched_region.lower() in applies_to or 
            matched_data_type.lower() in applies_to
        )
        
        if domain_match and applies_match:
            checklist = [str(item) for item in [
                row['Checklist 1'], row['Checklist 2'], row['Checklist 3']
            ] if pd.notna(item)]
            
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
    
    return {
        "domain": matched_domain,
        "data_type": matched_data_type,
        "region": matched_region,
        "compliance_matches": compliance_matches
    }

def generate_pdf_report(project_info, compliance_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("Compliance Assessment Report", styles['Title']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Project Details", styles['Heading2']))
    story.append(Paragraph(f"""
        <b>Domain:</b> {project_info['domain']}<br/>
        <b>Data Type:</b> {project_info['data_type']}<br/>
        <b>Region:</b> {project_info['region']}
    """, styles['BodyText']))
    story.append(Spacer(1, 24))
    
    met = [c for c in compliance_data if c['followed']]
    pending = [c for c in compliance_data if not c['followed']]
    
    story.append(Paragraph("Compliance Status", styles['Heading2']))
    status_table = Table([
        ["Total Requirements", len(compliance_data)],
        ["Compliant", f"{len(met)} ({len(met)/len(compliance_data):.0%})"],
        ["Pending", f"{len(pending)} ({len(pending)/len(compliance_data):.0%})"]
    ], colWidths=[2*inch, 1.5*inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    story.append(status_table)
    story.append(Spacer(1, 24))
    
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

# Page setup
st.set_page_config(page_title="Compliance Advisor Pro", layout="wide")

# Rest of your code continues below...
# [Keep all the remaining code the same, including the authentication, UI elements, etc.]
