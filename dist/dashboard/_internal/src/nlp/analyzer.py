import os
import sys
import spacy
import re
from collections import Counter
from fpdf import FPDF
from datetime import datetime

class AEOAnalyzer:
    def __init__(self, agency_name="AURAAEO PRO", logo_path=None):
        """
        Commercial Grade AEO Analyzer with PDF Export & White-Labeling.
        """
        self.agency_name = agency_name
        self.logo_path = logo_path
        
        # PyInstaller path handling for the bundled SpaCy model
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            model_path = os.path.join(base_path, "en_core_web_md")
        else:
            model_path = "en_core_web_md"

        try:
            # Loading the model directly from the directory path
            self.nlp = spacy.load(model_path)
        except Exception:
            raise ImportError(
                f"Model missing at {model_path}. "
                "Ensure 'en_core_web_md' is bundled correctly using --add-data."
            )

    def _get_readability_score(self, doc):
        """AI readability heuristic: Prefers 14-22 words per sentence."""
        sentences = list(doc.sents)
        if not sentences: return 0
        avg_len = len(doc) / len(sentences)
        if 14 <= avg_len <= 22: return 30  # Optimized for LLMs
        return 15 if avg_len < 30 else 5

    def _check_direct_answer_intent(self, text: str):
        """Checks for 'Definition' or 'Direct Answer' lead-ins."""
        patterns = [
            r"^[A-Z][\w\s]+ (is|refers to|means|provides|consists of|was established)",
            r"^(To|By|If) [\w\s]+, [A-Z]" 
        ]
        lead_text = text[:150].strip()
        return 25 if any(re.match(p, lead_text, re.IGNORECASE) for p in patterns) else 0

    def _eeat_signals(self, doc):
        """Measures Authority signals (Experience, Expertise, Authoritativeness, Trust)."""
        markers = ["study", "research", "certified", "according to", "data", "expert", "pro"]
        score = sum(5 for word in markers if word in doc.text.lower())
        if any(token.like_num for token in doc): 
            score += 10 # Data points/statistics increase trust
        return min(score, 25)

    def analyze(self, text: str):
        """Main analysis pipeline for AEO scoring."""
        if not text or len(text.strip()) < 50:
            return {"aeo_score": 0, "status": "Incomplete"}

        doc = self.nlp(text)
        
        # Entity extraction (LLMs look for specific entity labels to categorize data)
        aeo_labels = ["ORG", "PERSON", "GPE", "PRODUCT", "LAW", "FAC"]
        entities = [
            ent.text.strip() for ent in doc.ents 
            if ent.label_ in aeo_labels and len(ent.text.strip()) > 2
            and not ent.text.isdigit()
        ]
        
        entity_counts = Counter(entities).most_common(10)
        sentences = list(doc.sents)
        avg_sent_len = round(len(doc) / len(sentences), 2) if sentences else 0

        # Calculate Metric Components
        r_score = self._get_readability_score(doc)
        i_score = self._check_direct_answer_intent(text)
        e_score = self._eeat_signals(doc)
        d_score = 20 if len(set(entities)) >= 5 else (len(set(entities)) * 4)

        return {
            "aeo_score": min(r_score + i_score + e_score + d_score, 100),
            "top_entities": entity_counts,
            "avg_sentence_length": avg_sent_len,
            "metrics": {
                "Readability": r_score, 
                "Intent": i_score, 
                "EEAT": e_score, 
                "Entity Density": d_score
            },
            "status": "Success"
        }

    def export_pdf(self, url, results, output_name="AEO_Audit_Report.pdf"):
        """Generates the professional branded PDF report for the client."""
        pdf = FPDF()
        pdf.add_page()
        
        # Header (White Label)
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(20, 60, 120) # Professional blue
        pdf.cell(0, 20, f"{self.agency_name}", ln=True, align='C')
        
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 10, "AI Search Visibility & AEO Audit", ln=True, align='C')
        
        pdf.set_font("Helvetica", 'I', 9)
        pdf.cell(0, 10, f"Target: {url} | Date: {datetime.now().strftime('%B %d, %Y')}", ln=True, align='C')
        pdf.ln(10)
        
        # Score Section with background highlight
        pdf.set_fill_color(245, 245, 245)
        pdf.set_font("Helvetica", 'B', 18)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 20, f"Total AEO Score: {results['aeo_score']}/100", ln=True, align='C', fill=True)
        pdf.ln(10)

        # Breakdown table
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "Score Breakdown:", ln=True)
        pdf.set_font("Helvetica", '', 11)
        for key, val in results['metrics'].items():
            pdf.cell(100, 8, f"{key}:", border='B')
            pdf.cell(0, 8, f"{val} pts", border='B', ln=True, align='R')

        # Entities (The 'Meat' of the report)
        pdf.ln(10)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "Key Semantic Entities Recognized by AI:", ln=True)
        pdf.set_font("Helvetica", '', 10)
        for ent, count in results['top_entities']:
            pdf.cell(0, 7, f"• {ent} ({count} occurrences)", ln=True)

        # Strategic Recommendation
        pdf.ln(10)
        pdf.set_draw_color(20, 60, 120)
        pdf.set_line_width(0.5)
        pdf.rect(10, pdf.get_y(), 190, 30) # Box for recommendation
        
        pdf.set_y(pdf.get_y() + 5)
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(0, 5, "   Expert Strategy Recommendation:", ln=True)
        pdf.set_font("Helvetica", '', 10)
        
        if results['aeo_score'] < 70:
            msg = "   CRITICAL: Site lacks authority signals. Implement structured schema and increase"
            msg2 = "   entity-specific definitions to improve Perplexity/Gemini citation chances."
        else:
            msg = "   STRONG: Content is well-optimized for AI snippets. Recommended: Focus on"
            msg2 = "   brand-specific citations to solidify position as a primary source."
        
        pdf.cell(0, 5, msg, ln=True)
        pdf.cell(0, 5, msg2, ln=True)

        # Footer
        pdf.set_y(270)
        pdf.set_font("Helvetica", 'I', 8)
        pdf.cell(0, 10, f"Confidential Report generated by {self.agency_name} Software Engine.", align='C')

        pdf.output(output_name)
        return os.path.abspath(output_name)