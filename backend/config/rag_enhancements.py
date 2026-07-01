"""
RAG Enhancement Configuration - Optional Add-On Layers
All features are TOGGLEABLE and DO NOT modify existing behavior when disabled.
"""

# Feature flags - Set to False to disable any enhancement
ENABLE_QUERY_EXPANSION = True
ENABLE_RERANKING = True
ENABLE_ANSWER_VALIDATION = True
ENABLE_CACHING = True
ENABLE_METADATA_FILTERING = False  # Requires metadata in chunks

# Query Expansion Settings
QUERY_EXPANSION_CONFIG = {
    "max_variations": 3,  # Generate up to 3 alternative queries
    "temperature": 0.3,   # Low temperature for consistent expansions
    "merge_strategy": "union"  # "union" or "replace" original results
}

# Re-ranking Settings
RERANKING_CONFIG = {
    "enabled": ENABLE_RERANKING,
    "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",  # Lightweight model
    "top_k": 5,  # Re-rank top 5 from initial retrieval
    "score_boost": 0.1  # Boost re-ranked scores slightly
}

# Answer Validation Settings
VALIDATION_CONFIG = {
    "enabled": ENABLE_ANSWER_VALIDATION,
    "min_confidence": 0.3,  # Flag answers below this
    "check_hallucination": True,
    "check_grounding": True,
    "log_low_confidence": True  # Log but don't block low confidence answers
}

# Caching Settings
CACHE_CONFIG = {
    "enabled": ENABLE_CACHING,
    "ttl_seconds": 3600,  # 1 hour cache lifetime
    "similarity_threshold": 0.95,  # Very high threshold for cache hits
    "max_cache_size": 1000  # Max cached queries
}

# Metadata Filtering Settings
METADATA_CONFIG = {
    "enabled": ENABLE_METADATA_FILTERING,
    "available_filters": ["category", "date", "source"],
    "default_category": None  # None = no filtering
}
