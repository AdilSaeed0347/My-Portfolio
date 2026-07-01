"""
Universal Answer Blueprint System
Domain-agnostic configuration for consistent RAG responses
"""

# Universal answer blueprints - works for ANY domain
ANSWER_BLUEPRINTS = {
    "GREETING": {
        "required": [],
        "optional": [],
        "forbidden": [],
        "max_sentences": 2,
        "temperature": 0.3,
        "top_p": 0.9,
        "tone": "friendly"
    },

    "CAPABILITY": {
        "required": ["capabilities", "scope"],
        "optional": ["limitations"],
        "forbidden": ["unrelated_features"],
        "max_sentences": 3,
        "temperature": 0.25,
        "top_p": 0.85,
        "tone": "professional"
    },

    "USER_INTRODUCTION": {
        "required": ["acknowledgment"],
        "optional": ["personalization"],
        "forbidden": [],
        "max_sentences": 2,
        "temperature": 0.3,
        "top_p": 0.9,
        "tone": "warm"
    },

    "NAME_RECALL": {
        "required": ["stored_name"],
        "optional": ["context"],
        "forbidden": [],
        "max_sentences": 2,
        "temperature": 0.2,
        "top_p": 0.8,
        "tone": "personal"
    },

    "FACTOID": {
        "required": ["direct_answer"],
        "optional": ["brief_context"],
        "forbidden": ["unrelated_details", "speculation"],
        "max_sentences": 3,
        "temperature": 0.2,
        "top_p": 0.85,
        "tone": "professional",
        "priority": "direct_answer_first"
    },

    "EXPLORATORY": {
        "required": ["comprehensive_info", "organized_structure"],
        "optional": ["examples", "details"],
        "forbidden": ["speculation", "personal_opinions"],
        "max_sentences": 8,
        "temperature": 0.3,
        "top_p": 0.9,
        "tone": "informative",
        "priority": "most_important_first"
    },

    "VERIFICATION": {
        "required": ["factual_answer", "evidence"],
        "optional": ["source_reference"],
        "forbidden": ["uncertainty", "speculation"],
        "max_sentences": 4,
        "temperature": 0.15,
        "top_p": 0.8,
        "tone": "authoritative",
        "priority": "fact_first"
    },

    "ACKNOWLEDGMENT": {
        "required": ["polite_response"],
        "optional": ["offer_help"],
        "forbidden": [],
        "max_sentences": 2,
        "temperature": 0.3,
        "top_p": 0.9,
        "tone": "friendly"
    },

    "CLARIFICATION": {
        "required": ["apology", "corrected_answer"],
        "optional": ["explanation"],
        "forbidden": ["defensiveness"],
        "max_sentences": 4,
        "temperature": 0.25,
        "top_p": 0.85,
        "tone": "apologetic"
    },

    "OUT_OF_SCOPE": {
        "required": ["boundary_statement", "redirect"],
        "optional": ["capabilities_reminder"],
        "forbidden": ["attempting_answer"],
        "max_sentences": 2,
        "temperature": 0.2,
        "top_p": 0.8,
        "tone": "polite"
    },

    "POLITE_CHAT": {
        "required": ["friendly_response"],
        "optional": ["offer_help"],
        "forbidden": ["overly_personal"],
        "max_sentences": 2,
        "temperature": 0.35,
        "top_p": 0.9,
        "tone": "conversational"
    }
}

# Default blueprint for unknown intents
DEFAULT_BLUEPRINT = {
    "required": ["relevant_information"],
    "optional": ["context"],
    "forbidden": ["speculation", "unverified_claims"],
    "max_sentences": 5,
    "temperature": 0.3,
    "top_p": 0.9,
    "tone": "professional",
    "priority": "relevant_first"
}

