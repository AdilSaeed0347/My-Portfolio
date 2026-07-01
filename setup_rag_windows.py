#!/usr/bin/env python3
"""
Setup script for Adil's Portfolio RAG System (Windows Compatible)
Initializes the vector database with documents
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('setup.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_environment():
    """Check if environment is properly configured"""
    logger = logging.getLogger(__name__)
    
    # Check .env file
    env_file = project_root / '.env'
    if not env_file.exists():
        logger.error("[ERROR] .env file not found! Please create it with your API keys.")
        return False
    
    # Check for GROQ_API_KEY
    from dotenv import load_dotenv
    load_dotenv()
    
    groq_key = os.getenv('GROQ_API_KEY')
    if not groq_key:
        logger.error("[ERROR] GROQ_API_KEY not found in .env file!")
        return False
    
    logger.info("[SUCCESS] Environment configuration looks good!")
    return True

def check_directories():
    """Ensure all required directories exist"""
    logger = logging.getLogger(__name__)
    
    required_dirs = [
        'rag/documents',
        'rag/vectorstore',
        'rag/embeddings',
        'logs',
        'backend/routes',
        'backend/services'
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"[SUCCESS] Directory ensured: {dir_path}")
    
    return True

def initialize_rag_system():
    """Initialize the RAG system with documents"""
    logger = logging.getLogger(__name__)
    
    try:
        # Import retriever
        from rag.modules.retriever import DocumentRetriever
        
        logger.info("[STARTING] Initializing RAG system...")
        
        # Create retriever instance
        retriever = DocumentRetriever()
        
        # Check if documents are already loaded
        stats = retriever.get_statistics()
        logger.info(f"[INFO] Current stats: {stats}")
        
        if stats['total_chunks'] > 0:
            logger.info("[SUCCESS] RAG system already has documents loaded!")
            logger.info(f"   - Total chunks: {stats['total_chunks']}")
            logger.info(f"   - Project chunks: {stats['project_chunks']}")
            logger.info(f"   - Unique sources: {stats['unique_sources']}")
            return True
        
        # Load documents if empty
        documents_dir = project_root / 'rag' / 'documents'
        adil_file = documents_dir / 'Adil.txt'
        
        if adil_file.exists():
            logger.info(f"[LOADING] Loading document: {adil_file}")
            retriever.add_documents(str(adil_file), "Adil_Portfolio")
            
            # Check final stats
            final_stats = retriever.get_statistics()
            logger.info("[SUCCESS] RAG system initialized successfully!")
            logger.info(f"   - Total chunks: {final_stats['total_chunks']}")
            logger.info(f"   - Project chunks: {final_stats['project_chunks']}")
            logger.info(f"   - Index size: {final_stats['index_size']}")
            
            return True
        else:
            logger.error(f"[ERROR] Document file not found: {adil_file}")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize RAG system: {e}")
        return False

def test_rag_system():
    """Test the RAG system with sample queries"""
    logger = logging.getLogger(__name__)
    
    try:
        from backend.services.rag_pipeline import RAGPipeline
        import asyncio
        
        logger.info("[TESTING] Testing RAG system...")
        
        # Create pipeline instance
        pipeline = RAGPipeline()
        
        # Test queries
        test_queries = [
            "Who is Adil Saeed?",
            "What projects has Adil worked on?",
            "How can I contact Adil?",
            "Tell me about his education"
        ]
        
        async def run_tests():
            for query in test_queries:
                logger.info(f"[TEST] Testing query: {query}")
                try:
                    result = await pipeline.process_query(query)
                    logger.info(f"[SUCCESS] Query successful - Type: {result.query_type}")
                except Exception as e:
                    logger.error(f"[ERROR] Query failed: {e}")
                    return False
            return True
        
        # Run async tests
        success = asyncio.run(run_tests())
        
        if success:
            logger.info("[SUCCESS] All RAG system tests passed!")
            return True
        else:
            logger.error("[ERROR] Some RAG system tests failed!")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] Failed to test RAG system: {e}")
        return False

def main():
    """Main setup function"""
    logger = setup_logging()
    
    logger.info("[STARTING] Starting Adil's Portfolio RAG Setup...")
    
    # Step 1: Check environment
    if not check_environment():
        logger.error("[FAILED] Environment check failed!")
        return False
    
    # Step 2: Check directories
    if not check_directories():
        logger.error("[FAILED] Directory setup failed!")
        return False
    
    # Step 3: Initialize RAG system
    if not initialize_rag_system():
        logger.error("[FAILED] RAG system initialization failed!")
        return False
    
    # Step 4: Test RAG system
    if not test_rag_system():
        logger.error("[FAILED] RAG system testing failed!")
        return False
    
    logger.info("[COMPLETE] Setup completed successfully!")
    logger.info("You can now run the server with:")
    logger.info("   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)