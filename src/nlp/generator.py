import os
import time
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()


class AEOOptimizer:
    """
    Enterprise-grade AI optimizer for generating concise, factual
    direct answers from source text using Mistral API.
    """

    def __init__(self):
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            print("[ERROR] Mistral API Key not found. Optimizer disabled.")
            self.client = None
        else:
            self.client = Mistral(api_key=api_key)

        self.model = "mistral-large-latest"
        self.max_chunk_size = 2000  # max characters per prompt
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def generate_direct_answer(self, text: str) -> str:
        """
        Converts complex source text into a concise, high-density Direct Answer.
        Returns 45-60 word snippet with authoritative tone.
        """

        if not self.client:
            return "[ERROR] Mistral client not initialized."

        # Truncate or chunk text to prevent API overload
        text_chunk = text[: self.max_chunk_size]

        prompt = f"""
        TRANSFORM the following text into a concise Direct Answer snippet
        for an AI Answer Engine:

        CRITICAL RULES:
        1. Begin with a direct definition (e.g., 'X is...' or 'X provides...').
        2. Output must be 45-60 words only.
        3. Preserve key entities, numbers, and factual info.
        4. Use authoritative, objective tone. No marketing fluff.
        5. Do not invent facts. Only summarize what is present.

        SOURCE TEXT:
        {text_chunk}
        """

        # Retry logic for transient API issues
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.complete(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
                # Mistral response structure
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[WARNING] Mistral API attempt {attempt} failed: {e}")
                time.sleep(self.retry_delay)

        return "[ERROR] Failed to generate direct answer after multiple attempts."


# -----------------------------
# Quick test / local run
# -----------------------------
if __name__ == "__main__":
    sample_text = (
        "Kenya's Constitution 2010 guarantees every citizen the right to the highest "
        "attainable standard of health. The Ministry of Health ensures regulatory oversight "
        "and service delivery across counties."
    )
    optimizer = AEOOptimizer()
    result = optimizer.generate_direct_answer(sample_text)
    print("Direct Answer:\n", result)
