"""
In-Memory RAG System - Simple fallback when other vector DBs are not available
"""

import os
import json
import sys
from typing import Dict, Any, List, Optional
from openai import AzureOpenAI
import logging
import warnings
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.ssl_config import configure_openai_client, disable_ssl_warnings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InMemoryRAGSystem:
    """
    Simple in-memory RAG system that doesn't require external dependencies
    Data is stored in memory and lost when application restarts
    """
    
    def __init__(self):
        self.azure_api_key = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.embed_model = os.getenv("AZURE_OPENAI_EMBED_MODEL", "text-embedding-3-small")
        
        # SSL Verification setting
        self.verify_ssl = os.getenv("VERIFY_SSL", "True").lower() != "false"
        
        # Disable SSL warnings if needed
        disable_ssl_warnings()
        
        # Initialize embedding client
        self.embedding_client = configure_openai_client(
            AzureOpenAI,
            api_key=self.azure_api_key,
            azure_endpoint=self.azure_endpoint,
            api_version="2024-07-01-preview"
        )
        
        # In-memory storage
        self.documents = {}  # id -> {"text": str, "metadata": dict, "embedding": list}
        
        logger.info("Initialized in-memory RAG system (no persistence)")
        logger.warning("Data will be lost when application restarts!")
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Azure OpenAI"""
        try:
            response = self.embedding_client.embeddings.create(
                model=self.embed_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise
    
    def _sanitize_metadata(self, metadata: Dict) -> Dict:
        """Convert metadata to compatible types"""
        sanitized = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                sanitized[k] = v
            elif isinstance(v, list):
                sanitized[k] = json.dumps(v, ensure_ascii=False)
            elif isinstance(v, dict):
                sanitized[k] = json.dumps(v, ensure_ascii=False)
            else:
                sanitized[k] = str(v)
        return sanitized
    
    def load_data_to_index(self, json_path: str) -> bool:
        """Load travel data to in-memory storage"""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            loaded_count = 0
            for entry in data:
                entry_id = entry.get("id")
                text = entry.get("text")
                metadata = entry.get("metadata", {})
                
                if not entry_id or not text:
                    continue
                
                # Get embedding
                embedding = self.get_embedding(text)
                
                # Sanitize metadata
                metadata = self._sanitize_metadata(metadata)
                
                # Store in memory
                self.documents[entry_id] = {
                    "text": text,
                    "metadata": metadata,
                    "embedding": embedding
                }
                
                loaded_count += 1
            
            if loaded_count > 0:
                logger.info(f"Successfully loaded {loaded_count} documents to memory")
                return True
            else:
                logger.warning("No documents to load")
                return False
                
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search similar documents in memory"""
        try:
            if not self.documents:
                logger.warning("No documents in memory")
                return []
            
            # Get query embedding
            query_embedding = self.get_embedding(query)
            
            # Calculate similarities
            results = []
            for doc_id, doc_data in self.documents.items():
                doc_embedding = doc_data["embedding"]
                
                # Calculate cosine similarity
                similarity = cosine_similarity(
                    [query_embedding], 
                    [doc_embedding]
                )[0][0]
                
                results.append({
                    "id": doc_id,
                    "score": similarity,
                    "text": doc_data["text"],
                    "metadata": doc_data["metadata"]
                })
            
            # Sort by similarity (descending) and return top_k
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Query the RAG system with a question
        
        Args:
            question: User's question
            top_k: Number of top documents to retrieve
            
        Returns:
            Dict with answer and source documents
        """
        try:
            # Search for relevant documents
            documents = self.search(question, top_k)
            
            # Filter documents by relevance score (minimum threshold)
            min_score = 0.5  # Lowered threshold for better coverage
            relevant_docs = [doc for doc in documents if doc.get('score', 0) >= min_score]
            
            logger.info(f"Found {len(documents)} total docs, {len(relevant_docs)} above threshold {min_score}")
            
            if not relevant_docs:
                logger.info("No relevant docs found, returning no_relevant_info")
                return {
                    "answer": None,  # Signal that no relevant info was found
                    "source_documents": [],
                    "context_used": "",
                    "sources": [],
                    "no_relevant_info": True,
                    "query": question
                }
            
            logger.info(f"Using {len(relevant_docs)} relevant docs for answer generation")
            
            # Prepare context with numbered chunks for tracking
            context_parts = []
            chunk_mapping = {}
            for i, doc in enumerate(relevant_docs):
                chunk_id = f"CHUNK_{i+1}"
                context_parts.append(f"[{chunk_id}] {doc['text']}")
                chunk_mapping[chunk_id] = doc["id"]
            
            context = "\n".join(context_parts)
            
            # Generate answer with source tracking
            result = self._generate_answer_with_sources(question, context, chunk_mapping)
            
            # If no chunks were cited, fall back to showing all sources
            used_sources = result["used_sources"]
            if not used_sources and relevant_docs:
                logger.info("No chunks cited, falling back to all sources")
                used_sources = [doc["id"] for doc in relevant_docs[:3]]  # Show top 3
            
            logger.info(f"Final sources to display: {used_sources}")
            
            return {
                "answer": result["answer"],
                "source_documents": relevant_docs,
                "context_used": context,
                "sources": used_sources,  # Sources to display (used or fallback)
                "all_sources": [doc["id"] for doc in relevant_docs]  # All retrieved sources
            }
            
        except Exception as e:
            logger.error(f"Error in query: {e}")
            return {
                "answer": f"Xin lỗi, có lỗi xảy ra khi xử lý câu hỏi: {str(e)}",
                "source_documents": [],
                "context_used": "",
                "sources": [],
                "error": str(e)
            }
    
    def _generate_answer_with_sources(self, question: str, context: str, chunk_mapping: Dict) -> Dict[str, Any]:
        """Generate answer and track which chunks were actually used"""
        try:
            client = configure_openai_client(
                AzureOpenAI,
                api_key=self.azure_api_key,
                azure_endpoint=self.azure_endpoint,
                api_version="2024-07-01-preview"
            )
            
            prompt = f"""
            Bạn là trợ lý du lịch thông minh chuyên về du lịch Việt Nam.
            
            Dựa vào thông tin sau đây để trả lời câu hỏi của khách hàng:
            
            THÔNG TIN THAM KHẢO:
            {context}
            
            CÂU HỎI: {question}
            
            HƯỚNG DẪN QUAN TRỌNG:
            - Trả lời bằng tiếng Việt
            - BẮT BUỘC: Khi sử dụng thông tin từ chunk nào, PHẢI ghi [CHUNK_X] ngay sau thông tin đó
            - Ví dụ: "Hà Nội có Hồ Hoàn Kiếm [CHUNK_1] và phố cổ với 36 phố phường [CHUNK_2]"
            - Nếu thông tin không đủ để trả lời, hãy trả lời "NO_RELEVANT_INFO"
            - Chỉ sử dụng thông tin từ các chunk được cung cấp
            - Trả lời chi tiết và hữu ích
            
            Hãy trả lời và nhớ ghi rõ [CHUNK_X] cho mỗi thông tin sử dụng:
            """
            
            response = client.chat.completions.create(
                model="GPT-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            logger.info(f"Raw LLM response: {answer[:200]}...")
            
            # Check if no relevant info found
            if "NO_RELEVANT_INFO" in answer:
                logger.info("LLM returned NO_RELEVANT_INFO")
                return {
                    "answer": None,
                    "used_sources": []
                }
            
            # Extract which chunks were referenced
            import re
            used_chunks = re.findall(r'\[CHUNK_(\d+)\]', answer)
            logger.info(f"Found chunk references: {used_chunks}")
            
            used_sources = []
            for chunk_num in used_chunks:
                chunk_id = f"CHUNK_{chunk_num}"
                if chunk_id in chunk_mapping:
                    used_sources.append(chunk_mapping[chunk_id])
                    logger.info(f"Mapped {chunk_id} to {chunk_mapping[chunk_id]}")
            
            logger.info(f"Used sources: {used_sources}")
            
            # Clean the answer by removing chunk references
            clean_answer = re.sub(r'\[CHUNK_\d+\]', '', answer).strip()
            
            return {
                "answer": clean_answer,
                "used_sources": list(set(used_sources))  # Remove duplicates
            }
            
        except Exception as e:
            logger.error(f"Error generating answer with sources: {e}")
            return {
                "answer": f"Xin lỗi, có lỗi xảy ra khi tạo câu trả lời: {str(e)}",
                "used_sources": []
            }
    
    def get_index_stats(self) -> Dict:
        """Get statistics"""
        return {
            "total_vectors": len(self.documents),
            "dimension": 1536,
            "index_fullness": 0,
            "database": "In-Memory",
            "status": "active"
        }
    
    def delete_all_vectors(self) -> bool:
        """Delete all documents from memory"""
        try:
            self.documents.clear()
            logger.info("All documents deleted from memory")
            return True
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return False
    
    def get_index_stats(self) -> Dict:
        """Get statistics"""
        return {
            "total_vectors": len(self.documents),
            "dimension": 1536,
            "index_fullness": 0,
            "database": "In-Memory",
            "status": "active"
        }
    
    # Compatibility methods for Pinecone-like interface
    
    def index(self):
        """Compatibility wrapper to act like Pinecone index"""
        return self
    
    def upsert(self, vectors: List[tuple]) -> None:
        """Upsert vectors in Pinecone format"""
        for vector_tuple in vectors:
            if len(vector_tuple) == 3:
                doc_id, embedding, metadata = vector_tuple
                metadata = self._sanitize_metadata(metadata)
                text = metadata.get("text", "")
                
                self.documents[doc_id] = {
                    "text": text,
                    "metadata": metadata,
                    "embedding": embedding
                }
    
    def delete(self, ids: List[str]) -> None:
        """Delete documents by IDs"""
        for doc_id in ids:
            if doc_id in self.documents:
                del self.documents[doc_id]
    
    def describe_index_stats(self) -> Dict:
        """Compatibility method for Pinecone interface"""
        return self.get_index_stats()