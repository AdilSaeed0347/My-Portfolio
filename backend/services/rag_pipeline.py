# """
# backend/services/pipeline.py
# Unified RAG Pipeline — single source of truth.
# """

# import re
# import random
# import logging
# import time
# from datetime import datetime, timedelta
# from typing import Dict, List, Any, Optional

# from groq import AsyncGroq
# from config.settings import settings
# from services.retriever import UltraPreciseRetriever
# from services.formatter import ResponseFormatter
# from services.memory import ConversationMemory

# logger = logging.getLogger(__name__)

# # ---------------------------------------------------------------------------
# # MODULE-LEVEL CONSTANTS
# # ---------------------------------------------------------------------------

# _PERSPECTIVE_RULES = """
# PERSPECTIVE RULES (CRITICAL):
# - You are AdilChat, a portfolio assistant answering ABOUT Adil Saeed, NOT Adil himself.
# - ALWAYS use third person: "he", "his", "him", "Adil", "Adil's".
# - NEVER use first person: "I", "my", "me", "mine".
# - NEVER use second person when referring to Adil: "you", "your".

# SCOPE:
# - ONLY answer questions about Adil Saeed's portfolio.
# - If asked about anyone else → "I only have information about Adil Saeed."
# - If asked about unrelated topics → redirect politely.
# """

# _FORMATTING_RULES = """
# FORMATTING RULES:
# - Use **bold** ONLY for section headings when genuinely needed.
# - NO markdown headers (###, ##, #).
# - Bullet points for lists — max 5 items.
# - Plain sentences with natural flow for everything else.
# - Max 1-2 emojis per response.
# - For contact/social links: write platform names as plain text only
#   (e.g. "LinkedIn, GitHub, Facebook") — the system auto-converts to clickable links.
# """

# # FIX 7: Increased EXPLORATORY max_tokens from 320 → 500
# # so multi-topic queries ("skills AND projects") aren't truncated.
# _RETRIEVAL_CONFIG: Dict[str, Dict] = {
#     "FACTOID": {
#         "k": 6,
#         "score_threshold": 0.20,
#         "max_tokens": 150,
#     },
#     "VERIFICATION": {
#         "k": 7,
#         "score_threshold": 0.18,
#         "max_tokens": 250,
#     },
#     "EXPLORATORY": {
#         "k": 10,
#         "score_threshold": 0.15,
#         "max_tokens": 500,   # was 320 — too short for multi-topic answers
#     },
# }

# _TOPIC_ENHANCEMENTS: Dict[str, str] = {
#     "education": (
#         "adil saeed education academic university college degree bachelor diploma "
#         "imsciences institute management sciences peshawar mandani islamia charsadda "
#         "software engineering 2023 2027"
#     ),
#     "projects": (
#         "adil saeed projects portfolio built developed created giki prospectus chatbot "
#         "sentiment analysis face recognition cardioDiagnosis heart disease ocr text "
#         "recognition crop yield student attendance mlops ai ml"
#     ),
#     "skills": (
#         "adil saeed skills programming languages python java javascript html css sql "
#         "tensorflow pytorch scikit-learn keras numpy pandas opencv faiss huggingface "
#         "machine learning deep learning nlp computer vision"
#     ),
#     "experience": (
#         "adil saeed experience internship work job mlsa microsoft learn student "
#         "ambassadors ai ml lead giki intern project summer 2025"
#     ),
#     "contact": (
#         "adil saeed contact email linkedin github facebook medium social media "
#         "adilsaeed047 gmail professional networking"
#     ),
#     "personal": (
#         "adil saeed personal family brother asad ali elder mentor friends hasnain "
#         "saad khan rohail umer daud islamia college peshawar sir ali imran sindhu giki"
#     ),
#     "research": (
#         "adil saeed research paper publication article blog writing medium"
#     ),
# }


# # ---------------------------------------------------------------------------
# # INTENT CLASSIFIER
# # ---------------------------------------------------------------------------

# class _IntentClassifier:

#     _GREETING_KW = {
#         "hi", "hello", "hey", "greetings", "good morning",
#         "good afternoon", "good evening", "sup", "yo", "howdy", "hola",
#         "salam", "assalam",
#     }

#     _GREETING_BLOCKERS = {
#         "project", "skill", "experience", "internship", "expertise",
#         "education", "university", "college", "technologies", "framework",
#         "learning", "giki", "machine", "deep", "friend", "brother",
#         "contact", "email", "linkedin", "github", "list", "tell",
#         "who", "what", "where", "when", "which", "describe", "explain",
#         "work", "training", "diploma",
#     }

#     _POLITE_CHAT = {
#         "how are you", "how r u", "how are u", "how r you",
#         "whats up", "what's up", "how do you do",
#     }

#     # FIX 5: Removed "how do you" from CAPABILITY_KW — it was
#     # intercepting "how do you think is asad good for adil" and similar
#     # portfolio-relevant questions, routing them to capability handler.
#     _CAPABILITY_KW = {
#         "what can you do", "what do you do", "how can you help",
#         "what are you", "who are you",
#         "what is this chatbot", "tell me about yourself",
#         "your capabilities", "what information do you have",
#     }

#     _ACKNOWLEDGMENT_PHRASES = {
#         "thank you", "thanks", "thank", "ok thank",
#         "got it", "okay", "ok", "alright", "sure",
#         "appreciate it", "grateful", "cool", "nice",
#     }

#     _CLARIFICATION_KW = {
#         "i ask about", "i mean", "no i want", "not that",
#         "i said", "why you", "you give me",
#         "mix-up", "wrong", "that's not", "i meant",
#         "i was asking", "confused", "clarify",
#     }

#     _VERIFICATION_KW = {
#         "prove", "show", "demonstrate", "evidence", "verify",
#         "how do i know", "is it true", "proof",
#         "credentials", "certification", "certificate", "qualification",
#         "can adil prove", "is adil really",
#     }

#     _EXPLORATORY_KW = {
#         "tell me about", "overview", "background", "describe",
#         "explain", "everything about", "all about", "summary",
#         "introduction", "what does", "comprehensive", "who is", "who are",
#         "tell me everything", "give me details",
#     }

#     # FIX 5 (cont): Added "hire" keyword to experience topic so
#     # "why hire adil" routes to RAG retrieval, not chatbot-meta.
#     _TOPIC_KW: Dict[str, List[str]] = {
#         "education":   ["university", "degree", "study", "academic", "education",
#                         "school", "college", "course", "imsciences", "islamia",
#                         "mandani", "diploma", "gpa", "grade"],
#         "projects":    ["project", "built", "developed", "created", "portfolio",
#                         "application", "system", "ocr", "chatbot", "mlops",
#                         "work on", "docker", "tool"],
#         "skills":      ["skill", "technology", "programming", "language", "framework",
#                         "tool", "expertise", "proficient", "machine", "learning", "ai",
#                         "python", "java", "tensorflow"],
#         "experience":  ["experience", "job", "internship", "career",
#                         "position", "role", "employment", "giki", "mlsa", "microsoft",
#                         "hire", "hiring", "why hire", "instead of", "better than",
#                         "proven", "prove"],
#         "contact":     ["contact", "email", "phone", "reach", "linkedin",
#                         "github", "social", "connect", "facebook", "medium", "twitter"],
#         "personal":    ["family", "father", "mother", "brother", "sister",
#                         "friend", "personal", "hasnain", "saad", "rohail",
#                         "umer", "daud", "asad", "mentor"],
#         "research":    ["research", "paper", "publication", "article",
#                         "writing", "blog", "published"],
#     }

#     _NAME_PATTERNS = [
#         re.compile(r"\b(?:i\s*am|i\'m|my\s+name\s+is|call\s+me)\s+([a-zA-Z]+)", re.I),
#         re.compile(r"\b([a-zA-Z]+)\s+(?:here|speaking)\b", re.I),
#     ]

#     _NAME_RECALL_PATTERNS = [
#         re.compile(r"\bmy\s+name\b", re.I),
#         re.compile(r"\bwho\s+(?:am\s+)?i\b", re.I),
#         re.compile(r"\bwhat.*my\s+name", re.I),
#         re.compile(r"\bremember\s+me\b", re.I),
#     ]

#     _FAKE_NAMES = {"am", "is", "are", "be", "here", "there", "a", "an", "the"}

#     def classify(self, query: str, session_context: Optional[Dict] = None) -> Dict[str, Any]:
#         if not query or not query.strip():
#             return self._resp("INVALID", False)

#         # FIX 6: assign q ONCE here, remove duplicate assignment below
#         q = query.lower().strip()

#         # Gibberish detection
#         words = q.split()
#         real_words = [w for w in words if len(w) > 2 and w.isalpha()]
#         if len(words) >= 1 and len(real_words) == 0 and len(q) < 20:
#             return self._resp("INVALID", False)

#         # Priority order: most specific first

