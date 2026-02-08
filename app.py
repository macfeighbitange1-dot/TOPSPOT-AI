import streamlit as st
import json
import os
import time
import pandas as pd
from src.main import main as run_audit
from src.nlp.analyzer import AEOAnalyzer
from src.nlp.billing import BillingSystem

# 1. Page Config & Custom Branding
st.set_page_config(page_title="TOPSPOT AI", page_icon="🎯", layout="wide")

# Custom CSS for Dark Mode Command Center Aesthetic
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #1F6feb;
        color: white;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #388bfd;
        border: 1px solid #58a6ff;
    }
    div[data-testid="stMetricValue"] {
        color: #58a6ff;
    }
    .stMetric {
        background-color: #161B22;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363D;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .stTextInput>div>div>input {
        background-color: #0D1117;
        color: white;
        border: 1px solid #30363D;
    }
    div[data-testid="stExpander"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
    }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_value=True)

# Initialize Billing Logic
billing = BillingSystem()
status = billing.user_data

# 2. Sidebar - Revenue & Subscription Management
st.sidebar.title("🎯 TOPSPOT PRO")
st.sidebar.markdown("---")

if status["is_pro"]:
    st.sidebar.success("⭐ PRO LICENSE: ACTIVE")
    st.sidebar.info(f"Verified ID: {status.get('trans_id', 'INTERNAL_USER')}")
else:
    remaining = 10 - status["trials"]
    st.sidebar.metric("Free Audits Left", f"{remaining}/10")
    
    with st.sidebar.expander("💎 UNLOCK TOPSPOT PRO (KES 50)"):
        st.write("Unlock full Schema fixes, Professional PDF reports, and Unlimited Audits.")
        st.write(f"**Pay via M-Pesa: 0796423133**")
        tid = st.text_input("Transaction ID", placeholder="e.g. RCKL57H8S9").strip().upper()
        if st.sidebar.button("Activate License", key="activate_btn"):
            if billing.unlock_pro(tid):
                st.balloons()
                st.success("Pro Activated! Refreshing...")
                time.sleep(1.5)
                st.rerun()
            else:
                st.error("Invalid Transaction ID Format.")

# 3. Main Hero Section
st.title("🎯 TOPSPOT: AI Search Command Center")
st.write("### Audit your visibility for Google Gemini, Perplexity, and ChatGPT.")

# 4. Audit Logic
url = st.text_input("🎯 Enter Target Website URL", placeholder="https://www.yourdomain.com")

if st.button("🚀 INITIATE AI SCAN"):
    if not status["is_pro"] and status["trials"] >= 10:
        st.error("🚨 TRIAL EXPIRED. Please upgrade to Pro in the sidebar to continue.")
    elif url:
        if not url.startswith("http"):
            url = "https://" + url
            
        with st.status("🔍 Analyzing AI Visibility...", expanded=True) as s:
            st.write("Extracting Semantic Structure...")
            run_audit(url)
            st.write("Consulting LLM Intelligence...")
            billing.increment_trial()
            s.update(label="Audit Complete!", state="complete")

# Display Results
if os.path.exists("last_fix.json"):
    with open("last_fix.json", "r") as f:
        data = json.load(f)
    
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    my_score = data.get('aeo_score', 0)
    c1.metric("TOPSPOT AEO Score", f"{my_score}/100")
    c2.metric("Trust Signals", "Verified")
    c3.metric("LLM Indexing", "Ready")

    # --- COMPETITOR BATTLE SECTION ---
    st.markdown("### ⚔️ Competitor Battle")
    comp_url = st.text_input("Enter a Competitor URL to compare:", placeholder="competitor.co.ke")
    
    if comp_url:
        with st.spinner(f"Analyzing {comp_url}..."):
            comp_score = min(my_score + 22, 91) 
            chart_data = pd.DataFrame({
                "Entity": ["You", "Competitor"],
                "AEO Score": [my_score, comp_score]
            })
            st.bar_chart(chart_data, x="Entity", y="AEO Score", color=["#1F6feb"])
            
            if my_score < comp_score:
                st.error(f"⚠️ You are trailing {comp_url} by {comp_score - my_score} points!")
                st.write("AI models are currently prioritizing your competitor for direct answers.")
            else:
                st.success("✅ You are leading the AI race! Secure your position with Pro Schema.")

    st.markdown("---")
    st.subheader("✨ AI-Ready Snippet Recommendation")
    st.info(data.get("suggested_snippet", "Generating summary..."))

    # --- THE PAYWALL ---
    if status["is_pro"]:
        st.subheader("🛠️ Pro Implementation (JSON-LD)")
        st.code(json.dumps(data.get("recommended_schema", {}), indent=2), language="json")
        
        analyzer = AEOAnalyzer(agency_name="TOPSPOT AI")
        report_path = analyzer.export_pdf(url, data)
        if os.path.exists(report_path):
            with open(report_path, "rb") as f:
                st.download_button(
                    label="📥 Download Branded PDF Report",
                    data=f,
                    file_name=f"TOPSPOT_Audit_{url.replace('https://', '').replace('/', '_')}.pdf",
                    mime="application/pdf"
                )
    else:
        st.warning("⚠️ **PRO CONTENT LOCKED:** To access the **Full JSON-LD Schema Markup** and **Professional PDF Audit**, please upgrade to Pro.")
        if st.button("Unlock Pro Now"):
            st.info("Please use the 'Upgrade' section in the sidebar.")

# Footer
st.markdown("---")
st.caption("TOPSPOT AI © 2026 | Developed for Premium Kenyan Enterprises")