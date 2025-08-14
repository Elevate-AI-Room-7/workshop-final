"""
RAG System Factory - Creates appropriate RAG system based on configuration
"""

import os
import logging
from typing import Union

logger = logging.getLogger(__name__)


def create_rag_system() -> Union['PineconeRAGSystem', 'ChromaDBRAGSystem']:
    """
    Factory function to create appropriate RAG system based on environment configuration
    
    Returns:
        RAG system instance (either PineconeRAGSystem or ChromaDBRAGSystem)
    """
    vector_db_type = os.getenv("VECTOR_DB_TYPE", "chromadb").lower()
    
    logger.info(f"Creating RAG system with vector DB type: {vector_db_type}")
    
    if vector_db_type == "pinecone":
        from .pinecone_rag_system import PineconeRAGSystem
        return PineconeRAGSystem()
    elif vector_db_type == "chromadb":
        from .chromadb_rag_system import ChromaDBRAGSystem
        return ChromaDBRAGSystem()
    else:
        # Default to ChromaDB if unknown type
        logger.warning(f"Unknown vector DB type: {vector_db_type}, defaulting to ChromaDB")
        from .chromadb_rag_system import ChromaDBRAGSystem
        return ChromaDBRAGSystem()


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