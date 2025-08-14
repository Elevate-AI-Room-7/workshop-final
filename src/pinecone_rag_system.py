"""
Pinecone RAG System - Retrieval-Augmented Generation with Pinecone Vector Database
"""

import os
import json
from typing import Dict, Any, List, Optional
from pinecone import Pinecone, ServerlessSpec
from openai import AzureOpenAI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PineconeRAGSystem:
    """
    RAG System using Pinecone vector database
    """
    
    def __init__(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        
        # Embedding configuration (dedicated key)
        self.azure_embedding_api_key = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY")
        self.azure_embedding_endpoint = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
        self.embed_model = os.getenv("AZURE_OPENAI_EMBED_MODEL", "text-embedding-3-small")
        
        # Chat configuration (different key for GPT models)
        self.azure_chat_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_chat_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "travel-agency")
        
        # Initialize clients
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        self.embedding_client = AzureOpenAI(
            api_key=self.azure_embedding_api_key,
            azure_endpoint=self.azure_embedding_endpoint,
            api_version="2024-07-01-preview"
        )
        
        # Initialize index
        self.index = self._setup_index()
        
        # Ensure data is loaded
        self._ensure_data_loaded()
    
    def _setup_index(self):
        """Setup or create Pinecone index"""
        try:
            # Check if index exists
            if self.index_name not in self.pc.list_indexes().names():
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # text-embedding-3-small dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
            
            return self.pc.Index(self.index_name)
            
        except Exception as e:
            logger.error(f"Error setting up index: {e}")
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
        """Convert metadata to Pinecone-compatible types"""
        sanitized = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                sanitized[k] = v
            elif isinstance(v, list):
                sanitized[k] = [str(item) for item in v]
            elif isinstance(v, dict):
                sanitized[k] = json.dumps(v, ensure_ascii=False)
            else:
                sanitized[k] = str(v)
        return sanitized
    
    def load_data_to_index(self, json_path: str) -> bool:
        """Load travel data to Pinecone index"""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            vectors = []
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
                metadata["text"] = text  # Store original text for retrieval
                
                vectors.append((entry_id, embedding, metadata))
            
            if vectors:
                # Upsert in batches
                batch_size = 100
                for i in range(0, len(vectors), batch_size):
                    batch = vectors[i:i + batch_size]
                    self.index.upsert(batch)
                
                logger.info(f"Successfully loaded {len(vectors)} vectors to index")
                return True
            else:
                logger.warning("No vectors to load")
                return False
                
        except Exception as e:
            logger.error(f"Error loading data to index: {e}")
            return False
    
    def _ensure_data_loaded(self):
        """Ensure data is loaded in the index"""
        try:
            stats = self.index.describe_index_stats()
            total_count = stats.get('total_vector_count', 0)
            
            if total_count == 0:
                logger.info("Index is empty. Use Knowledge Base tab to add data.")
            else:
                logger.info(f"Index has {total_count} vectors")
                
        except Exception as e:
            logger.error(f"Error checking index stats: {e}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search similar documents in the index"""
        try:
            # Get query embedding
            query_embedding = self.get_embedding(query)
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Format results
            documents = []
            for match in results.get("matches", []):
                documents.append({
                    "id": match.get("id"),
                    "score": match.get("score", 0),
                    "text": match.get("metadata", {}).get("text", ""),
                    "metadata": match.get("metadata", {})
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
            client = AzureOpenAI(
                api_key=self.azure_chat_api_key,
                azure_endpoint=self.azure_chat_endpoint,
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
            client = AzureOpenAI(
                api_key=self.azure_chat_api_key,
                azure_endpoint=self.azure_chat_endpoint,
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
        """Get index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.get('total_vector_count', 0),
                "dimension": stats.get('dimension', 0),
                "index_fullness": stats.get('index_fullness', 0)
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}
    
    def delete_all_vectors(self) -> bool:
        """Delete all vectors from index"""
        try:
            self.index.delete(delete_all=True)
            logger.info("All vectors deleted from index")
            return True
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            return False