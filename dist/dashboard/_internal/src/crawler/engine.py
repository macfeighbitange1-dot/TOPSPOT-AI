import trafilatura
import requests
from typing import Dict, Optional

class SemanticIngestor:
    """
    Handles high-fidelity text extraction for AEO analysis.
    Upgraded with Browser-Spoofing to bypass anti-scraping blocks.
    """
    
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        # Modern Chrome User-Agent to look like a real human
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1', # Do Not Track request
        }

    def fetch_content(self, url: str) -> Dict[str, Optional[str]]:
        print(f"[LOG] Fetching content from: {url}...")
        
        try:
            # 1. Attempt high-level fetch with custom headers
            # Trafilatura's fetch_url is limited, so we use requests for better control
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status() # Raise error for 403, 404, etc.
            downloaded = response.text
            
            # Use raw_html to preserve data for the EEAT Validator in main.py
            raw_html = downloaded 
        except Exception as e:
            print(f"[!] Request Error: {e}")
            return {"error": f"Failed to retrieve content: {e}"}

        # 2. Extract meaningful text (AEO needs clean data)
        # include_tables=True is vital for AEO as AI searches love tabular data
        clean_text = trafilatura.extract(
            downloaded, 
            include_comments=False, 
            include_tables=True,
            no_fallback=False # Allow trafilatura to try its best
        )
        
        # 3. Extract Metadata
        metadata = trafilatura.metadata.extract_metadata(downloaded)

        if not clean_text:
            return {"error": "Extraction failed. The site may be blocking content or is JS-heavy."}

        return {
            "title": metadata.title if metadata else "No Title Found",
            "clean_text": clean_text,
            "raw_html": raw_html, # Vital for Phase 2 EEAT Validation
            "url": url
        }

if __name__ == "__main__":
    # Test with a site that usually blocks simple crawlers
    ingestor = SemanticIngestor()
    sample = ingestor.fetch_content("https://searchengineland.com/google-search-generative-experience-aeo-430345")
    if "error" not in sample:
        print(f"✅ Success! Title: {sample['title']}")
        print(f"Content Preview: {sample['clean_text'][:200]}...")
    else:
        print(f"❌ Still Blocked: {sample['error']}")