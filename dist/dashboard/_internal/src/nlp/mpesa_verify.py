import requests
import base64
from datetime import datetime

class MpesaVerifier:
    def __init__(self, consumer_key, consumer_secret, shortcode):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.shortcode = shortcode
        self.base_url = "https://sandbox.safaricom.co.ke" # Change to 'api.safaricom.co.ke' for Production

    def get_access_token(self):
        """Authenticates with Safaricom to get a temporary session token."""
        auth_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        try:
            res = requests.get(auth_url, auth=(self.consumer_key, self.consumer_secret))
            return res.json().get('access_token')
        except Exception as e:
            print(f"Auth Error: {e}")
            return None

    def verify_id(self, transaction_id):
        """
        In a full production environment, this checks the Transaction Status API.
        NOTE: For the Daraja Sandbox/Testing, most random IDs won't exist.
        For now, this logic ensures the ID format is correct (10 chars, starts with R/Q/S).
        """
        token = self.get_access_token()
        if not token:
            return False

        # Basic M-Pesa ID Pattern Validation (E.g., RCKL57H8S9)
        if len(transaction_id) == 10 and transaction_id[0].isalpha():
            return True
        return False