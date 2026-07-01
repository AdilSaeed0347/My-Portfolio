"""
Streamlined safety checker integrated with portfolio chatbot
Focused on essential security while maintaining user experience
"""
import re
import logging
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SafetyResult:
    is_safe: bool
    reason: str = ""
    confidence: float = 1.0
    suggestion: str = ""

class SafetyChecker:
    """Streamlined safety checker for Adil's portfolio chatbot"""
    
    def __init__(self):
        # Essential harmful patterns with word boundaries to avoid false positives
        self.harmful_patterns = [
            r'\bkill\b(?!\s*process)',  # "kill" but not "kill process"
            r'\bmurder\b', r'\bviolence\b', r'\battack\b(?!\s*vector)', 
            r'\bharm\b', r'\bdestroy\b',
            r'\bsex\b', r'\bporn\b', r'\bnude\b', r'\bexplicit\b', r'\badult\b',
            r'\bhate\b', r'\bracis[mt]\b', r'\bterroris[mt]\b', r'\bbomb\b', r'\bweapon\b',
            r'\bsuicide\b', r'\bself-harm\b', r'\bdrug\b', r'\billegal\b'
        ]
        
        # Simple spam detection
        self.spam_indicators = [
            r'(.)\1{8,}',  # 8+ repeated characters
            r'\b(free|buy|sell|click|visit|urgent|now)\b.*\b(link|website|discount)\b'
        ]

    def check_query(self, query: str) -> SafetyResult:
        """Main safety validation for user queries"""
        
        if not query or len(query.strip()) < 2:
            return SafetyResult(
                is_safe=False,
                reason="Please ask a specific question about Adil's portfolio.",
                confidence=1.0,
                suggestion="Try asking about his projects, skills, or contact information."
            )
        
        query_lower = query.lower().strip()
        
        # Length check
        if len(query) > 500:
            return SafetyResult(
                is_safe=False,
                reason="Please keep your question under 500 characters.",
                confidence=1.0,
                suggestion="Try breaking your question into smaller parts."
            )
        
        # Check for spam
        if self._is_spam(query_lower):
            return SafetyResult(
                is_safe=False,
                reason="Please ask a genuine question about Adil's portfolio.",
                confidence=0.9,
                suggestion="Ask about his projects, skills, education, or contact details."
            )
        
        # Check for harmful content with word boundaries
        harmful_result = self._check_harmful_content(query_lower)
        if not harmful_result.is_safe:
            return harmful_result
        
        # Basic injection detection
        if self._has_injection_attempt(query):
            return SafetyResult(
                is_safe=False,
                reason="Invalid input detected. Please ask a normal question.",
                confidence=1.0,
                suggestion="Ask about Adil's work, skills, or how to contact him."
            )
        
        return SafetyResult(is_safe=True)

    def _is_spam(self, query: str) -> bool:
        """Simple spam detection"""
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in self.spam_indicators)

    def _check_harmful_content(self, query: str) -> SafetyResult:
        """Check for harmful content using word boundaries"""
        
        # Check for harmful patterns with word boundaries
        for pattern in self.harmful_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return SafetyResult(
                    is_safe=False,
                    reason="I can only assist with professional questions about Adil's portfolio.",
                    confidence=0.95,
                    suggestion="Ask about his projects, technical skills, education, or contact information."
                )
        
        return SafetyResult(is_safe=True)

    def _has_injection_attempt(self, query: str) -> bool:
        """Simple injection detection"""
        injection_patterns = [
            r'<script|javascript:|eval\(',
            r'union\s+select|drop\s+table',
            r'insert\s+into|delete\s+from'
        ]
        
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in injection_patterns)

    def validate_session_id(self, session_id: str) -> bool:
        """Validate session ID format"""
        if not session_id or len(session_id) < 10:
            return False
        
        pattern = r'^session_\d+_[a-zA-Z0-9]+$'
        return bool(re.match(pattern, session_id))

    def sanitize_input(self, text: str) -> str:
        """Basic input sanitization"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()

    def get_safety_stats(self) -> Dict[str, Any]:
        """Get safety checker statistics"""
        return {
            "harmful_patterns_count": len(self.harmful_patterns),
            "spam_patterns_count": len(self.spam_indicators),
            "features": [
                "word_boundary_filtering",
                "spam_detection", 
                "injection_prevention",
                "technical_context_awareness"
            ],
            "status": "active"
        }
        
        
        #last code o run correctly 