#         if any(p in q for p in self._POLITE_CHAT):
#             return self._resp("POLITE_CHAT", False)

#         if any(k in q for k in self._CLARIFICATION_KW):
#             return self._resp("CLARIFICATION", True, topic=self._detect_topic(q),
#                               retrieval_type=self._retrieval_type(q))

#         if len(q) <= 30 and any(p in q for p in self._ACKNOWLEDGMENT_PHRASES):
#             return self._resp("ACKNOWLEDGMENT", False)

#         name = self._extract_name(query)
#         if name and self._valid_introduction(q, name):
#             return self._resp("USER_INTRODUCTION", False, user_name=name)

#         # FIX 5: capability check now uses full phrases, not partial words
#         if any(k in q for k in self._CAPABILITY_KW):
#             return self._resp("CAPABILITY", False)

#         if self._is_greeting(q):
#             return self._resp("GREETING", False)

#         if session_context and any(p.search(q) for p in self._NAME_RECALL_PATTERNS):
#             return self._resp("NAME_RECALL", False)

#         topic = self._detect_topic(q)
#         rt = self._retrieval_type(q)
#         return self._resp(rt, True, topic=topic, retrieval_type=rt)

#     def _is_greeting(self, q: str) -> bool:
#         if any(b in q for b in self._GREETING_BLOCKERS):
#             return False
#         words = set(q.split())
#         if len(words) <= 3 and words & self._GREETING_KW:
#             return True
#         return any(q.startswith(kw) for kw in self._GREETING_KW)

#     def _valid_introduction(self, q: str, name: str) -> bool:
#         if any(w in q for w in ("friend", "know", "met")):
#             return False
#         if re.search(r"\bwho\s+(is|are)\s+", q):
#             return False
#         return any(k in q for k in ("i am", "i'm", "my name is", "call me"))

#     def _extract_name(self, query: str) -> Optional[str]:
#         for pat in self._NAME_PATTERNS:
#             m = pat.search(query)
#             if m:
#                 name = m.group(1)
#                 if name and len(name) > 1 and name.isalpha() and name.lower() not in self._FAKE_NAMES:
#                     return name.capitalize()
#         return None

#     def _detect_topic(self, q: str) -> Optional[str]:
#         for topic, kws in self._TOPIC_KW.items():
#             if any(kw in q for kw in kws):
#                 return topic
#         return None

#     def _retrieval_type(self, q: str) -> str:
#         if any(k in q for k in self._VERIFICATION_KW):
#             return "VERIFICATION"
#         if any(k in q for k in self._EXPLORATORY_KW):
#             return "EXPLORATORY"
#         return "FACTOID"

#     def _resp(self, intent: str, needs_retrieval: bool,
#               user_name: Optional[str] = None,
#               topic: Optional[str] = None,
#               retrieval_type: str = "FACTOID") -> Dict[str, Any]:
#         return {
#             "intent": intent,
#             "needs_retrieval": needs_retrieval,
#             "user_name": user_name,
#             "topic": topic,
#             "retrieval_type": retrieval_type,
#         }


# # ---------------------------------------------------------------------------
# # SESSION MEMORY
# # ---------------------------------------------------------------------------

# class _SessionMemory:
#     def __init__(self, max_history: int = 5, timeout_minutes: int = 30):
#         self._sessions: Dict[str, Dict] = {}
#         self._max_history = max_history
#         self._timeout = timedelta(minutes=timeout_minutes)

#     def get_context(self, session_id: str) -> Dict:
#         s = self._get_or_create(session_id)
#         return {
#             "user_name":         s.get("user_name"),
#             "has_history":       s["count"] > 0,
#             "interaction_count": s["count"],
#             "greeted":           s.get("greeted", False),
#             "last_topic":        self._get_last_topic(s),
#         }

#     def set_user_name(self, session_id: str, name: str):
#         self._get_or_create(session_id)["user_name"] = name

#     def mark_greeted(self, session_id: str):
#         self._get_or_create(session_id)["greeted"] = True

#     def set_last_topic(self, session_id: str, topic: str, entities: List[str] = None):
#         s = self._get_or_create(session_id)
#         s["last_topic"] = {
#             "topic":     topic,
#             "entities":  entities or [],
#             "timestamp": datetime.now(),
#         }

#     def add_interaction(self, session_id: str, query: str, answer: str, intent: str):
#         s = self._get_or_create(session_id)
#         s["interactions"].append({"query": query, "answer": answer, "intent": intent})
#         if len(s["interactions"]) > self._max_history:
#             s["interactions"] = s["interactions"][-self._max_history:]
#         s["count"] += 1

#     def _get_or_create(self, session_id: str) -> Dict:
#         self._cleanup()
#         if session_id not in self._sessions:
#             self._sessions[session_id] = {
#                 "user_name":    None,
#                 "interactions": [],
#                 "greeted":      False,
#                 "count":        0,
#                 "last_topic":   None,
#                 "created_at":   datetime.now(),
#                 "last_active":  datetime.now(),
#             }
#         else:
#             self._sessions[session_id]["last_active"] = datetime.now()
#         return self._sessions[session_id]

#     def _get_last_topic(self, session: Dict) -> Optional[Dict]:
#         lt = session.get("last_topic")
#         if not lt:
#             return None
#         age = (datetime.now() - lt["timestamp"]).total_seconds()
#         return lt if age < 300 else None

#     def _cleanup(self):
#         expired = [
#             sid for sid, s in self._sessions.items()
#             if (datetime.now() - s["last_active"]) > self._timeout
#         ]
#         for sid in expired:
#             del self._sessions[sid]


# # ---------------------------------------------------------------------------
# # MAIN RAG PIPELINE
# # ---------------------------------------------------------------------------

# class RAGPipeline:

#     def __init__(self):
#         self.retriever   = UltraPreciseRetriever()
#         self.groq_client: Optional[AsyncGroq] = None
#         self.formatter   = ResponseFormatter()
#         self.memory      = ConversationMemory()
#         self._session    = _SessionMemory()
#         self._classifier = _IntentClassifier()
#         self.initialized = False

#     async def initialize(self):
#         try:
#             self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
#             await self.retriever.initialize()
#             self.initialized = True
#             logger.info("RAGPipeline initialised successfully")
#         except Exception as exc:
#             logger.error(f"RAGPipeline initialisation failed: {exc}")
#             raise

#     async def refresh_data(self) -> bool:
#         try:
#             await self.retriever.initialize()
#             return True
#         except Exception as exc:
#             logger.error(f"Refresh failed: {exc}")
#             return False

#     # -------------------------------------------------------------------------
#     # PUBLIC ENTRY POINT
#     # FIX 1: Removed the nested async def process_query() that was defined
#     # inside process_query() — this caused IndentationError at startup.
#     # The short/empty guard is now correctly placed at the top of the method.
#     # -------------------------------------------------------------------------

#     async def process_query(
#         self,
#         query:                str,
#         language:             str = "en",
#         session_id:           str = "default",
#         conversation_history: List = None,
#         user_context:         Dict = None,
#     ) -> Dict[str, Any]:

#         if not self.initialized:
#             raise RuntimeError("Pipeline not initialised — call initialize() first")

#         # Short / empty query guard (Fix 1 — now correctly placed)
#         stripped = query.strip() if query else ""
#         if len(stripped) < 2:
#             fallback = {
#                 "answer": (
#                     "It looks like your message was too short. "
#                     "Feel free to ask about Adil's projects, skills, education, or experience!"
#                 ),
#                 "sources":    [],
#                 "query_type": "invalid_input",
#                 "confidence": 0.95,
#                 "original_query": query or "",
#             }
#             return await self.formatter.format_response(fallback, language)

#         start = time.time()

#         try:
#             ctx    = self._session.get_context(session_id)
#             intent = self._classifier.classify(query, ctx)
#             raw    = await self._route(query, intent, ctx, session_id)

#             raw["original_query"] = query

#             result = await self.formatter.format_response(raw, language)
#             result["processing_time"] = round((time.time() - start) * 1000, 1)

#             self._session.add_interaction(
#                 session_id, query,
#                 result.get("answer", ""),
#                 intent["intent"],
#             )

#             return result

#         except Exception as exc:
#             logger.error(f"process_query error: {exc}", exc_info=True)
#             fallback = {
#                 "answer":         "I'm having a technical issue. Please try again.",
#                 "sources":        [],
#                 "query_type":     "error",
#                 "confidence":     0.0,
#                 "original_query": query,
#             }
#             return await self.formatter.format_response(fallback, language)

#     # -------------------------------------------------------------------------
#     # ROUTER
#     # FIX 2: Removed duplicate GREETING handler. Each intent appears once.
#     # -------------------------------------------------------------------------

#     async def _route(
#         self,
#         query:      str,
#         intent:     Dict[str, Any],
#         ctx:        Dict[str, Any],
#         session_id: str,
#     ) -> Dict[str, Any]:

