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

# Initialize Billing Logic
billing = BillingSystem()
status = billing.user_data

# 2. Sidebar - Revenue & Subscription Management
st.sidebar.title("🎯 TOPSPOT COMMAND")
st.sidebar.markdown("---")

if status["is_pro"]:
    st.sidebar.success("⭐ PRO LICENSE: ACTIVE")
    st.sidebar.info(f"Verified ID: {status.get('trans_id', 'VERIFIED')}")
else:
    st.sidebar.subheader("💎 UPGRADE TO PRO")
    
    # Tiered Pricing Options
    promo = st.sidebar.radio("Select Plan", ["Basic Audit (KES 99)", "Triple Threat (KES 250)", "Full Agency PDF (KES 499)"])
    
    # Automated M-Pesa STK Push Section (Direct Daraja Integration)
    st.sidebar.markdown("---")
    st.sidebar.write("**⚡ Instant Activation (STK Push)**")
    phone = st.sidebar.text_input("Enter M-Pesa Number", placeholder="07XXXXXXXX or 254XXXXXXXX")
    
    # Map selection to price
    amount = 99 if "99" in promo else 250 if "250" in promo else 499

    if st.sidebar.button(f"Pay KES {amount} via M-Pesa"):
        if phone:
            with st.sidebar.spinner("Requesting M-Pesa PIN prompt..."):
                response = billing.trigger_stk_push(phone, amount)
                if response.get("ResponseCode") == "0":
                    st.sidebar.success("✅ Prompt Sent! Enter PIN on your phone.")
                    st.sidebar.caption("Once paid, enter the M-Pesa ID below.")
                else:
                    st.sidebar.error("❌ M-Pesa Error. Check number and try again.")
        else:
            st.sidebar.warning("Please enter your phone number.")

    st.sidebar.markdown("---")
    st.sidebar.write("**Manual Verification**")
    tid = st.sidebar.text_input("M-Pesa Transaction ID", placeholder="e.g. RCKL57H8S9").strip().upper()
    
    if st.sidebar.button("Verify & Activate"):
        if billing.unlock_pro(tid):
            st.balloons()
            st.success("Pro Activated! Refreshing...")
            time.sleep(1.5)
            st.rerun()
        else:
            st.error("Invalid Transaction ID.")

# 3. Main Hero Section
st.title("🎯 TOPSPOT: AI Search Command Center")
st.write("### Audit visibility for Google Gemini, Perplexity, and ChatGPT.")

# 4. Audit Logic
url = st.text_input("🎯 Enter Target Website URL", placeholder="https://www.yourdomain.com")

if st.button("🚀 INITIATE AI SCAN"):
    if url:
        if not url.startswith("http"):
            url = "https://" + url
            
        with st.status("🔍 Analyzing AI Visibility...", expanded=True) as s:
            try:
                run_audit(url)
                if os.path.exists("last_fix.json"):
                    billing.increment_trial()
                    s.update(label="Audit Complete!", state="complete")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Engine Error: Data not saved.")
            except Exception as e:
                st.error(f"💥 System Error: {str(e)}")

