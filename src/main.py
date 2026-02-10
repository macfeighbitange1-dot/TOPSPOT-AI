import os
import json
import pandas as pd
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# -----------------------------
# Internal modules (package-safe)
# -----------------------------
try:
    from src.crawler.engine import SemanticIngestor
    from src.nlp.analyzer import AEOAnalyzer
    from src.nlp.generator import AEOOptimizer
    from src.core.schema_gen import SchemaGenerator
    from src.nlp.eeat_validator import EEATValidator
except ImportError as e:
    # Fallback to direct imports if package structure is shifting
    print(f"[WARNING] Standard import failed, attempting relative: {e}")
    try:
        from crawler.engine import SemanticIngestor
        from nlp.analyzer import AEOAnalyzer
        from nlp.generator import AEOOptimizer
        from core.schema_gen import SchemaGenerator
        from nlp.eeat_validator import EEATValidator
    except Exception as e_inner:
        print(f"[CRITICAL] Package structure is broken: {e_inner}")

load_dotenv()

class AuraAEOPipeline:
    """
    End-to-end AEO audit pipeline.
    Stable, analyzer-synced, and production hardened.
    """

    def __init__(self):
        self.ingestor = SemanticIngestor()
        self.analyzer = AEOAnalyzer()
        self.optimizer = AEOOptimizer()
        self.schema_gen = SchemaGenerator()
        self.results_cache = []

    def _clean_entities(self, entity_list):
        """Normalizes entity tuples to prevent unpacking errors."""
        stop_entities = {'PDF', 'URL', 'WIKIPEDIA', 'DOI', 'ISBN', 'HTTPS', 'HTTP'}
        cleaned = []
        if not entity_list: return cleaned

        for item in entity_list:
            try:
                # Handle (Name, Label) or (Name, Count) or just "Name"
                if isinstance(item, (list, tuple)) and len(item) > 0:
                    entity = str(item[0]).strip()
                else:
                    entity = str(item).strip()
                
                if entity.upper() not in stop_entities and len(entity) > 1:
                    cleaned.append(entity)
            except: continue
        return list(set(cleaned))

    def run_audit(self, url: str):
        print(f"\n[SYSTEM] Starting AEO audit for: {url}")

        # PHASE 1: Content Ingestion
        try:
            data = self.ingestor.fetch_content(url)
            scraped_text = data.get("clean_text", "") if data else ""
            raw_html = data.get("raw_html", "") if data else ""
        except Exception as e:
            print(f"[FAIL] Ingestion Error: {e}")
            return None

        if not scraped_text or len(scraped_text) < 50:
            print("[FAIL] Insufficient content.")
            return None

        # PHASE 2: Semantic & EEAT Analysis
        print("[PHASE 2] Running analysis...")
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            eeat_engine = EEATValidator(soup)
            eeat_results = eeat_engine.analyze_authority()
        except:
            eeat_results = {"eeat_score_bonus": 0, "has_author_byline": False}

        analysis = self.analyzer.analyze(scraped_text)
        
        base_score = analysis.get("aeo_score", 0)
        eeat_bonus = eeat_results.get("eeat_score_bonus", 0)
        final_score = min(base_score + eeat_bonus, 100)

        entities = self._clean_entities(analysis.get("top_entities", []))

        # PHASE 3: AI Outputs
        print("[PHASE 3] Generating recommendations...")
        suggested_answer = self.optimizer.generate_direct_answer(scraped_text)
        recommended_schema = self.schema_gen.generate_about_schema(entities)

        # PHASE 4: Structured Record
        record = {
            "metadata": {
                "url": url,
                "title": data.get("title", "Unknown Site"),
                "timestamp": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            },
            "basic_metrics": {
                "aeo_score": final_score,
                "eeat_bonus": eeat_bonus,
                "trust_signals": "Verified" if eeat_results.get("has_author_byline") else "Low",
                "top_entities": entities[:10]
            },
            "pro_features": {
                "suggested_snippet": suggested_answer,
                "recommended_schema": recommended_schema,
                "full_entity_cloud": entities[:20]
            }
        }

        # PHASE 5: File Persistence
        try:
            with open("last_fix.json", "w") as f:
                json.dump(record, f, indent=4)
            
            # History log management
            h_file = "audit_history.json"
            history = []
            if os.path.exists(h_file):
                with open(h_file, "r") as f:
                    try: history = json.load(f)
                    except: history = []
            
            history.append(record)
            with open(h_file, "w") as f:
                json.dump(history[-50:], f, indent=4) # Keep last 50 only
        except Exception as e:
            print(f"[ERROR] Persistence failed: {e}")

        return record

# --- GLOBAL BRIDGE ---
# This allows 'from src.main import main' to work perfectly
def main(url_override=None, return_score=False):
    if not url_override:
        return 0 if return_score else None
        
    pipeline = AuraAEOPipeline()
    result = pipeline.run_audit(url_override)

    if return_score:
        return result.get("basic_metrics", {}).get("aeo_score", 0) if result else 0
    return result

if __name__ == "__main__":
    target = input("Enter a URL to audit: ").strip()
    if target:
        main(target)