#         code = intent["intent"]

#         if code == "GREETING":
#             return self._handle_greeting(ctx, session_id)

#         if code == "INVALID":
#             return {
#                 "answer": (
#                     "That didn't quite make sense to me — could you rephrase? "
#                     "I'm here to help with questions about Adil's projects, "
#                     "skills, education, or experience."
#                 ),
#                 "sources":    [],
#                 "query_type": "invalid",
#                 "confidence": 0.95,
#             }

#         if code == "POLITE_CHAT":
#             return self._handle_polite_chat(ctx)

#         if code == "ACKNOWLEDGMENT":
#             return self._handle_acknowledgment(ctx)

#         if code == "CAPABILITY":
#             return self._handle_capability(ctx)

#         if code == "USER_INTRODUCTION":
#             name = intent.get("user_name", "")
#             self._session.set_user_name(session_id, name)
#             return self._handle_user_introduction(name)

#         if code == "NAME_RECALL":
#             return self._handle_name_recall(ctx)

#         if self._is_general_knowledge(query):
#             return await self._handle_general(query)

#         if self._is_chatbot_meta(query):
#             return await self._handle_chatbot_meta(query)

#         if code == "CLARIFICATION":
#             resp = await self._handle_knowledge(query, intent, ctx, session_id)
#             if resp.get("answer"):
#                 resp["answer"] = "Apologies for the confusion. " + resp["answer"]
#             return resp

#         return await self._handle_knowledge(query, intent, ctx, session_id)

#     # -------------------------------------------------------------------------
#     # CONVERSATIONAL HANDLERS
#     # -------------------------------------------------------------------------

#     def _handle_greeting(self, ctx: Dict, session_id: str) -> Dict[str, Any]:
#         name    = ctx.get("user_name")
#         greeted = ctx.get("greeted", False)

#         if name:
#             text = f"Hello {name}! How can I help you today?"
#         elif not greeted:
#             text = (
#                 "Hello! I'm AdilChat, Adil Saeed's AI portfolio assistant. "
#                 "Ask me about his projects, skills, education, experience, "
#                 "or how to contact him. What would you like to know?"
#             )
#             self._session.mark_greeted(session_id)
#         else:
#             text = "Hi again! What would you like to know about Adil?"

#         return {"answer": text, "sources": [], "query_type": "greeting", "confidence": 0.95}

#     def _handle_polite_chat(self, ctx: Dict) -> Dict[str, Any]:
#         name = ctx.get("user_name")
#         tail = f", {name}!" if name else "!"
#         return {
#             "answer":     f"Doing great, thanks for asking{tail} What can I help you with today?",
#             "sources":    [],
#             "query_type": "polite_chat",
#             "confidence": 0.95,
#         }

#     def _handle_acknowledgment(self, ctx: Dict) -> Dict[str, Any]:
#         name = ctx.get("user_name")
#         tail = f", {name}" if name else ""
#         phrases = [
#             f"You're welcome{tail}! Feel free to ask anything else about Adil.",
#             f"Happy to help{tail}! Is there anything else you'd like to know?",
#             f"Of course{tail}! Let me know if you have more questions about Adil's work.",
#         ]
#         return {
#             "answer":     random.choice(phrases),
#             "sources":    [],
#             "query_type": "acknowledgment",
#             "confidence": 0.95,
#         }

#     def _handle_capability(self, ctx: Dict) -> Dict[str, Any]:
#         name  = ctx.get("user_name")
#         intro = f"Happy to help, {name}!" if name else "Here's what I can do:"
#         text  = (
#             f"{intro}\n\n"
#             "I'm AdilChat — Adil Saeed's AI portfolio assistant. Ask me about:\n\n"
#             "**Projects** — AI/ML apps, OCR, RAG systems, and more\n"
#             "**Skills** — Python, TensorFlow, NLP, Computer Vision, and others\n"
#             "**Education** — IMSciences, GIKI Bootcamp, certifications\n"
#             "**Experience** — internships, MLSA leadership, conference roles\n"
#             "**Contact** — email, LinkedIn, GitHub, and social profiles\n\n"
#             "What would you like to explore?"
#         )
#         return {"answer": text, "sources": [], "query_type": "capability", "confidence": 0.95}

#     def _handle_user_introduction(self, name: str) -> Dict[str, Any]:
#         return {
#             "answer": (
#                 f"Nice to meet you, {name}! I'm AdilChat. "
#                 "Feel free to ask me anything about Adil Saeed's portfolio — "
#                 "projects, skills, education, or how to reach him."
#             ),
#             "sources":    [],
#             "query_type": "user_introduction",
#             "confidence": 0.95,
#         }

#     def _handle_name_recall(self, ctx: Dict) -> Dict[str, Any]:
#         name = ctx.get("user_name")
#         text = (
#             f"Your name is {name}. How else can I help?"
#             if name
#             else "I don't have your name yet — feel free to introduce yourself!"
#         )
#         return {"answer": text, "sources": [], "query_type": "name_recall", "confidence": 0.95}

#     # -------------------------------------------------------------------------
#     # GENERAL KNOWLEDGE HANDLER
#     # -------------------------------------------------------------------------

#     @staticmethod
#     def _is_general_knowledge(query: str) -> bool:
#         q = query.lower()
#         if re.search(r"\d+\s*[\+\-\*\/]\s*\d+", q):
#             return True
#         general_pats = [
#             r"capital of", r"weather in", r"temperature in",
#             r"president of", r"prime minister of",
#             r"how to (make|cook|bake)", r"population of",
#             r"currency of", r"recipe for",
#         ]
#         is_general = any(re.search(p, q) for p in general_pats)
#         about_adil = any(t in q for t in ("adil", "his", "him", "portfolio"))
#         return is_general and not about_adil

#     @staticmethod
#     def _is_chatbot_meta(query: str) -> bool:
#         q = query.lower()
#         # FIX 3: Removed broad patterns like "who are you" that could catch
#         # "who are adil's friends" — now requires more specific phrasing.
#         patterns = [
#             r"who (created|made|built) you",
#             r"what (is|are) you",
#             r"are you an? (ai|bot|chatbot|assistant)",
#             r"your (name|purpose|function)",
#             r"what is your name",
#             r"you an? (ai|bot)",
#         ]
#         return any(re.search(p, q) for p in patterns)

#     async def _handle_general(self, query: str) -> Dict[str, Any]:
#         m = re.search(r"(\d+)\s*([\+\-\*\/])\s*(\d+)", query)
#         if m:
#             try:
#                 result = eval(m.group(0))
#                 return {
#                     "answer":     f"The result is **{result}**.",
#                     "sources":    [],
#                     "query_type": "math",
#                     "confidence": 0.99,
#                 }
#             except Exception:
#                 pass

#         try:
#             resp = await self.groq_client.chat.completions.create(
#                 model=settings.GROQ_MODEL_EN,
#                 messages=[
#                     {"role": "system", "content": "Answer the question briefly and accurately in one sentence."},
#                     {"role": "user",   "content": query},
#                 ],
#                 temperature=0.1,
#                 max_tokens=80,
#             )
#             return {
#                 "answer":     resp.choices[0].message.content.strip(),
#                 "sources":    [],
#                 "query_type": "general",
#                 "confidence": 0.80,
#             }
#         except Exception as exc:
#             logger.error(f"General query LLM error: {exc}")
#             return {
#                 "answer":     "I specialise in Adil Saeed's portfolio. Ask about his projects, skills, or experience!",
#                 "sources":    [],
#                 "query_type": "redirect",
#                 "confidence": 0.70,
#             }

#     async def _handle_chatbot_meta(self, query: str) -> Dict[str, Any]:
#         return {
#             "answer": (
#                 "I'm AdilChat, an AI assistant created by Adil Saeed to help people "
#                 "learn about his professional background. I can tell you about his "
#                 "projects, skills, education, experience, and how to contact him!"
#             ),
#             "sources":    [],
#             "query_type": "chatbot_meta",
#             "confidence": 0.95,
#         }

#     # -------------------------------------------------------------------------
#     # KNOWLEDGE / RAG HANDLER
#     # -------------------------------------------------------------------------

#     async def _handle_knowledge(
#         self,
#         query:      str,
#         intent:     Dict[str, Any],
#         ctx:        Dict[str, Any],
#         session_id: str,
#     ) -> Dict[str, Any]:

#         topic          = intent.get("topic")
#         retrieval_type = intent.get("retrieval_type", "FACTOID")
#         cfg            = _RETRIEVAL_CONFIG[retrieval_type]

#         norm_query     = self._normalise(query)
#         enhanced_query = self._enhance_query(norm_query, query, topic, ctx)

#         logger.info(f"RAG | type={retrieval_type} k={cfg['k']} thresh={cfg['score_threshold']} topic={topic}")

#         docs = await self._retrieve(enhanced_query, cfg)

