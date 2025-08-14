"""
ChromaDB RAG System - Simple ChromaDB-only implementation
"""

import os
import sys
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.ssl_config import disable_ssl_warnings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_rag_system():
    """
    Create ChromaDB RAG system
    
    Returns:
        ChromaDBRAGSystem instance
    """
    logger.info("Creating ChromaDB RAG system...")
    
    try:
        from .chromadb_rag_system import ChromaDBRAGSystem
        return ChromaDBRAGSystem()
    except ImportError as e:
        logger.error(f"ChromaDB not installed: {e}")
        logger.error("Please install ChromaDB: pip install chromadb")
        raise ImportError("ChromaDB is required but not installed")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        raise


# For backward compatibility
def get_rag_system():
    """Alias for create_rag_system"""
    return create_rag_system()