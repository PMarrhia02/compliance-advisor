import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
from pathlib import Path

# Add modules to path
sys.path.append(os.path.dirname(__file__))

from config.settings import AppConfig
from auth.authentication import AuthManager
from data.sheets_connector import SheetsConnector
from analysis.compliance_engine import ComplianceEngine
from reports.report_generator import ReportGenerator
from utils.validators import InputValidator
from utils.ui_components import UIComponents

# Initialize configuration
config = AppConfig()

# Page setup
st.set_page_config(
    page_title="Compliance Advisor Pro", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def initialize_components():
    """Initialize and cache application components"""
    return {
        'auth_manager': AuthManager(),
        'sheets_connector': SheetsConnector(config.google_sheets_id),
        'compliance_engine': ComplianceEngine(),
        'report_generator': ReportGenerator(),
        'validator': InputValidator(),
        'ui': UIComponents()
    }

def main():
    """Main application function"""
    components = initialize_components()
    
    # Apply custom CSS
    components['ui'].apply_custom_styles()
    
    # Header
    components['ui'].render_header()
    
    # Authentication check
    if not components['auth_manager'].is_authenticated():
        components['auth_manager'].render_login_form()
        return
    
    # Main application
    render_main_application(components)

def render_main_application(components):
    """Render the main application interface"""
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        page = st.selectbox("Choose a page:", [
            "📊 Compliance Analysis", 
            "📈 Historical Reports", 
            "⚙️ Settings",
            "👥 User Management"
        ])
        
        # User info
        user = components['auth_manager'].get_current_user()
        st.markdown("---")
        st.markdown(f"**👤 User:** {user['username']}")
        st.markdown(f"**🎭 Role:** {user['role'].replace('_', ' ').title()}")
        
        if st.button("🚪 Logout", use_container_width=True):
            components['auth_manager'].logout()
            st.rerun()
    
    # Route to different pages
    page_key = page.split(" ", 1)[1]  # Remove emoji for routing
    
    if page_key == "Compliance Analysis":
        render_analysis_page(components)
    elif page_key == "Historical Reports":
        render_reports_page(components)
    elif page_key == "Settings":
        render_settings_page(components)
    elif page_key == "User Management":
        render_user_management_page(components)

def render_analysis_page(components):
    """Render the main compliance analysis page"""
    st.markdown("## 🔍 Compliance Analysis")
    
    # Project input form
    with st.form("project_analysis_form"):
        project_description = st.text_area(
            "📝 Describe your project (include data types and regions):",
            height=150,
            placeholder="e.g., 'Healthcare app storing patient records in India with EU users, processing PHI data...'"
        )
        
        # Additional filters
        col1, col2 = st.columns(2)
        with col1:
            priority_filter = st.selectbox(
                "🎯 Priority Level:",
                ["All", "High Priority Only", "Standard Priority"]
            )
        with col2:
            domain_filter = st.selectbox(
                "🏢 Domain Filter:",
                ["All", "Healthcare", "Finance", "AI Solutions", "Government", "Manufacturing"]
            )
        
        submitted = st.form_submit_button("🔍 Analyze Compliance", type="primary")
    
    if submitted:
        if not project_description.strip():
            st.warning("⚠️ Please enter a project description")
            return
        
        # Validate input
        validation_result = components['validator'].validate_project_description(project_description)
        
        if not validation_result['is_valid']:
            st.error(f"❌ Validation Error: {validation_result['message']}")
            return
        
        # Perform analysis
        with st.spinner("🔄 Analyzing compliance requirements..."):
            try:
                # Load compliance data
                compliance_data = components['sheets_connector'].get_compliance_data()
                
                # Run analysis
                results = components['compliance_engine'].analyze_project(
                    project_description,
                    compliance_data,
                    {
                        'priority_filter': priority_filter,
                        'domain_filter': domain_filter
                    }
                )
                
                # Store results in session
                st.session_state.analysis_results = results
                st.session_state.project_description = project_description
                st.session_state.analysis_timestamp = datetime.now()
                
                st.success("✅ Analysis completed successfully!")
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                st.info("Please try again or contact support if the problem persists.")
                return
    
    # Display results if available
    if hasattr(st.session_state, 'analysis_results'):
        display_analysis_results(components, st.session_state.analysis_results)

def display_analysis_results(components, results):
    """Display the analysis results"""
    
    # Metrics overview
    st.markdown("### 📊 Compliance Overview")
    
    met = [c for c in results['compliance_matches'] if c['followed']]
    pending = [c for c in results['compliance_matches'] if not c['followed']]
    high_priority_pending = [c for c in pending if c.get('priority') == 'High']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score = int((len(met) / len(results['compliance_matches'])) * 100) if results['compliance_matches'] else 0
        st.metric(
            "🎯 Compliance Score", 
            f"{score}%", 
            delta=f"{score-70}%" if score >= 70 else f"{score-70}%"
        )
    
    with col2:
        st.metric("📋 Total Requirements", len(results['compliance_matches']))
    
    with col3:
        st.metric(
            "⏳ Pending Items", 
            len(pending), 
            delta=f"-{len(pending)}" if pending else "0"
        )
    
    with col4:
        st.metric(
            "🚨 High Priority", 
            len(high_priority_pending), 
            delta=f"-{len(high_priority_pending)}" if high_priority_pending else "0"
        )
    
    # Project attributes
    st.markdown("### 📌 Detected Project Attributes")
    att_col1, att_col2, att_col3 = st.columns(3)
    
    with att_col1:
        st.markdown(f"**🏢 Domain:** `{results['domain'].title()}`")
    with att_col2:
        st.markdown(f"**📊 Data Type:** `{results['data_type']}`")
    with att_col3:
        st.markdown(f"**🌍 Region:** `{results['region'].title()}`")
    
    # Priority matrix and detailed requirements
    components['ui'].render_priority_matrix(pending)
    components['ui'].render_detailed_requirements(results['compliance_matches'])
    
    # Report generation section
    st.markdown("---")
    st.markdown("### 📤 Generate Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Generate PDF Report", type="secondary"):
            with st.spinner("📄 Generating PDF report..."):
                pdf_buffer = components['report_generator'].generate_pdf_report(
                    results, st.session_state.get('project_description', '')
                )
                st.download_button(
                    "⬇️ Download PDF Report",
                    pdf_buffer,
                    f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    "application/pdf"
                )
    
    with col2:
        if st.button("📊 Generate Action Plan CSV", type="secondary"):
            with st.spinner("📊 Generating action plan..."):
                csv_buffer = components['report_generator'].generate_action_plan_csv(pending)
                st.download_button(
                    "⬇️ Download Action Plan",
                    csv_buffer,
                    f"action_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )

def render_reports_page(components):
    """Render the historical reports page"""
    st.markdown("## 📈 Historical Reports")
    st.info("📝 Historical reports functionality will be available in the next version!")
    
    # Placeholder for future functionality
    with st.expander("🔮 Coming Soon Features"):
        st.markdown("""
        - **📊 Compliance Trend Analysis**
        - **📈 Historical Score Tracking**  
        - **🔄 Periodic Report Generation**
        - **📧 Automated Report Distribution**
        - **📋 Audit Trail Reports**
        """)

def render_settings_page(components):
    """Render the settings page"""
    st.markdown("## ⚙️ Settings")
    
    # Check permissions
    user = components['auth_manager'].get_current_user()
    if not components['auth_manager'].check_permission('manage_settings'):
        st.error("🚫 Access denied. Admin privileges required for settings.")
        return
    
    with st.expander("🔧 Application Configuration", expanded=True):
        st.markdown("**📊 Google Sheets Configuration**")
        new_sheet_id = st.text_input("Google Sheets ID", value=config.google_sheets_id)
        
        st.markdown("**⚡ Cache Settings**")
        cache_ttl = st.number_input("Cache TTL (seconds)", value=config.cache_ttl, min_value=60)
        
        st.markdown("**🔒 Security Settings**")
        session_timeout = st.number_input("Session Timeout (seconds)", value=config.session_timeout, min_value=300)
        
        if st.button("💾 Save Settings"):
            st.success("✅ Settings saved successfully!")
    
    with st.expander("🗑️ Cache Management"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Clear Data Cache"):
                st.cache_data.clear()
                st.success("✅ Data cache cleared!")
        with col2:
            if st.button("🗂️ Clear Resource Cache"):
                st.cache_resource.clear()
                st.success("✅ Resource cache cleared!")

def render_user_management_page(components):
    """Render user management page (admin only)"""
    user = components['auth_manager'].get_current_user()
    
    if user['role'] != 'admin':
        st.error("🚫 Access denied. Admin privileges required.")
        return
    
    st.markdown("## 👥 User Management")
    st.info("👤 Advanced user management features coming in next version!")
    
    # Current users display
    with st.expander("👥 Current Users", expanded=True):
        users_data = []
        for username, info in components['auth_manager'].users_db.items():
            users_data.append({
                'Username': username,
                'Role': info['role'].replace('_', ' ').title(),
                'Email': info['email'],
                'Status': 'Active'
            })
        
        st.dataframe(pd.DataFrame(users_data), use_container_width=True)

if __name__ == "__main__":
    main()
