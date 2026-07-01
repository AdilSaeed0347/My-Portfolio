"""
Minimal working chat API routes - UPDATED with image support
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import time
import logging
from datetime import datetime
from services.rag_pipeline import RAGPipeline
from services.safety import SafetyChecker
from services.memory import ConversationMemory
from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize basic services
safety_checker = SafetyChecker()
conversation_memory = ConversationMemory()

# Request/response models
class ChatMessage(BaseModel):
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="ISO timestamp")

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="User query")
    language: str = Field(default="en", description="Language code (en/ur)")
    session_id: str = Field(..., min_length=5, description="Session identifier")
    timestamp: str = Field(..., description="Request timestamp")
    conversation_history: Optional[List[ChatMessage]] = Field(default=[], description="Recent conversation")

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

    @validator('language')
    def validate_language(cls, v):
        if v not in ['en', 'ur']:
            return 'en'
        return v

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Bot response")
    sources: List[str] = Field(default=[], description="Information sources")
    query_type: str = Field(default="general", description="Query type")
    confidence: Optional[float] = Field(default=None, description="Confidence score")
    processing_time: float = Field(..., description="Processing time in milliseconds")
    session_id: str = Field(..., description="Session identifier")
    # NEW: Image support fields
    images: List[Dict[str, str]] = Field(default=[], description="Images to display")
    show_images_after_ms: int = Field(default=0, description="Delay before showing images")
    response_length: Optional[str] = Field(default=None, description="Response length type")

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, http_request: Request):
    """Main chat endpoint - UPDATED with image support"""
    start_time = time.time()
    
    try:
        logger.info(f"Chat request: session={request.session_id}, query='{request.query[:50]}...'")
        
        # Basic safety check
        safety_result = safety_checker.check_query(request.query)
        if not safety_result.is_safe:
            raise HTTPException(
                status_code=400,
                detail=safety_result.reason
            )
        
        # Update conversation memory
        if request.conversation_history:
            conversation_memory.update_conversation(
                request.session_id, 
                [msg.dict() for msg in request.conversation_history]
            )
        
        # Process with RAG pipeline
        try:
            rag_pipeline = getattr(http_request.app.state, 'rag_pipeline', None)
            
            if not rag_pipeline:
                raise Exception("RAG pipeline not available")
            
            logger.debug("Processing with RAG pipeline...")
            
            # Process query - UPDATED to include query in result
            result = await rag_pipeline.process_query(
                query=request.query,
                language=request.language,
                session_id=request.session_id
            )
            
            # Extract results - UPDATED to handle new fields
            response_text = result.get("answer", "")
            sources = result.get("sources", [])
            confidence = result.get("confidence", 0.8)
            query_type = result.get("query_type", "general")
            images = result.get("images", [])
            show_images_after_ms = result.get("show_images_after_ms", 0)
            response_length = result.get("response_length", None)
            
            logger.info("RAG pipeline processed successfully")
            
        except Exception as e:
            logger.error(f"RAG pipeline error: {e}")
            
            # Simple fallback
            response_text = _generate_simple_fallback(request.query, request.language)
            sources = ["Assistant"]
            confidence = 0.6
            query_type = "fallback"
            images = []
            show_images_after_ms = 0
            response_length = None
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Build response - UPDATED with new fields
        response = ChatResponse(
            answer=response_text,
            sources=sources,
            query_type=query_type,
            confidence=confidence,
            processing_time=processing_time,
            session_id=request.session_id,
            images=images,
            show_images_after_ms=show_images_after_ms,
            response_length=response_length
        )
        
        logger.info(f"Request processed in {processing_time:.2f}ms")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        
        error_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            answer=_get_error_message(request.language),
            sources=[],
            query_type="error",
            confidence=0.0,
            processing_time=error_time,
            session_id=request.session_id,
            images=[],
            show_images_after_ms=0
        )

def _generate_simple_fallback(query: str, language: str) -> str:
    """Simple fallback response"""
    if language == "ur":
        return f"""معذرت، میں '{query}' کے بارے میں مکمل معلومات نہیں دے سکا۔

میں عادل سعید کا AI Assistant ہوں۔ آپ پوچھ سکتے ہیں:
- عادل کے projects
- Technical skills
- Educational background
- Contact information

📧 رابطہ: adilsaeed047@gmail.com"""
    else:
        return f"""I couldn't provide complete information about '{query}'.

I'm Adil Saeed's AI Assistant. You can ask about:
- Adil's projects
- Technical skills  
- Educational background
- Contact information

📧 Contact: adilsaeed047@gmail.com"""

def _get_error_message(language: str) -> str:
    """Get error message"""
    if language == "ur":
        return "تکنیکی مسئلہ ہے۔ برائے کرم دوبارہ کوشش کریں۔"
    else:
        return "Technical issue occurred. Please try again."

# Health check endpoint
@router.get("/chat/health")
async def chat_health():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "safety_checker": "active",
            "conversation_memory": "active",
            "groq_configured": bool(getattr(settings, 'GROQ_API_KEY', None))
        },
        "active_sessions": conversation_memory.get_active_session_count(),
        "features": ["image_support", "response_length_control"]  # NEW
    }

@router.get("/chat/stats")
async def chat_stats():
    """Chat statistics"""
    return {
        "memory_stats": conversation_memory.get_memory_stats(),
        "supported_languages": ["en", "ur"],
        "max_query_length": 500,
        "features": ["conversation_memory", "safety_checking", "multilingual", "image_integration"]  # UPDATED
    }