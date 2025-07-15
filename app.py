import streamlit as st

# Streamlit app title
st.title("🔐 AI-Powered Compliance Advisor for Compunnel")
st.write("Enter your project brief below to get compliance recommendations based on domain, data, and geography.")

# Input text area
project_description = st.text_area("📄 Project Description", height=200)

# Run when button is clicked
if st.button("Analyze Project"):
    if project_description.strip() == "":
        st.warning("Please enter a project description.")
    else:
        text = project_description.lower()

        # RULE-BASED MATCHING
        domains = {
            "healthcare": ["healthcare", "hospital", "patient", "medical", "clinic"],
            "finance": ["bank", "finance", "credit card", "payment", "fintech"],
            "ecommerce": ["ecommerce", "shopping", "online store", "retail"],
        }

        data_types = {
            "PHI": ["health data", "patient", "medical record", "PHI"],
            "PII": ["personal data", "name", "address", "email", "phone"],
            "financial": ["credit card", "bank account", "payment", "transaction"],
        }

        regions = {
            "USA": ["united states", "us", "usa", "america"],
            "EU": ["europe", "germany", "france", "eu", "european union"],
            "India": ["india", "indian"],
        }

        def match_category(rules, text):
            for label, keywords in rules.items():
                for word in keywords:
                    if word in text:
                        return label
            return "Unknown"

        matched_domain = match_category(domains, text)
        matched_data_type = match_category(data_types, text)
        matched_region = match_category(regions, text)

        # COMPLIANCE MAPPING
        compliance_suggestions = []

        if matched_domain == "healthcare" and matched_data_type == "PHI":
            compliance_suggestions.append("HIPAA")

        if matched_data_type in ["PII", "PHI"]:
            if matched_region == "EU":
                compliance_suggestions.append("GDPR")
            elif matched_region == "India":
                compliance_suggestions.append("DPDP (India)")
            elif matched_region == "USA":
                compliance_suggestions.append("CCPA or State-level Privacy Laws")

        if matched_data_type == "financial":
            compliance_suggestions.append("PCI-DSS")

        compliance_suggestions.append("ISO 27001 (General Best Practices)")
        compliance_suggestions = list(set(compliance_suggestions))

        # CHECKLISTS
        checklists = {
            "HIPAA": [
                "✔️ Sign a Business Associate Agreement (BAA)",
                "✔️ Implement access control and audit logs",
                "✔️ Train employees on PHI handling",
                "✔️ Encrypt health data at rest and in transit"
            ],
            "GDPR": [
                "✔️ Appoint a Data Protection Officer (DPO)",
                "✔️ Provide right to access and erasure",
                "✔️ Obtain clear consent before data collection",
                "✔️ Report data breaches within 72 hours"
            ],
            "PCI-DSS": [
                "✔️ Use and maintain firewalls",
                "✔️ Encrypt transmission of cardholder data",
                "✔️ Maintain secure systems and applications",
                "✔️ Regularly test security systems"
            ],
            "ISO 27001 (General Best Practices)": [
                "✔️ Define an information security policy",
                "✔️ Conduct a risk assessment",
                "✔️ Apply access controls",
                "✔️ Monitor and review security controls regularly"
            ],
            "DPDP (India)": [
                "✔️ Classify personal data under new DPDP rules",
                "✔️ Ensure consent and purpose limitation",
                "✔️ Nominate a Data Fiduciary",
                "✔️ Enable grievance redressal mechanisms"
            ],
            "CCPA or State-level Privacy Laws": [
                "✔️ Provide opt-out for data selling",
                "✔️ Enable data access and deletion requests",
                "✔️ Update privacy policy to match CCPA",
                "✔️ Implement data inventory tracking"
            ]
        }

        # COMPUNNEL EXISTING COMPLIANCES — you can customize this list
        compunnel_compliances = ["ISO 27001 (General Best Practices)", "SOC 2", "CCPA or State-level Privacy Laws", "GDPR"]

        # COMPLIANCE GAP ANALYSIS
        already_available = [c for c in compliance_suggestions if c in compunnel_compliances]
        missing_compliances = [c for c in compliance_suggestions if c not in compunnel_compliances]

        # DISPLAY OUTPUT
        st.subheader("🔍 Detected Project Info")
        st.write(f"**Domain**: {matched_domain}")
        st.write(f"**Data Type**: {matched_data_type}")
        st.write(f"**Geography**: {matched_region}")

        st.subheader("✅ Required Compliance Frameworks for This Project")
        for c in compliance_suggestions:
            st.write(f"- {c}")

        st.subheader("🏢 Compunnel Compliance Coverage")

        st.markdown("✅ **Already Compliant With:**")
        if already_available:
            for comp in already_available:
                st.success(f"{comp}")
        else:
            st.warning("None matched yet.")

        st.markdown("❗ **Needs to be Implemented for this Project:**")
        if missing_compliances:
            for comp in missing_compliances:
                st.error(f"{comp}")
        else:
            st.info("All required compliances already exist.")

        st.subheader("📋 Detailed Checklist")
        for c in compliance_suggestions:
            st.markdown(f"**{c}**")
            for item in checklists.get(c, ["Checklist not available."]):
                st.write(f"  - {item}")
