import re

class CitationMonitor:
    def __init__(self, brand_name: str, domain: str):
        self.brand_name = brand_name.lower()
        self.domain = domain.lower()

    def check_citation(self, ai_response_text: str, source_links: list = None) -> dict:
        """
        Analyzes an AI response to see if the brand is mentioned or linked.
        """
        text_match = self.brand_name in ai_response_text.lower()
        
        link_match = False
        if source_links:
            link_match = any(self.domain in link.lower() for link in source_links)

        status = "NOT FOUND"
        if text_match and link_match:
            status = "FULL CITATION (Text + Link)"
        elif text_match:
            status = "MENTION ONLY (No Link)"
        elif link_match:
            status = "SOURCE ONLY (Link Only)"

        return {
            "status": status,
            "cited": text_match or link_match,
            "sentiment": "Neutral" # Placeholder for future Mistral sentiment analysis
        }