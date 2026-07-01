# """
# Query Expansion Enhancement - OPTIONAL ADD-ON
# Generates alternative queries to improve retrieval recall.

# SAFETY GUARANTEE:
# - Only used when ENABLE_QUERY_EXPANSION = True
# - Original query is ALWAYS included in results
# - Falls back to original query if expansion fails
# - Does NOT modify existing retrieval logic
# """
# import logging
# from typing import List
# from groq import AsyncGroq

# from config.settings import settings
# from config.rag_enhancements import QUERY_EXPANSION_CONFIG

# logger = logging.getLogger(__name__)


# class QueryExpander:
#     """
#     Optional query expansion layer.
#     Generates semantically similar queries for better coverage.
#     """

#     def __init__(self):
#         self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
#         self.config = QUERY_EXPANSION_CONFIG

#     async def expand_query(self, original_query: str) -> List[str]:
#         """
#         Generate alternative phrasings of the query.

#         CRITICAL: Original query is ALWAYS first in the list.

#         Args:
#             original_query: User's original question

#         Returns:
#             List[str]: [original_query, variation1, variation2, ...]

#         Safety:
#             - If expansion fails, returns [original_query] only
#             - Never modifies the original query
#             - Preserves existing behavior on failure
#         """
#         try:
#             # Generate variations
#             prompt = f"""Generate {self.config['max_variations']} alternative ways to ask this question.
# Keep the same meaning but use different keywords.

# Original: "{original_query}"

# Requirements:
# - Use synonyms and related terms
# - Be concise (1 sentence each)
# - Keep same intent

# Format: One per line, no numbering."""

#             response = await self.groq_client.chat.completions.create(
#                 model=settings.GROQ_MODEL_EN,
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=self.config['temperature'],
#                 max_tokens=100
#             )

#             # Parse variations
#             variations = [
#                 line.strip()
#                 for line in response.choices[0].message.content.strip().split('\n')
#                 if line.strip() and len(line.strip()) > 5
#             ]

#             # SAFETY: Original query is ALWAYS first
#             expanded = [original_query] + variations[:self.config['max_variations']]

#             logger.info(f"Query expansion: {original_query} → {len(expanded)} variations")
#             return expanded

#         except Exception as e:
#             # SAFETY: On error, fall back to original query only
#             logger.warning(f"Query expansion failed: {e}. Using original query only.")
#             return [original_query]

#     def merge_results(self, results_by_query: List[List[dict]], strategy: str = None) -> List[dict]:
#         """
#         Merge results from multiple query variations.

#         Args:
#             results_by_query: List of result lists from each query variation
#             strategy: "union" (combine all) or "intersection" (only common)

#         Returns:
#             Merged and deduplicated results

#         Safety:
#             - Preserves original query results (first in list)
#             - Deduplicates by content to avoid redundancy
#             - Maintains score information
#         """
#         if not results_by_query:
#             return []

#         strategy = strategy or self.config['merge_strategy']

#         if strategy == "union":
#             # Combine all results, deduplicate by content
#             seen_content = set()
#             merged = []

#             for results in results_by_query:
#                 for result in results:
#                     content = result.get('content', '')
#                     if content not in seen_content:
#                         seen_content.add(content)
#                         merged.append(result)

#             # Sort by score (highest first)
#             merged.sort(key=lambda x: x.get('score', 0), reverse=True)

#             logger.debug(f"Merged {sum(len(r) for r in results_by_query)} results → {len(merged)} unique")
#             return merged

#         elif strategy == "intersection":
#             # Only keep results that appear in multiple variations
#             # (More conservative, higher precision)
#             content_counts = {}

#             for results in results_by_query:
#                 for result in results:
#                     content = result.get('content', '')
#                     if content not in content_counts:
#                         content_counts[content] = {'count': 0, 'result': result}
#                     content_counts[content]['count'] += 1

#             # Keep results that appear in at least 2 variations
#             threshold = max(2, len(results_by_query) // 2)
#             merged = [
#                 data['result']
#                 for content, data in content_counts.items()
#                 if data['count'] >= threshold
#             ]

#             merged.sort(key=lambda x: x.get('score', 0), reverse=True)

#             logger.debug(f"Intersection merge: {len(merged)} results (threshold={threshold})")
#             return merged

#         else:
#             # SAFETY: Unknown strategy, return original results only
#             logger.warning(f"Unknown merge strategy: {strategy}. Using original results.")
#             return results_by_query[0] if results_by_query else []


# # Global instance (lazy loaded)
# _query_expander = None

# def get_query_expander() -> QueryExpander:
#     """Get or create global QueryExpander instance"""
#     global _query_expander
#     if _query_expander is None:
#         _query_expander = QueryExpander()
#     return _query_expander
