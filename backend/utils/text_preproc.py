"""
Streamlined text preprocessing for Adil's portfolio chatbot
Focuses on essential corrections and portfolio-specific enhancements
"""
import re
import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

class TextPreprocessor:
    """Lightweight text preprocessing for portfolio queries"""
    
    def __init__(self):
        # Essential portfolio corrections
        self.corrections = {
            # Name variations (most critical)
            r'\b(adeel|aadil|adel|adeal)\b': 'adil',
            r'\b(saed|seed|said)\b': 'saeed',
            
            # Key professional terms
            r'\b(programing|programeing)\b': 'programming',
            r'\b(developement|devlopment)\b': 'development',
            r'\b(tecnoogy|tecnology)\b': 'technology',
            r'\b(artifical|artificail)\b': 'artificial',
            r'\b(machien|mashine)\b': 'machine',
            r'\b(projets|projet)\b': 'projects',
            r'\b(skils|skiils)\b': 'skills',
            
            # Contact terms
            r'\b(linkdin|linkedn)\b': 'linkedin',
            r'\b(contect|contac)\b': 'contact',
            r'\b(emai|emial)\b': 'email',
            r'\b(githab|guthub)\b': 'github',
            
            # Common query words
            r'\b(wich|whch)\b': 'which',
            r'\b(wher|whre)\b': 'where',
            r'\b(aout|abou)\b': 'about',
            r'\b(tel|tel)\b': 'tell'
        }
        
        # Concept normalization
        self.concept_map = {
            'programming': ['coding', 'development', 'dev'],
            'skills': ['abilities', 'expertise', 'knowledge'],
            'contact': ['reach', 'connect', 'hire'],
            'projects': ['work', 'portfolio', 'apps'],
            'education': ['study', 'learning', 'degree'],
            'experience': ['background', 'career', 'history']
        }

    async def process(self, text: str, language: str = "en") -> str:
        """Main preprocessing pipeline"""
        
        if not text or not text.strip():
            return ""
        
        try:
            # Step 1: Basic cleaning
            processed = self._clean_text(text)
            
            # Step 2: Apply corrections
            processed = self._apply_corrections(processed)
            
            # Step 3: Normalize concepts
            processed = self._normalize_concepts(processed)
            
            return processed.strip()
            
        except Exception as e:
            logger.error(f"Preprocessing error: {e}")
            return text.strip()

    def _clean_text(self, text: str) -> str:
        """Basic text cleaning"""
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Fix punctuation
        text = re.sub(r'([!?]){2,}', r'\1', text)
        text = re.sub(r'\.{3,}', '...', text)
        
        return text.strip()

    def _apply_corrections(self, text: str) -> str:
        """Apply portfolio-specific corrections"""
        
        for pattern, replacement in self.corrections.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text

    def _normalize_concepts(self, text: str) -> str:
        """Normalize portfolio concepts"""
        
        text_lower = text.lower()
        
        for standard_term, synonyms in self.concept_map.items():
            for synonym in synonyms:
                pattern = r'\b' + re.escape(synonym) + r'\b'
                if re.search(pattern, text_lower):
                    text = re.sub(pattern, standard_term, text, flags=re.IGNORECASE)
        
        return text

    async def resolve_coreferences(self, text: str, context: Dict) -> str:
        """Simple coreference resolution"""
        
        if not context or not context.get('has_context'):
            return text
        
        last_entity = context.get('last_entity', 'adil')
        recent_topics = context.get('recent_topics', [])
        
        # Resolve pronouns
        if last_entity == 'adil':
            text = re.sub(r'\b(he|his|him)\b', 'Adil', text, flags=re.IGNORECASE)
        
        # Resolve context references
        if recent_topics and 'projects' in recent_topics:
            text = re.sub(r'\b(it|this|that)\b', 'Adil\'s projects', text, flags=re.IGNORECASE)
        
        return text

    def detect_language(self, text: str) -> str:
        """Simple language detection"""
        
        # Check for Urdu script
        urdu_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        total_chars = len(re.findall(r'\S', text))
        
        if total_chars > 0 and urdu_chars / total_chars > 0.3:
            return "ur"
        
        # Check for Urdu words
        urdu_words = ['aap', 'kya', 'hai', 'ke', 'mein', 'se']
        text_words = text.lower().split()
        urdu_count = sum(1 for word in text_words if word in urdu_words)
        
        if len(text_words) > 0 and urdu_count / len(text_words) > 0.2:
            return "ur"
        
        return "en"

    def extract_intent(self, text: str) -> Tuple[str, List[str]]:
        """Extract query intent"""
        
        text_lower = text.lower()
        
        intent_keywords = {
            'projects': ['project', 'work', 'build', 'app', 'development'],
            'skills': ['skill', 'programming', 'technology'],
            'education': ['education', 'degree', 'university', 'study'],
            'contact': ['contact', 'email', 'phone', 'linkedin', 'hire'],
            'about': ['who', 'about', 'background', 'bio'],
            'experience': ['experience', 'career', 'history', 'work']
        }
        
        # Score intents
        intent_scores = {}
        for intent, keywords in intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            primary_intent = max(intent_scores, key=intent_scores.get)
            return primary_intent, list(intent_scores.keys())
        
        return 'general', ['general']

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract portfolio entities"""
        
        entities = {
            'people': [],
            'technologies': [],
            'contacts': []
        }
        
        text_lower = text.lower()
        
        # People
        if re.search(r'\b(adil|saeed)\b', text_lower):
            entities['people'].append('adil')
        
        # Technologies
        tech_matches = re.findall(r'\b(python|javascript|ai|ml|react|django)\b', text_lower)
        entities['technologies'].extend(tech_matches)
        
        # Contact methods
        contact_matches = re.findall(r'\b(email|linkedin|github|phone)\b', text_lower)
        entities['contacts'].extend(contact_matches)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities

    def get_stats(self) -> Dict[str, Any]:
        """Get preprocessor statistics"""
        
        return {
            "correction_patterns": len(self.corrections),
            "concept_groups": len(self.concept_map),
            "supported_languages": ["en", "ur"],
            "features": [
                "portfolio_corrections",
                "concept_normalization", 
                "coreference_resolution",
                "language_detection",
                "intent_extraction"
            ]
        }
    
    #last code that run 