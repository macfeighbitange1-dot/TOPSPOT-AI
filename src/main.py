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
    raise ImportError(
        f"Module import failed: {e}\n"
        "Check that all src subfolders have __init__.py and files exist."
    )

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

    # -----------------------------
    # SAFE ENTITY CLEANING
    # -----------------------------
    def _clean_entities(self, entity_list):
        """
        Normalizes entity tuples from analyzer.
        Prevents unpack errors if entity_list is malformed.
        """
        stop_entities = {'PDF', 'URL', 'WIKIPEDIA', 'DOI', 'ISBN', 'HTTPS', 'HTTP'}
        cleaned = []

        if not entity_list:
            return cleaned

        for item in entity_list:
            try:
                # Accept either tuple (entity, count) or string
                if isinstance(item, (list, tuple)) and len(item) > 0:
                    entity = str(item[0]).strip()
                else:
                    entity = str(item).strip()
                if entity.upper() not in stop_entities and entity:
                    cleaned.append(entity)
            except Exception:
                continue
        return cleaned

    # -----------------------------
    # MAIN PIPELINE
    # -----------------------------
    def run_audit(self, url: str):
        print(f"\n[SYSTEM] Starting AEO audit for: {url}")

        # PHASE 1: Content Ingestion
        data = self.ingestor.fetch_content(url)
        scraped_text = data.get("clean_text", "") if data else ""
        raw_html = data.get("raw_html", "") if data else ""

        print(f"[DEBUG] Extracted {len(scraped_text)} characters")

        if not scraped_text or len(scraped_text) < 80:
            print("[FAIL] Insufficient content for semantic analysis.")
            return None

        # PHASE 2: Semantic & EEAT Analysis
        print("[PHASE 2] Running semantic & authority analysis...")
        soup = BeautifulSoup(raw_html, "html.parser")
        eeat_engine = EEATValidator(soup)
        eeat_results = eeat_engine.analyze_authority()

        analysis = self.analyzer.analyze(scraped_text)

        if analysis.get("status") != "Success":
            print("[FAIL] Analyzer returned invalid status.")
            return None

        base_score = analysis.get("aeo_score", 0)
        eeat_bonus = eeat_results.get("eeat_score_bonus", 0)
        final_score = min(base_score + eeat_bonus, 100)

        entities = self._clean_entities(analysis.get("top_entities", []))

        print(f"[DEBUG] Base: {base_score} | EEAT Bonus: {eeat_bonus} | Final: {final_score}")

        # PHASE 3: AI Outputs
        print("[PHASE 3] Generating AI-ready outputs...")
        suggested_answer = self.optimizer.generate_direct_answer(scraped_text)
        recommended_schema = self.schema_gen.generate_about_schema(entities)

        # PHASE 4: Structured Record
        record = {
            "metadata": {
                "url": url,
                "title": data.get("title", "Unknown"),
                "timestamp": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            },
            "basic_metrics": {
                "aeo_score": final_score,
                "eeat_bonus": eeat_bonus,
                "trust_signals": "Verified" if eeat_results.get("has_author_byline") else "Low",
                "top_entities": entities[:5]
            },
            "pro_features": {
                "suggested_snippet": suggested_answer,
                "recommended_schema": recommended_schema,
                "full_entity_cloud": entities[:15],
                "is_locked": True
            }
        }

        # PHASE 5: Safe Logging
        try:
            with open("last_fix.json", "w") as f:
                json.dump(record, f, indent=4)

            history_file = "audit_history.json"
            history = []

            if os.path.exists(history_file):
                try:
                    with open(history_file, "r") as f:
                        history = json.load(f)
                except (json.JSONDecodeError, TypeError):
                    history = []

            history.append(record)
            with open(history_file, "w") as f:
                json.dump(history, f, indent=4)

            print("[SUCCESS] Audit logged successfully.")
        except Exception as e:
            print(f"[ERROR] Logging failed: {e}")

        self.results_cache.append(record)
        return record


# -----------------------------
# Bridge for external calls
# -----------------------------
def main(url_override=None, return_score=False):
    pipeline = AuraAEOPipeline()
    result = pipeline.run_audit(url_override)

    if return_score:
        return result.get("basic_metrics", {}).get("aeo_score", 0) if result else 0

    return result


if __name__ == "__main__":
    target = input("Enter a URL to audit: ").strip()
    if target:
        main(target)