#         if not docs:
#             logger.warning("Primary retrieval empty — emergency fallback")
#             docs = await self._emergency_retrieve(enhanced_query)

#         if not docs:
#             return self._no_info_response(topic)

#         max_score = max(d.get("retrieval_score", 0) for d in docs)
#         if max_score < 0.12:
#             return {
#                 "answer": (
#                     "I don't have verified information about that specific detail. "
#                     "You can ask about Adil's education, projects, skills, experience, "
#                     "or contact information."
#                 ),
#                 "sources":    [],
#                 "query_type": "low_confidence",
#                 "confidence": 0.35,
#             }

#         answer = await self._generate(query, docs, retrieval_type, topic, ctx)

#         if topic:
#             self._session.set_last_topic(session_id, topic)

#         confidence = self._confidence(max_score, len(docs))

#         return {
#             "answer":     answer,
#             "sources":    ["📚 Adil_Data"],
#             "query_type": f"{topic or 'portfolio'}_{retrieval_type.lower()}",
#             "confidence": confidence,
#         }

#     # -------------------------------------------------------------------------
#     # RETRIEVAL HELPERS
#     # -------------------------------------------------------------------------

#     @staticmethod
#     def _normalise(query: str) -> str:
#         fixes = {
#             "adeel":      "adil",
#             "contct":     "contact",
#             "porjects":   "projects",
#             "skils":      "skills",
#             "eduction":   "education",
#             "experiance": "experience",
#             "mobil":      "mobile",
#             "phon":       "phone",
#             "socila":     "social",
#             "mdeia":      "media",
#             "acounts":    "accounts",
#             "instent":    "instead",   # seen in logs: "instent of other"
#             "insted":     "instead",
#         }
#         q = query.lower().strip()
#         for wrong, right in fixes.items():
#             q = q.replace(wrong, right)
#         return q

#     @staticmethod
#     def _enhance_query(norm_query: str, original_query: str, topic: Optional[str], ctx: Dict) -> str:
#         q = norm_query

#         if "friend" in q:
#             return (
#                 "adil saeed friends peer network hasnain saad khan rohail umer khan "
#                 "daud khan islamia college peshawar medical students law fellow classmates"
#             )

#         if any(t in q for t in ("social media", "social accounts", "all accounts", "online presence")):
#             return (
#                 "adil saeed social media accounts linkedin github facebook twitter "
#                 "medium professional networking contact information online"
#             )

#         # FIX 3: "why hire adil" / "instead of other" queries get
#         # both experience AND skills context for a strong answer.
#         if any(t in q for t in ("hire", "instead of", "better than", "why adil")):
#             return (
#                 "adil saeed why hire strengths achievements projects skills experience "
#                 "gpa certifications leadership workshops ambassador giki imsciences"
#             )

#         base = original_query
#         if topic and topic in _TOPIC_ENHANCEMENTS:
#             base = f"{original_query} {_TOPIC_ENHANCEMENTS[topic]}"

#         last_topic = ctx.get("last_topic")
#         if last_topic and RAGPipeline._is_follow_up(original_query):
#             entities = last_topic.get("entities", [])
#             if entities:
#                 base = f"{base} {' '.join(entities)}"

#         return base

#     @staticmethod
#     def _is_follow_up(query: str) -> bool:
#         indicators = {
#             "first one", "second one", "third one", "last one",
#             "first", "second", "third", "last",
#             "tell me more", "more about", "more details", "more info",
#             "what about that", "about that one", "the one",
#             "it", "that", "them", "those",
#         }
#         q = query.lower()
#         if len(query.split()) <= 5:
#             return any(i in q for i in indicators)
#         return False

#     async def _retrieve(self, query: str, cfg: Dict) -> List[Dict]:
#         try:
#             raw = await self.retriever.hybrid_retrieve(query=query, top_k=cfg["k"])
#         except Exception as exc:
#             logger.error(f"Retrieval error: {exc}")
#             return []

#         seen:   set  = set()
#         result: List = []
#         for doc in raw:
#             doc_id = doc.get("id", "")
#             score  = doc.get("retrieval_score", 0)
#             if doc_id not in seen and score >= cfg["score_threshold"]:
#                 seen.add(doc_id)
#                 result.append(doc)

#         return sorted(result, key=lambda d: d.get("retrieval_score", 0), reverse=True)

#     async def _emergency_retrieve(self, query: str) -> List[Dict]:
#         try:
#             raw  = await self.retriever.hybrid_retrieve(query=query, top_k=15)
#             docs = [d for d in raw if d.get("retrieval_score", 0) >= 0.08]
#             return sorted(docs, key=lambda d: d.get("retrieval_score", 0), reverse=True)
#         except Exception as exc:
#             logger.error(f"Emergency retrieval error: {exc}")
#             return []

#     # -------------------------------------------------------------------------
#     # RESPONSE GENERATION
#     # FIX 4: Added explicit instruction to extract specific details from context
#     # so "bootcamp training" answers use actual data, not LLM guesses.
#     # -------------------------------------------------------------------------

#     async def _generate(
#         self,
#         query:          str,
#         docs:           List[Dict],
#         retrieval_type: str,
#         topic:          Optional[str],
#         ctx:            Dict,
#     ) -> str:

#         cfg = _RETRIEVAL_CONFIG[retrieval_type]

#         ctx_limit = {"FACTOID": 2, "VERIFICATION": 4, "EXPLORATORY": 6}
#         chunks    = docs[:ctx_limit.get(retrieval_type, 4)]
#         context   = "\n\n".join(d.get("content", "") for d in chunks)
#         num_chunks = len(chunks)

#         emoji = {
#             "contact":    "📧",
#             "skills":     "🛠️",
#             "projects":   "💻",
#             "education":  "🎓",
#             "experience": "💼",
#             "personal":   "👤",
#             "research":   "📄",
#         }.get(topic or "", "📋")

#         ctx_note = (
#             f"You have {num_chunks} context chunks below. "
#             "Extract specific facts, names, tools, technologies, and dates "
#             "directly from the context. NEVER guess or say 'likely'. "
#             "If a detail is in the context, state it. If it is not, say so briefly."
#         )

#         base_rules = f"""
# You are an AI assistant answering questions based on Adil Saeed's portfolio.

# Rules:
# - Only answer using the provided context.
# - If the query is unclear, irrelevant, or gibberish, politely ask the user to rephrase.
# - If the query is outside the portfolio, say you don't have that information
#   and guide the user to ask about projects, skills, education, or experience.
# - Do NOT force an answer from unrelated context.
# - Keep responses clear, helpful, and natural (not repetitive).
# Tone: Friendly, concise, and human-like.

# {_PERSPECTIVE_RULES}
# {_FORMATTING_RULES}

# {ctx_note}
# """

#         if retrieval_type == "FACTOID":
#             system = base_rules + f"""
# RULES:
# 1. Answer ONLY the specific question — no extra biography.
# 2. Maximum 2-3 sentences.
# 3. Start with {emoji} if relevant.
# 4. Third person only (he/his/him)."""

#         elif retrieval_type == "VERIFICATION":
#             system = base_rules + f"""
# RULES:
# 1. Provide the factual answer with specific evidence from context.
# 2. Name exact credentials, institutions, technologies, or achievements.
# 3. Be confident and precise.
# 4. Third person only (he/his/him)."""

#         else:  # EXPLORATORY
#             system = base_rules + f"""
# RULES:
# 1. Start with {emoji} and a clear, relevant heading.
# 2. Use bullet points for lists — pull real names and details from context.
# 3. If the query asks about multiple topics (e.g. skills AND projects),
#    address each separately with specific extracted details.
# 4. Be comprehensive but concise — no padding, no filler sentences.
# 5. Third person only (he/his/him).
# 6. NEVER start with "Adil Saeed is…" — use a heading instead."""

#         user_name = ctx.get("user_name")
#         name_note = f"User's name: {user_name}\n" if user_name else ""
#         user_msg  = (
#             f"{name_note}Query: {query}\n\n"
#             f"Context:\n{context}\n\n"
#             "Answer using only the context above. "
#             "Extract specific details — do not summarise vaguely."
#         )

#         try:
#             resp = await self.groq_client.chat.completions.create(
#                 model=settings.GROQ_MODEL_EN,
#                 messages=[
#                     {"role": "system", "content": system},
#                     {"role": "user",   "content": user_msg},
#                 ],
#                 temperature=0.1,
#                 max_tokens=cfg["max_tokens"],
#             )
#             answer = resp.choices[0].message.content.strip()

#             if retrieval_type != "FACTOID":
#                 answer = re.sub(r"^Adil Saeed is\s*", "", answer)
#                 answer = re.sub(r"\bI am\b", "Adil is", answer)
#                 answer = re.sub(r"\bmy\b", "Adil's", answer, flags=re.IGNORECASE)

#             return answer

#         except Exception as exc:
#             logger.error(f"LLM generation error: {exc}")
#             return "I had a technical issue. Please try again."

