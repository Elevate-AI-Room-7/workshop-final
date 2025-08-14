"""
ChromaDB RAG System - Retrieval-Augmented Generation with ChromaDB Vector Database
"""

import os
import json
import sys
from typing import Dict, Any, List, Optional
import chromadb
from chromadb.config import Settings
from openai import AzureOpenAI
import logging
import warnings

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.ssl_config import configure_openai_client, disable_ssl_warnings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChromaDBRAGSystem:
    """
    RAG System using ChromaDB vector database
    """
    
    def __init__(self):
        self.azure_api_key = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.embed_model = os.getenv("AZURE_OPENAI_EMBED_MODEL", "text-embedding-3-small")
        self.collection_name = os.getenv("CHROMADB_COLLECTION_NAME", "travel-agency")
        self.persist_directory = os.getenv("CHROMADB_PERSIST_DIR", "./chromadb_data")
        
        # SSL Verification setting
        self.verify_ssl = os.getenv("VERIFY_SSL", "True").lower() != "false"
        
        # Disable SSL warnings if needed
        disable_ssl_warnings()
        
        # Initialize ChromaDB client
        self.client = self._setup_chromadb()
        
        # Initialize embedding client
        self.embedding_client = configure_openai_client(
            AzureOpenAI,
            api_key=self.azure_api_key,
            azure_endpoint=self.azure_endpoint,
            api_version="2024-07-01-preview"
        )
        
        # Initialize or get collection
        self.collection = self._setup_collection()
        
        # Ensure data is loaded
        self._ensure_data_loaded()
    
    def _setup_chromadb(self):
        """Setup ChromaDB client"""
        try:
            # Create persistent client
            client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info(f"ChromaDB client initialized with persist directory: {self.persist_directory}")
            return client
        except Exception as e:
            logger.error(f"Error setting up ChromaDB: {e}")
            raise
    
    def _setup_collection(self):
        """Setup or create ChromaDB collection"""
        try:
            # Try to get existing collection
            try:
                collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=None  # We'll handle embeddings manually
                )
                logger.info(f"Using existing collection: {self.collection_name}")
            except:
                # Create new collection if doesn't exist
                collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=None,  # We'll handle embeddings manually
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
            
            return collection
            
        except Exception as e:
            logger.error(f"Error setting up collection: {e}")
            raise
    
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
        """Convert metadata to ChromaDB-compatible types"""
        sanitized = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                sanitized[k] = v
            elif isinstance(v, list):
                # ChromaDB doesn't support lists in metadata, convert to string
                sanitized[k] = json.dumps(v, ensure_ascii=False)
            elif isinstance(v, dict):
                sanitized[k] = json.dumps(v, ensure_ascii=False)
            else:
                sanitized[k] = str(v)
        return sanitized
    
    def load_data_to_index(self, json_path: str) -> bool:
        """Load travel data to ChromaDB collection"""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            ids = []
            embeddings = []
            metadatas = []
            documents = []
            
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
                
                ids.append(entry_id)
                embeddings.append(embedding)
                metadatas.append(metadata)
                documents.append(text)
            
            if ids:
                # Add to collection in batches
                batch_size = 100
                for i in range(0, len(ids), batch_size):
                    batch_ids = ids[i:i + batch_size]
                    batch_embeddings = embeddings[i:i + batch_size]
                    batch_metadatas = metadatas[i:i + batch_size]
                    batch_documents = documents[i:i + batch_size]
                    
                    self.collection.add(
                        ids=batch_ids,
                        embeddings=batch_embeddings,
                        metadatas=batch_metadatas,
                        documents=batch_documents
                    )
                
                logger.info(f"Successfully loaded {len(ids)} vectors to collection")
                return True
            else:
                logger.warning("No vectors to load")
                return False
                
        except Exception as e:
            logger.error(f"Error loading data to collection: {e}")
            return False
    
    def _ensure_data_loaded(self):
        """Ensure data is loaded in the collection"""
        try:
            count = self.collection.count()
            
            if count == 0:
                logger.info("Collection is empty. Use Knowledge Base tab to add data.")
            else:
                logger.info(f"Collection has {count} vectors")
                
        except Exception as e:
            logger.error(f"Error checking collection: {e}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search similar documents in the collection"""
        try:
            # Get query embedding
            query_embedding = self.get_embedding(query)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["metadatas", "documents", "distances"]
            )
            
            # Format results
            documents = []
            if results and results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    # ChromaDB returns distance, convert to similarity score
                    # For cosine distance: similarity = 1 - distance
                    distance = results['distances'][0][i] if results['distances'] else 0
                    score = 1 - distance
                    
                    documents.append({
                        "id": results['ids'][0][i],
                        "score": score,
                        "text": results['documents'][0][i] if results['documents'] else "",
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                    })
            
            return documents
            
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
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using context and question"""
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
            
            HƯỚNG DẪN:
            - Trả lời bằng tiếng Việt
            - Sử dụng thông tin từ ngữ cảnh được cung cấp
            - Nếu không có thông tin phù hợp, hãy nói rõ
            - Trả lời ngắn gọn, chi tiết và hữu ích
            - Giữ giọng điệu thân thiện và chuyên nghiệp
            
            TRẢ LỜI:
            """
            
            response = client.chat.completions.create(
                model="GPT-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Xin lỗi, có lỗi xảy ra khi tạo câu trả lời: {str(e)}"
    
    def get_index_stats(self) -> Dict:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                "total_vectors": count,
                "dimension": 1536,
                "index_fullness": 0,  # ChromaDB doesn't have this concept
                "database": "ChromaDB",
                "collection": self.collection_name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def delete_all_vectors(self) -> bool:
        """Delete all vectors from collection"""
        try:
            # Get all IDs
            all_data = self.collection.get()
            if all_data and all_data['ids']:
                self.collection.delete(ids=all_data['ids'])
                logger.info("All vectors deleted from collection")
            return True
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            return False
    
    # Additional ChromaDB-specific methods for compatibility with Pinecone interface
    
    def index(self):
        """Compatibility wrapper to act like Pinecone index"""
        return self
    
    def upsert(self, vectors: List[tuple]) -> None:
        """Upsert vectors in Pinecone format"""
        ids = []
        embeddings = []
        metadatas = []
        
        for vector_tuple in vectors:
            if len(vector_tuple) == 3:
                id, embedding, metadata = vector_tuple
                ids.append(id)
                embeddings.append(embedding)
                metadatas.append(self._sanitize_metadata(metadata))
        
        if ids:
            # Extract text from metadata for documents
            documents = [m.get("text", "") for m in metadatas]
            
            # Upsert to ChromaDB
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
    
    def delete(self, ids: List[str]) -> None:
        """Delete vectors by IDs"""
        if ids:
            self.collection.delete(ids=ids)
    
    def describe_index_stats(self) -> Dict:
        """Compatibility method for Pinecone interface"""
        return self.get_index_stats()