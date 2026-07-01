"""
Streamlined conversation memory for context resolution
Focuses on last 2-5 turns and entity tracking
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class ConversationMemory:
    """Lightweight memory for context resolution"""
    
    def __init__(self, max_turns: int = 5):
        self.sessions: Dict[str, Dict] = {}
        self.max_turns = max_turns
        self.entity_patterns = {
            'adil': [r'\badil\b', r'\byou\b', r'\byour\b', r'\bcreator\b'],
            'projects': [r'\bproject\b', r'\bapp\b', r'\bwork\b', r'\bdevelop\b'],
            'skills': [r'\bskill\b', r'\bprogramming\b', r'\btechnology\b'],
            'friends': [r'\bfriend\b', r'\bsaad\b', r'\brohail\b', r'\bdaud\b'],
            'education': [r'\beducation\b', r'\buniversity\b', r'\bstudy\b'],
            'contact': [r'\bcontact\b', r'\bemail\b', r'\bphone\b', r'\bhire\b']
        }

    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get context for coreference resolution"""
        
        if not session_id or session_id not in self.sessions:
            return {
                'has_context': False,
                'last_entity': None,
                'recent_topics': [],
                'conversation_count': 0
            }
        
        session = self.sessions[session_id]
        recent_turns = session.get('turns', [])[-self.max_turns:]
        
        # Extract last mentioned entity and topics
        last_entity = self._get_last_entity(recent_turns)
        recent_topics = self._get_recent_topics(recent_turns)
        
        return {
            'has_context': True,
            'last_entity': last_entity,
            'recent_topics': recent_topics,
            'conversation_count': len([t for t in recent_turns if t.get('role') == 'user']),
            'last_query': session.get('last_query', '')
        }

    def add_interaction(self, session_id: str, user_query: str, assistant_response: str):
        """Add interaction to memory"""
        
        if not session_id:
            return
        
        # Initialize session if new
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'turns': [],
                'created': datetime.now(),
                'last_updated': datetime.now()
            }
        
        session = self.sessions[session_id]
        
        # Add new turns
        session['turns'].extend([
            {'role': 'user', 'content': user_query, 'timestamp': datetime.now()},
            {'role': 'assistant', 'content': assistant_response, 'timestamp': datetime.now()}
        ])
        
        # Keep only recent turns
        session['turns'] = session['turns'][-self.max_turns * 2:]  # *2 for user+assistant pairs
        session['last_query'] = user_query
        session['last_updated'] = datetime.now()

    def _get_last_entity(self, turns: List[Dict]) -> Optional[str]:
        """Get the last mentioned entity for pronoun resolution"""
        
        # Look through recent user turns in reverse order
        user_turns = [t for t in turns if t.get('role') == 'user']
        
        for turn in reversed(user_turns):
            content = turn.get('content', '').lower()
            
            # Check for explicit entity mentions
            for entity, patterns in self.entity_patterns.items():
                if any(re.search(pattern, content) for pattern in patterns):
                    return entity
        
        # Default to 'adil' since it's his portfolio
        return 'adil'

    def _get_recent_topics(self, turns: List[Dict]) -> List[str]:
        """Get recent conversation topics"""
        
        topics = []
        user_turns = [t for t in turns if t.get('role') == 'user'][-3:]  # Last 3 user turns
        
        for turn in user_turns:
            content = turn.get('content', '').lower()
            
            for topic, patterns in self.entity_patterns.items():
                if any(re.search(pattern, content) for pattern in patterns):
                    if topic not in topics:
                        topics.append(topic)
        
        return topics

    def should_resolve_coreference(self, query: str) -> bool:
        """Check if query needs coreference resolution"""
        
        query_lower = query.lower()
        
        # Check for pronouns that need resolution
        pronouns = [r'\bhe\b', r'\bhis\b', r'\bhim\b', r'\bthat\b', r'\bthis\b', r'\bit\b']
        
        return any(re.search(pronoun, query_lower) for pronoun in pronouns)

    def resolve_coreferences(self, query: str, context: Dict) -> str:
        """Simple coreference resolution"""
        
        if not self.should_resolve_coreference(query) or not context.get('has_context'):
            return query
        
        resolved_query = query
        last_entity = context.get('last_entity', 'adil')
        
        # Resolve pronouns based on last entity
        if last_entity == 'adil':
            resolved_query = re.sub(r'\bhe\b', 'Adil', resolved_query, flags=re.IGNORECASE)
            resolved_query = re.sub(r'\bhis\b', "Adil's", resolved_query, flags=re.IGNORECASE)
            resolved_query = re.sub(r'\bhim\b', 'Adil', resolved_query, flags=re.IGNORECASE)
        
        # Resolve context-based references
        recent_topics = context.get('recent_topics', [])
        if recent_topics:
            main_topic = recent_topics[0]
            
            if main_topic in ['projects', 'skills', 'education']:
                resolved_query = re.sub(r'\bthat\b', f"Adil's {main_topic}", resolved_query, flags=re.IGNORECASE)
                resolved_query = re.sub(r'\bthis\b', f"Adil's {main_topic}", resolved_query, flags=re.IGNORECASE)
                resolved_query = re.sub(r'\bit\b', f"Adil's {main_topic}", resolved_query, flags=re.IGNORECASE)
        
        # Log resolution if changes were made
        if resolved_query != query:
            logger.info(f"Resolved: '{query}' → '{resolved_query}' (entity: {last_entity})")
        
        return resolved_query

    def update_conversation(self, session_id: str, conversation_history: List[Dict]):
        """Update conversation from external history"""
        
        if not session_id or not conversation_history:
            return
        
        # Take only recent turns
        recent_history = conversation_history[-self.max_turns:]
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'turns': [],
                'created': datetime.now(),
                'last_updated': datetime.now()
            }
        
        # Update session with recent history
        self.sessions[session_id]['turns'] = recent_history
        self.sessions[session_id]['last_updated'] = datetime.now()
        
        # Extract last user query
        user_turns = [t for t in recent_history if t.get('role') == 'user']
        if user_turns:
            self.sessions[session_id]['last_query'] = user_turns[-1].get('content', '')

    def cleanup_old_sessions(self, hours: int = 24) -> int:
        """Remove sessions older than specified hours"""
        
        cutoff = datetime.now() - timedelta(hours=hours)
        old_sessions = [
            sid for sid, session in self.sessions.items()
            if session.get('last_updated', datetime.min) < cutoff
        ]
        
        for session_id in old_sessions:
            del self.sessions[session_id]
        
        if old_sessions:
            logger.info(f"Cleaned {len(old_sessions)} old sessions")
        
        return len(old_sessions)

    def get_active_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        
        if not self.sessions:
            return {
                'active_sessions': 0,
                'total_turns': 0,
                'status': 'empty'
            }
        
        total_turns = sum(len(session.get('turns', [])) for session in self.sessions.values())
        
        # Analyze topics across sessions
        all_topics = []
        for session in self.sessions.values():
            turns = session.get('turns', [])
            topics = self._get_recent_topics(turns)
            all_topics.extend(topics)
        
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        return {
            'active_sessions': len(self.sessions),
            'total_turns': total_turns,
            'max_turns_per_session': self.max_turns,
            'popular_topics': topic_counts,
            'features': ['coreference_resolution', 'entity_tracking', 'topic_analysis']
        }

    def clear_session(self, session_id: str) -> bool:
        """Clear specific session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def clear_all_sessions(self) -> int:
        """Clear all sessions"""
        count = len(self.sessions)
        self.sessions.clear()
        return count
    #last code that run 