#     # -------------------------------------------------------------------------
#     # UTILITY HELPERS
#     # -------------------------------------------------------------------------

#     @staticmethod
#     def _confidence(max_score: float, num_docs: int) -> float:
#         base = max_score
#         if num_docs >= 3 and max_score >= 0.7:
#             return min(0.95, base + 0.10)
#         if num_docs >= 2 and max_score >= 0.5:
#             return min(0.85, base + 0.05)
#         return max(0.30, base * 0.80)

#     @staticmethod
#     def _no_info_response(topic: Optional[str]) -> Dict[str, Any]:
#         topic_str = topic.replace("_", " ") if topic else "that"
#         phrases = [
#             f"I don't have details about {topic_str} in Adil's portfolio. "
#             "Try asking about his projects, skills, education, experience, or contact info.",
#             f"That's outside what I have on {topic_str}. "
#             "I can answer questions about Adil's work, studies, and skills — want to try one?",
#             f"I couldn't find information about {topic_str}. "
#             "You can ask about Adil's technical projects, programming skills, academic background, or how to reach him.",
#         ]
#         return {
#             "answer":     random.choice(phrases),
#             "sources":    [],
#             "query_type": "no_info",
#             "confidence": 0.30,
#         }


# # ---------------------------------------------------------------------------
# # BACKWARD-COMPATIBILITY SHIM
# # ---------------------------------------------------------------------------

# def classify_query_type(query: str) -> str:
#     return _IntentClassifier().classify(query)["retrieval_type"]


"""
backend/services/pipeline.py
Unified RAG Pipeline — robust and production-friendly.
"""

import re
import random
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from groq import AsyncGroq
from config.settings import settings
from services.retriever import UltraPreciseRetriever
from services.formatter import ResponseFormatter
from services.memory import ConversationMemory

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# GLOBAL CONFIG
# -----------------------------------------------------------------------------

_PERSPECTIVE_RULES = """
PERSPECTIVE RULES (CRITICAL):
- You are AdilChat, a portfolio assistant answering ABOUT Adil Saeed, NOT Adil himself.
- ALWAYS use third person: "he", "his", "him", "Adil", "Adil's".
- NEVER use first person for Adil: "I", "my", "me", "mine".
- NEVER use second person for Adil: "you", "your".

SCOPE:
- ONLY answer questions about Adil Saeed's portfolio.
- If asked about anyone else -> "I only have information about Adil Saeed."
- If asked about unrelated topics -> redirect politely.
"""

_FORMATTING_RULES = """
FORMATTING RULES:
- Use **bold** ONLY for section headings when needed.
- NO markdown headers (#, ##, ###).
- Bullet points max 5 items.
- Keep answers concise and natural.
- Max 1-2 emojis per response.
- For contact/social links: write platform names only (system converts links).
"""

# Base retrieval config. Runtime tuning adapts from these.
_RETRIEVAL_CONFIG: Dict[str, Dict[str, Any]] = {
    "FACTOID": {"k": 6, "score_threshold": 0.22, "max_tokens": 180},
    "VERIFICATION": {"k": 8, "score_threshold": 0.18, "max_tokens": 280},
    "EXPLORATORY": {"k": 10, "score_threshold": 0.15, "max_tokens": 520},
}

_TOPIC_ENHANCEMENTS: Dict[str, str] = {
    "education": "adil saeed education university degree college imsciences giki diploma academic",
    "projects": "adil saeed projects built developed ocr rag chatbot sentiment analysis mlops ai ml",
    "skills": "adil saeed skills python java javascript html css tensorflow pytorch nlp cv",
    "experience": "adil saeed experience internship mlsa microsoft lead giki role achievements",
    "contact": "adil saeed contact email linkedin github facebook medium social accounts",
    "personal": "adil saeed personal family brother asad friends hasnain saad rohail umer daud",
    "research": "adil saeed research paper publication article writing medium",
}

_STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "about",
    "is", "are", "was", "were", "be", "with", "that", "this", "it", "as",
    "me", "you", "your", "his", "her", "their", "my"
}

# -----------------------------------------------------------------------------
# INTENT CLASSIFIER
# -----------------------------------------------------------------------------

class _IntentClassifier:
    _GREETING_KW = {
        "hi", "hello", "hey", "greetings", "good morning", "good afternoon",
        "good evening", "salam", "assalam", "yo", "howdy", "hola"
    }

    _GREETING_BLOCKERS = {
        "project", "skills", "experience", "education", "contact",
        "who", "what", "where", "when", "which", "explain", "describe",
        "linkedin", "github", "email", "friend", "brother", "internship"
    }

    _POLITE_CHAT = {"how are you", "how r u", "what's up", "whats up"}
    _CAPABILITY_KW = {
        "what can you do", "how can you help", "what is this chatbot",
        "tell me about yourself", "your capabilities", "what information do you have"
    }
    _ACK_KW = {"thanks", "thank you", "ok thanks", "appreciate", "got it"}
    _CLARIFICATION_KW = {"i mean", "not that", "i said", "wrong", "clarify"}

    _VERIFICATION_KW = {
        "prove", "evidence", "verify", "is it true", "credentials",
        "certificate", "qualification", "why hire", "better than", "instead of"
    }
    _EXPLORATORY_KW = {
        "tell me about", "overview", "explain", "all about", "summary",
        "comprehensive", "details", "who is", "background"
    }

    _TOPIC_KW = {
        "education": ["education", "degree", "university", "college", "imsciences", "academic"],
        "projects": ["project", "built", "developed", "created", "ocr", "chatbot", "portfolio"],
        "skills": ["skill", "technology", "programming", "language", "framework", "python", "ai", "ml"],
        "experience": ["experience", "internship", "role", "job", "mlsa", "giki", "hire"],
        "contact": ["contact", "email", "linkedin", "github", "facebook", "social"],
        "personal": ["family", "brother", "friend", "asad", "hasnain", "saad", "rohail", "umer", "daud"],
        "research": ["research", "paper", "publication", "article", "blog"],
    }

    _NAME_PATTERNS = [
        re.compile(r"\b(?:i am|i'm|my name is|call me)\s+([a-zA-Z]+)\b", re.I),
    ]
    _NAME_RECALL_PATTERNS = [
        re.compile(r"\bmy name\b", re.I),
        re.compile(r"\bwho am i\b", re.I),
        re.compile(r"\bremember me\b", re.I),
    ]
    _FAKE_NAMES = {"am", "is", "are", "the", "a", "an", "here", "there"}

    def classify(self, query: str, session_context: Optional[Dict] = None) -> Dict[str, Any]:
        if not query or not query.strip():
            return self._resp("INVALID", False)

        q = query.lower().strip()

        # gibberish guard
        words = q.split()
        if words and all(not w.isalpha() for w in words) and len(q) < 20:
            return self._resp("INVALID", False)

        if any(p in q for p in self._POLITE_CHAT):
            return self._resp("POLITE_CHAT", False)

        if any(p in q for p in self._CLARIFICATION_KW):
            return self._resp("CLARIFICATION", True, topic=self._detect_topic(q), retrieval_type=self._retrieval_type(q))

        if len(q) <= 30 and any(p in q for p in self._ACK_KW):
            return self._resp("ACKNOWLEDGMENT", False)

        name = self._extract_name(query)
        if name and self._valid_introduction(q):
            return self._resp("USER_INTRODUCTION", False, user_name=name)

        if any(k in q for k in self._CAPABILITY_KW):
            return self._resp("CAPABILITY", False)

        if self._is_greeting(q):
            return self._resp("GREETING", False)

        if session_context and any(p.search(q) for p in self._NAME_RECALL_PATTERNS):
            return self._resp("NAME_RECALL", False)

        topic = self._detect_topic(q)
        rt = self._retrieval_type(q)
        return self._resp(rt, True, topic=topic, retrieval_type=rt)

    def _is_greeting(self, q: str) -> bool:
        if any(b in q for b in self._GREETING_BLOCKERS):
            return False
        parts = set(q.split())
        return (len(parts) <= 3 and bool(parts & self._GREETING_KW)) or any(q.startswith(k) for k in self._GREETING_KW)

    def _extract_name(self, query: str) -> Optional[str]:
        for pat in self._NAME_PATTERNS:
            m = pat.search(query)
            if m:
                n = m.group(1).strip()
                if n.isalpha() and n.lower() not in self._FAKE_NAMES:
                    return n.capitalize()
        return None

    def _valid_introduction(self, q: str) -> bool:
        if re.search(r"\bwho (is|are)\b", q):
            return False
        return any(k in q for k in ("i am", "i'm", "my name is", "call me"))

    def _detect_topic(self, q: str) -> Optional[str]:
        # score-based topic detection to reduce first-match errors
        scores = {}
        for t, kws in self._TOPIC_KW.items():
            s = sum(1 for kw in kws if kw in q)
            if s > 0:
                scores[t] = s
        if not scores:
            return None
        return max(scores.items(), key=lambda x: x[1])[0]

    def _retrieval_type(self, q: str) -> str:
        if any(k in q for k in self._VERIFICATION_KW):
            return "VERIFICATION"
        if any(k in q for k in self._EXPLORATORY_KW) or (" and " in q and len(q.split()) > 8):
            return "EXPLORATORY"
        return "FACTOID"

    @staticmethod
    def _resp(intent: str, needs_retrieval: bool, user_name: Optional[str] = None,
              topic: Optional[str] = None, retrieval_type: str = "FACTOID") -> Dict[str, Any]:
        return {
            "intent": intent,
            "needs_retrieval": needs_retrieval,
            "user_name": user_name,
            "topic": topic,
            "retrieval_type": retrieval_type,
        }

