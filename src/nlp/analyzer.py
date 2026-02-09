import os
import sys
import spacy
import re
from collections import Counter
from fpdf import FPDF
from datetime import datetime


class AEOAnalyzer:
    """
    Global-grade AI Search / AEO Analyzer
    Optimized for LLM citation engines (Google AI, Bing, Perplexity, GPT)
    """

    def __init__(self, agency_name="AURAAEO", logo_path=None):
        self.agency_name = agency_name
        self.logo_path = logo_path

        # Handle PyInstaller / local execution
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
            model_path = os.path.join(base_path, "en_core_web_md")
        else:
            model_path = "en_core_web_md"

        try:
            self.nlp = spacy.load(model_path)
        except Exception as e:
            raise ImportError(
                "SpaCy model 'en_core_web_md' not found. "
                "Install it using: python -m spacy download en_core_web_md"
            ) from e

    # --------------------------------------------------
    # CORE METRICS
    # --------------------------------------------------

    def _readability_score(self, doc):
        sentences = list(doc.sents)
        if not sentences:
            return 0

        avg_len = len(doc) / len(sentences)

        if 14 <= avg_len <= 22:
            return 30
        elif 10 <= avg_len < 14 or 22 < avg_len <= 28:
            return 22
        else:
            return 12

    def _direct_answer_intent(self, text: str):
        lead = text[:220].lower()

        strong = [
            r"\b(is|means|refers to|defined as)\b",
            r"\b(what is|who is|how does|why does)\b"
        ]

        moderate = [
            r"\b(services include|we provide|our platform)\b",
            r"\b(features|benefits|solutions)\b"
        ]

        if any(re.search(p, lead) for p in strong):
            return 25
        if any(re.search(p, lead) for p in moderate):
            return 15
        return 5

    def _eeat_score(self, doc):
        markers = [
            "research", "data", "study", "according to", "certified",
            "expert", "official", "authority", "trusted"
        ]

        score = sum(4 for m in markers if m in doc.text.lower())

        if any(t.like_num for t in doc):
            score += 8

        if any(ent.label_ == "ORG" for ent in doc.ents):
            score += 6

        return min(score, 25)

    def _entity_density(self, doc):
        allowed = {"ORG", "PERSON", "GPE", "PRODUCT", "LAW", "FAC"}
        entities = [
            ent.text.strip()
            for ent in doc.ents
            if ent.label_ in allowed and len(ent.text.strip()) > 2
        ]

        unique_entities = set(entities)

        score = min(len(unique_entities) * 4, 20)
        top_entities = Counter(entities).most_common(10)

        return score, top_entities

    # --------------------------------------------------
    # MAIN PUBLIC METHOD (🔥 THIS FIXES YOUR CRASH)
    # --------------------------------------------------

    def analyze(self, text: str):
        """
        Primary AEO analysis method.
        This is what app.py calls.
        """

        if not text or len(text.strip()) < 80:
            return {
                "aeo_score": 0,
                "status": "Insufficient Content",
                "top_entities": [],
                "avg_sentence_length": 0,
                "metrics": {}
            }

        doc = self.nlp(text)
        sentences = list(doc.sents)

        avg_sentence_length = (
            round(len(doc) / len(sentences), 2) if sentences else 0
        )

        readability = self._readability_score(doc)
        intent = self._direct_answer_intent(text)
        eeat = self._eeat_score(doc)
        entity_score, top_entities = self._entity_density(doc)

        total_score = min(
            readability + intent + eeat + entity_score,
            100
        )

        return {
            "aeo_score": total_score,
            "top_entities": top_entities,
            "avg_sentence_length": avg_sentence_length,
            "metrics": {
                "Readability": readability,
                "Intent Match": intent,
                "EEAT Signals": eeat,
                "Entity Strength": entity_score
            },
            "status": "Success"
        }

    # --------------------------------------------------
    # OPTIONAL PDF EXPORT (SAFE)
    # --------------------------------------------------

    def export_pdf(self, url, results, output_
