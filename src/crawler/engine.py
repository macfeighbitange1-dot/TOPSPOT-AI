import trafilatura
import requests
import random
import time
from typing import Dict, Optional

class SemanticIngestor:
    """
    Advanced Stealth Ingestor.
    Uses browser fingerprinting and behavioral jitter to bypass anti-bot shields.
    """
    
    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        # 10x BETTER: Rotating list of real browser fingerprints
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
        ]
        
        # Look like traffic coming from high-authority sources
        self.referers = [
            'https://www.google.com/',
            'https://www.bing.com/',
            'https://twitter.com/',
            'https://duckduckgo.com/'
        ]

    def fetch_content(self, url: str) -> Dict[str, Optional[str]]:
        # 1. Random Jitter: Pause for 0.5 to 2 seconds to mimic human reading speed
        time.sleep(random.uniform(0.5, 2.0))
        
        # 2. Pick random identity for this request
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': random.choice(self.referers),
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        print(f"[LOG] Stealth-Fetching: {url}")
        
        try:
            # 3. Use a Session to handle cookies automatically
            with requests.Session() as session:
                response = session.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                downloaded = response.text
                raw_html = downloaded
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                return {"error": "Access Forbidden (403). The site is actively blocking automated audits."}
            return {"error": f"HTTP Error: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"Connection Failed: {str(e)}"}

        # 4. Deep Extraction via Trafilatura
        # We use 'favor_precision' to ensure we don't get menu/footer noise
        clean_text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            include_images=False,
            favor_precision=True,
            no_fallback=False
        )
        
        metadata = trafilatura.metadata.extract_metadata(downloaded)

        if not clean_text or len(clean_text) < 100:
            return {"error": "Extraction too thin. Likely blocked by a Javascript wall."}

        return {
            "title": metadata.title if metadata else "No Title Found",
            "clean_text": clean_text,
            "raw_html": raw_html,
            "url": url
        }

if __name__ == "__main__":
    ingestor = SemanticIngestor()
    # Test with a high-security site
    sample = ingestor.fetch_content("https://www.wikipedia.org/")
    if "error" not in sample:
        print(f"✅ Success! Scraped {len(sample['clean_text'])} characters.")
    else:
        print(f"❌ Error: {sample['error']}")