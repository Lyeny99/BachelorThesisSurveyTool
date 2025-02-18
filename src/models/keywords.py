import json
import os
from typing import List


class KeywordManager:
    """
    Handles saving, loading, and modifying keywords for chart generation.
    """

    keyword_file = os.getcwd() + "/static/keywords.json"

    @staticmethod
    def load_keywords():
        """Load keywords from a JSON file."""
        if os.path.exists(KeywordManager.keyword_file):
            with open(KeywordManager.keyword_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    @staticmethod
    def save_keywords(keywords: List[str]):
        """Save keywords to a JSON file."""
        with open(KeywordManager.keyword_file, "w", encoding="utf-8") as f:
            json.dump(keywords, f, indent=4)

    @staticmethod
    def add_keyword(keyword: List[str]):
        """Add a new keyword to the list."""
        keywords = KeywordManager.load_keywords()
        if keyword not in keywords:
            keywords.append(keyword)
            KeywordManager.save_keywords(keywords)

    @staticmethod
    def delete_keyword(keyword: List[str]):
        """Remove a keyword from the list."""
        keywords = KeywordManager.load_keywords()
        keywords = [k for k in keywords if k != keyword]
        KeywordManager.save_keywords(keywords)
