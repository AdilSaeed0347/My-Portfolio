"""
Enhanced query splitter that properly handles multi-person queries
Separates questions about different people clearly
"""
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class QuerySplitter:
    """Enhanced splitter for multi-person and multi-intent queries"""
    
    def __init__(self):
        # Updated person detection patterns with better coverage
        self.person_patterns = {
            'adil': ['adil', 'saeed', 'adil saeed', 'creator', 'your'],
            'asad': ['asad', 'asad ali', 'brother'],
            'saad': ['saad', 'saad khan', 'saad ahmad'],
            'rohail': ['rohail'],
            'daud': ['daud', 'daud khan'],
            'umer': ['umer', 'umer khan'],
            'hasnain': ['hasnain']
        }
        
        # Enhanced split patterns
        self.split_patterns = [
            r'\band\s+who\s+is\b',     # "who is X and who is Y"
            r'\bwho\s+is\b.*?\band\b', # "who is X and Y"
            r'\band\s+tell\s+me\b',    # "tell me about X and tell me about Y"
            r'\band\s+what\s+about\b', # "what about X and what about Y"
            r'\band\s+what\s+is\b',    # "what is X and what is Y"
            r'\band\b',                # Simple "and" connector
            r'\balso\b',               # "also tell me"
            r'[,;]',                   # Comma/semicolon separators
        ]

    def split_query(self, query: str) -> List[Dict[str, str]]:
        """Split query into parts and detect person-specific queries"""
        
        if not query or len(query.strip()) < 10:
            return [{"query": query, "intent": self._detect_intent(query)}]
        
        try:
            # First check for multi-person queries
            people_mentioned = self._detect_people_in_query(query)
            
            if len(people_mentioned) > 1:
                # Split by people - this is the key improvement
                return self._split_by_people(query, people_mentioned)
            
            # Check for multi-topic queries about Adil
            if self._should_split_topics(query):
                return self._split_by_topics(query)
            
            # Single query - determine if it's about Adil or others
            detected_intent = self._detect_intent(query)
            result = {"query": query, "intent": detected_intent}
            
            # Add person context if asking about specific person
            if len(people_mentioned) == 1:
                result["person"] = people_mentioned[0]
            
            return [result]
            
        except Exception as e:
            logger.error(f"Query splitting error: {e}")
            return [{"query": query, "intent": "general"}]

    def _detect_people_in_query(self, query: str) -> List[str]:
        """Detect which people are mentioned in the query"""
        
        query_lower = query.lower()
        people_found = []
        
        # More precise detection
        for person, patterns in self.person_patterns.items():
            # Check for exact matches or word boundaries
            for pattern in patterns:
                if person == 'adil':
                    # For Adil, be more liberal with matching
                    if (pattern in query_lower or 
                        re.search(rf'\b{re.escape(pattern)}\b', query_lower)):
                        if person not in people_found:
                            people_found.append(person)
                        break
                else:
                    # For others, require exact word boundary matches
                    if re.search(rf'\b{re.escape(pattern)}\b', query_lower):
                        if person not in people_found:
                            people_found.append(person)
                        break
        
        return people_found

    def _split_by_people(self, query: str, people: List[str]) -> List[Dict[str, str]]:
        """Split query by different people mentioned"""
        
        result = []
        
        # Determine the main question type
        main_intent = self._detect_intent(query)
        
        # Create separate queries for each person
        for person in people:
            if person == 'adil':
                # For Adil, create comprehensive query
                person_query = self._create_adil_query(query, main_intent)
                result.append({
                    "query": person_query,
                    "intent": main_intent,
                    "person": person,
                    "priority": "high"  # Adil queries get priority
                })
            else:
                # For others, create query that will trigger "others" response
                person_query = self._create_others_query(query, person, main_intent)
                result.append({
                    "query": person_query,
                    "intent": "others_query",
                    "person": person,
                    "priority": "medium"
                })
        
        # Sort by priority (Adil first)
        result.sort(key=lambda x: x.get("priority", "low"), reverse=True)
        
        logger.info(f"Split by people: {[(r['person'], r['query'][:30]) for r in result]}")
        return result

    def _create_adil_query(self, original_query: str, intent: str) -> str:
        """Create a comprehensive query for Adil"""
        
        query_lower = original_query.lower()
        
        # Extract the essence of the question
        if 'who is' in query_lower:
            if 'qualification' in query_lower or 'education' in query_lower:
                return "Who is Adil Saeed and what is his educational background?"
            elif 'project' in query_lower:
                return "Who is Adil Saeed and what are his projects?"
            elif 'skill' in query_lower:
                return "Who is Adil Saeed and what are his skills?"
            else:
                return "Who is Adil Saeed?"
                
        elif 'tell me about' in query_lower or 'about' in query_lower:
            return "Tell me about Adil Saeed"
            
        elif 'education' in query_lower or 'qualification' in query_lower:
            return "What is Adil Saeed's educational background?"
            
        elif 'project' in query_lower:
            return "What are Adil Saeed's projects?"
            
        elif 'skill' in query_lower:
            return "What are Adil Saeed's technical skills?"
            
        elif 'contact' in query_lower:
            return "How to contact Adil Saeed?"
            
        else:
            return "Who is Adil Saeed?"

    def _create_others_query(self, original_query: str, person: str, intent: str) -> str:
        """Create query for non-Adil people"""
        
        person_name = person.replace('_', ' ').title()
        
        # Map person keys to proper names
        name_mapping = {
            'asad': 'Asad Ali',
            'saad': 'Saad Khan', 
            'daud': 'Daud Khan',
            'umer': 'Umer Khan',
            'rohail': 'Rohail',
            'hasnain': 'Hasnain'
        }
        
        proper_name = name_mapping.get(person, person_name)
        
        return f"Who is {proper_name}?"

    def _should_split_topics(self, query: str) -> bool:
        """Check if query should be split by topics (enhanced)"""
        
        query_lower = query.lower()
        
        # More comprehensive topic detection
        topics = [
            'project', 'skill', 'education', 'contact', 'experience', 
            'qualification', 'work', 'development', 'programming'
        ]
        
        topic_count = sum(1 for topic in topics if topic in query_lower)
        
        # Enhanced conjunction detection
        conjunctions = [
            'and', 'also', 'plus', 'additionally', 'furthermore',
            'what about', 'tell me about', 'along with'
        ]
        
        conjunction_count = sum(1 for conj in conjunctions if conj in query_lower)
        
        # Split if multiple topics AND conjunctions present
        return topic_count > 1 and conjunction_count > 0

    def _split_by_topics(self, query: str) -> List[Dict[str, str]]:
        """Split query by different topics (enhanced)"""
        
        # Try splitting on conjunctions
        for pattern in self.split_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                parts = re.split(pattern, query, flags=re.IGNORECASE)
                
                if len(parts) > 1:
                    cleaned_parts = []
                    
                    for part in parts:
                        part = part.strip()
                        if len(part) > 5:  # Skip very short parts
                            
                            # Ensure each part is a complete question
                            part_lower = part.lower()
                            
                            if not any(part_lower.startswith(word) for word in 
                                     ['what', 'who', 'tell', 'show', 'how', 'where', 'when']):
                                # Make it a complete question about Adil
                                if 'qualification' in part_lower or 'education' in part_lower:
                                    part = f"What are Adil's qualifications and {part}"
                                elif 'project' in part_lower:
                                    part = f"What are Adil's projects and {part}"
                                elif 'skill' in part_lower:
                                    part = f"What are Adil's skills and {part}"
                                else:
                                    part = f"Tell me about Adil's {part}"
                            
                            cleaned_parts.append({
                                "query": part,
                                "intent": self._detect_intent(part),
                                "person": "adil"
                            })
                    
                    if len(cleaned_parts) > 1:
                        logger.info(f"Split by topics: {[p['query'][:30] for p in cleaned_parts]}")
                        return cleaned_parts
        
        # If no splitting happened, return as single query
        return [{"query": query, "intent": self._detect_intent(query), "person": "adil"}]

    def _detect_intent(self, query: str) -> str:
        """Enhanced intent detection"""
        
        if not query:
            return "general"
        
        query_lower = query.lower()
        
        # More specific intent patterns
        intent_patterns = {
            "introduction": [
                r'\bwho\s+is\b', r'\babout\b', r'\bintroduce\b', 
                r'\btell\s+me\s+about\b', r'\bknow\s+about\b'
            ],
            "education": [
                r'\beducation\b', r'\bdegree\b', r'\buniversity\b', r'\bstudy\b',
                r'\bqualification\b', r'\bacademic\b', r'\blearning\b', r'\bbootcamp\b'
            ],
            "projects": [
                r'\bproject\b', r'\bdevelop\b', r'\bbuild\b', r'\bocr\b', 
                r'\bchatbot\b', r'\bapp\b', r'\bapplication\b', r'\bwork\s+on\b'
            ],
            "skills": [
                r'\bskill\b', r'\bpython\b', r'\bjavascript\b', r'\bprogramming\b',
                r'\btechnology\b', r'\bexpertise\b', r'\bknowledge\b', r'\btools\b'
            ],
            "contact": [
                r'\bcontact\b', r'\bemail\b', r'\bphone\b', r'\breach\b',
                r'\bhire\b', r'\bconnect\b', r'\bget\s+in\s+touch\b'
            ],
            "experience": [
                r'\bexperience\b', r'\binternship\b', r'\bwork\b', r'\bjob\b',
                r'\bcareer\b', r'\bprofessional\b', r'\bbackground\b'
            ]
        }
        
        # Check patterns in order of specificity
        for intent, patterns in intent_patterns.items():
            if any(re.search(pattern, query_lower) for pattern in patterns):
                return intent
        
        # Default based on question words
        if any(word in query_lower for word in ['who', 'about']):
            return "introduction"
        elif any(word in query_lower for word in ['what', 'tell']):
            return "general"
        
        return "general"

    def get_query_metadata(self, query: str) -> Dict[str, Any]:
        """Get metadata about the query for debugging"""
        
        people = self._detect_people_in_query(query)
        intent = self._detect_intent(query)
        should_split = self._should_split_topics(query)
        
        return {
            "original_query": query,
            "people_mentioned": people,
            "detected_intent": intent,
            "should_split_topics": should_split,
            "query_length": len(query),
            "complexity": "multi_person" if len(people) > 1 else "single" if not should_split else "multi_topic"
        }
    
    #last code that run 