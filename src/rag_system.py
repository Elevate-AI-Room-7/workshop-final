"""
ChromaDB RAG System - Simple ChromaDB-only implementation
"""

import os
import sys
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import SSL config, but don't fail if not available
try:
    from config.ssl_config import disable_ssl_warnings
except ImportError:
    logger.warning("SSL config not found, continuing without SSL configuration")


def create_rag_system():
    """
    Create ChromaDB RAG system
    
    Returns:
        ChromaDBRAGSystem instance
    """
    logger.info("Creating ChromaDB RAG system...")
    
    try:
        # Try relative import first (when used as module)
        try:
            from .chromadb_rag_system import ChromaDBRAGSystem
        except ImportError:
            # Fallback to absolute import (when used as script)
            from chromadb_rag_system import ChromaDBRAGSystem
        
        return ChromaDBRAGSystem()
    except ImportError as e:
        logger.error(f"ChromaDB RAG system not found: {e}")
        logger.error("Please ensure chromadb_rag_system.py exists in src/ directory")
        raise ImportError("ChromaDB RAG system module not found")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        raise


# For backward compatibility
def get_rag_system():
    """Alias for create_rag_system"""
    return create_rag_system()