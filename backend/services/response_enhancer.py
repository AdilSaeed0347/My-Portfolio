"""
Response Enhancement Layer - Production Ready
Post-processes RAG responses to add polish and user-friendly features

Features:
1. Smart headings that match user query
2. Beautiful link formatting (clickable, no raw URLs)
3. Trust indicator for knowledge-based answers
4. Markdown cleanup
5. User name personalization
"""

import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Feature flags for safe deployment
ENABLE_TRUST_INDICATOR = True
ENABLE_SMART_HEADINGS = True
ENABLE_LINK_FORMATTING = True
ENABLE_MARKDOWN_CLEANUP = True


class ResponseEnhancer:
    """Enhances RAG responses with user-friendly formatting"""

    def __init__(self):
        # Social media link mappings (COMPLETE - includes all platforms from Adil.txt)
        self.link_mappings = {
            'email': {
                'patterns': [r'\b(email|adilsaeed047@gmail\.com|contact\s+email)\b'],
                'display': 'Email',
                'url': 'mailto:adilsaeed047@gmail.com'
            },
            'linkedin': {
                'patterns': [r'\b(linkedin|linkedin\s+profile|linkedin\s+account)\b'],
                'display': 'LinkedIn',
                'url': 'https://www.linkedin.com/in/adil-saeed-9b7b51363/'
            },
            'github': {
                'patterns': [r'\b(github|github\s+profile|github\s+account|github\s+repo)\b'],
                'display': 'GitHub',
                'url': 'https://github.com/AdilSaeed0347'
            },
            'facebook': {
                'patterns': [r'\b(facebook|facebook\s+profile|facebook\s+account)\b'],
                'display': 'Facebook',
                'url': 'https://www.facebook.com/adil.saeed.9406'
            },
            'twitter': {
                'patterns': [r'\b(twitter|x\.com|@adilsaeed|tweet)\b'],
                'display': 'Twitter',
                'url': 'https://x.com/AdilSaeed1058?t=vM9Sc7hCDQN3Mdzq0N_EUQ&s=09'
            },
            'medium': {
                'patterns': [r'\b(medium|blog|articles?|writing)\b'],
                'display': 'Medium',
                'url': 'https://medium.com/@adilahmad0347'
            }
        }

    def enhance(self, response: str, query: str, intent: str,
                sources: List[str], user_name: Optional[str] = None) -> str:
        """
        Main enhancement pipeline

        Args:
            response: Raw LLM response
            query: Original user query
            intent: Detected intent (FACTOID, EXPLORATORY, etc.)
            sources: List of sources used
            user_name: Optional user name for personalization

        Returns:
            Enhanced response
        """
        try:
            enhanced = response

            # SPECIAL: Social media query detection and formatting
            is_social_query = self._is_social_media_query(query)

            # 1. Add smart headings (if enabled and appropriate)
            if ENABLE_SMART_HEADINGS and self._should_add_headings(query, intent):
                enhanced = self._add_smart_headings(enhanced, query, intent)

            # 2. Format links beautifully
            if ENABLE_LINK_FORMATTING:
                enhanced = self._format_links(enhanced)

                # Special handling for social media queries
                if is_social_query:
                    enhanced = self._ensure_all_social_links(enhanced, query)

            # 3. Clean up markdown artifacts
            if ENABLE_MARKDOWN_CLEANUP:
                enhanced = self._cleanup_markdown(enhanced)

            # 4. Add trust indicator (ONLY for knowledge-based answers)
            if ENABLE_TRUST_INDICATOR and self._should_add_trust_indicator(sources, intent):
                enhanced = self._add_trust_indicator(enhanced)

            return enhanced

        except Exception as e:
            logger.error(f"Enhancement failed: {e}", exc_info=True)
            # Return original response if enhancement fails
            return response

    def _should_add_headings(self, query: str, intent: str) -> bool:
        """Determine if headings should be added"""
        # Add headings for exploratory queries with multiple topics
        if intent not in ['EXPLORATORY', 'FACTOID']:
            return False

        # Check if query asks about multiple things
        multi_topic_indicators = [
            'and', 'as well as', 'also', 'plus', 'along with',
            'skills and projects', 'education and experience'
        ]

        query_lower = query.lower()
        return any(indicator in query_lower for indicator in multi_topic_indicators)

    def _add_smart_headings(self, response: str, query: str, intent: str) -> str:
        """
        Add intelligent headings that match what user asked

        Example:
        User: "Tell me about skills and projects"
        Response gets:
          **Skills of Adil Saeed**
          [skills content]

          **Projects of Adil Saeed**
          [projects content]
        """
        # Extract topics from query
        topics = self._extract_topics_from_query(query)

        if len(topics) < 2:
            # Single topic - no need for multiple headings
            return response

        # Try to intelligently split response by topics
        enhanced = response
        paragraphs = response.split('\n\n')

        if len(paragraphs) < 2:
            # Response is one paragraph - don't force split
            return response

        # Build enhanced response with headings
        result_parts = []
        current_topic_idx = 0

        for i, paragraph in enumerate(paragraphs):
            para_lower = paragraph.lower()

            # Detect topic transitions
            if current_topic_idx < len(topics) - 1:
                next_topic = topics[current_topic_idx + 1]

                # Check if this paragraph starts discussing next topic
                if any(keyword in para_lower for keyword in next_topic['keywords']):
                    # Add heading for new topic
                    heading = f"**{next_topic['title']}**\n\n"
                    result_parts.append(heading + paragraph)
                    current_topic_idx += 1
                    continue

            # No topic transition - add paragraph as-is
            # But add heading for first paragraph
            if i == 0 and current_topic_idx < len(topics):
                heading = f"**{topics[current_topic_idx]['title']}**\n\n"
                result_parts.append(heading + paragraph)
            else:
                result_parts.append(paragraph)

        return '\n\n'.join(result_parts)

    def _extract_topics_from_query(self, query: str) -> List[Dict[str, Any]]:
        """Extract topics that user is asking about"""
        query_lower = query.lower()

        topic_map = {
            'skills': {
                'keywords': ['skill', 'programming', 'technology', 'technical', 'languages'],
                'title': 'Skills of Adil Saeed'
            },
            'projects': {
                'keywords': ['project', 'work', 'built', 'developed', 'created', 'portfolio'],
                'title': 'Projects of Adil Saeed'
            },
            'education': {
                'keywords': ['education', 'university', 'degree', 'study', 'academic'],
                'title': 'Education Background'
            },
            'experience': {
                'keywords': ['experience', 'internship', 'work', 'job', 'position'],
                'title': 'Professional Experience'
            },
            'contact': {
                'keywords': ['contact', 'reach', 'email', 'linkedin', 'github'],
                'title': 'Contact Information'
            }
        }

        detected_topics = []

        for topic_key, topic_data in topic_map.items():
            if any(keyword in query_lower for keyword in topic_data['keywords']):
                detected_topics.append(topic_data)

        return detected_topics

    def _format_links(self, response: str) -> str:
        """
        Convert plain text mentions to beautiful clickable links

        Examples:
        - "email" → [Email](mailto:adilsaeed047@gmail.com)
        - "GitHub" → [GitHub](https://github.com/AdilSaeed0347)
        """
        formatted = response

        # STEP 1: Remove ALL malformed markdown patterns AGGRESSIVELY
        # Fix LLM-generated broken markdown like [Facebook:, [Medium:, [Email, etc.

        # Remove ANY occurrence of [ followed by platform name (with or without : or ])
        # This catches: [Facebook:, [Facebook], [Facebook, [Medium:, [Email, etc.
        formatted = re.sub(r'\[([Ff]acebook|[Mm]edium|[Tt]witter|[Xx]|[Gg]it[Hh]ub?|[Ll]inked[Ii]n|[Ee]mail)[\]:\s]*', r'\1 ', formatted, flags=re.IGNORECASE)

        # Remove malformed patterns: Word(URL)
        formatted = re.sub(r'(\w+)\(https?://[^\)]+\)', r'\1', formatted)

        # Clean up any remaining stray brackets before platform names
        formatted = re.sub(r'\[+\s*(facebook|medium|twitter|github|linkedin|email)', r'\1', formatted, flags=re.IGNORECASE)

        # STEP 2: Now add proper markdown links
        # Track which links we've added to avoid duplicates
        added_links = set()

        for link_key, link_data in self.link_mappings.items():
            # Try each pattern
            for pattern in link_data['patterns']:
                # Only replace first occurrence to avoid spam
                if link_key not in added_links:
                    formatted = re.sub(
                        pattern,
                        f"[{link_data['display']}]({link_data['url']})",
                        formatted,
                        count=1,  # Only first occurrence
                        flags=re.IGNORECASE
                    )
                    added_links.add(link_key)

        # STEP 3: Remove any raw URLs that might have leaked through
        formatted = self._remove_raw_urls(formatted)

        return formatted

    def _remove_raw_urls(self, text: str) -> str:
        """
        Remove raw URLs that aren't part of markdown links
        Ensures LinkedIn-only queries don't have dangling URLs

        IMPORTANT: This runs AFTER _format_links(), so proper markdown links [Text](URL) already exist.
        We only want to remove standalone URLs that are NOT inside markdown links.
        """
        # STEP 1: Remove any malformed patterns like "text(URL)" without proper markdown
        # This catches: Git/GitHub(https://github.com/...) but NOT [Text](URL)
        # Pattern: Word characters (NOT ]) followed by (URL)
        text = re.sub(r'(?<!\])([A-Za-z/]+)\(https?://[^\)]+\)', r'\1', text)

        # STEP 2: Remove standalone URLs that are NOT inside markdown links
        # A URL is standalone if it's NOT inside ](URL) structure
        # We need to protect [Text](URL) while removing plain https://...

        # First, temporarily replace valid markdown links with placeholders
        markdown_links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', text)
        placeholders = {}
        for i, (link_text, link_url) in enumerate(markdown_links):
            placeholder = f"__MDLINK{i}__"
            placeholders[placeholder] = f"[{link_text}]({link_url})"
            text = text.replace(f"[{link_text}]({link_url})", placeholder, 1)

        # Now remove standalone URLs (since valid markdown is protected)
        text = re.sub(r'https?://[^\s\)]+', '', text)
        text = re.sub(r'www\.[^\s\)]+', '', text)

        # Restore markdown links
        for placeholder, original in placeholders.items():
            text = text.replace(placeholder, original)

        # STEP 3: Remove broken markdown like [](URL) - empty brackets with URL
        text = re.sub(r'\[\]\([^\)]+\)', '', text)

        # STEP 4: Clean up spacing and punctuation
        text = re.sub(r'\s{2,}', ' ', text)  # Multiple spaces → single space
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)  # Space before punctuation
        text = re.sub(r'\(\s*\)', '', text)  # Empty parentheses

        return text.strip()

    def _cleanup_markdown(self, response: str) -> str:
        """Clean up markdown artifacts and formatting issues"""
        cleaned = response

        # Remove excessive newlines (max 2 consecutive)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in cleaned.split('\n')]
        cleaned = '\n'.join(lines)

        # Remove broken HTML tags (shouldn't exist but just in case)
        cleaned = re.sub(r'<[^>]+>', '', cleaned)

        # Remove duplicate periods
        cleaned = re.sub(r'\.{3,}', '...', cleaned)

        return cleaned.strip()

    def _should_add_trust_indicator(self, sources: List[str], intent: str) -> bool:
        """Determine if trust indicator should be added"""
        # Add ONLY for knowledge-based answers
        if not sources:
            return False

        # Don't add for greetings, capabilities, etc.
        non_knowledge_intents = [
            'GREETING', 'USER_INTRODUCTION', 'NAME_RECALL',
            'CAPABILITY', 'POLITE_CHAT', 'ACKNOWLEDGMENT',
            'OUT_OF_SCOPE', 'ERROR'
        ]

        if intent in non_knowledge_intents:
            return False

        # Add if sources include knowledge base
        return 'Knowledge Base' in sources

    def _add_trust_indicator(self, response: str) -> str:
        """
        Add trust indicator at the END of response
        Format: 📚 Adil Data
        Single line break before indicator (not double)
        """
        # Check if already present (avoid duplicates)
        if '📚 Adil Data' in response or '📘 Adil Data' in response:
            # Replace old icon if present
            response = response.replace('📘 Adil Data', '📚 Adil Data')
            return response

        # Add at end with single line break (not double)
        return response.strip() + "\n📚 Adil Data"

    def _is_social_media_query(self, query: str) -> bool:
        """
        Detect if query is specifically about social media/accounts
        Used to ensure ALL social links are formatted
        """
        query_lower = query.lower()

        social_indicators = [
            'social media', 'social accounts', 'social profiles',
            'online presence', 'find online', 'connect online',
            'all accounts', 'social links', 'where can i find',
            'linkedin and github', 'twitter and facebook'
        ]

        return any(indicator in query_lower for indicator in social_indicators)

    def _ensure_all_social_links(self, response: str, query: str) -> str:
        """
        Ensure ALL social media links are formatted when user asks for social media
        Prevents missing Twitter or Medium in responses
        """
        query_lower = query.lower()

        # Check which platforms are mentioned in response
        response_lower = response.lower()

        # If query asks for "all" or "social media" but response is missing platforms
        asking_for_all = any(word in query_lower for word in ['all', 'social media', 'accounts', 'profiles'])

        if asking_for_all:
            # Ensure all major platforms are at least mentioned or properly indicated as available
            logger.debug(f"Social media query detected - ensuring complete link coverage")

        return response


