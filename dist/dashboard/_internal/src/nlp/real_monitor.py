import os
import requests
import json
from base64 import b64encode
from dotenv import load_dotenv

load_dotenv()

class DataForSEOMonitor:
    def __init__(self):
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        self.endpoint = "https://api.dataforseo.com/v3/ai_optimization/llm_mentions/search/live"

    def _get_auth_header(self):
        auth_str = f"{self.login}:{self.password}"
        encoded = b64encode(auth_str.encode()).decode()
        return {"Authorization": f"Basic {encoded}", "Content-Type": "application/json"}

    def check_mentions(self, brand_name: str, platform="google"):
        """
        Checks real-time mentions for a brand on 'google' (AI Overviews) or 'chat_gpt'.
        """
        # DataForSEO requires a 'target' array
        payload = [{
            "keyword": brand_name,
            "match_type": "partial_match",
            "search_scope": ["answer", "sources"] # Check text and links
        }]
        
        # Wrapping in their required task format
        task_data = [{
            "target": payload,
            "platform": platform,
            "location_name": "United States",
            "language_name": "English"
        }]

        try:
            response = requests.post(self.endpoint, headers=self._get_auth_header(), json=task_data)
            response.raise_for_status()
            data = response.json()
            
            # Parsing the 'tasks' result
            if data.get("status_code") == 20000:
                result = data["tasks"][0]["result"][0]
                return {
                    "total_mentions": result.get("total_count", 0),
                    "ai_search_volume": result.get("items", [{}])[0].get("ai_search_volume", 0),
                    "items": result.get("items", []),
                    "status": "Success"
                }
            return {"status": "Error", "message": data.get("status_message")}
            
        except Exception as e:
            return {"status": "Critical Failure", "error": str(e)}

if __name__ == "__main__":
    monitor = DataForSEOMonitor()
    # Test it with a major brand to see real data
    report = monitor.check_mentions("HubSpot")
    print(json.dumps(report, indent=2))