"""
Query Expansion Module - ADDITIVE ENHANCEMENT
Expands queries with synonyms and related terms for better retrieval recall.

SAFETY:
- This is an OPTIONAL add-on layer
- Original query is ALWAYS included in expansions
- Returns only original query if expansion fails
- Can be disabled by not calling it
"""
import logging
from typing import List, Set

logger = logging.getLogger(__name__)


class QueryExpander:
    """
    Expand user queries with synonyms and related terms.
    Improves retrieval recall by searching with multiple variations.

    CRITICAL: Original query is ALWAYS preserved. Expansions are additive only.
    """

    def __init__(self):
        """Initialize synonym mappings and expansion rules"""

        # Domain-specific synonym dictionary
        self.synonyms = {
            # Education terms
            'education': ['university', 'degree', 'academic', 'study', 'institution', 'school'],
            'university': ['institution', 'college', 'imsciences', 'academic'],
            'degree': ['bachelor', 'diploma', 'certification', 'credential'],
            'gpa': ['academic performance', 'grade', 'cgpa', 'marks'],

            # Skills terms
            'skills': ['technologies', 'expertise', 'proficiency', 'capabilities', 'abilities'],
            'programming': ['coding', 'development', 'software engineering'],
            'languages': ['technologies', 'programming languages', 'tech stack'],

            # Projects terms
            'projects': ['work', 'portfolio', 'applications', 'systems', 'implementations'],
            'built': ['developed', 'created', 'implemented', 'designed', 'engineered'],
            'chatbot': ['conversational ai', 'ai assistant', 'dialogue system'],

            # Contact terms
            'contact': ['reach', 'connect', 'get in touch', 'find', 'communicate'],
            'email': ['contact email', 'professional email', 'adilsaeed047'],
            'social media': ['linkedin', 'github', 'facebook', 'profiles', 'networking'],

            # Experience terms
            'experience': ['work experience', 'internship', 'job', 'career', 'professional background'],
            'internship': ['training', 'apprenticeship', 'work placement', 'bootcamp'],

            # AI/ML terms
            'ai': ['artificial intelligence', 'machine learning', 'deep learning', 'ml'],
            'machine learning': ['ml', 'ai', 'neural networks', 'deep learning'],
            'llm': ['large language models', 'language models', 'nlp', 'gpt'],

            # Personal terms
            'brother': ['asad ali', 'elder brother', 'family', 'sibling'],
            'mentor': ['inspiration', 'role model', 'guide', 'sir ali imran'],
            'friend': ['companion', 'colleague', 'peer']
        }

        # Entity variations
        self.entity_variations = {
            'adil': ['adil saeed', 'adeel', 'him', 'his'],
            'imsciences': ['institute of management sciences', 'ims', 'university'],
            'giki': ['ghulam ishaq khan institute', 'giki bootcamp', 'giki training'],
            'asad ali': ['elder brother', 'asad', 'brother'],
            'sir ali imran': ['ali imran sindhu', 'ali imran', 'mentor']
        }

        # Context-aware expansions
        self.context_expansions = {
            'what certifications': [
                'list all certifications',
                'certificates and credentials',
                'training programs completed'
            ],
            'social media': [
                'github linkedin facebook profiles',
                'professional networking accounts',
                'online presence and links'
            ],
            'projects': [
                'portfolio projects developed',
                'ai ml applications built',
                'technical implementations'
            ]
        }

    def expand_query(self, query: str, max_expansions: int = 3) -> List[str]:
        """
        Expand query with synonyms and related terms.

        SAFETY:
        - Original query is ALWAYS first in the list
        - If expansion fails, returns [original_query] only
        - Expansions are additive, never replace original

        Args:
            query: Original user query
            max_expansions: Maximum number of additional variations (default 3)

        Returns:
            List of query variations (original + expansions)
        """
        query_lower = query.lower().strip()

        # CRITICAL: Original query always included
        expanded_queries = [query]

        try:
            # Check for context-aware expansions first
            for context_pattern, expansions in self.context_expansions.items():
                if context_pattern in query_lower:
                    expanded_queries.extend(expansions[:max_expansions])
                    logger.info(f"Context expansion: {context_pattern} → {len(expansions)} variations")
                    return expanded_queries[:max_expansions + 1]

            # Synonym-based expansion
            words = query_lower.split()
            synonym_variations = set()

            for word in words:
                if word in self.synonyms:
                    # Create variations by substituting synonyms
                    for synonym in self.synonyms[word][:2]:  # Top 2 synonyms
                        variation = query_lower.replace(word, synonym)
                        if variation != query_lower:
                            synonym_variations.add(variation)

            # Add top variations
            expanded_queries.extend(list(synonym_variations)[:max_expansions])

            # Entity variation expansion
            for entity, variations in self.entity_variations.items():
                if entity in query_lower:
                    for variation in variations[:2]:
                        expanded_query = query_lower.replace(entity, variation)
                        if expanded_query not in expanded_queries:
                            expanded_queries.append(expanded_query)

            # Limit total expansions
            final_expansions = expanded_queries[:max_expansions + 1]

            logger.info(f"Query expanded: '{query}' → {len(final_expansions)} variations")
            return final_expansions

        except Exception as e:
            # SAFETY: On failure, return original query only
            logger.warning(f"Query expansion failed: {e}. Using original query.")
            return [query]

    def get_multi_angle_queries(self, query: str) -> List[str]:
        """
        Generate multi-angle queries for comprehensive retrieval.

        For complex queries, generates different perspectives:
        - What: factual information
        - How: process/implementation
        - Why: motivation/purpose

        Returns:
            List of queries from different angles
        """
        query_lower = query.lower().strip()
        angles = [query]  # Original always included

        try:
            # Skills query angles
            if any(term in query_lower for term in ['skills', 'technologies', 'programming']):
                angles.extend([
                    "technical skills programming languages frameworks",
                    "ai machine learning tools expertise",
                    "web development frontend backend technologies"
                ])

            # Projects query angles
            elif any(term in query_lower for term in ['projects', 'portfolio', 'built']):
                angles.extend([
                    "ai ml projects chatbot ocr systems",
                    "web development applications implementations",
                    "portfolio work technical projects"
                ])

            # Education query angles
            elif any(term in query_lower for term in ['education', 'university', 'study']):
                angles.extend([
                    "university degree imsciences peshawar gpa",
                    "academic background education institutions",
                    "software engineering bachelor degree"
                ])

            # Contact query angles
            elif any(term in query_lower for term in ['contact', 'reach', 'email']):
                angles.extend([
                    "email adilsaeed047 contact information",
                    "github linkedin facebook social profiles",
                    "professional networking communication"
                ])

            return angles[:5]  # Max 5 angles

        except Exception as e:
            logger.warning(f"Multi-angle generation failed: {e}")
            return [query]

    def expand_with_specificity_levels(self, query: str) -> List[str]:
        """
        Generate queries at different specificity levels.

        - Specific: exact terms
        - Moderate: with synonyms
        - Broad: general concepts

        Returns:
            List of queries from specific to broad
        """
        query_lower = query.lower().strip()

        # Level 1: Specific (original)
        specific = query

        # Level 2: Moderate (with synonyms)
        moderate = self.expand_query(query, max_expansions=1)

        # Level 3: Broad (conceptual)
        broad_map = {
            'certifications': 'professional training credentials achievements',
            'projects': 'technical work portfolio implementations',
            'skills': 'technical expertise capabilities proficiency',
            'education': 'academic background university degree',
            'contact': 'professional communication networking'
        }

        broad_query = query
        for key, broad_term in broad_map.items():
            if key in query_lower:
                broad_query = broad_term
                break

        # Combine all levels
        all_levels = [specific] + moderate[1:] + [broad_query]

        # Remove duplicates while preserving order
        seen = set()
        unique_levels = []
        for q in all_levels:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_levels.append(q)

        return unique_levels[:4]  # Max 4 levels


# Global instance
_query_expander = None

def get_query_expander() -> QueryExpander:
    """Get or create global QueryExpander instance"""
    global _query_expander
    if _query_expander is None:
        _query_expander = QueryExpander()
        logger.info("Query Expander initialized")
    return _query_expander