# -----------------------------------------------------------------------------
# SESSION MEMORY (with lightweight entity/result tracking for follow-ups)
# -----------------------------------------------------------------------------

class _SessionMemory:
    def __init__(self, max_history: int = 6, timeout_minutes: int = 30):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._max_history = max_history
        self._timeout = timedelta(minutes=timeout_minutes)

    def get_context(self, session_id: str) -> Dict[str, Any]:
        s = self._get_or_create(session_id)
        return {
            "user_name": s.get("user_name"),
            "greeted": s.get("greeted", False),
            "interaction_count": s.get("count", 0),
            "last_topic": self._fresh_last_topic(s),
            "last_entities": s.get("last_entities", []),
            "last_results": s.get("last_results", []),  # ordered list for "first one"
            "has_history": s.get("count", 0) > 0,
        }

    def set_user_name(self, session_id: str, name: str):
        self._get_or_create(session_id)["user_name"] = name

    def mark_greeted(self, session_id: str):
        self._get_or_create(session_id)["greeted"] = True

    def set_last_topic(self, session_id: str, topic: Optional[str], entities: Optional[List[str]] = None):
        s = self._get_or_create(session_id)
        s["last_topic"] = {"topic": topic, "timestamp": datetime.now()}
        s["last_entities"] = entities or []

    def set_last_results(self, session_id: str, ordered_results: List[str]):
        s = self._get_or_create(session_id)
        s["last_results"] = ordered_results[:10]

    def add_interaction(self, session_id: str, query: str, answer: str, intent: str):
        s = self._get_or_create(session_id)
        s["interactions"].append({"query": query, "answer": answer, "intent": intent, "ts": datetime.now().isoformat()})
        if len(s["interactions"]) > self._max_history:
            s["interactions"] = s["interactions"][-self._max_history:]
        s["count"] += 1

    def _fresh_last_topic(self, s: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        lt = s.get("last_topic")
        if not lt:
            return None
        if (datetime.now() - lt["timestamp"]).total_seconds() <= 420:
            return lt
        return None

    def _cleanup(self):
        expired = []
        for sid, st in self._sessions.items():
            if (datetime.now() - st["last_active"]) > self._timeout:
                expired.append(sid)
        for sid in expired:
            del self._sessions[sid]

    def _get_or_create(self, session_id: str) -> Dict[str, Any]:
        self._cleanup()
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "user_name": None,
                "greeted": False,
                "count": 0,
                "interactions": [],
                "last_topic": None,
                "last_entities": [],
                "last_results": [],
                "created_at": datetime.now(),
                "last_active": datetime.now(),
            }
        else:
            self._sessions[session_id]["last_active"] = datetime.now()
        return self._sessions[session_id]

# -----------------------------------------------------------------------------
# MAIN PIPELINE
# -----------------------------------------------------------------------------

