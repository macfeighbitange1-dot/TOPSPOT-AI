import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

class AEOOptimizer:
    def __init__(self):
        # Ensure you have MISTRAL_API_KEY=your_key in your .env file
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            print("[ERROR]: Mistral API Key not found. Optimizer will fail.")
            self.client = None
        else:
            self.client = Mistral(api_key=api_key)
        
        # 'mistral-large-latest' is recommended for complex reasoning/legal text
        self.model = "mistral-large-latest"

    def generate_direct_answer(self, text: str) -> str:
        """Transforms complex text into a concise 45-60 word Direct Answer."""
        if not self.client:
            return "Error: Mistral Client not initialized."

        prompt = f"""
        REWRITE this text into a 'Direct Answer' snippet for an AI Answer Engine.
        
        CRITICAL RULES:
        1. Start with a direct definition (e.g., 'X is...' or 'X provides...').
        2. Keep it between 45 and 55 words exactly.
        3. Maintain high factual density—keep entities and numbers.
        4. Use objective, authoritative tone. No marketing fluff.

        SOURCE TEXT:
        {text[:2000]}
        """

        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Mistral API Error: {str(e)}"