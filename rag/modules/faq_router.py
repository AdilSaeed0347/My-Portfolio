"""
FAQ Router Module - ADDITIVE ENHANCEMENT
Direct routing for common queries to ensure complete, accurate responses.

SAFETY:
- This is an OPTIONAL add-on layer
- Returns None if no FAQ match found → falls back to normal retrieval
- Can be disabled by not calling it
- Zero modification to existing retrieval logic
"""
import logging
import re
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class FAQRouter:
    """
    Direct routing for frequently asked questions.
    Ensures complete responses for common queries like "all certifications", "social media links", etc.

    CRITICAL: This is an ADD-ON LAYER. If no FAQ matches, returns None → normal pipeline continues.
    """

    def __init__(self):
        """Initialize FAQ patterns and response templates"""

        # FAQ patterns - detect common complete information queries
        self.faq_patterns = {
            'all_certifications': [
                r'all\s+(certifications?|certificates?|credentials?)',
                r'list\s+(of\s+)?(certifications?|certificates?)',
                r'what\s+(certifications?|certificates?)\s+does\s+adil\s+have',
                r'show\s+me\s+(all\s+)?(certifications?|certificates?)'
            ],
            'all_social_media': [
                r'all\s+social\s+media',
                r'social\s+media\s+(links?|accounts?|profiles?)',
                r'all\s+(links?|profiles?)',
                r'linkedin\s+and\s+github',
                r'social\s+(links?|profiles?|platforms?)'
            ],
            'all_contact': [
                r'(how\s+to\s+)?contact(\s+adil)?',
                r'(get\s+in\s+touch|reach\s+out)',
                r'email\s+and\s+social',
                r'contact\s+(information|details?|methods?)'
            ],
            'all_projects': [
                r'all\s+projects?',
                r'list\s+(of\s+)?projects?',
                r'what\s+projects?\s+(has\s+adil|did\s+adil)',
                r'show\s+me\s+(his\s+)?projects?'
            ],
            'all_skills': [
                r'all\s+skills?',
                r'technical\s+skills?',
                r'what\s+(programming\s+)?languages?',
                r'tech\s+stack',
                r'what\s+technologies'
            ],
            'education': [
                r'where\s+did\s+adil\s+study',
                r'what\s+university',
                r'education\s+(background|details?)',
                r'degree\s+(and\s+)?university'
            ],
            'who_is_adil': [
                r'who\s+is\s+adil',
                r'tell\s+me\s+about\s+adil',
                r'introduce\s+adil',
                r'what\s+does\s+adil\s+do'
            ],
            'gpa': [
                r'what.*gpa',
                r'gpa\s+(is|of\s+adil)',
                r'academic\s+performance'
            ],
            'giki_bootcamp': [
                r'giki\s+bootcamp',
                r'tell\s+me\s+about\s+giki',
                r'what\s+is\s+giki'
            ]
        }

        # Aggregation queries that need special retrieval
        self.aggregation_intents = {
            'all_certifications', 'all_social_media', 'all_contact',
            'all_projects', 'all_skills'
        }

    def route_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Check if query matches FAQ patterns and return routing decision.

        SAFETY:
        - Returns None if no match → normal pipeline continues
        - Returns routing info if match → caller can use it or ignore it
        - Non-invasive to existing flow

        Args:
            query: User's query

        Returns:
            None if no FAQ match, or {
                'faq_type': str,
                'is_aggregation': bool,
                'search_hints': List[str],
                'response_format': str
            }
        """
        query_lower = query.lower().strip()

        # Check each FAQ pattern
        for faq_type, patterns in self.faq_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    logger.info(f"✅ FAQ Match: {faq_type}")

                    return {
                        'faq_type': faq_type,
                        'is_aggregation': faq_type in self.aggregation_intents,
                        'search_hints': self._get_search_hints(faq_type),
                        'response_format': self._get_response_format(faq_type),
                        'confidence': 0.95
                    }

        # No FAQ match
        return None

    def _get_search_hints(self, faq_type: str) -> List[str]:
        """
        Get search query hints for comprehensive retrieval.

        Returns:
            List of search queries to execute for complete information
        """
        search_map = {
            'all_certifications': [
                'certifications certificates credentials training bootcamp',
                'deeplearning.ai andrew ng courses',
                'giki bootcamp llm machine learning',
                'google cloud platform fundamentals'
            ],
            'all_social_media': [
                'github linkedin facebook social media profiles',
                'adilsaeed047 networking contact online',
                'professional profiles links platforms'
            ],
            'all_contact': [
                'email adilsaeed047 contact information',
                'github linkedin facebook social profiles',
                'professional networking communication'
            ],
            'all_projects': [
                'projects portfolio development work built',
                'chatbot ocr sentiment analysis face recognition',
                'machine learning ai applications systems'
            ],
            'all_skills': [
                'programming languages python javascript java',
                'machine learning deep learning ai technologies',
                'web development html css frameworks tools'
            ],
            'education': [
                'university imsciences peshawar degree gpa',
                'islamia college diploma dit academic',
                'bachelor software engineering student'
            ],
            'who_is_adil': [
                'adil saeed software engineering student',
                'imsciences ai machine learning',
                'professional summary background profile'
            ],
            'gpa': [
                'gpa 3.6 academic performance grade',
                'imsciences university achievement merit'
            ],
            'giki_bootcamp': [
                'giki bootcamp machine learning llm',
                'ghulam ishaq khan training 2025',
                'advanced ai neural networks deep learning'
            ]
        }

        return search_map.get(faq_type, [query])

    def _get_response_format(self, faq_type: str) -> str:
        """
        Get response format instructions for LLM.

        Returns:
            Format instructions for this FAQ type
        """
        format_map = {
            'all_certifications': 'comprehensive_list',
            'all_social_media': 'links_with_platforms',
            'all_contact': 'contact_methods_list',
            'all_projects': 'projects_with_details',
            'all_skills': 'categorized_skills',
            'education': 'education_timeline',
            'who_is_adil': 'professional_bio',
            'gpa': 'factoid',
            'giki_bootcamp': 'program_details'
        }

        return format_map.get(faq_type, 'standard')

    def get_retrieval_strategy(self, faq_type: str) -> Dict[str, Any]:
        """
        Get optimized retrieval strategy for FAQ type.

        Returns:
            {
                'top_k': int,
                'score_threshold': float,
                'merge_strategy': str,
                'prioritize_complete_chunks': bool
            }
        """
        # Aggregation queries need more chunks
        if faq_type in self.aggregation_intents:
            return {
                'top_k': 15,  # Retrieve more for comprehensive coverage
                'score_threshold': 0.3,  # Lower threshold to get all relevant info
                'merge_strategy': 'union',  # Combine all results
                'prioritize_complete_chunks': True
            }

        # Factoid queries need precise chunks
        elif faq_type in ['gpa', 'education']:
            return {
                'top_k': 3,  # Few precise chunks
                'score_threshold': 0.6,  # High threshold for accuracy
                'merge_strategy': 'top_ranked',
                'prioritize_complete_chunks': True
            }

        # Default strategy
        else:
            return {
                'top_k': 8,
                'score_threshold': 0.4,
                'merge_strategy': 'hybrid',
                'prioritize_complete_chunks': True
            }


# Global instance for singleton pattern
_faq_router = None

def get_faq_router() -> FAQRouter:
    """Get or create global FAQRouter instance"""
    global _faq_router
    if _faq_router is None:
        _faq_router = FAQRouter()
        logger.info("FAQ Router initialized")
    return _faq_router
