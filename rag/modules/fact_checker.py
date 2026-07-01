"""
Fact Checker Module - ADDITIVE ENHANCEMENT
Post-processing layer to detect hallucinations and invented facts.

SAFETY:
- This is an OPTIONAL add-on layer
- Runs AFTER response generation
- Only flags suspicious content, never blocks responses
- Can be disabled by not calling it
"""
import logging
import re
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


class FactChecker:
    """
    Post-processing fact checker to detect potential hallucinations.
    Compares generated response against source chunks to flag invented information.

    CRITICAL: This is a MONITORING layer. It flags issues but doesn't block responses.
    """

    def __init__(self):
        """Initialize fact-checking rules and patterns"""

        # Known facts from Adil's portfolio (ground truth)
        self.ground_truth_facts = {
            # Education
            'university': 'imsciences',
            'institution_full': 'institute of management sciences',
            'gpa': '3.6',
            'degree': 'software engineering',
            'location': 'peshawar',

            # Contact
            'email': 'adilsaeed047@gmail.com',
            'github': 'github.com/adilsaeed047',

            # People
            'brother': 'asad ali',
            'mentor': 'sir ali imran',

            # Programs
            'bootcamp': 'giki',
            'bootcamp_full': 'giki ml → llm bootcamp 2025',

            # Key skills
            'primary_languages': ['python', 'java', 'javascript'],
            'ai_expertise': ['machine learning', 'deep learning', 'nlp', 'computer vision']
        }

        # Forbidden claims (things Adil does NOT have)
        self.forbidden_claims = [
            r'azure\s+certification',
            r'aws\s+certified',
            r'phd',
            r'doctorate',
            r'published\s+papers',
            r'professor',
            r'google\s+certification\s+(?!fundamentals)',  # He only has GCP fundamentals
            r'worked\s+at\s+microsoft',  # He's an ambassador, not employee
            r'stanford',
            r'mit',
            r'harvard',
            r'openai\s+employee'
        ]

        # Suspicious patterns that often indicate hallucination
        self.suspicious_patterns = [
            r'approximately\s+\d+\s+years',  # Vague experience claims
            r'over\s+\d+\s+projects',  # Exaggerated project counts
            r'expert\s+in\s+over\s+\d+',  # Inflated expertise claims
            r'certified\s+in\s+\d+',  # False certification claims
            r'published\s+\d+\s+papers'  # Academic paper claims
        ]

    def check_response(self, response: str, source_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check response for potential hallucinations.

        SAFETY:
        - Does NOT modify the response
        - Returns validation report only
        - Caller decides what to do with the report

        Args:
            response: Generated response text
            source_chunks: Retrieved chunks used for generation

        Returns:
            {
                'is_valid': bool,
                'confidence': float (0-1),
                'issues': List[str],
                'forbidden_claims': List[str],
                'unsupported_facts': List[str],
                'verdict': str
            }
        """
        response_lower = response.lower()

        # Extract source content
        source_text = ' '.join([chunk.get('content', '').lower() for chunk in source_chunks])

        issues = []
        forbidden_found = []
        unsupported_facts = []

        # Check 1: Forbidden claims
        for pattern in self.forbidden_claims:
            matches = re.findall(pattern, response_lower)
            if matches:
                forbidden_found.append(f"Forbidden claim: {pattern}")
                issues.append(f"⚠️ HALLUCINATION: Mentioned '{pattern}' which is not in portfolio")

        # Check 2: Suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, response_lower):
                issues.append(f"⚠️ SUSPICIOUS: Pattern '{pattern}' often indicates hallucination")

        # Check 3: Number verification
        unsupported_numbers = self._check_numbers(response, source_text)
        if unsupported_numbers:
            unsupported_facts.extend(unsupported_numbers)
            issues.append(f"⚠️ NUMBERS: {len(unsupported_numbers)} numbers not in source")

        # Check 4: Proper noun verification
        unsupported_entities = self._check_entities(response, source_text)
        if unsupported_entities:
            unsupported_facts.extend(unsupported_entities)
            issues.append(f"⚠️ ENTITIES: {len(unsupported_entities)} entities not in source")

        # Check 5: Fact grounding
        grounding_score = self._calculate_grounding(response, source_text)

        # Calculate confidence
        if forbidden_found:
            confidence = 0.2  # Very low if forbidden claims present
        elif len(issues) > 3:
            confidence = 0.5  # Low if many issues
        elif grounding_score < 0.6:
            confidence = 0.6  # Medium if poor grounding
        else:
            confidence = 0.9  # High if all checks pass

        # Verdict
        if forbidden_found:
            verdict = "HALLUCINATION_DETECTED"
        elif len(issues) > 2:
            verdict = "SUSPICIOUS"
        elif grounding_score < 0.7:
            verdict = "LOW_GROUNDING"
        else:
            verdict = "VALID"

        is_valid = verdict in ["VALID", "LOW_GROUNDING"]

        result = {
            'is_valid': is_valid,
            'confidence': confidence,
            'issues': issues,
            'forbidden_claims': forbidden_found,
            'unsupported_facts': unsupported_facts,
            'grounding_score': grounding_score,
            'verdict': verdict
        }

        # Log warnings for suspicious responses
        if not is_valid or len(issues) > 0:
            logger.warning(f"Fact check: {verdict} | Confidence: {confidence:.2f} | Issues: {len(issues)}")
            for issue in issues:
                logger.warning(f"  - {issue}")

        return result

    def _check_numbers(self, response: str, source_text: str) -> List[str]:
        """
        Check if numbers in response are supported by source.

        Returns:
            List of unsupported numbers with context
        """
        unsupported = []

        # Extract numbers from response
        response_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', response)

        for number in response_numbers:
            # Check if number exists in source
            if number not in source_text:
                # Get context around the number
                context_match = re.search(rf'.{{0,30}}{re.escape(number)}.{{0,30}}', response)
                context = context_match.group(0) if context_match else number

                unsupported.append(f"Number '{number}' in context: '{context}'")

        return unsupported

    def _check_entities(self, response: str, source_text: str) -> List[str]:
        """
        Check if proper nouns/entities in response are in source.

        Returns:
            List of unsupported entities
        """
        unsupported = []

        # Extract capitalized words (potential proper nouns)
        entities = re.findall(r'\b[A-Z][a-z]{2,}\b', response)

        # Common words to ignore
        ignore_words = {'Adil', 'He', 'His', 'The', 'A', 'An', 'I', 'You', 'This', 'That'}

        for entity in entities:
            if entity in ignore_words:
                continue

            # Check if entity (case-insensitive) is in source
            if entity.lower() not in source_text:
                unsupported.append(f"Entity: {entity}")

        return unsupported

    def _calculate_grounding(self, response: str, source_text: str) -> float:
        """
        Calculate how well the response is grounded in source text.

        Returns:
            float: Grounding score (0-1)
        """
        response_lower = response.lower()

        # Extract meaningful words from response
        response_words = re.findall(r'\b\w{4,}\b', response_lower)  # Words 4+ chars

        if not response_words:
            return 0.5

        # Count how many response words appear in source
        grounded_words = sum(1 for word in response_words if word in source_text)

        grounding_score = grounded_words / len(response_words)

        return grounding_score

    def validate_specific_fact(self, claim: str, fact_type: str) -> Tuple[bool, str]:
        """
        Validate specific fact claims against ground truth.

        Args:
            claim: The claim to validate (e.g., "3.8 GPA")
            fact_type: Type of fact (e.g., "gpa", "university", "email")

        Returns:
            (is_valid, message)
        """
        claim_lower = claim.lower()

        if fact_type == 'gpa':
            # Check if claimed GPA matches ground truth
            if '3.6' in claim_lower:
                return True, "✅ GPA claim is accurate (3.6)"
            else:
                return False, f"❌ GPA claim incorrect. Should be 3.6, not '{claim}'"

        elif fact_type == 'university':
            if 'imsciences' in claim_lower or 'institute of management sciences' in claim_lower:
                return True, "✅ University is correct (IMSciences)"
            else:
                return False, f"❌ University incorrect. Should be IMSciences, not '{claim}'"

        elif fact_type == 'email':
            if 'adilsaeed047@gmail.com' in claim_lower:
                return True, "✅ Email is correct"
            else:
                return False, f"❌ Email incorrect. Should be adilsaeed047@gmail.com, not '{claim}'"

        # Add more fact types as needed

        return True, "No specific validation for this fact type"

    def get_correction_suggestion(self, issue_type: str, incorrect_value: str) -> str:
        """
        Get correction suggestion for detected issue.

        Args:
            issue_type: Type of issue detected
            incorrect_value: The incorrect value found

        Returns:
            Suggested correction
        """
        corrections = {
            'azure certification': "Adil does NOT have Azure certification",
            'aws certified': "Adil does NOT have AWS certification",
            'phd': "Adil is an undergraduate student, not PhD",
            'worked at microsoft': "Adil is a Microsoft Learn Student Ambassador, not an employee"
        }

        for pattern, correction in corrections.items():
            if pattern in incorrect_value.lower():
                return correction

        return "Please verify this claim against the source documents"


# Global instance
_fact_checker = None

def get_fact_checker() -> FactChecker:
    """Get or create global FactChecker instance"""
    global _fact_checker
    if _fact_checker is None:
        _fact_checker = FactChecker()
        logger.info("Fact Checker initialized")
    return _fact_checker
