import os
from nlp.monitor import CitationMonitor
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

class BotSimulator:
    def __init__(self, brand: str, domain: str):
        self.client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        self.monitor = CitationMonitor(brand, domain)

    def simulate_search(self, query: str):
        print(f"\n[SIMULATING]: '{query}'")
        
        # PRO TIP: In a real production environment, you would use DataForSEO here.
        # For this local test, we will ask Mistral to "simulate" a Perplexity response.
        
        prompt = f"Act as Perplexity AI. Provide a concise answer to: '{query}'. Include 3 source links at the end."
        
        try:
            response = self.client.chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt}]
            )
            ai_text = response.choices[0].message.content
            
            # Simple regex to find links in the simulated response
            links = re.findall(r'(https?://[^\s]+)', ai_text)
            
            result = self.monitor.check_citation(ai_text, links)
            return {
                "query": query,
                "ai_response": ai_text[:100] + "...",
                "citation_status": result['status']
            }
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    # Change these to YOUR brand details
    sim = BotSimulator(brand="HubSpot", domain="hubspot.com")
    
    with open("prompts.txt", "r") as f:
        queries = f.readlines()
    
    for q in queries:
        report = sim.simulate_search(q.strip())
        print(f"RESULT: {report['citation_status']}")