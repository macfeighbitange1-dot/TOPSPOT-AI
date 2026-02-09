import os
import sys
import spacy
import re
from collections import Counter
from fpdf import FPDF
from datetime import datetime

class AEOAnalyzer:
    def __init__(self, agency_name="AURAAEO PRO", logo_path=None):
        self.agency_name = agency_name
        self.logo_path = logo_path

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            model_path = os.path.join(base_path, "en_core_web_md")
        else:
            model_path = "en_core_web_md"

        try:
            self.nlp = spacy.load(model_path)
        except Exception:
            raise ImportError("SpaCy model en_core_web_md not found.")

    # ---------- CORE METRICS ----------

    def _get_readability_score(self, doc):
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

    def _check_direct_answer_intent(self, text: str):
        lead = text[:200].lower()

        strong_patterns = [
            r"\b(is|means|refers to|defined as)\b",
            r"\b(what is|who is|how does|why does)\b"
        ]

        soft_patterns = [
            r"\b(services include|we provide|our platform|helps you)\b",
            r"\b(features|benefits|solutions)\b"
        ]

        if any(re.search(p, lead) for p in strong_patterns):
            return 25
        elif any(re.search(p, lead) for p in soft_patterns):
            return 15
        return 5

    def _eeat_signals(self, doc):
        markers = [
            "research", "data", "study", "according to", "certified",
            "expert", "trusted", "official", "authority"
        ]

        score = sum(4 for m in markers if m in doc.text.lower())

        if any(t.like_num for t in doc):
            score += 8

        if any(ent.label_ == "ORG" for ent in doc.ents):
            score += 6

        return min(score, 25)

    def _entity_density(self, doc):
        allowed = {"ORG", "PERSON", "GPE", "PRODUCT", "LAW", "FAC"}
        entities = {ent.text.strip() for ent in doc.ents if ent.label_ in allowed}
