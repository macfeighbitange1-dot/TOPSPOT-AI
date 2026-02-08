import re
from bs4 import BeautifulSoup

class EEATValidator:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup

    def analyze_authority(self) -> dict:
        signals = {
            "has_author_byline": False,
            "linkedin_found": False,
            "bio_page_linked": False,
            "eeat_score_bonus": 0
        }

        # 1. Search for LinkedIn profiles (High Trust Signal)
        for link in self.soup.find_all('a', href=True):
            href = link['href'].lower()
            if "linkedin.com/in/" in href:
                signals["linkedin_found"] = True
            if "about" in href or "author" in href:
                signals["bio_page_linked"] = True

        # 2. Look for common Author class names (Byline Check)
        author_patterns = ["author", "byline", "writer", "entry-author"]
        for pattern in author_patterns:
            if self.soup.find(class_=re.compile(pattern, re.I)):
                signals["has_author_byline"] = True
                break

        # Calculate Bonus
        if signals["has_author_byline"]: signals["eeat_score_bonus"] += 10
        if signals["linkedin_found"]: signals["eeat_score_bonus"] += 20
        if signals["bio_page_linked"]: signals["eeat_score_bonus"] += 10

        return signals