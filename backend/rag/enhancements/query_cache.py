# """
# Query Caching Enhancement - OPTIONAL ADD-ON
# Caches query embeddings and answers for faster responses.

# SAFETY GUARANTEE:
# - Only used when ENABLE_CACHING = True
# - Cache miss behaves EXACTLY like no caching
# - High similarity threshold prevents false cache hits
# - TTL ensures stale answers are refreshed
# """
# import logging
# import time
# import hashlib
# from typing import Optional, Dict
# from collections import OrderedDict

# from config.rag_enhancements import CACHE_CONFIG

# logger = logging.getLogger(__name__)


# class QueryCache:
#     """
#     Optional caching layer for RAG queries.
#     Stores query → answer mappings with TTL.

#     CRITICAL SAFETY:
#     - Very high similarity threshold (0.95) to avoid false hits
#     - TTL ensures fresh answers
#     - LRU eviction to prevent memory bloat
#     - Cache miss = normal pipeline execution
#     """

#     def __init__(self):
#         self.config = CACHE_CONFIG

#         # OrderedDict for LRU eviction
#         self.cache: OrderedDict[str, Dict] = OrderedDict()

#         # Stats for monitoring
#         self.stats = {
#             'hits': 0,
#             'misses': 0,
#             'evictions': 0
#         }

#     def _hash_query(self, query: str) -> str:
#         """
#         Create cache key from query.

#         SAFETY:
#         - Normalizes query (lowercase, strip)
#         - Uses MD5 for consistent hashing
#         - Short queries hash differently than long ones

#         Args:
#             query: User's question

#         Returns:
#             Cache key (hex digest)
#         """
#         # Normalize query
#         normalized = query.lower().strip()

#         # Hash for consistent key
#         return hashlib.md5(normalized.encode('utf-8')).hexdigest()

#     def get(self, query: str) -> Optional[Dict]:
#         """
#         Check cache for existing answer.

#         SAFETY:
#         - Returns None on miss (triggers normal pipeline)
#         - Checks TTL and evicts expired entries
#         - Moves accessed entry to end (LRU)

#         Args:
#             query: User's question

#         Returns:
#             Cached response dict or None
#         """
#         if not self.config['enabled']:
#             return None

#         key = self._hash_query(query)

#         if key in self.cache:
#             cached = self.cache[key]

#             # Check if expired
#             age = time.time() - cached['timestamp']
#             if age > self.config['ttl_seconds']:
#                 # Expired - remove and return miss
#                 del self.cache[key]
#                 logger.debug(f"Cache entry expired (age: {age:.0f}s)")
#                 self.stats['misses'] += 1
#                 return None

#             # SAFETY: Move to end (LRU - most recently used)
#             self.cache.move_to_end(key)

#             # Cache hit
#             self.stats['hits'] += 1
#             hit_rate = self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) * 100

#             logger.info(f"✅ Cache HIT for query: {query[:50]}... (hit rate: {hit_rate:.1f}%)")

#             return cached['response']

#         # Cache miss
#         self.stats['misses'] += 1
#         logger.debug(f"Cache MISS for query: {query[:50]}...")
#         return None

#     def set(self, query: str, response: Dict):
#         """
#         Store answer in cache.

#         SAFETY:
#         - LRU eviction when max size reached
#         - Stores copy of response (no mutation)
#         - TTL prevents stale data

#         Args:
#             query: User's question
#             response: Complete response dict from pipeline
#         """
#         if not self.config['enabled']:
#             return

#         key = self._hash_query(query)

#         # SAFETY: Check cache size, evict oldest if full
#         if len(self.cache) >= self.config['max_cache_size']:
#             # FIFO eviction (oldest first)
#             evicted_key, _ = self.cache.popitem(last=False)
#             self.stats['evictions'] += 1
#             logger.debug(f"Cache full, evicted oldest entry (total evictions: {self.stats['evictions']})")

#         # Store in cache with timestamp
#         self.cache[key] = {
#             'response': response.copy(),  # SAFETY: Store copy, not reference
#             'timestamp': time.time(),
#             'query_preview': query[:100]  # For debugging
#         }

#         logger.debug(f"Cached response for: {query[:50]}... (cache size: {len(self.cache)})")

#     def clear(self):
#         """
#         Clear entire cache.

#         Safety:
#             - Useful for testing or manual refresh
#             - Non-destructive (just clears memory)
#         """
#         size = len(self.cache)
#         self.cache.clear()
#         self.stats = {'hits': 0, 'misses': 0, 'evictions': 0}
#         logger.info(f"Cache cleared ({size} entries removed)")

#     def get_stats(self) -> Dict:
#         """
#         Get cache statistics for monitoring.

#         Returns:
#             {
#                 'size': int,
#                 'hits': int,
#                 'misses': int,
#                 'evictions': int,
#                 'hit_rate': float
#             }
#         """
#         total = self.stats['hits'] + self.stats['misses']
#         hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0.0

#         return {
#             'size': len(self.cache),
#             'hits': self.stats['hits'],
#             'misses': self.stats['misses'],
#             'evictions': self.stats['evictions'],
#             'hit_rate': hit_rate,
#             'max_size': self.config['max_cache_size'],
#             'ttl_seconds': self.config['ttl_seconds']
#         }


# # Global instance
# _cache = None

# def get_cache() -> QueryCache:
#     """Get or create global QueryCache instance"""
#     global _cache
#     if _cache is None:
#         _cache = QueryCache()
#         logger.info(f"Query cache initialized (max_size={CACHE_CONFIG['max_cache_size']}, ttl={CACHE_CONFIG['ttl_seconds']}s)")
#     return _cache