# Universal prompt template
UNIVERSAL_ANSWER_TEMPLATE = """
ANSWER DISCIPLINE SYSTEM - FOLLOW EXACTLY

INTENT: {intent}
REQUIRED INFORMATION: {required_fields}
OPTIONAL INFORMATION: {optional_fields}
FORBIDDEN CONTENT: {forbidden_content}
MAXIMUM LENGTH: {max_sentences} sentences
TONE: {tone}

CRITICAL RULES:
1. CONSISTENCY: Same question → Same FACTS (wording can vary naturally)
2. PRECISION: Use ONLY information from provided context
3. STRUCTURE: Present information in order of importance
4. FOCUS: Stay strictly within the intent scope
5. NO SPECULATION: If information is missing, say so directly

CONTROLLED VARIABILITY:
- You MAY rephrase sentences for natural language
- You MUST NOT add facts not in context
- You MUST NOT omit required information
- You MUST NOT change factual content

{priority_instruction}
"""

# Priority instructions by intent
PRIORITY_INSTRUCTIONS = {
    "direct_answer_first": "Start with the direct answer, then provide context if needed.",
    "most_important_first": "Begin with the most critical information, then add details.",
    "fact_first": "Lead with the factual statement, then provide supporting evidence.",
    "present_state_first": "Focus on current status before historical information.",
    "relevant_first": "Prioritize the most relevant information to the query."
}


def get_answer_blueprint(intent: str) -> dict:
    """
    Universal blueprint loader - works for ANY intent.

    Args:
        intent: Query intent type

    Returns:
        Blueprint configuration dictionary
    """
    return ANSWER_BLUEPRINTS.get(intent, DEFAULT_BLUEPRINT)


def get_generation_config(intent: str) -> dict:
    """
    Get LLM generation parameters for intent.

    Args:
        intent: Query intent type

    Returns:
        Dict with temperature and top_p settings
    """
    blueprint = get_answer_blueprint(intent)
    return {
        "temperature": blueprint.get("temperature", 0.3),
        "top_p": blueprint.get("top_p", 0.9)
    }


def build_discipline_instructions(intent: str, blueprint: dict) -> str:
    """
    Build universal answer discipline instructions.

    Args:
        intent: Query intent type
        blueprint: Answer blueprint configuration

    Returns:
        Formatted instruction string
    """
    # Get priority instruction if specified
    priority_key = blueprint.get("priority", "relevant_first")
    priority_instruction = PRIORITY_INSTRUCTIONS.get(
        priority_key,
        PRIORITY_INSTRUCTIONS["relevant_first"]
    )

    # Format required/optional/forbidden as readable lists
    required = ", ".join(blueprint.get("required", ["relevant information"]))
    optional = ", ".join(blueprint.get("optional", ["additional context"]))
    forbidden = ", ".join(blueprint.get("forbidden", ["speculation"]))

    return UNIVERSAL_ANSWER_TEMPLATE.format(
        intent=intent,
        required_fields=required,
        optional_fields=optional,
        forbidden_content=forbidden,
        max_sentences=blueprint.get("max_sentences", 5),
        tone=blueprint.get("tone", "professional"),
        priority_instruction=priority_instruction
    )


def should_filter_chunk(chunk_text: str, blueprint: dict) -> bool:
    """
    Universal chunk filter based on forbidden content.

    Args:
        chunk_text: Text content of chunk
        blueprint: Answer blueprint configuration

    Returns:
        True if chunk should be filtered out
    """
    forbidden = blueprint.get("forbidden", [])

    # Convert forbidden keywords to indicators
    forbidden_indicators = []
    for item in forbidden:
        # Convert snake_case to space-separated words
        indicators = item.replace("_", " ").split()
        forbidden_indicators.extend(indicators)

    chunk_lower = chunk_text.lower()

    # Check if any forbidden indicator is present
    return any(indicator in chunk_lower for indicator in forbidden_indicators)


def filter_chunks_by_blueprint(chunks: list, intent: str) -> list:
    """
    Universal chunk filtering based on intent blueprint.

    Args:
        chunks: List of retrieved chunks
        intent: Query intent type

    Returns:
        Filtered list of chunks
    """
    blueprint = get_answer_blueprint(intent)

    # Filter out chunks with forbidden content
    filtered = [
        chunk for chunk in chunks
        if not should_filter_chunk(chunk.get('content', ''), blueprint)
    ]

    # If filtering removed all chunks, return original (safety)
    if not filtered and chunks:
        return chunks

    return filtered or chunks
