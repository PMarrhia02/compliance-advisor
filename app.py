    # Show detailed checklist
    st.subheader("📋 Checklist for Each Compliance")
    for c in compliance_suggestions:
        st.markdown(f"### 🛡️ {c['name']}")

        # Checklist items
        checklist_items = [item for item in c["checklist"] if pd.notna(item) and item not in ["Yes", "No"]]
        if checklist_items:
            st.markdown("**Checklist Items:**")
            for item in checklist_items:
                st.write(f"- {item}")

        # Followed By Compunnel
        followed_status = "✅ Yes" if c["followed"] else "❌ No"
        st.markdown(f"**Followed By Compunnel**: {followed_status}")

        # Why Required
        if c["why"]:
            st.markdown(f"**Why Required**: {c['why']}")

        # Extra columns: Date Added and Trigger Alert (if present in DataFrame)
        if "Date Added" in compliance_df.columns:
            date_added = compliance_df[compliance_df["Compliance Name"] == c["name"]]["Date Added"].values[0]
            st.markdown(f"**Date Added**: {date_added}")

        if "Trigger Alert" in compliance_df.columns:
            trigger_alert = compliance_df[compliance_df["Compliance Name"] == c["name"]]["Trigger Alert"].values[0]
            st.markdown(f"**Trigger Alert**: {trigger_alert}")
