import json

class SchemaGenerator:
    """
    Automates the creation of structured data to bridge the gap 
    between complex text and AI understanding.
    """
    
    @staticmethod
    def generate_faq_schema(question: str, answer: str) -> str:
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [{
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": answer
                }
            }]
        }
        return json.dumps(schema, indent=2)

    @staticmethod
    def generate_about_schema(entities: list) -> str:
        # Tells the AI exactly what entities this page is an authority on
        schema = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "about": [{"@type": "Thing", "name": name} for name, count in entities]
        }
        return json.dumps(schema, indent=2)