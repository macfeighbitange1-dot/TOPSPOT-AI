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

# Optimized Billing Initialization
@st.cache_resource
def get_billing_system():
    return BillingSystem()

billing = get_billing_system()
status = billing.user_data

# Normalize status keys for stability
status.setdefault("is_pro", False)
status.setdefault("trials", 0)
status.setdefault("trans_id", None)
status.setdefault("free_token_used", False)

# Custom CSS for Dark Mode Command Center Aesthetic
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    section[data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3.5em; 
        background-color: #1F6feb; color: white; font-weight: bold; 
        border: none; transition: 0.3s; 
    }
    .stButton>button:hover { background-color: #388bfd; border: 1px solid #58a6ff; }
    div[data-testid="stMetricValue"] { color: #58a6ff; }
    .stMetric { 
        background-color: #161B22; padding: 20px; border-radius: 12px; 
        border: 1px solid #30363D; box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
    }
    .stTextInput>div>div>input { background-color: #0D1117; color: white; border: 1px solid #30363D; }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 2. Sidebar - Revenue & Subscription Management
st.sidebar.title("🎯 TOPSPOT COMMAND")
st.sidebar.markdown("---")

if status.get("is_pro"):
    st.sidebar.success("⭐ PRO LICENSE: ACTIVE")
    st.sidebar.info(f"Verified ID: {status.get('trans_id', 'VERIFIED')}")
else:
    st.sidebar.subheader("💎 UPGRADE TO PRO")
    promo = st.sidebar.radio(
        "Select Plan",
        ["Basic Audit (KES 99)", "Triple Threat (KES 250)", "Full Agency PDF (KES 499)"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.write("**⚡ Instant Activation (STK Push)**")
    phone = st.sidebar.text_input("Enter M-Pesa Number", placeholder="07XXXXXXXX or 254XXXXXXXX")
    
    amount = 99 if "99" in promo else 250 if "250" in promo else 499

    if st.sidebar.button(f"Pay KES {amount} via M-Pesa"):
        if phone:
            with st.sidebar.spinner("Requesting M-Pesa PIN prompt..."):
                response = billing.trigger_stk_push(phone, amount)
                if response and response.get("ResponseCode") == "0":
                    st.sidebar.success("✅ Prompt Sent! Enter PIN.")
                else:
                    st.sidebar.error("❌ M-Pesa Error. Try again.")
        else:
            st.sidebar.warning("Please enter your phone number.")

    st.sidebar.markdown("---")
    tid = st.sidebar.text_input("Manual M-Pesa ID Verification", placeholder="e.g. RCKL57H8S9").strip().upper()
    
    if st.sidebar.button("Verify & Activate"):
        if billing.unlock_pro(tid):
            st.balloons()
            st.success("Pro Activated! Refreshing...")
            time.sleep(1.5)
            st.rerun()
        else:
            st.error("Invalid Transaction ID.")

# Admin Access
st.sidebar.markdown("---")
if st.sidebar.button("🛡️ Admin Portal"):
    st.switch_page("admin.py")

# 3. Main Hero Section
st.title("🎯 TOPSPOT: AI Search Command Center")
st.write("### Audit visibility for Google Gemini, Perplexity, and ChatGPT.")

# 4. Audit Logic
url_input = st.text_input("🎯 Enter Target Website URL", placeholder="https://www.yourdomain.com").strip()

if st.button("🚀 INITIATE AI SCAN"):
    if url_input:
        target_url = url_input if url_input.startswith("http") else "https://" + url_input
        with st.status("🔍 Analyzing AI Visibility...", expanded=True) as s:
            try:
                # Clear old results to prevent ghost data
                if os.path.exists("last_fix.json"): os.remove("last_fix.json")
                
                # Run the actual main.py pipeline
                run_audit(target_url)
                
                if os.path.exists("last_fix.json"):
                    billing.increment_trial()
                    s.update(label="Audit Complete!", state="complete")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Engine Error: Data file not generated.")
            except Exception as e:
                st.error(f"💥 System Error: {str(e)}")

# --- RESULTS DISPLAY SECTION ---
if os.path.exists("last_fix.json"):
    with open("last_fix.json", "r") as f:
        data = json.load(f)
    
    basic = data.get('basic_metrics', {})
    pro = data.get('pro_features', {})
    meta = data.get('metadata', {})

    st.markdown(f"## 📊 Results for: {meta.get('title', url_input)}")
    
    c1, c2, c3 = st.columns(3)
    my_score = basic.get('aeo_score', 0)
    c1.metric("TOPSPOT AEO Score", f"{my_score}/100")
    c2.metric("Trust Signals", basic.get('trust_signals', 'Low'))
    c3.metric("LLM Status", "Indexed")

    st.markdown("---")
    
    # PDF Generator Button (Pro Only)
    if status.get("is_pro"):
        if st.button("📄 Generate & Download Branded PDF Report"):
            analyzer = AEOAnalyzer()
            pdf_path = analyzer.export_pdf(meta.get('url'), data)
            with open(pdf_path, "rb") as pdf_file:
                st.download_button("Click to Download Report", data=pdf_file, file_name=f"AEO_Report_{meta.get('title')}.pdf")

    st.markdown("### ⚔️ Competitor Battle")
    
    col_a, col_b, col_c = st.columns(3)
    comp1 = col_a.text_input("Competitor 1", placeholder="rival1.com", key="c1")
    comp2 = col_b.text_input("Competitor 2", placeholder="rival2.com", key="c2")
    comp3 = col_c.text_input("Competitor 3", placeholder="rival3.com", key="c3")

    if st.button("Run Triple Threat Comparison"):
        if billing.can_access_premium():
            with st.status("⚔️ Battle in progress...", expanded=False) as s:
                if not status.get("is_pro"):
                    billing.use_free_token()
                    st.toast("🎁 Free Premium Token Used!", icon="✨")

                # Safer score extraction
                score1 = run_audit(comp1, return_score=True) if comp1 else 0
                score2 = run_audit(comp2, return_score=True) if comp2 else 0
                score3 = run_audit(comp3, return_score=True) if comp3 else 0
                
                chart_data = pd.DataFrame({
                    "Entity": ["You", "Comp 1", "Comp 2", "Comp 3"],
                    "AEO Score": [my_score, score1, score2, score3]
                })
                st.bar_chart(chart_data, x="Entity", y="AEO Score")
                s.update(label="Battle Complete!", state="complete")
        else:
            st.warning("🔒 Upgrade to Pro to unlock unlimited competitor battles.")

    st.markdown("---")
    st.subheader("✨ AI-Ready Snippet Recommendation")
    if billing.can_access_premium():
        st.info(pro.get("suggested_snippet", "Snippet analysis complete."))
        st.subheader("🛠️ Pro Implementation (JSON-LD)")
        st.code(json.dumps(pro.get("recommended_schema", {}), indent=2), language="json")
    else:
        st.info("⚠️ [LOCKED] Upgrade to Pro (KES 99) to view AI snippets and JSON-LD schema.")

# --- HISTORY SECTION ---
st.markdown("---")
st.subheader("📜 Recent Audit History")
if os.path.exists("audit_history.json"):
    try:
        with open("audit_history.json", "r") as f:
            history_data = json.load(f)
            # Display last 5 in a clean table
            df_history = pd.DataFrame([
                {
                    "Timestamp": item['metadata']['timestamp'],
                    "Website": item['metadata']['url'],
                    "AEO Score": f"{item['basic_metrics']['aeo_score']}/100"
                } for item in reversed(history_data[-5:])
            ])
            st.table(df_history)
    except:
        st.write("History log is empty or corrupted.")

with st.expander("📂 System Diagnostics"):
    st.write(f"Session Status: `{status}`")
    st.write(f"Working Dir: `{os.getcwd()}`")

st.markdown("---")
st.caption("TOPSPOT AI © 2026 | Global AI Search Visibility Platform")