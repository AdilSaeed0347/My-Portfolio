# """
# Answer Validation Enhancement - OPTIONAL ADD-ON
# Validates LLM answers against source chunks (non-blocking).

# SAFETY GUARANTEE:
# - Only used when ENABLE_ANSWER_VALIDATION = True
# - NEVER blocks or modifies answers
# - Only logs warnings for low confidence
# - Operates as passive monitoring layer
# """
# import logging
# from typing import List, Dict, Set
# import re

# from config.rag_enhancements import VALIDATION_CONFIG

# logger = logging.getLogger(__name__)


# class AnswerValidator:
#     """
#     Optional answer validation layer.
#     Detects potential hallucinations and unsupported claims.

#     CRITICAL: This is a MONITORING tool only.
#     It NEVER blocks or modifies answers.
#     """

#     def __init__(self):
#         self.config = VALIDATION_CONFIG

#         # Stop words to exclude from validation
#         self.stop_words = {
#             'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
#             'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was',
#             'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
#             'do', 'does', 'did', 'will', 'would', 'could', 'should',
#             'may', 'might', 'can', 'this', 'that', 'these', 'those'
#         }

#     def validate(self, answer: str, source_chunks: List[str]) -> Dict:
#         """
#         Validate answer against source chunks.

#         SAFETY:
#         - Does NOT modify the answer
#         - Returns validation metrics only
#         - Intended for logging and monitoring

#         Args:
#             answer: Generated answer text
#             source_chunks: List of source chunk texts

#         Returns:
#             {
#                 'is_valid': bool,
#                 'confidence': float (0-1),
#                 'grounding_score': float (0-1),
#                 'unsupported_claims': List[str],
#                 'warnings': List[str]
#             }
#         """
#         if not self.config['enabled']:
#             # SAFETY: If disabled, return neutral validation
#             return {
#                 'is_valid': True,
#                 'confidence': 1.0,
#                 'grounding_score': 1.0,
#                 'unsupported_claims': [],
#                 'warnings': []
#             }

#         # Combine all source text
#         source_text = " ".join(source_chunks).lower()

#         # Extract claims from answer (split by sentences)
#         claims = self._extract_claims(answer)

#         # Check each claim against sources
#         unsupported = []
#         grounding_scores = []

#         for claim in claims:
#             score = self._check_claim_grounding(claim, source_text)
#             grounding_scores.append(score)

#             if score < 0.3:  # Less than 30% grounded
#                 unsupported.append(claim)

#         # Calculate overall metrics
#         avg_grounding = sum(grounding_scores) / len(grounding_scores) if grounding_scores else 0.5
#         confidence = 1.0 - (len(unsupported) / len(claims)) if claims else 0.5

#         # Generate warnings (non-blocking)
#         warnings = []
#         if confidence < self.config['min_confidence']:
#             warnings.append(f"Low confidence: {confidence:.2f}")

#         if len(unsupported) > 0:
#             warnings.append(f"{len(unsupported)}/{len(claims)} claims not well-grounded")

#         # Check for hallucination indicators
#         if self.config['check_hallucination']:
#             hallucination_warnings = self._detect_hallucinations(answer, source_text)
#             warnings.extend(hallucination_warnings)

#         is_valid = len(unsupported) == 0 and confidence >= self.config['min_confidence']

#         # SAFETY: Log but don't block
#         if not is_valid and self.config['log_low_confidence']:
#             logger.warning(f"Answer validation: confidence={confidence:.2f}, warnings={warnings}")

#         return {
#             'is_valid': is_valid,
#             'confidence': confidence,
#             'grounding_score': avg_grounding,
#             'unsupported_claims': unsupported,
#             'warnings': warnings
#         }

#     def _extract_claims(self, text: str) -> List[str]:
#         """
#         Extract individual claims from answer.

#         Args:
#             text: Answer text

#         Returns:
#             List of claim sentences
#         """
#         # Split by sentence markers
#         sentences = re.split(r'[.!?]+', text)

#         # Clean and filter
#         claims = [
#             s.strip()
#             for s in sentences
#             if s.strip() and len(s.strip()) > 10  # Ignore very short fragments
#         ]

#         return claims

#     def _check_claim_grounding(self, claim: str, source_text: str) -> float:
#         """
#         Check if claim is grounded in source text.

#         Args:
#             claim: Claim sentence
#             source_text: Combined source text (lowercase)

#         Returns:
#             float: Grounding score (0-1)
#         """
#         # Extract keywords from claim
#         claim_lower = claim.lower()
#         words = re.findall(r'\b\w+\b', claim_lower)

#         # Filter stop words
#         keywords = [w for w in words if w not in self.stop_words and len(w) > 3]

#         if not keywords:
#             return 0.5  # Neutral if no meaningful keywords

#         # Check how many keywords appear in source
#         found = sum(1 for kw in keywords if kw in source_text)

#         # Calculate coverage
#         coverage = found / len(keywords)

#         return coverage

#     def _detect_hallucinations(self, answer: str, source_text: str) -> List[str]:
#         """
#         Detect potential hallucination indicators.

#         Args:
#             answer: Generated answer
#             source_text: Source chunks text

#         Returns:
#             List of warning messages
#         """
#         warnings = []

#         # Check for hedging language (might indicate uncertainty)
#         hedging_patterns = [
#             'i think', 'i believe', 'probably', 'maybe', 'perhaps',
#             'might be', 'could be', 'seems like'
#         ]

#         answer_lower = answer.lower()
#         for pattern in hedging_patterns:
#             if pattern in answer_lower:
#                 warnings.append(f"Hedging language detected: '{pattern}'")
#                 break  # One warning is enough

#         # Check for specific numbers not in source
#         answer_numbers = set(re.findall(r'\b\d+\b', answer))
#         source_numbers = set(re.findall(r'\b\d+\b', source_text))

#         unsupported_numbers = answer_numbers - source_numbers
#         if unsupported_numbers:
#             warnings.append(f"Numbers not in source: {unsupported_numbers}")

#         # Check for proper nouns not in source
#         # (Capitalized words that might be names/places)
#         answer_proper_nouns = set(re.findall(r'\b[A-Z][a-z]+\b', answer))
#         source_proper_nouns = set(re.findall(r'\b[A-Z][a-z]+\b', " ".join(
#             [chunk.capitalize() for chunk in source_text.split('.')]
#         )))

#         unsupported_proper = answer_proper_nouns - source_proper_nouns - {'I', 'The', 'A', 'An'}
#         if len(unsupported_proper) > 2:  # Allow some flexibility
#             warnings.append(f"Proper nouns not clearly in source: {len(unsupported_proper)}")

#         return warnings


# # Global instance
# _validator = None

# def get_validator() -> AnswerValidator:
#     """Get or create global AnswerValidator instance"""
#     global _validator
#     if _validator is None:
#         _validator = AnswerValidator()
#     return _validator
