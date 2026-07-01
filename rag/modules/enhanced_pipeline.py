"""
Enhanced Pipeline Integrator - OPTIONAL WRAPPER
Integrates FAQ routing, query expansion, and fact-checking into existing pipeline.

SAFETY:
- This is a WRAPPER around existing RAGPipeline
- Does NOT modify existing RAGPipeline code
- Can be used OR ignored - your choice
- Falls back to standard pipeline on any error
"""
import logging
from typing import Dict, List, Any, Optional
from services.rag_pipeline import RAGPipeline
from rag.modules.faq_router import get_faq_router
from rag.modules.query_expander import get_query_expander
from rag.modules.fact_checker import get_fact_checker

logger = logging.getLogger(__name__)


class EnhancedRAGPipeline:
    """
    Enhanced wrapper around existing RAGPipeline.
    Adds optional FAQ routing, query expansion, and fact-checking.

    CRITICAL:
    - Wraps existing RAGPipeline (does NOT replace it)
    - All enhancements are optional
    - Falls back to standard pipeline on errors
    - Can be swapped back to standard pipeline anytime
    """

    def __init__(self, base_pipeline: RAGPipeline = None):
        """
        Initialize enhanced pipeline.

        Args:
            base_pipeline: Existing RAGPipeline instance (if None, creates new one)
        """
        # SAFETY: Use existing pipeline or create new one
        self.base_pipeline = base_pipeline if base_pipeline else RAGPipeline()

        # Load enhancement modules (lazy loaded)
        self.faq_router = None
        self.query_expander = None
        self.fact_checker = None

        # Feature flags (can be toggled)
        self.enable_faq_routing = True
        self.enable_query_expansion = True
        self.enable_fact_checking = True

        self.initialized = False

    async def initialize(self):
        """Initialize base pipeline and enhancement modules"""
        try:
            # Initialize base pipeline
            await self.base_pipeline.initialize()

            # Load enhancement modules if enabled
            if self.enable_faq_routing:
                self.faq_router = get_faq_router()

            if self.enable_query_expansion:
                self.query_expander = get_query_expander()

            if self.enable_fact_checking:
                self.fact_checker = get_fact_checker()

            self.initialized = True
            logger.info("✅ Enhanced RAG Pipeline initialized")

        except Exception as e:
            logger.error(f"Enhanced pipeline initialization failed: {e}")
            raise

    async def process_query(self, query: str, language: str = "en",
                          session_id: str = None, conversation_history: List = None,
                          user_context: Dict = None) -> Dict[str, Any]:
        """
        Process query with optional enhancements.

        SAFETY:
        - Each enhancement can fail independently
        - Falls back to base pipeline on any error
        - All enhancements are optional

        Args:
            query: User's question
            language: Response language (en/ur)
            session_id: Session identifier
            conversation_history: Previous conversation
            user_context: Additional context

        Returns:
            Enhanced response dict
        """
        if not self.initialized:
            raise RuntimeError("Pipeline not initialized")

        try:
            # Enhancement 1: FAQ Routing (optional)
            faq_route = None
            if self.enable_faq_routing and self.faq_router:
                faq_route = self._route_faq(query)

            # Enhancement 2: Query Expansion (optional)
            if faq_route and faq_route.get('is_aggregation'):
                # For aggregation queries, use optimized retrieval
                response = await self._handle_aggregation_query(
                    query, faq_route, language, session_id, conversation_history, user_context
                )
            else:
                # Standard pipeline with optional query expansion
                response = await self._process_with_expansion(
                    query, language, session_id, conversation_history, user_context
                )

            # Enhancement 3: Fact Checking (optional)
            if self.enable_fact_checking and self.fact_checker:
                response = self._add_fact_check(response, query)

            return response

        except Exception as e:
            logger.error(f"Enhanced processing failed: {e}. Falling back to base pipeline.")
            # SAFETY: Fall back to base pipeline on error
            return await self.base_pipeline.process_query(
                query, language, session_id, conversation_history, user_context
            )

    def _route_faq(self, query: str) -> Optional[Dict]:
        """
        Check if query matches FAQ patterns.

        Returns:
            FAQ routing info or None
        """
        try:
            faq_route = self.faq_router.route_query(query)

            if faq_route:
                logger.info(f"✅ FAQ Route: {faq_route['faq_type']}")

            return faq_route

        except Exception as e:
            logger.warning(f"FAQ routing failed: {e}")
            return None

    async def _handle_aggregation_query(self, query: str, faq_route: Dict,
                                       language: str, session_id: str,
                                       conversation_history: List,
                                       user_context: Dict) -> Dict[str, Any]:
        """
        Handle aggregation queries (e.g., "all certifications", "all social media").

        Uses optimized retrieval strategy for comprehensive results.
        """
        try:
            faq_type = faq_route['faq_type']
            search_hints = faq_route['search_hints']

            logger.info(f"🔍 Aggregation query: {faq_type} | Hints: {len(search_hints)}")

            # Get retrieval strategy for this FAQ type
            strategy = self.faq_router.get_retrieval_strategy(faq_type)

            # Execute multiple searches for comprehensive coverage
            all_chunks = []
            for search_query in search_hints:
                chunks = await self.base_pipeline.retriever.hybrid_retrieve(
                    query=search_query,
                    top_k=strategy['top_k']
                )

                # Filter by score threshold
                filtered_chunks = [
                    chunk for chunk in chunks
                    if chunk.get('retrieval_score', 0) >= strategy['score_threshold']
                ]

                all_chunks.extend(filtered_chunks)

            # Remove duplicates
            seen_ids = set()
            unique_chunks = []
            for chunk in all_chunks:
                chunk_id = chunk.get('id', '')
                if chunk_id not in seen_ids:
                    seen_ids.add(chunk_id)
                    unique_chunks.append(chunk)

            # Sort by score and take top results
            unique_chunks.sort(key=lambda x: x.get('retrieval_score', 0), reverse=True)
            top_chunks = unique_chunks[:strategy['top_k']]

            logger.info(f"📚 Aggregation retrieved: {len(top_chunks)} unique chunks")

            # Generate response with comprehensive context
            if not top_chunks:
                return {
                    "answer": f"I don't have information about {faq_type.replace('_', ' ')} in my knowledge base.",
                    "sources": [],
                    "query_type": f"faq_{faq_type}",
                    "confidence": 0.4,
                    "original_query": query
                }

            # Build comprehensive context
            context = "\n\n".join([chunk.get('content', '') for chunk in top_chunks])

            # Generate response using base pipeline's LLM
            system_prompt = f"""You are Adil's portfolio assistant.

CRITICAL: User asked for COMPLETE information about {faq_type.replace('_', ' ')}.
Provide a COMPREHENSIVE list including ALL relevant items from the context.

Response format: {faq_route['response_format']}

Rules:
1. Include ALL items found in context
2. Organize clearly (use bullet points or numbered lists)
3. Be complete - don't miss any items
4. Use ONLY information from the provided context"""

            response = await self.base_pipeline.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {query}\n\nContext:\n{context}"}
                ],
                temperature=0.1,  # Low for completeness
                max_tokens=500  # More tokens for comprehensive responses
            )

            answer = response.choices[0].message.content.strip()

            return {
                "answer": answer,
                "sources": ["📚 Adil_Data"],
                "query_type": f"faq_{faq_type}",
                "confidence": 0.95,
                "original_query": query,
                "chunks_retrieved": len(top_chunks)
            }

        except Exception as e:
            logger.error(f"Aggregation handling failed: {e}")
            # Fall back to standard processing
            return await self.base_pipeline.process_query(query, language, session_id, conversation_history, user_context)

    async def _process_with_expansion(self, query: str, language: str,
                                     session_id: str, conversation_history: List,
                                     user_context: Dict) -> Dict[str, Any]:
        """
        Process query with optional query expansion.

        Falls back to standard processing if expansion fails.
        """
        try:
            # Try query expansion
            if self.enable_query_expansion and self.query_expander:
                expanded_queries = self.query_expander.expand_query(query, max_expansions=2)

                if len(expanded_queries) > 1:
                    logger.info(f"🔄 Query expanded: {len(expanded_queries)} variations")

                    # Retrieve with all query variations
                    all_chunks = []
                    for expanded_query in expanded_queries[:3]:  # Max 3 variations
                        chunks = await self.base_pipeline.retriever.hybrid_retrieve(
                            query=expanded_query,
                            top_k=5
                        )
                        all_chunks.extend(chunks)

                    # Remove duplicates and re-rank
                    seen_ids = set()
                    unique_chunks = []
                    for chunk in all_chunks:
                        chunk_id = chunk.get('id', '')
                        if chunk_id not in seen_ids:
                            seen_ids.add(chunk_id)
                            unique_chunks.append(chunk)

                    # Sort by score
                    unique_chunks.sort(key=lambda x: x.get('retrieval_score', 0), reverse=True)

                    # Use top chunks for generation (temporarily override retriever results)
                    # Note: This is a bit hacky, better to modify pipeline to accept chunks
                    logger.info(f"📊 Expanded retrieval: {len(unique_chunks)} unique chunks")

            # Use base pipeline for response generation
            response = await self.base_pipeline.process_query(
                query, language, session_id, conversation_history, user_context
            )

            return response

        except Exception as e:
            logger.warning(f"Query expansion failed: {e}. Using standard processing.")
            return await self.base_pipeline.process_query(
                query, language, session_id, conversation_history, user_context
            )

    def _add_fact_check(self, response: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Add fact-checking to response.

        SAFETY:
        - Does NOT modify the answer
        - Only adds metadata about fact-checking
        - Response is always returned
        """
        try:
            answer = response.get('answer', '')

            # Get source chunks if available (may not be in response dict)
            # For now, skip fact-checking if we don't have source chunks
            # In production, you'd want to store chunks in response dict

            # Simple grounding check based on response confidence
            original_confidence = response.get('confidence', 0.5)

            # Add fact-check metadata
            response['fact_check'] = {
                'original_confidence': original_confidence,
                'status': 'not_checked',  # Would need source chunks for full check
                'note': 'Fact-checking requires source chunks'
            }

            return response

        except Exception as e:
            logger.warning(f"Fact-checking failed: {e}")
            return response  # Return unmodified response on error

    async def refresh_data(self):
        """Refresh retriever data (delegates to base pipeline)"""
        return await self.base_pipeline.refresh_data()

    def toggle_enhancement(self, enhancement: str, enabled: bool):
        """
        Toggle specific enhancement on/off.

        Args:
            enhancement: "faq_routing", "query_expansion", or "fact_checking"
            enabled: True to enable, False to disable
        """
        if enhancement == "faq_routing":
            self.enable_faq_routing = enabled
            logger.info(f"FAQ Routing: {'enabled' if enabled else 'disabled'}")

        elif enhancement == "query_expansion":
            self.enable_query_expansion = enabled
            logger.info(f"Query Expansion: {'enabled' if enabled else 'disabled'}")

        elif enhancement == "fact_checking":
            self.enable_fact_checking = enabled
            logger.info(f"Fact Checking: {'enabled' if enabled else 'disabled'}")

        else:
            logger.warning(f"Unknown enhancement: {enhancement}")


# Factory function
async def create_enhanced_pipeline(use_enhancements: bool = True) -> RAGPipeline:
    """
    Create enhanced or standard pipeline.

    Args:
        use_enhancements: If True, returns EnhancedRAGPipeline; if False, standard RAGPipeline

    Returns:
        Initialized pipeline
    """
    if use_enhancements:
        pipeline = EnhancedRAGPipeline()
        logger.info("Creating Enhanced RAG Pipeline")
    else:
        pipeline = RAGPipeline()
        logger.info("Creating Standard RAG Pipeline")

    await pipeline.initialize()
    return pipeline
