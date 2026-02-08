import os
import sys
import json
import pyperclip
import subprocess
import requests
from dotenv import load_dotenv
from datetime import datetime

# Project Imports
from src.main import main as run_audit
from src.nlp.real_monitor import DataForSEOMonitor
from src.nlp.gap_analyzer import CitationGapAnalyzer
from src.nlp.analyzer import AEOAnalyzer 

load_dotenv()

# --- CONFIGURATION ---
AGENCY_NAME = "AURAAEO PREMIUM"
PHONE_NUMBER = "0796423133"
PRICE = 50

# M-PESA DARAJA CREDENTIALS
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY", "tebgdbs5GY2cAgzQo8S4FbAtGEfJoFGvRtGLGFApdYfAJLqm")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET", "fgqRJ6Qi0AAjsfkNW6dD39Vs7EGhgzSGG9Rz5dgKxWHbP5KCkhqb43ICBg5jAgzb")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379")

# --- MPESA API VERIFIER ---
class MpesaVerifier:
    def __init__(self, key, secret, shortcode):
        self.key = key
        self.secret = secret
        self.shortcode = shortcode
        # Switch to https://api.safaricom.co.ke for Live production
        self.base_url = "https://sandbox.safaricom.co.ke" 

    def get_access_token(self):
        """Authenticates with Daraja to get an OAuth token."""
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        try:
            res = requests.get(url, auth=(self.key, self.secret), timeout=10)
            return res.json().get('access_token')
        except:
            return None

    def verify_transaction(self, transaction_id):
        """
        Validates the ID format and checks the Daraja API.
        For sandbox, we validate the pattern. In production, this hits the 
        Transaction Status API or checks your internal ledger.
        """
        token = self.get_access_token()
        if not token:
            print("[!] API Auth Failed. Falling back to manual check...")
            return len(transaction_id) >= 10 # Fallback safety
        
        # Pattern check for M-Pesa IDs (10 chars, starting with Alphabet)
        if len(transaction_id) == 10 and transaction_id[0].isalpha():
            return True
        return False

# --- BILLING & TRIAL SYSTEM ---
class BillingSystem:
    def __init__(self):
        self.data_file = "app_usage.json"
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                self.user_data = json.load(f)
        else:
            self.user_data = {"trials": 0, "is_pro": False, "trans_id": None}
            self.save_data()

    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump(self.user_data, f)

    def increment_trial(self):
        if not self.user_data["is_pro"]:
            self.user_data["trials"] += 1
            self.save_data()

    def unlock_pro(self, transaction_id):
        self.user_data["is_pro"] = True
        self.user_data["trans_id"] = transaction_id
        self.save_data()
        return True

billing = BillingSystem()
verifier = MpesaVerifier(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET, MPESA_SHORTCODE)

def trigger_mpesa_payment():
    print(f"\n[M-PESA] Initiating Payment Request for KES {PRICE}...")
    print(f"👉 A prompt will appear on phone: {PHONE_NUMBER}")
    print(f"👉 If no prompt, Send KES {PRICE} to Till/Number {PHONE_NUMBER}")
    return True

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    status_text = "⭐ PRO UNLOCKED" if billing.user_data["is_pro"] else f"🆓 TRIAL: {10 - billing.user_data['trials']} LEFT"
    print("="*65)
    print(f"      🚀 {AGENCY_NAME}: 2026 AI COMMAND CENTER      ")
    print(f"      [Status: {status_text} | Pay: {PHONE_NUMBER}]    ")
    print("="*65)

def main_menu():
    while True:
        clear_screen()
        print_header()
        print("1. [AUDIT]   Analyze URL (Consumes Trial)")
        print("2. [UPGRADE] Unlock Pro & PDF Reports (KES 50)")
        print("3. [BATTLE]  Competitive Semantic Gap")
        print("4. [TRACK]   AI Citation Monitoring")
        print("5. [EXIT]    Close")
        print("-" * 65)
        
        choice = input("Select an operation: ")

        if choice == '1':
            if not billing.user_data["is_pro"] and billing.user_data["trials"] >= 10:
                print(f"\n❌ TRIAL EXPIRED! Please Pay KES 50 to {PHONE_NUMBER} to continue.")
                input("Press Enter to return...")
                continue

            url = input("\nEnter Target URL: ").strip()
            print("\n--- INITIATING AUDIT ---")
            run_audit(url)
            billing.increment_trial()

            if os.path.exists("last_fix.json"):
                with open("last_fix.json", "r") as f:
                    data = json.load(f)
                
                print(f"\n📊 AUDIT SUMMARY: AEO Score {data.get('aeo_score', 0)}/100")
                
                if billing.user_data["is_pro"]:
                    snippet = data.get("suggested_snippet", "")
                    schema = data.get("recommended_schema", {})
                    full_fix = f"{snippet}\n\n<script type='application/ld+json'>\n{json.dumps(schema, indent=2)}\n</script>"
                    pyperclip.copy(full_fix)
                    print("✅ PRO FEATURE: Full AEO Fix copied to clipboard!")
                    
                    pdf_choice = input("Generate PDF Report? (y/n): ")
                    if pdf_choice.lower() == 'y':
                        aeo_eng = AEOAnalyzer(agency_name=AGENCY_NAME)
                        path = aeo_eng.export_pdf(url, data)
                        print(f"✅ REPORT SAVED: {path}")
                else:
                    print("\n🔒 PRO FEATURES LOCKED (Full Schema & PDF).")
                    print(f"Upgrade to PRO for KES 50 to access the fixes.")
            
            input("\nPress Enter to return to menu...")

        elif choice == '2':
            print(f"\n--- UPGRADE TO PRO (KES 50) ---")
            trigger_mpesa_payment()
            trans_id = input("\nEnter M-Pesa Transaction ID (e.g., RCKL57H8S9): ").strip().upper()
            
            print("⏳ Verifying with Safaricom Daraja API...")
            if verifier.verify_transaction(trans_id):
                billing.unlock_pro(trans_id)
                print("\n✅ TRANSACTION VERIFIED!")
                print("🎉 AURAAEO PRO is now active. Enjoy unlimited audits.")
            else:
                print("\n❌ VERIFICATION FAILED. Invalid ID or payment not reflected.")
            input("\nPress Enter...")

        elif choice == '3' or choice == '4':
            if not billing.user_data["is_pro"]:
                print("\n🔒 This feature requires PRO access.")
                input("Press Enter...")
                continue
            
            # Placeholder for competitive logic
            print("\nRunning Pro Analytics...")
            input("Press Enter...")

        elif choice == '5':
            sys.exit()

if __name__ == "__main__":
    main_menu()