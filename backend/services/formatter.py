"""
Fixed formatter addressing critical issues and adding image support
"""
import re
import logging
import json
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """Fixed formatter with critical issue resolution and image support"""
    
    def __init__(self):
        self.social_links = {
            'email': 'mailto:adilsaeed047@gmail.com',
            'github': 'https://github.com/AdilSaeed0347',
            'linkedin': 'https://www.linkedin.com/in/adil-saeed-9b7b51363/',
            'facebook': 'https://www.facebook.com/adil.saeed.9406'
        }
        
        # Image configuration
        self.images_dir = Path("rag/documents/images")
        self.image_metadata = self._load_image_metadata()

    def _load_image_metadata(self) -> List[Dict]:
        """Load image metadata for smart image matching"""
        try:
            metadata_file = self.images_dir.parent / "images_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load image metadata: {e}")
        
        # Fallback: scan images directory
        return self._create_fallback_metadata()

    def _create_fallback_metadata(self) -> List[Dict]:
        """Create fallback metadata by scanning images folder"""
        metadata = []
        if not self.images_dir.exists():
            return metadata
            
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        for img_file in self.images_dir.iterdir():
            if img_file.suffix.lower() in image_extensions:
                # Generate tags from filename
                name_parts = img_file.stem.lower().replace('_', ' ').replace('-', ' ').split()
                tags = [part for part in name_parts if len(part) > 2]
                
                metadata.append({
                    "file": img_file.name,
                    "tags": tags,
                    "caption": f"Image: {img_file.stem.replace('_', ' ').title()}",
                    "alt": f"Image related to {' '.join(tags)}"
                })
        
        return metadata

    def _detect_image_request(self, query: str) -> bool:
        """Detect if user is requesting images"""
        image_keywords = [
            'show me', 'picture', 'photo', 'image', 'pic', 'screenshot',
            'look like', 'appearance', 'face', 'portrait', 'visual'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in image_keywords)

    def _search_relevant_images(self, query: str, max_images: int = 2) -> List[Dict]:
        """Search for relevant images based on query"""
        if not self.image_metadata:
            return []
            
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_images = []
        
        for img in self.image_metadata:
            score = 0
            img_tags = [tag.lower() for tag in img.get('tags', [])]
            
            # Exact tag matches
            for tag in img_tags:
                if tag in query_lower:
                    score += 2
            
            # Word matches
            tag_words = set(' '.join(img_tags).split())
            word_matches = len(query_words.intersection(tag_words))
            score += word_matches
            
            if score > 0:
                scored_images.append((score, img))
        
        # Sort by score and return top results
        scored_images.sort(key=lambda x: x[0], reverse=True)
        return [img for _, img in scored_images[:max_images]]

    async def format_response(self, response_data: Dict[str, Any], language: str = "en") -> Dict[str, Any]:
        """Main formatting with critical fixes and image support"""
        
        try:
            answer = response_data.get("answer", "")
            query = response_data.get("original_query", "")
            
            if not answer:
                response_data["answer"] = self._get_default_response(language)
                response_data["images"] = []
                return response_data
            
            # CRITICAL FIX 1: Remove duplicate "Adil Saeed is" phrases
            answer = self._fix_duplicate_phrases(answer)
            
            # CRITICAL FIX 2: Determine response length based on query intent
            response_length = self._determine_response_length(query, answer)
            
            # CRITICAL FIX 3: Ensure response starts with key information
            answer = self._prioritize_key_information(answer, query)
            
            # CRITICAL FIX 4: Apply length control
            answer = self._apply_length_control(answer, response_length)
            
            # Clean and format
            cleaned_answer = self._clean_response(answer)
            linked_answer = self._add_links(cleaned_answer)
            final_answer = self._add_signature(linked_answer, language)
            
            # Image integration
            images = []
            if query and self._detect_image_request(query):
                images = self._search_relevant_images(query)
                if images:
                    # Add image context to response
                    final_answer = self._add_image_context(final_answer, images)
            
            response_data["answer"] = final_answer
            response_data["images"] = images
            response_data["response_length"] = response_length
            response_data["show_images_after_ms"] = 2500 if images else 0
            
            return response_data
            
        except Exception as e:
            logger.error(f"Formatting error: {e}")
            response_data["answer"] = self._get_fallback_response(language)
            response_data["images"] = []
            return response_data

    def _fix_duplicate_phrases(self, answer: str) -> str:
        """CRITICAL FIX: Remove duplicate 'Adil Saeed is' phrases"""
        
        # Fix the specific "Adil Saeed is Adil Saeed is" bug
        answer = re.sub(r'\bAdil Saeed is\s+Adil Saeed is\b', 'Adil Saeed is', answer, flags=re.IGNORECASE)
        
        # Fix other duplicate patterns
        answer = re.sub(r'\bAdil is\s+Adil is\b', 'Adil is', answer, flags=re.IGNORECASE)
        answer = re.sub(r'\bAdil Saeed\s+Adil Saeed\b', 'Adil Saeed', answer)
        
        # Remove redundant introductory phrases
        redundant_intros = [
            r'^Based on the context[,.]?\s*',
            r'^According to the information[,.]?\s*',
            r'^From the provided context[,.]?\s*',
            r'^The context shows that\s*',
            r'^Looking at the information[,.]?\s*'
        ]
        
        for pattern in redundant_intros:
            answer = re.sub(pattern, '', answer, flags=re.IGNORECASE)
        
        return answer.strip()

    def _determine_response_length(self, query: str, answer: str) -> str:
        """CRITICAL FIX: Smart response length determination"""
        if not query:
            return 'medium'
            
        query_lower = query.lower()
        
        # Short response indicators
        short_keywords = [
            'briefly', 'quick', 'short', 'just tell', 'simply',
            'who is', 'what is', 'when', 'where', 'which',
            'yes or no', 'name of', 'how many', 'how much'
        ]
        
        # Detailed response indicators  
        detailed_keywords = [
            'explain', 'describe', 'tell me about', 'elaborate',
            'detailed', 'comprehensive', 'thoroughly', 'in depth',
            'how does', 'why', 'process', 'methodology', 'all about'
        ]
        
        # Check for explicit length requests
        for keyword in detailed_keywords:
            if keyword in query_lower:
                return 'detailed'
                
        for keyword in short_keywords:
            if keyword in query_lower:
                return 'short'
        
        # Auto-determine based on query complexity
        word_count = len(query.split())
        if word_count > 10:
            return 'detailed'
        elif word_count < 4:
            return 'short'
        
        return 'medium'

    def _prioritize_key_information(self, answer: str, query: str) -> str:
        """CRITICAL FIX: Ensure response starts with key information"""
        
        if not query:
            return answer
            
        query_lower = query.lower()
        
        # Extract key information patterns
        key_patterns = {
            'contact': r'(email|adilsaeed047@gmail\.com|contact)',
            'education': r'(IMSciences|Institute of Management Sciences|university|degree)',
            'skills': r'(Python|JavaScript|programming|AI|machine learning)',
            'projects': r'(OCR|chatbot|sentiment analysis|face recognition)',
            'experience': r'(Microsoft|GIKI|internship|bootcamp)'
        }
        
        # Find what user is asking about
        query_intent = None
        for intent, pattern in key_patterns.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                query_intent = intent
                break
        
        if not query_intent:
            return answer
        
        # Extract relevant sentences and prioritize them
        sentences = self._split_sentences(answer)
        
        # Find sentences containing key information
        key_sentences = []
        other_sentences = []
        
        pattern = key_patterns[query_intent]
        for sentence in sentences:
            if re.search(pattern, sentence, re.IGNORECASE):
                key_sentences.append(sentence)
            else:
                other_sentences.append(sentence)
        
        # Reconstruct with key information first
        if key_sentences:
            return ' '.join(key_sentences + other_sentences)
        
        return answer

    def _apply_length_control(self, answer: str, response_length: str) -> str:
        """CRITICAL FIX: Apply proper length control"""
        
        sentences = self._split_sentences(answer)
        
        if response_length == 'short':
            # Keep only 1-2 most important sentences
            return '. '.join(sentences[:2]) + '.' if sentences else answer
            
        elif response_length == 'detailed':
            # Keep full response but ensure it's well-structured
            return answer
            
        else:  # medium
            # Keep 3-4 sentences for balanced response
            if len(sentences) > 4:
                return '. '.join(sentences[:4]) + '.'
            return answer

    def _split_sentences(self, text: str) -> List[str]:
        """Helper to split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _add_image_context(self, answer: str, images: List[Dict]) -> str:
        """Add context when images are included"""
        if not images:
            return answer
            
        if len(images) == 1:
            image_note = "\n\nHere's a relevant image for you:"
        else:
            image_note = f"\n\nHere are {len(images)} relevant images:"
            
        return answer + image_note

    def _clean_response(self, answer: str) -> str:
        """Clean response with existing logic"""
        
        # Keep existing cleaning but fix critical issues
        broken_contact_pattern = r'\*\*[^*]*\*\*[^[]*target="_blank"[^>]*>.*?(?=\n\n|\*\*|$)'
        answer = re.sub(broken_contact_pattern, '', answer, flags=re.DOTALL)
        
        answer = re.sub(r'target="_blank"[^>]*>', '', answer)
        answer = re.sub(r'rel="[^"]*"[^>]*>', '', answer)
        answer = re.sub(r'class="[^"]*"[^>]*>', '', answer)
        answer = re.sub(r'<[^>]+>', '', answer)
        
        # Remove raw URLs
        answer = re.sub(r'https?://[^\s]+', '', answer)
        answer = re.sub(r'www\.[^\s]+', '', answer)
        
        # Clean whitespace
        answer = re.sub(r'\n{3,}', '\n\n', answer)
        answer = re.sub(r'\s{3,}', ' ', answer)
        
        return answer.strip()

    def _add_links(self, answer: str) -> str:
        """Add links without duplicates - keep existing logic"""
        
        links_added = set()
        
        if 'email' in answer.lower() and 'Email' not in links_added:
            answer = re.sub(r'\b(email|adilsaeed047@gmail\.com)\b', 
                           '[Email]', answer, flags=re.IGNORECASE, count=1)
            links_added.add('Email')
        
        if 'linkedin' in answer.lower() and 'LinkedIn' not in links_added:
            answer = re.sub(r'\b(linkedin|linkedin profile)\b', 
                           '[LinkedIn]', answer, flags=re.IGNORECASE, count=1)
            links_added.add('LinkedIn')
        
        if 'github' in answer.lower() and 'GitHub' not in links_added:
            answer = re.sub(r'\b(github|github profile)\b', 
                           '[GitHub]', answer, flags=re.IGNORECASE, count=1)
            links_added.add('GitHub')
        
        return answer

    def _add_signature(self, answer: str, language: str) -> str:
        """Add clean signature"""
        signature = "\n📚 Adil_Data"
        return answer + signature

    def _get_default_response(self, language: str) -> str:
        """Default response"""
        return """You can ask about Adil Saeed:
- Projects and development work
- Technical skills and expertise  
- Contact information

📚 Adil_Data"""

    def _get_fallback_response(self, language: str) -> str:
        """Fallback response"""
        return """Technical issue occurred. Please try again.

📚 Adil_Data"""

    def format_multi_query_response(self, responses: List[Dict], language: str) -> str:
        """Multi-query formatting with fixes"""
        
        if not responses:
            return self._get_default_response(language)
        
        best_response = max(responses, key=lambda x: x.get("confidence", 0))
        
        # Apply all the same fixes
        processed_response = {
            "answer": best_response.get("answer", ""),
            "original_query": best_response.get("original_query", "")
        }
        
        formatted =  self.format_response(processed_response, language)
        return formatted.get("answer", self._get_default_response(language))