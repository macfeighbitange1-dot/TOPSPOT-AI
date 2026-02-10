import os
import sys
import spacy
import re
from collections import Counter
from fpdf import FPDF
from datetime import datetime

class AEOAnalyzer:
    """
    Global-grade AI Search / AEO Analyzer.
    Fixed to resolve 'unpacking' errors and optimized for Streamlit Cloud.
    """

    def __init__(self, agency_name="AURAAEO", logo_path=None):
        self.agency_name = agency_name
        self.logo_path = logo_path

        # Handle Streamlit Cloud vs Local paths
        try:
            # Try loading the medium model (better for AEO)
            self.nlp = spacy.load("en_core_web_md")
        except:
            try:
                # Fallback to small model if medium isn't installed
                self.nlp = spacy.load("en_core_web_sm")
            except Exception as e:
                # Direct instruction if both fail
                raise ImportError(
                    "SpaCy model not found. Run: python -m spacy download en_core_web_sm"
                )

    # --------------------------------------------------
    # CORE METRICS
    # --------------------------------------------------

    def _readability_score(self, doc):
        sentences = list(doc.sents)
        if not sentences: return 0
        avg_len = len(doc) / len(sentences)
        if 14 <= avg_len <= 22: return 30
        elif 10 <= avg_len < 14 or 22 < avg_len <= 28: return 22
        else: return 12

    def _direct_answer_intent(self, text: str):
        lead = text[:220].lower()
        strong = [r"\b(is|means|refers to|defined as)\b", r"\b(what is|who is|how does|why does)\b"]
        moderate = [r"\b(services include|we provide|our platform)\b", r"\b(features|benefits|solutions)\b"]
        if any(re.search(p, lead) for p in strong): return 25
        if any(re.search(p, lead) for p in moderate): return 15
        return 5

    def _eeat_score(self, doc):
        markers = ["research", "data", "study", "according to", "certified", "expert", "official", "authority", "trusted"]
        score = sum(4 for m in markers if m in doc.text.lower())
        if any(t.like_num for t in doc): score += 8
        if any(ent.label_ == "ORG" for ent in doc.ents): score += 6
        return min(score, 25)

    def _entity_density(self, doc):
        """
        FIXED: Returns (Name, Label) instead of (Name, Count) 
        to match dashboard 'unpacking' expectations.
        """
        allowed = {"ORG", "PERSON", "GPE", "PRODUCT", "LAW", "FAC"}
        # Capture name and category label
        entities = [
            (ent.text.strip(), ent.label_) 
            for ent in doc.ents 
            if ent.label_ in allowed and len(ent.text.strip()) > 2
        ]
        
        # Get unique entities to avoid cluttering the dashboard
        unique_entities = list(set(entities))[:10]
        
        # Calculate score based on entity variety
        score = min(len(unique_entities) * 4, 20)
        
        return score, unique_entities

    # --------------------------------------------------
    # MAIN PUBLIC METHOD
    # --------------------------------------------------

    def analyze(self, text: str):
        if not text or len(text.strip()) < 80:
            return {
                "aeo_score": 0,
                "status": "Insufficient Content",
                "top_entities": [],
                "metrics": {}
            }

        doc = self.nlp(text)
        sentences = list(doc.sents)

        # Calculation Logic
        avg_sentence_length = round(len(doc) / max(len(sentences), 1), 2)
        sentence_lengths = [len(s) for s in sentences]
        variance = sum((l - avg_sentence_length) ** 2 for l in sentence_lengths) / max(len(sentence_lengths), 1)
        variance_score = 8 if variance > 15 else 4

        token_count = len(doc)
        entity_count = len([ent for ent in doc.ents if ent.label_ in {"ORG","PERSON","GPE"}])
        semantic_density = entity_count / max(token_count, 1)
        density_score = 18 if semantic_density >= 0.03 else 12 if semantic_density >= 0.015 else 6

        readability = self._readability_score(doc)
        intent = self._direct_answer_intent(text)
        eeat = self._eeat_score(doc)
        
        # GET FIXED ENTITIES HERE
        entity_score, top_entities = self._entity_density(doc)

        raw_score = readability + intent + eeat + entity_score + variance_score + density_score
        
        return {
            "status": "Success",
            "aeo_score": min(int(raw_score), 100),
            "top_entities": top_entities, # Guaranteed [(Name, Label), ...]
            "metrics": {
                "Readability": readability,
                "Intent Match": intent,
                "EEAT Signals": eeat,
                "Entity Strength": entity_score,
                "Semantic Density": round(semantic_density, 4)
            }
        }

    def export_pdf(self, url, results, output_name="AEO_Audit_Report.pdf"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 22)
        pdf.cell(0, 20, f"{self.agency_name} - Audit Report", ln=True, align='C')
        pdf.set_font("Helvetica", 'B', 18)
        pdf.cell(0, 20, f"Total AEO Score: {results['aeo_score']}/100", ln=True, align='C')
        
        # Breakdown
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "Breakdown:", ln=True)
        for k, v in results['metrics'].items():
            pdf.cell(0, 8, f"{k}: {v}", ln=True)
            
        pdf.output(output_name)
        return os.path.abspath(output_name)