class RAGPipeline:
    def __init__(self):
        self.retriever = UltraPreciseRetriever()
        self.groq_client: Optional[AsyncGroq] = None
        self.formatter = ResponseFormatter()
        self.memory = ConversationMemory()
        self._session = _SessionMemory()
        self._classifier = _IntentClassifier()
        self.initialized = False

    async def initialize(self):
        try:
            self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            await self.retriever.initialize()
            self.initialized = True
            logger.info("RAGPipeline initialized successfully")
        except Exception as exc:
            logger.error(f"RAGPipeline initialization failed: {exc}")
            raise

    async def refresh_data(self) -> bool:
        try:
            await self.retriever.initialize()
            return True
        except Exception as exc:
            logger.error(f"refresh_data failed: {exc}")
            return False

    async def process_query(
        self,
        query: str,
        language: str = "en",
        session_id: str = "default",
        conversation_history: List = None,
        user_context: Dict = None,
    ) -> Dict[str, Any]:
        if not self.initialized:
            raise RuntimeError("Pipeline not initialized — call initialize() first")

        stripped = (query or "").strip()
        if len(stripped) < 2:
            return await self.formatter.format_response({
                "answer": "Your message is too short. Ask about Adil's projects, skills, education, or experience.",
                "sources": [],
                "query_type": "invalid_input",
                "confidence": 0.95,
                "original_query": query or "",
            }, language)

        t0 = time.time()
        try:
            ctx = self._session.get_context(session_id)

            # follow-up resolution before intent classification
            resolved_query = self._resolve_follow_up_query(stripped, ctx)

            intent = self._classifier.classify(resolved_query, ctx)
            raw = await self._route(resolved_query, intent, ctx, session_id)
            raw["original_query"] = query

            result = await self.formatter.format_response(raw, language)
            result["processing_time"] = round((time.time() - t0) * 1000, 1)

            self._session.add_interaction(session_id, query, result.get("answer", ""), intent["intent"])
            return result

        except Exception as exc:
            logger.error(f"process_query error: {exc}", exc_info=True)
            return await self.formatter.format_response({
                "answer": "I'm having a temporary issue. Please try again.",
                "sources": [],
                "query_type": "error",
                "confidence": 0.0,
                "original_query": query,
            }, language)

    # -------------------------------------------------------------------------
    # ROUTING
    # -------------------------------------------------------------------------

    async def _route(self, query: str, intent: Dict[str, Any], ctx: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        code = intent["intent"]

        if code == "GREETING":
            return self._handle_greeting(ctx, session_id)
        if code == "INVALID":
            return {"answer": "Could you rephrase that? I can help with Adil's portfolio details.",
                    "sources": [], "query_type": "invalid", "confidence": 0.95}
        if code == "POLITE_CHAT":
            return self._handle_polite_chat(ctx)
        if code == "ACKNOWLEDGMENT":
            return self._handle_acknowledgment(ctx)
        if code == "CAPABILITY":
            return self._handle_capability(ctx)
        if code == "USER_INTRODUCTION":
            nm = intent.get("user_name", "")
            self._session.set_user_name(session_id, nm)
            return self._handle_user_introduction(nm)
        if code == "NAME_RECALL":
            return self._handle_name_recall(ctx)

        if self._is_general_knowledge(query):
            return await self._handle_general(query)

        if self._is_chatbot_meta(query):
            return self._handle_chatbot_meta()

        resp = await self._handle_knowledge(query, intent, ctx, session_id)
        if code == "CLARIFICATION" and resp.get("answer"):
            resp["answer"] = "Thanks for clarifying. " + resp["answer"]
        return resp

    # -------------------------------------------------------------------------
    # Conversational handlers
    # -------------------------------------------------------------------------

    def _handle_greeting(self, ctx: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        name = ctx.get("user_name")
        greeted = ctx.get("greeted", False)

        if name:
            ans = f"Hello {name}! What would you like to know about Adil's portfolio?"
        elif not greeted:
            ans = ("Hello! I'm AdilChat, Adil Saeed's portfolio assistant. "
                   "Ask me about his projects, skills, education, experience, or contact.")
            self._session.mark_greeted(session_id)
        else:
            ans = "Hi again! Ask me anything about Adil's projects, skills, education, or experience."

        return {"answer": ans, "sources": [], "query_type": "greeting", "confidence": 0.95}

    def _handle_polite_chat(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        nm = ctx.get("user_name")
        tail = f", {nm}" if nm else ""
        return {"answer": f"Doing well{tail}! What would you like to know about Adil?",
                "sources": [], "query_type": "polite_chat", "confidence": 0.95}

    def _handle_acknowledgment(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        nm = ctx.get("user_name")
        tail = f", {nm}" if nm else ""
        opts = [
            f"You're welcome{tail}! Ask anything else about Adil.",
            f"Happy to help{tail}! Want to explore projects, skills, or experience next?",
            f"Anytime{tail}! I'm here for Adil's portfolio details.",
        ]
        return {"answer": random.choice(opts), "sources": [], "query_type": "acknowledgment", "confidence": 0.95}

    def _handle_capability(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        nm = ctx.get("user_name")
        intro = f"Great question, {nm}." if nm else "Great question."
        return {
            "answer": (
                f"{intro}\n\n"
                "I can help with:\n"
                "**Projects** — what he built and tech used\n"
                "**Skills** — languages, frameworks, AI/ML stack\n"
                "**Education** — institutions, programs, certifications\n"
                "**Experience** — internships, leadership, achievements\n"
                "**Contact** — email and social platforms"
            ),
            "sources": [],
            "query_type": "capability",
            "confidence": 0.95,
        }

    @staticmethod
    def _handle_user_introduction(name: str) -> Dict[str, Any]:
        return {
            "answer": f"Nice to meet you, {name}! Ask me anything about Adil Saeed's portfolio.",
            "sources": [],
            "query_type": "user_introduction",
            "confidence": 0.95,
        }

    @staticmethod
    def _handle_name_recall(ctx: Dict[str, Any]) -> Dict[str, Any]:
        n = ctx.get("user_name")
        if n:
            return {"answer": f"Your name is {n}. What would you like to ask next?",
                    "sources": [], "query_type": "name_recall", "confidence": 0.95}
        return {"answer": "I don't have your name yet. You can say: 'My name is ...'",
                "sources": [], "query_type": "name_recall", "confidence": 0.95}

    # -------------------------------------------------------------------------
    # General/meta
    # -------------------------------------------------------------------------

    @staticmethod
    def _is_general_knowledge(query: str) -> bool:
        q = query.lower()
        if re.search(r"\d+\s*[\+\-\*\/]\s*\d+", q):
            return True
        pats = [r"capital of", r"weather in", r"population of", r"currency of", r"recipe for"]
        is_general = any(re.search(p, q) for p in pats)
        about_adil = any(w in q for w in ("adil", "portfolio", "his", "him"))
        return is_general and not about_adil

    @staticmethod
    def _is_chatbot_meta(query: str) -> bool:
        q = query.lower()
        pats = [
            r"who (made|created|built) you",
            r"what is your name",
            r"are you (an )?(ai|bot|assistant|chatbot)",
            r"what are you"
        ]
        return any(re.search(p, q) for p in pats)

    async def _handle_general(self, query: str) -> Dict[str, Any]:
        m = re.search(r"(\d+)\s*([\+\-\*\/])\s*(\d+)", query)
        if m:
            a, op, b = m.groups()
            a, b = int(a), int(b)
            val = None
            if op == "+": val = a + b
            elif op == "-": val = a - b
            elif op == "*": val = a * b
            elif op == "/": val = a / b if b != 0 else "undefined"
            return {"answer": f"The result is **{val}**.", "sources": [], "query_type": "math", "confidence": 0.99}

        try:
            r = await self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL_EN,
                messages=[
                    {"role": "system", "content": "Answer in one short sentence."},
                    {"role": "user", "content": query},
                ],
                temperature=0.1,
                max_tokens=60,
            )
            return {"answer": r.choices[0].message.content.strip(),
                    "sources": [], "query_type": "general", "confidence": 0.78}
        except Exception:
            return {"answer": "I focus on Adil Saeed's portfolio. Ask about his projects, skills, education, or experience.",
                    "sources": [], "query_type": "redirect", "confidence": 0.70}

    @staticmethod
    def _handle_chatbot_meta() -> Dict[str, Any]:
        return {
            "answer": ("I'm AdilChat, an AI assistant built to explain Adil Saeed's portfolio, "
                       "including projects, skills, education, experience, and contact info."),
            "sources": [],
            "query_type": "chatbot_meta",
            "confidence": 0.95,
        }

    # -------------------------------------------------------------------------
    # FOLLOW-UP RESOLUTION
    # -------------------------------------------------------------------------

    def _resolve_follow_up_query(self, query: str, ctx: Dict[str, Any]) -> str:
        q = query.lower()
        last_results = ctx.get("last_results", [])
        last_entities = ctx.get("last_entities", [])
        last_topic = (ctx.get("last_topic") or {}).get("topic")

        # Ordinal references
        ord_map = {"first": 0, "second": 1, "third": 2, "last": -1}
        for k, idx in ord_map.items():
            if f"{k} one" in q or re.search(rf"\b{k}\b", q):
                if last_results:
                    ref = last_results[idx]
                    return f"{query} about {ref}"

        # Pronoun/implicit references
        if any(t in q for t in ("that project", "that one", "it", "them", "those", "more about that")):
            hints = []
            if last_topic:
                hints.append(last_topic)
            hints.extend(last_entities[:3])
            if hints:
                return f"{query} {' '.join(hints)}"

        return query

    # -------------------------------------------------------------------------
    # KNOWLEDGE (RAG)
    # -------------------------------------------------------------------------

    async def _handle_knowledge(self, query: str, intent: Dict[str, Any], ctx: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        topic = intent.get("topic")
        retrieval_type = intent.get("retrieval_type", "FACTOID")

        norm = self._normalize(query)
        enhanced = self._enhance_query(norm, query, topic, ctx)

        # dynamic tuning
        cfg = self._adaptive_config(retrieval_type, enhanced)

        docs = await self._retrieve(enhanced, cfg)
        if not docs:
            docs = await self._emergency_retrieve(enhanced)

        if not docs:
            return self._no_info_response(topic)

        # rerank + diversify
        docs = self._rerank_and_diversify(enhanced, docs, keep=min(8, cfg["k"]))

        # context selection
        chunks = self._select_context_chunks(docs, retrieval_type, max_chars=5200)
        if not chunks:
            return self._no_info_response(topic)

        # collect entities/results from chunks for future follow-up resolution
        entities = self._extract_entities_from_docs(chunks)
        ordered_results = self._extract_ordered_items(chunks)

        answer, cited_sources, grounded_ratio = await self._generate(
            query=query,
            chunks=chunks,
            retrieval_type=retrieval_type,
            topic=topic,
            ctx=ctx,
            max_tokens=cfg["max_tokens"],
        )

        self._session.set_last_topic(session_id, topic, entities=entities)
        if ordered_results:
            self._session.set_last_results(session_id, ordered_results)

        conf = self._confidence(
            max_score=max(d.get("retrieval_score", 0.0) for d in chunks),
            num_docs=len(chunks),
            grounded_ratio=grounded_ratio
        )

        return {
            "answer": answer,
            "sources": cited_sources,
            "query_type": f"{topic or 'portfolio'}_{retrieval_type.lower()}",
            "confidence": conf,
        }

    # -------------------------------------------------------------------------
    # Retrieval utilities
    # -------------------------------------------------------------------------

    @staticmethod
    def _normalize(query: str) -> str:
        fixes = {
            "adeel": "adil",
            "porject": "project",
            "porjects": "projects",
            "skils": "skills",
            "eduction": "education",
            "experiance": "experience",
            "contct": "contact",
            "socila": "social",
            "mdeia": "media",
            "insted": "instead",
            "instent": "instead",
        }
        q = query.lower().strip()
        for w, r in fixes.items():
            q = q.replace(w, r)
        return q

    def _enhance_query(self, norm_query: str, original_query: str, topic: Optional[str], ctx: Dict[str, Any]) -> str:
        q = norm_query

        # direct targeted boosts
        if "friend" in q:
            return "adil saeed friends network hasnain saad rohail umer daud asad"
        if any(t in q for t in ("social media", "social accounts", "all accounts", "online presence")):
            return "adil saeed contact linkedin github facebook medium social profiles"

        base = original_query
        if topic and topic in _TOPIC_ENHANCEMENTS:
            base = f"{base} {_TOPIC_ENHANCEMENTS[topic]}"

        # carry last entities into ambiguous follow-up
        if any(x in q for x in ("that", "it", "them", "those", "more about")):
            ents = ctx.get("last_entities") or []
            if ents:
                base = f"{base} {' '.join(ents[:3])}"

        return base

    def _adaptive_config(self, retrieval_type: str, query: str) -> Dict[str, Any]:
        cfg = dict(_RETRIEVAL_CONFIG[retrieval_type])

        q = query.lower()
        complexity = len(query.split())
        multi_topic = (" and " in q) or ("compare" in q) or ("difference" in q)

        if retrieval_type == "FACTOID":
            if complexity > 12:
                cfg["k"] = min(cfg["k"] + 2, 9)
                cfg["max_tokens"] = 220
        elif retrieval_type == "EXPLORATORY":
            if multi_topic:
                cfg["k"] = min(cfg["k"] + 3, 14)
                cfg["max_tokens"] = 650
            if complexity < 6:
                cfg["score_threshold"] = max(0.12, cfg["score_threshold"] - 0.02)
        elif retrieval_type == "VERIFICATION":
            cfg["k"] = min(cfg["k"] + 1, 10)

        return cfg

    async def _retrieve(self, query: str, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            raw = await self.retriever.hybrid_retrieve(query=query, top_k=cfg["k"])
        except Exception as exc:
            logger.error(f"Retrieve error: {exc}")
            return []

        # dedup by (id + chunk index if available)
        seen = set()
        docs = []
        for d in raw:
            doc_id = str(d.get("id", ""))
            chunk_idx = str(d.get("chunk_index", d.get("chunk_id", "")))
            key = f"{doc_id}:{chunk_idx}"
            score = float(d.get("retrieval_score", 0.0))
            if key in seen:
                continue
            if score < cfg["score_threshold"]:
                continue
            seen.add(key)
            docs.append(d)

        return sorted(docs, key=lambda x: x.get("retrieval_score", 0.0), reverse=True)

    async def _emergency_retrieve(self, query: str) -> List[Dict[str, Any]]:
        try:
            raw = await self.retriever.hybrid_retrieve(query=query, top_k=14)
            docs = [d for d in raw if float(d.get("retrieval_score", 0.0)) >= 0.08]
            return sorted(docs, key=lambda x: x.get("retrieval_score", 0.0), reverse=True)
        except Exception as exc:
            logger.error(f"Emergency retrieve error: {exc}")
            return []

    def _rerank_and_diversify(self, query: str, docs: List[Dict[str, Any]], keep: int = 8) -> List[Dict[str, Any]]:
        # lightweight rerank: lexical overlap + retrieval score
        q_terms = {t for t in re.findall(r"[a-zA-Z0-9]+", query.lower()) if t not in _STOPWORDS and len(t) > 2}
        rescored = []
        for d in docs:
            txt = (d.get("content") or "").lower()
            d_terms = set(re.findall(r"[a-zA-Z0-9]+", txt))
            overlap = len(q_terms & d_terms) / (len(q_terms) + 1e-6)
            base = float(d.get("retrieval_score", 0.0))
            d["_rerank_score"] = 0.72 * base + 0.28 * overlap
            rescored.append(d)

        rescored.sort(key=lambda x: x.get("_rerank_score", 0.0), reverse=True)

        # simple diversity by source/id
        selected = []
        used_sources = set()
        for d in rescored:
            src = str(d.get("source", d.get("id", "unknown")))
            if src not in used_sources or len(selected) < max(2, keep // 2):
                selected.append(d)
                used_sources.add(src)
            if len(selected) >= keep:
                break

        return selected

    def _select_context_chunks(self, docs: List[Dict[str, Any]], retrieval_type: str, max_chars: int = 5200) -> List[Dict[str, Any]]:
        limits = {"FACTOID": 3, "VERIFICATION": 5, "EXPLORATORY": 7}
        max_n = limits.get(retrieval_type, 5)

        chosen = []
        total = 0
        for d in docs:
            c = (d.get("content") or "").strip()
            if not c:
                continue
            c_len = len(c)
            if total + c_len > max_chars and chosen:
                continue
            chosen.append(d)
            total += c_len
            if len(chosen) >= max_n:
                break
        return chosen

    @staticmethod
    def _extract_entities_from_docs(docs: List[Dict[str, Any]]) -> List[str]:
        text = " ".join((d.get("content") or "")[:600] for d in docs)
        # simple proper noun extractor
        cands = re.findall(r"\b[A-Z][a-zA-Z0-9\-\+]{2,}\b", text)
        uniq = []
        seen = set()
        for c in cands:
            lc = c.lower()
            if lc in seen:
                continue
            seen.add(lc)
            uniq.append(c)
        return uniq[:10]

    @staticmethod
    def _extract_ordered_items(docs: List[Dict[str, Any]]) -> List[str]:
        items = []
        for d in docs:
            txt = d.get("content") or ""
            # pick list-like lines
            for line in txt.splitlines():
                line = line.strip("-• ").strip()
                if 4 <= len(line) <= 80 and any(k in line.lower() for k in ("project", "intern", "cert", "skill", "bootcamp")):
                    items.append(line)
        # dedup preserve order
        out = []
        seen = set()
        for it in items:
            k = it.lower()
            if k not in seen:
                seen.add(k)
                out.append(it)
        return out[:10]

    # -------------------------------------------------------------------------
    # Generation + citation
    # -------------------------------------------------------------------------

    async def _generate(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        retrieval_type: str,
        topic: Optional[str],
        ctx: Dict[str, Any],
        max_tokens: int,
    ) -> Tuple[str, List[str], float]:

        emoji = {
            "contact": "📧", "skills": "🛠️", "projects": "💻", "education": "🎓",
            "experience": "💼", "personal": "👤", "research": "📄"
        }.get(topic or "", "📋")

        # Build context with chunk IDs
        context_parts = []
        for i, d in enumerate(chunks, start=1):
            cid = f"C{i}"
            d["_cid"] = cid
            snippet = (d.get("content") or "").strip()
            context_parts.append(f"[{cid}] {snippet}")
        context = "\n\n".join(context_parts)

        if retrieval_type == "FACTOID":
            task_rule = f"Answer in 2-3 sentences. Start with {emoji} if relevant."
        elif retrieval_type == "VERIFICATION":
            task_rule = "Provide precise proof-style answer with concrete details from context."
        else:
            task_rule = f"Use short heading + bullets if needed. Start with {emoji}. Cover each asked part."

        system = f"""
You answer using ONLY provided context chunks.
Never guess. If missing info, say it briefly.
Use third person for Adil.
{_PERSPECTIVE_RULES}
{_FORMATTING_RULES}
{task_rule}

At the end, add one short line:
CITATIONS: [C#], [C#]
(Only include chunk IDs actually used.)
"""

        user_name = ctx.get("user_name")
        uname = f"User name: {user_name}\n" if user_name else ""
        user = f"{uname}Query: {query}\n\nContext chunks:\n{context}"

        try:
            resp = await self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL_EN,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.1,
                max_tokens=max_tokens,
            )
            txt = (resp.choices[0].message.content or "").strip()
        except Exception as exc:
            logger.error(f"Generation error: {exc}")
            return "I had a technical issue. Please try again.", [], 0.0

        answer, citation_ids = self._split_citations(txt)
        sources = self._map_citations_to_sources(citation_ids, chunks)

        grounded_ratio = min(1.0, len(citation_ids) / max(1, min(4, len(chunks))))
        if not sources:
            # fallback source list
            sources = [self._safe_source_label(d, i + 1) for i, d in enumerate(chunks[:2])]

        return answer, sources, grounded_ratio

    @staticmethod
    def _split_citations(text: str) -> Tuple[str, List[str]]:
        lines = text.splitlines()
        cite_line_idx = None
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().lower().startswith("citations:"):
                cite_line_idx = i
                break

        if cite_line_idx is None:
            return text.strip(), []

        ans = "\n".join(lines[:cite_line_idx]).strip()
        line = lines[cite_line_idx]
        ids = re.findall(r"\[(C\d+)\]", line, flags=re.I)
        ids = [x.upper() for x in ids]
        # dedup order
        seen = set()
        ordered = []
        for x in ids:
            if x not in seen:
                seen.add(x)
                ordered.append(x)
        return ans, ordered

    def _map_citations_to_sources(self, citation_ids: List[str], chunks: List[Dict[str, Any]]) -> List[str]:
        id_to_doc = {d.get("_cid"): d for d in chunks if d.get("_cid")}
        out = []
        for cid in citation_ids:
            d = id_to_doc.get(cid)
            if d:
                out.append(self._safe_source_label(d, int(cid[1:])))
        # dedup
        seen = set()
        fin = []
        for s in out:
            if s not in seen:
                seen.add(s)
                fin.append(s)
        return fin

    @staticmethod
    def _safe_source_label(doc: Dict[str, Any], idx: int) -> str:
        src = str(doc.get("source") or doc.get("id") or f"chunk_{idx}")
        return f"📚 {src}"

    # -------------------------------------------------------------------------
    # Confidence & fallback
    # -------------------------------------------------------------------------

    @staticmethod
    def _confidence(max_score: float, num_docs: int, grounded_ratio: float) -> float:
        # weighted confidence: retrieval strength + support count + grounding
        retrieval_part = min(1.0, max_score)
        support_part = min(1.0, num_docs / 5.0)
        conf = 0.50 * retrieval_part + 0.20 * support_part + 0.30 * grounded_ratio
        return round(max(0.25, min(0.96, conf)), 2)

    @staticmethod
    def _no_info_response(topic: Optional[str]) -> Dict[str, Any]:
        ts = topic.replace("_", " ") if topic else "that"
        choices = [
            f"I don't have verified details about {ts} in Adil's portfolio yet.",
            f"I couldn't find reliable context for {ts}.",
            f"There isn't enough grounded information for {ts} right now.",
        ]
        return {
            "answer": random.choice(choices) + " You can ask about projects, skills, education, experience, or contact info.",
            "sources": [],
            "query_type": "no_info",
            "confidence": 0.30,
        }

# -----------------------------------------------------------------------------
# Backward-compatibility shim
# -----------------------------------------------------------------------------

def classify_query_type(query: str) -> str:
    return _IntentClassifier().classify(query).get("retrieval_type", "FACTOID")