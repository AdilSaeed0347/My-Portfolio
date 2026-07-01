# """
# Re-Ranking Enhancement - OPTIONAL ADD-ON
# Re-ranks retrieved chunks using cross-encoder for better precision.

# SAFETY GUARANTEE:
# - Only used when ENABLE_RERANKING = True
# - Operates AFTER existing retrieval (non-invasive)
# - Falls back to original scores if re-ranking fails
# - Does NOT modify retrieval logic
# """
# import logging
# from typing import List, Dict

# logger = logging.getLogger(__name__)

# # Lazy import to avoid dependency if not used
# _cross_encoder = None


# def get_cross_encoder():
#     """
#     Lazy load cross-encoder model.

#     Safety:
#         - Only loaded if re-ranking is actually used
#         - Fails gracefully if model unavailable
#     """
#     global _cross_encoder
#     if _cross_encoder is None:
#         try:
#             from sentence_transformers import CrossEncoder
#             from config.rag_enhancements import RERANKING_CONFIG

#             model_name = RERANKING_CONFIG['model']
#             _cross_encoder = CrossEncoder(model_name)
#             logger.info(f"Loaded cross-encoder: {model_name}")

#         except ImportError:
#             logger.warning("sentence-transformers not installed. Re-ranking disabled.")
#             _cross_encoder = False  # Sentinel to avoid retrying
#         except Exception as e:
#             logger.error(f"Failed to load cross-encoder: {e}")
#             _cross_encoder = False

#     return _cross_encoder if _cross_encoder is not False else None


# class ReRanker:
#     """
#     Optional re-ranking layer using cross-encoder.
#     Improves precision of top-K results.
#     """

#     def __init__(self):
#         self.model = None  # Lazy loaded

#     def rerank(self, query: str, chunks: List[dict], top_k: int = 5) -> List[dict]:
#         """
#         Re-rank chunks using cross-encoder scoring.

#         CRITICAL SAFETY:
#         - Original chunks are NOT modified
#         - If re-ranking fails, returns original chunks in original order
#         - Preserves all chunk metadata

#         Args:
#             query: User's question
#             chunks: Retrieved chunks from existing retrieval
#             top_k: Number of top chunks to return after re-ranking

#         Returns:
#             Re-ranked chunks (or original if re-ranking fails)
#         """
#         if not chunks:
#             return chunks

#         # Lazy load model
#         if self.model is None:
#             self.model = get_cross_encoder()

#         # SAFETY: If model unavailable, return original chunks
#         if self.model is None:
#             logger.debug("Cross-encoder unavailable, using original ranking")
#             return chunks[:top_k]

#         try:
#             # Create query-chunk pairs
#             pairs = [[query, chunk.get('content', '')] for chunk in chunks]

#             # Score all pairs
#             scores = self.model.predict(pairs)

#             # SAFETY: Create new list with rerank scores, preserve originals
#             reranked_chunks = []
#             for chunk, score in zip(chunks, scores):
#                 # Create shallow copy to avoid modifying original
#                 reranked_chunk = chunk.copy()
#                 reranked_chunk['rerank_score'] = float(score)
#                 # Preserve original score
#                 reranked_chunk['original_score'] = chunk.get('score', 0.0)
#                 reranked_chunks.append(reranked_chunk)

#             # Sort by rerank score (descending)
#             reranked_chunks.sort(key=lambda x: x['rerank_score'], reverse=True)

#             logger.info(f"Re-ranked {len(chunks)} chunks, returning top {top_k}")

#             return reranked_chunks[:top_k]

#         except Exception as e:
#             # SAFETY: On any error, fall back to original chunks
#             logger.warning(f"Re-ranking failed: {e}. Using original ranking.")
#             return chunks[:top_k]


# # Global instance
# _reranker = None

# def get_reranker() -> ReRanker:
#     """Get or create global ReRanker instance"""
#     global _reranker
#     if _reranker is None:
#         _reranker = ReRanker()
#     return _reranker