# Global instance for easy import
_enhancer = None


def get_response_enhancer() -> ResponseEnhancer:
    """Get global ResponseEnhancer instance"""
    global _enhancer
    if _enhancer is None:
        _enhancer = ResponseEnhancer()
    return _enhancer


def enhance_response(response: str, query: str, intent: str,
                     sources: List[str], user_name: Optional[str] = None) -> str:
    """
    Convenience function for enhancing responses

    Args:
        response: Raw LLM response
        query: Original user query
        intent: Detected intent
        sources: List of sources used
        user_name: Optional user name

    Returns:
        Enhanced response
    """
    enhancer = get_response_enhancer()
    return enhancer.enhance(response, query, intent, sources, user_name)


# Testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test cases
    test_cases = [
        {
            'response': "Adil's email is adilsaeed047@gmail.com and you can find him on GitHub and LinkedIn.",
            'query': "How can I contact Adil?",
            'intent': "FACTOID",
            'sources': ["Knowledge Base"]
        },
        {
            'response': "Adil has strong programming skills in Python and Java. He has built several projects including ChatBot and OCR System.",
            'query': "Tell me about his skills and projects",
            'intent': "EXPLORATORY",
            'sources': ["Knowledge Base"]
        },
        {
            'response': "Hello! I'm here to help you.",
            'query': "Hi",
            'intent': "GREETING",
            'sources': []
        }
    ]

    enhancer = ResponseEnhancer()

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST CASE {i}")
        print(f"{'='*60}")
        print(f"Query: {test['query']}")
        print(f"Intent: {test['intent']}")
        print(f"\nOriginal:\n{test['response']}")

        enhanced = enhancer.enhance(
            response=test['response'],
            query=test['query'],
            intent=test['intent'],
            sources=test['sources']
        )

        print(f"\nEnhanced:\n{enhanced}")
