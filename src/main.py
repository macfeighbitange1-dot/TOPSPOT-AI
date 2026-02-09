import os
import pandas as pd
import json
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Modular internal packages
from src.crawler.engine import SemanticIngestor
from src.nlp.analyzer import AEOAnalyzer
from src.nlp.generator import AEOOptimizer
from src.core.schema_gen import SchemaGenerator
from src.nlp.eeat_validator import EEATValidator 

load_dotenv()

class AuraAEOPipeline:
    def __init__(self):
        self.ingestor = SemanticIngestor()
        self.analyzer = AEOAnalyzer()
        self.optimizer = AEOOptimizer()
        self.gen = SchemaGenerator()
        self.results_cache = []

    def _clean_entities(self, entity_list):
        """Filters out technical noise from the entity results."""
        stop_entities = ['PDF', 'URL', 'WIKIPEDIA', 'DOI', 'ISBN', 'HTTPS', 'HTTP']
        return [e for e in entity_list if str(e[0]).upper() not in stop_entities]

    def run_audit(self, url: str):
        """Performs a full AEO audit and prepares tiered data for the Paywall."""
        print(f"\n[SYSTEM]: Initiating Scan for {url}...")
        
        # PHASE 1: Data Ingestion
        data = self.ingestor.fetch_content(url)
        if not data or "error" in data or not data.get("clean_text"):
            print(f"FAILED: Could not extract content from {url}.")
            return None

        # PHASE 2: Semantic & EEAT Analysis
        soup = BeautifulSoup(data.get('raw_html', ''), 'html.parser')
        eeat_engine = EEATValidator(soup)
        eeat_results = eeat_engine.analyze_authority()
        
        analysis = self.analyzer.analyze(data['clean_text'])
        
        # Scoring Logic
        base_score = analysis.get("aeo_score", 0)
        eeat_bonus = eeat_results.get("eeat_score_bonus", 0)
        final_score = min(base_score + eeat_bonus, 100) 
        entities = self._clean_entities(analysis.get("top_entities", []))
        
        # PHASE 3: Generate Pro Features (The Value)
        print("[!] Generating Pro Recommendations...")
        suggested_answer = self.optimizer.generate_direct_answer(data['clean_text'])
        recommended_schema = self.gen.generate_about_schema(entities)
        
        # PHASE 4: TIERED RECORD CREATION (Volume Strategy Logic)
        record = {
            "metadata": {
                "url": url,
                "title": data.get("title", "Unknown"),
                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "basic_metrics": {
                "aeo_score": final_score,
                "eeat_bonus": eeat_bonus,
                "trust_signals": "Verified" if eeat_results['has_author_byline'] else "Low",
                "top_entities": [str(e[0]) for e in entities[:5]]
            },
            "pro_features": {
                "suggested_snippet": suggested_answer,
                "recommended_schema": recommended_schema,
                "full_entity_cloud": [str(e[0]) for e in entities[:15]],
                "is_locked": True # Default to locked until app.py confirms payment
            }
        }
        
        # SAVE TO ROOT for Streamlit Dashboard
        try:
            with open("last_fix.json", "w") as f:
                json.dump(record, f, indent=4)
            print(f"[DEBUG] Audit Complete for {url}. Results stored in last_fix.json")
        except Exception as e:
            print(f"[ERROR] IO Failure: {e}")

        self.results_cache.append(record)
        return record

def main(url_override=None, return_score=False):
    """Bridge function for app.py to trigger the audit."""
    pipeline = AuraAEOPipeline()
    result = pipeline.run_audit(url_override)
    
    # NEW LOGIC: If return_score is True, return just the integer for the chart
    if return_score:
        if result and "basic_metrics" in result:
            return result["basic_metrics"].get("aeo_score", 0)
        return 0
        
    return result

if __name__ == "__main__":
    target = input("Enter a URL to audit: ").strip()
    if target:
        main(target)