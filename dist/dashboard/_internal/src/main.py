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
        """Performs a full AEO audit including EEAT Validation & Mistral Optimization."""
        print(f"\n[SYSTEM]: Analyzing {url}...")
        
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
        
        # Scoring Logic: Base AEO Score + EEAT Bonus
        base_score = analysis.get("aeo_score", 0)
        eeat_bonus = eeat_results.get("eeat_score_bonus", 0)
        final_score = min(base_score + eeat_bonus, 100) 
        
        entities = self._clean_entities(analysis.get("top_entities", []))
        
        # PHASE 3: Reporting
        print(f"\n{'='*15} MISTRAL AEO AUDIT {'='*15}")
        print(f"URL: {url}")
        print(f"AEO Score: {final_score}/100 (Base: {base_score} | EEAT Bonus: +{eeat_bonus})")
        print(f"Trust Signals: Author Found: {eeat_results['has_author_byline']} | Social: {eeat_results['linkedin_found']}")
        print(f"Top Topic Entities: {entities[:5]}")
        print(f"Readability: {analysis.get('avg_sentence_length')} words/sentence")
        
        # PHASE 4: Optimization with Mistral
        suggested_answer = "N/A"
        recommended_schema = {}
        
        if final_score < 80: 
            print("\n[!] Score below threshold. Invoking Mistral Optimizer...")
            suggested_answer = self.optimizer.generate_direct_answer(data['clean_text'])
            print(f"MISTRAL SUGGESTED SNIPPET:\n> {suggested_answer}")
            recommended_schema = self.gen.generate_about_schema(entities)
        
        # Record keeping for dashboard.py
        record = {
            "url": url,
            "title": data.get("title", "Unknown"),
            "score": final_score,
            "eeat_bonus": eeat_bonus,
            "top_entities": [str(e[0]) for e in entities[:10]],
            "suggested_snippet": suggested_answer,
            "recommended_schema": recommended_schema
        }
        
        with open("last_fix.json", "w") as f:
            json.dump(record, f, indent=4)

        self.results_cache.append(record)
        print(f"\n{'='*49}")
        return record

def main(url_override=None):
    pipeline = AuraAEOPipeline()
    if url_override:
        pipeline.run_audit(url_override)
    else:
        target_url = input("Enter a URL to audit: ").strip()
        if target_url:
            pipeline.run_audit(target_url)

if __name__ == "__main__":
    main()