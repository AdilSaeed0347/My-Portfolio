# """
# Enhanced Retriever Wrapper - OPTIONAL ADD-ON
# Wraps existing retriever with optional enhancements.

# CRITICAL SAFETY:
# - Does NOT replace existing retriever
# - All enhancements are opt-in via config
# - Falls back to original retriever on any failure
# - Can be disabled completely
# """
# import logging
# from typing import List, Dict, Optional

# from config.rag_enhancements import (
#     ENABLE_QUERY_EXPANSION,
#     ENABLE_RERANKING,
#     ENABLE_CACHING,
#     RERANKING_CONFIG
# )

# from .query_expander import get_query_expander
# from .reranker import get_reranker
# from .query_cache import get_cache

# logger = logging.getLogger(__name__)


# class EnhancedRetriever:
#     """
#     Optional enhancement wrapper for existing retriever.

#     SAFETY GUARANTEES:
#     1. Existing retriever is NEVER modified
#     2. All enhancements can be toggled off
#     3. Failures fall back to original behavior
#     4. Can be swapped out without code changes
#     """

#     def __init__(self, base_retriever):
#         """
#         Wrap existing retriever with optional enhancements.

#         SAFETY: base_retriever is stored as-is, never modified.

#         Args:
#             base_retriever: Your existing UltraPreciseRetriever instance
#         """
#         self.base_retriever = base_retriever  # CRITICAL: Never modified

#         # Lazy load enhancement layers (only if enabled)
#         self.query_expander = get_query_expander() if ENABLE_QUERY_EXPANSION else None
#         self.reranker = get_reranker() if ENABLE_RERANKING else None
#         self.cache = get_cache() if ENABLE_CACHING else None

#         logger.info(f"Enhanced retriever initialized (expansion={ENABLE_QUERY_EXPANSION}, reranking={ENABLE_RERANKING}, caching={ENABLE_CACHING})")

#     async def hybrid_retrieve(
#         self,
#         query: str,
#         top_k: int = 10,
#         use_enhancements: bool = True
#     ) -> List[Dict]:
#         """
#         Retrieve with optional enhancements.

#         CRITICAL SAFETY:
#         - If use_enhancements=False, calls base retriever directly
#         - Cache hit bypasses ALL retrieval (fast path)
#         - Query expansion + re-ranking are additive only
#         - Any enhancement failure → falls back to base retrieval

#         Args:
#             query: User's question
#             top_k: Number of results to return
#             use_enhancements: If False, skips ALL enhancements (testing/debugging)

#         Returns:
#             List of retrieved chunks (enhanced or original)
#         """
#         # SAFETY: Allow bypass of all enhancements
#         if not use_enhancements:
#             logger.debug("Enhancements disabled, using base retriever")
#             return await self.base_retriever.hybrid_retrieve(query, top_k=top_k)

#         # --- LAYER 1: CACHE CHECK (Fastest path) ---
#         if self.cache:
#             try:
#                 cached_results = self.cache.get(query)
#                 if cached_results is not None:
#                     # Cache hit - return immediately
#                     logger.info(f"✅ Cache hit - skipping retrieval")
#                     return cached_results.get('chunks', [])[:top_k]
#             except Exception as e:
#                 logger.warning(f"Cache check failed: {e}. Proceeding with retrieval.")

#         # --- LAYER 2: QUERY EXPANSION (Optional) ---
#         queries_to_run = [query]  # Original query always included

#         if self.query_expander and ENABLE_QUERY_EXPANSION:
#             try:
#                 expanded_queries = await self.query_expander.expand_query(query)
#                 queries_to_run = expanded_queries  # Includes original + variations
#                 logger.debug(f"Expanded to {len(queries_to_run)} queries")
#             except Exception as e:
#                 logger.warning(f"Query expansion failed: {e}. Using original query only.")
#                 queries_to_run = [query]

#         # --- LAYER 3: BASE RETRIEVAL (Existing retriever - UNCHANGED) ---
#         all_results = []

#         try:
#             for query_variant in queries_to_run:
#                 # SAFETY: Call existing retriever with SAME signature
#                 results = await self.base_retriever.hybrid_retrieve(
#                     query_variant,
#                     top_k=top_k * 2  # Retrieve more for better re-ranking
#                 )
#                 all_results.append(results)

#             # Merge results from all query variations
#             if self.query_expander and len(all_results) > 1:
#                 merged_results = self.query_expander.merge_results(all_results)
#             else:
#                 merged_results = all_results[0] if all_results else []

#         except Exception as e:
#             # SAFETY: On retrieval failure, fall back to single query
#             logger.error(f"Enhanced retrieval failed: {e}. Falling back to base retriever.")
#             merged_results = await self.base_retriever.hybrid_retrieve(query, top_k=top_k)

#         # --- LAYER 4: RE-RANKING (Optional) ---
#         if self.reranker and ENABLE_RERANKING and merged_results:
#             try:
#                 reranked_top_k = RERANKING_CONFIG.get('top_k', top_k)
#                 final_results = self.reranker.rerank(
#                     query,
#                     merged_results,
#                     top_k=reranked_top_k
#                 )
#                 logger.debug(f"Re-ranked {len(merged_results)} → {len(final_results)} chunks")
#             except Exception as e:
#                 logger.warning(f"Re-ranking failed: {e}. Using original ranking.")
#                 final_results = merged_results[:top_k]
#         else:
#             final_results = merged_results[:top_k]

#         # --- LAYER 5: CACHE STORE (For next time) ---
#         if self.cache and final_results:
#             try:
#                 # Store in cache for future queries
#                 cache_entry = {
#                     'chunks': final_results,
#                     'query': query
#                 }
#                 self.cache.set(query, cache_entry)
#             except Exception as e:
#                 logger.warning(f"Cache store failed: {e}. Continuing without caching.")

#         return final_results

#     def get_cache_stats(self) -> Optional[Dict]:
#         """
#         Get cache statistics (if caching enabled).

#         Returns:
#             Cache stats dict or None if caching disabled
#         """
#         if self.cache:
#             return self.cache.get_stats()
#         return None

#     def clear_cache(self):
#         """Clear cache (if enabled)"""
#         if self.cache:
#             self.cache.clear()
#             logger.info("Cache cleared")


# def create_enhanced_retriever(base_retriever) -> EnhancedRetriever:
#     """
#     Factory function to create enhanced retriever.

#     SAFETY:
#     - Check config before creating
#     - Can return base retriever if all enhancements disabled

#     Args:
#         base_retriever: Existing retriever instance

#     Returns:
#         EnhancedRetriever (or base retriever if all disabled)
#     """
#     # Check if ANY enhancement is enabled
#     any_enabled = any([
#         ENABLE_QUERY_EXPANSION,
#         ENABLE_RERANKING,
#         ENABLE_CACHING
#     ])

#     if not any_enabled:
#         logger.info("All enhancements disabled, using base retriever")
#         return base_retriever

#     # Create enhanced wrapper
#     return EnhancedRetriever(base_retriever)
