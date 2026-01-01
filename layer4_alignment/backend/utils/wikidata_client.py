"""
Wikidata Client

Fetches Wikidata QIDs for terms to provide global concept identifiers.
"""

import requests
from typing import Optional, Dict, Any, List
from functools import lru_cache


class WikidataClient:
    """
    Client for Wikidata API.
    
    Fetches QIDs (global identifiers) for terms, enabling
    cross-lingual linking of concepts.
    """
    
    API_URL = "https://www.wikidata.org/w/api.php"
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "EconMindMatrix/4.0 (Layer4Alignment)"
        })
    
    @lru_cache(maxsize=1000)
    def search_qid(self, term: str, language: str = "en") -> Optional[str]:
        """
        Search for Wikidata QID by term.
        
        Args:
            term: The term to search for
            language: Language code for search
            
        Returns:
            QID string (e.g., "Q17127698") or None
        """
        params = {
            "action": "wbsearchentities",
            "search": term,
            "language": language,
            "format": "json",
            "limit": 1
        }
        
        try:
            response = self.session.get(
                self.API_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            results = data.get("search", [])
            if results:
                return results[0].get("id")
            
        except Exception as e:
            print(f"[WARN] Wikidata search failed for '{term}': {e}")
        
        return None
    
    def get_labels(self, qid: str, languages: List[str] = None) -> Dict[str, str]:
        """
        Get labels (translations) for a QID in multiple languages.
        
        Args:
            qid: Wikidata QID (e.g., "Q17127698")
            languages: List of language codes
            
        Returns:
            Dict mapping language code to label
        """
        if languages is None:
            languages = ["en", "zh", "ja", "ko", "fr", "de", "es", "ru"]
        
        params = {
            "action": "wbgetentities",
            "ids": qid,
            "props": "labels",
            "languages": "|".join(languages),
            "format": "json"
        }
        
        try:
            response = self.session.get(
                self.API_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            entities = data.get("entities", {})
            entity = entities.get(qid, {})
            labels_data = entity.get("labels", {})
            
            labels = {}
            for lang, info in labels_data.items():
                labels[lang] = info.get("value", "")
            
            return labels
            
        except Exception as e:
            print(f"[WARN] Wikidata get_labels failed for '{qid}': {e}")
        
        return {}
    
    def get_description(self, qid: str, language: str = "en") -> Optional[str]:
        """
        Get description for a QID.
        
        Args:
            qid: Wikidata QID
            language: Language code
            
        Returns:
            Description string or None
        """
        params = {
            "action": "wbgetentities",
            "ids": qid,
            "props": "descriptions",
            "languages": language,
            "format": "json"
        }
        
        try:
            response = self.session.get(
                self.API_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            entities = data.get("entities", {})
            entity = entities.get(qid, {})
            descriptions = entity.get("descriptions", {})
            lang_desc = descriptions.get(language, {})
            
            return lang_desc.get("value")
            
        except Exception as e:
            print(f"[WARN] Wikidata get_description failed: {e}")
        
        return None
    
    def enrich_term(self, term: str, language: str = "en") -> Dict[str, Any]:
        """
        Enrich a term with Wikidata information.
        
        Args:
            term: The term to enrich
            language: Primary language
            
        Returns:
            Dict with qid, labels, and description
        """
        qid = self.search_qid(term, language)
        
        if not qid:
            return {"qid": None, "labels": {}, "description": None}
        
        labels = self.get_labels(qid)
        description = self.get_description(qid, language)
        
        return {
            "qid": qid,
            "labels": labels,
            "description": description
        }
