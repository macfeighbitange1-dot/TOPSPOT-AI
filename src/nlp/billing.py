import os
import json
import requests
import base64
from datetime import datetime

class BillingSystem:
    def __init__(self):
        self.data_file = "app_usage.json"
        
        # Safaricom Daraja Credentials - LIVE PRODUCTION
        self.shortcode = "174379" 
        self.passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
        self.consumer_key = "tebgdbs5GY2cAgzQo8S4FbAtGEfJoFGvRtGLGFApdYfAJLqm"
        self.consumer_secret = "fgqRJ6Qi0AAjsfkNW6dD39Vs7EGhgzSGG9Rz5dgKxWHbP5KCkhqb43ICBg5jAgzb"
        
        # Base URL for Production
        self.base_url = "https://api.safaricom.co.ke" 
        
        self.load_data()

    def load_data(self):
        """Initializes or loads the user data file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    self.user_data = json.load(f)
            except json.JSONDecodeError:
                self._reset_user_data()
        else:
            self._reset_user_data()

    def _reset_user_data(self):
        """Sets default user data status using the new 10x structure."""
        self.user_data = {
            "user_profile": {
                "account_id": "GUEST-USER",
                "tier": "FREE",
                "is_pro": False,
                "free_token_used": False,
                "trial_count": 0
            },
            "billing_data": {
                "trans_id": None,
                "subscription_start": None,
                "last_payment_kes": 0,
                "payment_status": "PENDING"
            }
        }
        self.save_data()

    def save_data(self):
        """Persists user status to local JSON storage."""
        with open(self.data_file, "w") as f:
            json.dump(self.user_data, f, indent=4)

    def can_access_premium(self):
        """Logic check: Accesses new nested JSON structure."""
        profile = self.user_data.get("user_profile", {})
        if profile.get("is_pro", False):
            return True
        if not profile.get("free_token_used", False):
            return True
        return False

    def use_free_token(self):
        """Consumes the token within the user_profile nesting."""
        self.user_data["user_profile"]["free_token_used"] = True
        self.save_data()

    def _get_access_token(self):
        """Generates the OAuth2 access token from Safaricom Production."""
        api_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        try:
            r = requests.get(api_url, auth=(self.consumer_key, self.consumer_secret))
            r.raise_for_status()
            return r.json().get('access_token')
        except Exception as e:
            print(f"[ERROR] Live Daraja Token Generation Failed: {e}")
            return None

    def trigger_stk_push(self, phone, amount=99):
        """Sends a real M-Pesa STK Push request via Production API."""
        access_token = self._get_access_token()
        if not access_token:
            return {"error": "Authentication Failed"}

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        
        phone = str(phone).strip().replace("+", "")
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        elif (phone.startswith("7") or phone.startswith("1")) and len(phone) == 9:
            phone = "254" + phone

        api_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone,
            "PartyB": self.shortcode,
            "PhoneNumber": phone,
            "CallBackURL": "https://yourdomain.com/callback", 
            "AccountReference": "TOPSPOT_AI",
            "TransactionDesc": f"Payment for {amount} Tier"
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers)
            res_data = response.json()
            print(f"[M-PESA LIVE] Request Sent: {res_data.get('CustomerMessage', 'Requested')}")
            return res_data
        except Exception as e:
            print(f"[ERROR] Live STK Push API Error: {e}")
            return {"error": str(e)}

    def unlock_pro(self, transaction_id):
        """Grants access and updates new billing_data structure."""
        if not transaction_id:
            return False
            
        transaction_id = str(transaction_id).strip().upper()
        if len(transaction_id) >= 10 and transaction_id[0].isalpha():
            self.user_data["user_profile"]["is_pro"] = True
            self.user_data["user_profile"]["tier"] = "PRO"
            self.user_data["billing_data"]["trans_id"] = transaction_id
            self.user_data["billing_data"]["payment_status"] = "VERIFIED"
            self.save_data()
            return True
        return False

    def increment_trial(self):
        """Tracks usage in user_profile trial_count."""
        if not self.user_data["user_profile"]["is_pro"]:
            self.user_data["user_profile"]["trial_count"] += 1
            self.save_data()
        return self.user_data["user_profile"]["trial_count"]

    def get_status(self):
        """Fetches current subscription and token status."""
        return self.user_data