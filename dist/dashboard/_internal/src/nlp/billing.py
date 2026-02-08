import os
import json
import requests
from datetime import datetime
from base64 import b64encode

class BillingManager:
    def __init__(self):
        self.counter_file = "user_data.json"
        self.passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
        self.shortcode = "174379"
        self.consumer_key = "tebgdbs5GY2cAgzQo8S4FbAtGEfJoFGvRtGLGFApdYfAJLqm"
        self.consumer_secret = "fgqRJ6Qi0AAjsfkNW6dD39Vs7EGhgzSGG9Rz5dgKxWHbP5KCkhqb43ICBg5jAgzb"

    def get_user_status(self):
        """Checks how many trials are left."""
        if not os.path.exists(self.counter_file):
            data = {"trials": 0, "is_pro": False}
            with open(self.counter_file, "w") as f: json.dump(data, f)
            return data
        with open(self.counter_file, "r") as f:
            return json.load(f)

    def increment_trial(self):
        status = self.get_user_status()
        if not status["is_pro"]:
            status["trials"] += 1
            with open(self.counter_file, "w") as f: json.dump(status, f)
        return status["trials"]

    def trigger_stk_push(self, phone):
        """Triggers a 50 KES M-Pesa prompt on the user's phone."""
        print(f"\n[M-PESA] Sending KES 50 request to {phone}...")
        # (This is a simplified version of the Daraja logic)
        # In a production exe, we usually ask them to input the Transaction ID manually 
        # unless you have a live server callback.
        print("👉 Please check your phone and enter your M-Pesa PIN.")
        return True

    def verify_transaction(self, trans_id):
        """Unlocks PRO mode if ID is valid (Length check for demo)."""
        if len(trans_id) >= 10: # Basic M-Pesa ID validation (e.g., RCL57H8S92)
            status = {"trials": 10, "is_pro": True, "trans_id": trans_id}
            with open(self.counter_file, "w") as f: json.dump(status, f)
            return True
        return False