"""
RAG System Factory - Creates appropriate RAG system based on configuration
"""

import os
import logging
from typing import Union

logger = logging.getLogger(__name__)


def create_rag_system() -> Union['PineconeRAGSystem', 'ChromaDBRAGSystem', 'InMemoryRAGSystem']:
    """
    Factory function to create appropriate RAG system based on environment configuration
    
    Returns:
        RAG system instance (PineconeRAGSystem, ChromaDBRAGSystem, or InMemoryRAGSystem)
    """
    vector_db_type = os.getenv("VECTOR_DB_TYPE", "chromadb").lower()
    
    logger.info(f"Creating RAG system with vector DB type: {vector_db_type}")
    
    if vector_db_type == "pinecone":
        try:
            from .pinecone_rag_system import PineconeRAGSystem
            return PineconeRAGSystem()
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            logger.info("Falling back to in-memory RAG system")
            return _create_fallback_rag_system()
    
    elif vector_db_type == "chromadb":
        try:
            from .chromadb_rag_system import ChromaDBRAGSystem
            return ChromaDBRAGSystem()
        except ImportError as e:
            logger.error(f"ChromaDB not installed: {e}")
            logger.info("ChromaDB requires additional dependencies. See scripts/install_chromadb.bat")
            logger.info("Falling back to Pinecone or in-memory system")
            return _create_fallback_rag_system()
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            logger.info("Falling back to in-memory RAG system")
            return _create_fallback_rag_system()
    
    else:
        # Default to ChromaDB if unknown type, with fallback
        logger.warning(f"Unknown vector DB type: {vector_db_type}, trying ChromaDB first")
        try:
            from .chromadb_rag_system import ChromaDBRAGSystem
            return ChromaDBRAGSystem()
        except:
            return _create_fallback_rag_system()

def _create_fallback_rag_system():
    """Create fallback RAG system when primary options fail"""
    # Try Pinecone first if available
    try:
        from .pinecone_rag_system import PineconeRAGSystem
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if pinecone_api_key:
            logger.info("Trying Pinecone as fallback")
            return PineconeRAGSystem()
    except Exception as e:
        logger.error(f"Pinecone fallback failed: {e}")
    
    # Fall back to in-memory system
    logger.info("Using in-memory RAG system (no persistence)")
    return _create_in_memory_rag_system()

def _create_in_memory_rag_system():
    """Create a simple in-memory RAG system"""
    from .in_memory_rag_system import InMemoryRAGSystem
    return InMemoryRAGSystem()


class RAGSystemInterface:
    """
    Common interface for all RAG systems to ensure compatibility
    """
    
    def get_embedding(self, text: str):
        """Get embedding for text"""
        raise NotImplementedError
    
    def search(self, query: str, top_k: int = 5):
        """Search similar documents"""
        raise NotImplementedError
    
    def query(self, question: str, top_k: int = 5):
        """Query the RAG system with a question"""
        raise NotImplementedError
    
    def load_data_to_index(self, json_path: str):
        """Load data to the vector database"""
        raise NotImplementedError
    
    def get_index_stats(self):
        """Get statistics about the vector database"""
        raise NotImplementedError
    
    def delete_all_vectors(self):
        """Delete all vectors from the database"""
        raise NotImplementedError