# --- RESULTS DISPLAY SECTION ---
if os.path.exists("last_fix.json"):
    with open("last_fix.json", "r") as f:
        data = json.load(f)
    
    basic = data.get('basic_metrics', {})
    pro = data.get('pro_features', {})
    meta = data.get('metadata', {})

    display_name = meta.get('title', url) if meta.get('title') != "Unknown" else url
    st.markdown(f"## 📊 Results for: {display_name}")
    
    c1, c2, c3 = st.columns(3)
    my_score = basic.get('aeo_score', 0)
    c1.metric("TOPSPOT AEO Score", f"{my_score}/100")
    c2.metric("Trust Signals", basic.get('trust_signals', 'Analyzing'))
    c3.metric("LLM Status", "Indexed")

    # --- THE TRIPLE THREAT / COMPETITOR BATTLE ---
    st.markdown("---")
    st.markdown("### ⚔️ Competitor Battle")
    
    col_a, col_b, col_c = st.columns(3)
    comp1 = col_a.text_input("Competitor 1", placeholder="rival1.com")
    comp2 = col_b.text_input("Competitor 2", placeholder="rival2.com")
    comp3 = col_c.text_input("Competitor 3", placeholder="rival3.com")

    if st.button("Run Triple Threat Comparison"):
        if billing.can_access_premium():
            with st.status("⚔️ Battle in progress...", expanded=False) as s:
                # Consume free token if not Pro
                if not status["is_pro"]:
                    billing.use_free_token()
                    st.toast("🎁 Free Premium Token Used!", icon="✨")

                # 1. Audit the rivals for real (Calling your main audit function)
                score1 = run_audit(comp1, return_score=True) if comp1 else 0
                score2 = run_audit(comp2, return_score=True) if comp2 else 0
                score3 = run_audit(comp3, return_score=True) if comp3 else 0
                
                # 2. Build the REAL dataframe
                chart_data = pd.DataFrame({
                    "Entity": ["You", (comp1[:12] if comp1 else "Comp 1"), 
                               (comp2[:12] if comp2 else "Comp 2"), 
                               (comp3[:12] if comp3 else "Comp 3")],
                    "AEO Score": [my_score, score1, score2, score3]
                })
                
                st.bar_chart(chart_data, x="Entity", y="AEO Score", color=["#1F6feb"])
                s.update(label="Battle Complete!", state="complete")
        else:
            st.warning("🔒 Free token used. Upgrade to Pro (KES 250) to continue comparing competitors.")

    # --- SNIPPET SECTION (GATED) ---
    st.markdown("---")
    st.subheader("✨ AI-Ready Snippet Recommendation")
    if billing.can_access_premium():
        st.info(pro.get("suggested_snippet", "Generating snippet content..."))
    else:
        st.info("⚠️ [LOCKED] Upgrade to Pro (KES 99) to view the high-authority snippet recommended for LLMs.")

    # --- THE PAYWALL / PRO TOOLS ---
    st.markdown("---")
    if billing.can_access_premium():
        st.subheader("🛠️ Pro Implementation (JSON-LD)")
        st.code(json.dumps(pro.get("recommended_schema", {}), indent=2), language="json")
        
        if st.button("Generate Branded PDF Report"):
            if status["is_pro"]:
                st.write("Generating Professional Report...")
                st.success("Report Ready for Download")
            else:
                st.warning("🔒 Full PDF Agency reports require a Pro License.")
    else:
        st.warning("⚠️ **PRO CONTENT LOCKED**")
        st.write("Unlock the Full Schema, Snippets, and Professional PDF Reports starting at KES 99.")
        if st.button("Unlock All Pro Features Now"):
            st.session_state['expand_sidebar'] = True
            st.rerun()

# --- SYSTEM DEBUG FOOTER ---
with st.expander("📂 System Diagnostics (Developer Only)"):
    st.write(f"Working Directory: `{os.getcwd()}`")
    st.write(f"Files in root: `{os.listdir('.')}`")
    st.write(f"Session Status: `{status}`")

# --- CLIENT AUDIT HISTORY ---
st.markdown("---")
st.subheader("📜 Recent Audit History")

if os.path.exists("audit_history.json"):
    with open("audit_history.json", "r") as f:
        try:
            history_data = json.load(f)
            # Convert to a clean table for the client
            history_list = []
            for entry in reversed(history_data): # Show newest first
                history_list.append({
                    "Date": entry['metadata']['timestamp'],
                    "Website": entry['metadata']['url'],
                    "AEO Score": f"{entry['basic_metrics']['aeo_score']}/100",
                    "Trust": entry['basic_metrics']['trust_signals']
                })
            
            st.table(pd.DataFrame(history_list).head(10)) # Show last 10
        except Exception as e:
            st.error("Error loading audit history.")
else:
    st.info("No history found. Complete your first scan to start the log.")

st.markdown("---")
st.caption("TOPSPOT AI © 2026 | Developed for Premium Kenyan Enterprises")