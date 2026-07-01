# """
# backend/services/user_context.py
# PRODUCTION-GRADE User Context Memory System
# Stores user session data in-memory for personalized interactions
# """
# import logging
# from typing import Dict, List, Optional, Any
# from datetime import datetime, timedelta
# from collections import defaultdict

# logger = logging.getLogger(__name__)

# class UserContextManager:
#     """
#     In-memory session manager for user context.
#     Stores user name, conversation history, and preferences per session.
#     """

#     def __init__(self, max_history: int = 5, session_timeout_minutes: int = 30):
#         """
#         Initialize user context manager.

#         Args:
#             max_history: Maximum number of interactions to store per session
#             session_timeout_minutes: Session expiry time in minutes
#         """
#         self.sessions: Dict[str, Dict[str, Any]] = {}
#         self.max_history = max_history
#         self.session_timeout = timedelta(minutes=session_timeout_minutes)

#         logger.info(f"UserContextManager initialized (max_history={max_history}, timeout={session_timeout_minutes}min)")

#     def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
#         """
#         Get existing session or create new one.

#         Args:
#             session_id: Unique session identifier

#         Returns:
#             Session data dictionary
#         """
#         # Clean expired sessions periodically
#         self._cleanup_expired_sessions()

#         if session_id not in self.sessions:
#             logger.info(f"Creating new session: {session_id}")
#             self.sessions[session_id] = {
#                 'user_name': None,
#                 'history': [],
#                 'metadata': {},
#                 'created_at': datetime.now(),
#                 'last_activity': datetime.now()
#             }
#         else:
#             # Update last activity
#             self.sessions[session_id]['last_activity'] = datetime.now()

#         return self.sessions[session_id]

#     def set_user_name(self, session_id: str, name: str):
#         """
#         Store user name for session.

#         Args:
#             session_id: Session identifier
#             name: User's name
#         """
#         session = self.get_or_create_session(session_id)
#         session['user_name'] = name
#         logger.info(f"Session {session_id}: User name set to '{name}'")

#     def get_user_name(self, session_id: str) -> Optional[str]:
#         """
#         Retrieve user name from session.

#         Args:
#             session_id: Session identifier

#         Returns:
#             User's name or None
#         """
#         if session_id in self.sessions:
#             return self.sessions[session_id].get('user_name')
#         return None

#     def add_interaction(self, session_id: str, query: str, response: str, metadata: Optional[Dict] = None):
#         """
#         Add interaction to session history.

#         Args:
#             session_id: Session identifier
#             query: User's query
#             response: Bot's response
#             metadata: Optional metadata (intent, confidence, etc.)
#         """
#         session = self.get_or_create_session(session_id)

#         interaction = {
#             'query': query,
#             'response': response,
#             'timestamp': datetime.now().isoformat(),
#             'metadata': metadata or {}
#         }

#         # Add to history with max limit
#         session['history'].append(interaction)
#         if len(session['history']) > self.max_history:
#             session['history'] = session['history'][-self.max_history:]

#         logger.debug(f"Session {session_id}: Added interaction (history size: {len(session['history'])})")

#     def get_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
#         """
#         Get conversation history for session.

#         Args:
#             session_id: Session identifier
#             limit: Optional limit on number of interactions

#         Returns:
#             List of interactions
#         """
#         if session_id not in self.sessions:
#             return []

#         history = self.sessions[session_id]['history']

#         if limit:
#             return history[-limit:]

#         return history

#     def get_context(self, session_id: str) -> Dict[str, Any]:
#         """
#         Get full context for session (name + recent history).

#         Args:
#             session_id: Session identifier

#         Returns:
#             Context dictionary with user_name and recent_queries
#         """
#         session = self.get_or_create_session(session_id)

#         return {
#             'user_name': session.get('user_name'),
#             'recent_queries': [
#                 {'query': h['query'], 'response': h['response']}
#                 for h in session['history'][-3:]  # Last 3 interactions
#             ],
#             'session_age_minutes': self._get_session_age_minutes(session_id)
#         }

#     def set_metadata(self, session_id: str, key: str, value: Any):
#         """
#         Store custom metadata for session.

#         Args:
#             session_id: Session identifier
#             key: Metadata key
#             value: Metadata value
#         """
#         session = self.get_or_create_session(session_id)
#         session['metadata'][key] = value
#         logger.debug(f"Session {session_id}: Metadata '{key}' set")

#     def get_metadata(self, session_id: str, key: str, default: Any = None) -> Any:
#         """
#         Retrieve custom metadata from session.

#         Args:
#             session_id: Session identifier
#             key: Metadata key
#             default: Default value if key not found

#         Returns:
#             Metadata value or default
#         """
#         if session_id in self.sessions:
#             return self.sessions[session_id]['metadata'].get(key, default)
#         return default

#     def clear_session(self, session_id: str):
#         """
#         Clear session data.

#         Args:
#             session_id: Session identifier
#         """
#         if session_id in self.sessions:
#             del self.sessions[session_id]
#             logger.info(f"Session {session_id} cleared")

#     def get_active_session_count(self) -> int:
#         """Get number of active sessions"""
#         return len(self.sessions)

#     def _get_session_age_minutes(self, session_id: str) -> int:
#         """Calculate session age in minutes"""
#         if session_id not in self.sessions:
#             return 0

#         created_at = self.sessions[session_id]['created_at']
#         age = datetime.now() - created_at
#         return int(age.total_seconds() / 60)

#     def _cleanup_expired_sessions(self):
#         """Remove expired sessions to prevent memory leak"""
#         expired_sessions = []

#         for session_id, session_data in self.sessions.items():
#             last_activity = session_data.get('last_activity', session_data['created_at'])
#             age = datetime.now() - last_activity

#             if age > self.session_timeout:
#                 expired_sessions.append(session_id)

#         for session_id in expired_sessions:
#             logger.info(f"Removing expired session: {session_id}")
#             del self.sessions[session_id]

#         if expired_sessions:
#             logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")


# # Global singleton instance
# _context_manager = None

# def get_context_manager() -> UserContextManager:
#     """Get global UserContextManager instance"""
#     global _context_manager
#     if _context_manager is None:
#         _context_manager = UserContextManager()
#     return _context_manager
