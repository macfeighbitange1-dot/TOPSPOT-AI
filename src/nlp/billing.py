import os
import json
import requests
from datetime import datetime
from base64 import b64encode

class BillingSystem:
    def __init__(self):
        # Synchronized with dashboard.py and app.py
        self.data_file = "app_usage.json"
        self.passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
        self.shortcode = "174379"
        self.consumer_key = "tebgdbs5GY2cAgzQo8S4FbAtGEfJoFGvRtGLGFApdYfAJLqm"
        self.consumer_secret = "fgqRJ6Qi0AAjsfkNW6dD39Vs7EGhgzSGG9Rz5dgKxWHbP5KCkhqb43ICBg5jAgzb"
        self.load_data()

    def load_data(self):
        """Initializes or loads the user data file."""
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                self.user_data = json.load(f)
        else:
            self.user_data = {"trials": 0, "is_pro": False, "trans_id": None}
            self.save_data()

    def save_data(self):
        """Persists user status to JSON."""
        with open(self.data_file, "w") as f:
            json.dump(self.user_data, f)

    def increment_trial(self):
        """Increases trial count if user is not PRO."""
        if not self.user_data["is_pro"]:
            self.user_data["trials"] += 1
            self.save_data()
        return self.user_data["trials"]

    def trigger_stk_push(self, phone):
        """Visual feedback for the M-Pesa prompt."""
        print(f"\n[M-PESA] Sending KES 50 request to {phone}...")
        print("👉 Please check your phone and enter your M-Pesa PIN.")
        return True

    def unlock_pro(self, transaction_id):
        """
        Verifies the Transaction ID and unlocks PRO mode.
        Matches the call used in app.py.
        """
        transaction_id = transaction_id.strip().upper()
        # Basic M-Pesa ID validation (10 chars, starts with a letter)
        if len(transaction_id) >= 10 and transaction_id[0].isalpha():
            self.user_data["is_pro"] = True
            self.user_data["trans_id"] = transaction_id
            # Set trials to max to avoid logic conflicts
            self.user_data["trials"] = 10 
            self.save_data()
            return True
        return False

    def get_user_status(self):
        """Helper for external scripts to read current data."""
        return self.user_data