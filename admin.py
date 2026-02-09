import streamlit as st
import json
import os
import pandas as pd

def show_admin_dashboard():
    st.title("🛡️ TOPSPOT: Admin Command Center")
    
    # Simple Password Protection (Change 'admin123' to your secret)
    password = st.sidebar.text_input("Admin Key", type="password")
    if password != "admin123":
        st.warning("Please enter a valid Admin Key to view sensitive data.")
        return

    st.success("Access Granted. Monitoring Live Revenue & Traffic.")

    # 1. Financial Overview (M-Pesa Logs)
    st.subheader("💰 M-Pesa Transaction Logs")
    if os.path.exists("app_usage.json"):
        with open("app_usage.json", "r") as f:
            usage = json.load(f)
            st.write(f"**Current Pro Status:** {usage.get('is_pro')}")
            st.write(f"**Verified ID:** {usage.get('trans_id')}")

    # 2. Global Audit History (Client Tracking)
    st.subheader("📊 Global Audit Ledger")
    if os.path.exists("audit_history.json"):
        with open("audit_history.json", "r") as f:
            history = json.load(f)
            df = pd.json_normalize(history)
            # Simplify view for Admin
            admin_df = df[['metadata.timestamp', 'metadata.url', 'basic_metrics.aeo_score']]
            st.dataframe(admin_df, use_container_width=True)
    else:
        st.info("No audit history recorded yet.")

if __name__ == "__main__":
    show_admin_dashboard()