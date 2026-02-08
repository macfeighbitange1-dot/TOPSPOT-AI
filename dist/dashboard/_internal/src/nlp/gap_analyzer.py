import os
import requests
from base64 import b64encode
from dotenv import load_dotenv

# Import your own tools
from src.crawler.engine import SemanticIngestor
from src.nlp.analyzer import AEOAnalyzer

load_dotenv()

class CitationGapAnalyzer:
    def __init__(self):
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        self.ingestor = SemanticIngestor()
        self.analyzer = AEOAnalyzer()

    def get_gap_report(self, my_brand: str, competitor_brand: str):
        """
        The Master Logic: 
        1. If these are URLs, do a direct Semantic Battle.
        2. If they are brand names AND we have API keys, try DataForSEO.
        3. Otherwise, return a helpful error.
        """
        
        # Check if we are dealing with URLs
        if my_brand.startswith("http") and competitor_brand.startswith("http"):
            return self.run_local_battle(my_brand, competitor_brand)
        
        # If they aren't URLs, we NEED the API
        if not self.login or not self.password:
            return {
                "error": "To compare BRAND NAMES, you need a DataForSEO API key in .env. \n"
                         "TO COMPARE FOR FREE: Enter full URLs starting with 'https://' instead!"
            }

        # [DataForSEO API Logic would go here, but let's prioritize the Free Battle]
        return {"error": "API Auth Failed. Use full URLs to bypass API requirements."}

    def run_local_battle(self, my_url: str, comp_url: str):
        """
        Uses your existing high-power engines to find what the competitor has that you don't.
        """
        print(f"\n[BATTLE] Scraped Analysis Initiated...")
        
        # 1. Fetch both
        my_data = self.ingestor.fetch_content(my_url)
        comp_data = self.ingestor.fetch_content(comp_url)

        if not my_data or not comp_data or "error" in my_data or "error" in comp_data:
            return {"error": "Battle failed: One of the URLs could not be reached."}

        # 2. Analyze both
        my_res = self.analyzer.analyze(my_data['clean_text'])
        comp_res = self.analyzer.analyze(comp_data['clean_text'])

        # 3. Calculate Entity Gap
        my_ents = set([e[0] for e in my_res.get('top_entities', [])])
        comp_ents = set([e[0] for e in comp_res.get('top_entities', [])])
        
        missing = list(comp_ents - my_ents)
        shared = list(comp_ents & my_ents)

        return {
            "status": "Success",
            "scores": {
                "you": my_res['aeo_score'],
                "competitor": comp_res['aeo_score']
            },
            "gap_analysis": {
                "missing_entities": missing,
                "shared_entities": shared,
                "threat_level": "High" if comp_res['aeo_score'] > my_res['aeo_score'] else "Low"
            }
        }