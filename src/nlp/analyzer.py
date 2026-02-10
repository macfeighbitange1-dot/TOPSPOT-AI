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
    # MAIN PUBLIC METHOD (ENTERPRISE-LEVEL)
    # --------------------------------------------------

    def analyze(self, text: str):
        """
        Primary AEO analysis method.
        Enterprise-grade scoring with Sentence Complexity, Semantic Density, and Variance.
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

        # --- Sentence Complexity & Variance ---
        avg_sentence_length = round(len(doc) / max(len(sentences), 1), 2)
        sentence_lengths = [len(s) for s in sentences]
        variance = sum((l - avg_sentence_length) ** 2 for l in sentence_lengths) / max(len(sentence_lengths), 1)
        variance_score = 8 if variance > 15 else 4

        # --- Semantic Density ---
        token_count = len(doc)
        entity_count = len([ent for ent in doc.ents if ent.label_ in {"ORG","PERSON","GPE","PRODUCT","LAW"}])
        semantic_density = entity_count / max(token_count, 1)
        density_score = 18 if semantic_density >= 0.03 else 12 if semantic_density >= 0.015 else 6

        # --- Readability, Intent, EEAT, Entity Strength ---
        readability = self._readability_score(doc)
        intent = self._direct_answer_intent(text)
        eeat = self._eeat_score(doc)
        entity_score, top_entities = self._entity_density(doc)

        # --- TOTAL SCORE ---
        raw_score = readability + intent + eeat + entity_score + variance_score + density_score
        final_score = min(int(raw_score), 100)

        return {
            "status": "Success",
            "aeo_score": final_score,
            "top_entities": top_entities,
            "avg_sentence_length": avg_sentence_length,
            "metrics": {
                "Readability": readability,
                "Intent Match": intent,
                "EEAT Signals": eeat,
                "Entity Strength": entity_score,
                "Sentence Variance": round(variance, 2),
                "Semantic Density": round(semantic_density, 4)
            }
        }

    # --------------------------------------------------
    # OPTIONAL PDF EXPORT
    # --------------------------------------------------

    def export_pdf(self, url, results, output_name="AEO_Audit_Report.pdf"):
        pdf = FPDF()
        pdf.add_page()

        # Header
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(20, 60, 120)
        pdf.cell(0, 20, f"{self.agency_name}", ln=True, align='C')

        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 10, "AI Search Visibility & AEO Audit", ln=True, align='C')

        pdf.set_font("Helvetica", 'I', 9)
        pdf.cell(0, 10, f"Target: {url} | Date: {datetime.now().strftime('%B %d, %Y')}", ln=True, align='C')
        pdf.ln(10)

        # Score
        pdf.set_fill_color(245, 245, 245)
        pdf.set_font("Helvetica", 'B', 18)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 20, f"Total AEO Score: {results['aeo_score']}/100", ln=True, align='C', fill=True)
        pdf.ln(10)

        # Breakdown
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "Score Breakdown:", ln=True)
        pdf.set_font("Helvetica", '', 11)
        for k, v in results['metrics'].items():
            pdf.cell(100, 8, f"{k}:", border='B')
            pdf.cell(0, 8, f"{v} pts", border='B', ln=True, align='R')

        # Entities
        pdf.ln(10)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "Key Semantic Entities Recognized by AI:", ln=True)
        pdf.set_font("Helvetica", '', 10)
        for ent, count in results['top_entities']:
            pdf.cell(0, 7, f"• {ent} ({count} occurrences)", ln=True)

        # Save PDF
        pdf.output(output_name)
        return os.path.abspath(output_name)
