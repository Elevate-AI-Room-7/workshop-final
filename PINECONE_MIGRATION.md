# 🔄 Pinecone Migration Guide

Hướng dẫn chi tiết về việc migrate dữ liệu lên Pinecone Vector Database

## 📋 Tổng quan

Project này sử dụng **Pinecone** làm vector database để lưu trữ và tìm kiếm thông tin du lịch. Dữ liệu sẽ được chuyển đổi thành embeddings và upload lên Pinecone index.

## 🏗️ Kiến trúc Pinecone

```
Azure OpenAI Embeddings → Pinecone Index → RAG Search → GPT Response
```

### Thành phần chính:

1. **PineconeRAGSystem**: Class quản lý kết nối và operations với Pinecone
2. **Azure OpenAI Embeddings**: Tạo vector embeddings từ text
3. **Pinecone Index**: Lưu trữ vectors và metadata
4. **RAG Query**: Tìm kiếm và tạo context cho GPT

## 🚀 Bước 1: Chuẩn bị Pinecone

### 1.1. Tạo Pinecone Account

1. Truy cập: https://www.pinecone.io
2. Đăng ký tài khoản miễn phí
3. Tạo project mới

### 1.2. Cấu hình Index

```python
# Index configuration
{
    "name": "travel-agency",
    "dimension": 1536,  # text-embedding-3-small dimension
    "metric": "cosine",
    "cloud": "aws",
    "region": "us-east-1"
}
```

### 1.3. Lấy API Credentials

Trong Pinecone Console:
- Vào **API Keys** tab
- Copy **API Key**
- Note **Environment** và **Index Name**

## 🔧 Bước 2: Cấu hình Project

### 2.1. Environment Variables

Trong file `.env`:

```env
# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=travel-agency
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1

# Azure OpenAI cho Embeddings
AZURE_OPENAI_EMBEDDING_API_KEY=your_embedding_key
AZURE_OPENAI_EMBEDDING_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_EMBED_MODEL=text-embedding-3-small
```

### 2.2. Kiểm tra kết nối

```bash
# Test Pinecone connection
python scripts/test_pinecone_connection.py
```

Script này sẽ kiểm tra:
- ✅ DNS resolution
- ✅ HTTPS connectivity  
- ✅ Pinecone API authentication
- ✅ Index access

## 📊 Bước 3: Migration Scripts

### 3.1. Generate Sample Data

```bash
# Tạo và upload dữ liệu mẫu
python scripts/generate_sample_data.py
```

**Dữ liệu mẫu bao gồm**:
- **10 tỉnh thành**: Hà Nội, TP.HCM, Đà Nẵng, Nha Trang, Đà Lạt, Huế, Hội An, Sapa, Phú Quốc, Cần Thơ
- **3 categories**: Attractions, Foods, Hotels
- **~90 records** tổng cộng

### 3.2. Data Structure

Mỗi record trong Pinecone có cấu trúc:

```json
{
  "id": "hanoi_attraction_1",
  "values": [0.1, 0.2, ...],  // 1536-dimension embedding
  "metadata": {
    "text": "Hồ Hoàn Kiếm là biểu tượng của Hà Nội...",
    "location": "Hà Nội",
    "category": "attraction",
    "name": "Hồ Hoàn Kiếm",
    "description": "Hồ nước ngọt tự nhiên...",
    "rating": 4.8,
    "price_range": "free"
  }
}
```

### 3.3. Upload Process

Script `generate_sample_data.py` thực hiện:

1. **Tạo dữ liệu mẫu** từ `PROVINCES_DATA`
2. **Generate embeddings** qua Azure OpenAI
3. **Sanitize metadata** cho Pinecone format
4. **Batch upload** (100 records/batch)
5. **Verification** và báo cáo kết quả

```python
# Core upload logic
for record in records:
    # Get embedding
    embedding = rag_system.get_embedding(record["text"])
    
    # Sanitize metadata
    metadata = rag_system._sanitize_metadata(record["metadata"])
    metadata["text"] = record["text"]
    
    # Upsert to Pinecone
    rag_system.index.upsert([(record["id"], embedding, metadata)])
```

## 🔍 Bước 4: Verification

### 4.1. Kiểm tra Index Stats

```bash
# Trong Python console
from src.pinecone_rag_system import PineconeRAGSystem

rag = PineconeRAGSystem()
stats = rag.get_index_stats()
print(f"Total vectors: {stats['total_vectors']}")
```

### 4.2. Test Search

```python
# Test search functionality
results = rag.search("Hà Nội du lịch", top_k=5)
for doc in results:
    print(f"ID: {doc['id']}, Score: {doc['score']:.3f}")
    print(f"Text: {doc['text'][:100]}...")
```

### 4.3. Test RAG Query

```python
# Test full RAG pipeline
result = rag.query("Gợi ý địa điểm du lịch ở Hà Nội")
print("Answer:", result['answer'])
print("Sources:", result['sources'])
```

## 🛠️ Bước 5: Custom Data Upload

### 5.1. JSON Format

Để upload dữ liệu tùy chỉnh, tạo file JSON với format:

```json
[
  {
    "id": "unique_id_1",
    "text": "Text content để tạo embedding và tìm kiếm",
    "metadata": {
      "location": "Tên địa điểm",
      "category": "attraction|food|hotel",
      "name": "Tên cụ thể",
      "description": "Mô tả chi tiết",
      "rating": 4.5,
      "price_range": "budget|mid|luxury"
    }
  }
]
```

### 5.2. Upload Custom Data

```python
# Upload từ JSON file
from src.pinecone_rag_system import PineconeRAGSystem

rag = PineconeRAGSystem()
success = rag.load_data_to_index("path/to/your/data.json")
print(f"Upload successful: {success}")
```

### 5.3. Upload qua Streamlit UI

1. Chạy app: `streamlit run app.py`
2. Vào **Knowledge Base** tab
3. Upload JSON file qua interface
4. Kiểm tra kết quả upload

## 📈 Performance Tuning

### 5.1. Batch Size

```python
# Trong generate_sample_data.py
batch_size = 100  # Adjust based on data size và API limits
```

### 5.2. Embedding Model

```env
# Trong .env file
AZURE_OPENAI_EMBED_MODEL=text-embedding-3-small  # 1536 dimensions
# Hoặc text-embedding-3-large cho quality cao hơn (3072 dimensions)
```

### 5.3. Search Parameters

```python
# Trong PineconeRAGSystem.query()
min_score = 0.5      # Minimum similarity threshold
top_k = 5           # Number of documents to retrieve
```

## 🚨 Troubleshooting

### Connection Issues

```bash
# Test từng bước
python scripts/test_pinecone_connection.py
```

**Lỗi thường gặp**:
- **API Key invalid**: Kiểm tra key trong Pinecone console
- **Index not found**: Tạo index với đúng tên và cấu hình
- **Dimension mismatch**: Đảm bảo index dimension = embedding model dimension
- **Rate limiting**: Giảm batch size hoặc thêm delay

### Data Issues

```python
# Kiểm tra dữ liệu uploaded
stats = rag.get_index_stats()
print(f"Current vector count: {stats['total_vectors']}")

# Test search
results = rag.search("test query")
print(f"Search returned {len(results)} results")
```

### Performance Issues

```python
# Monitor search latency
import time
start = time.time()
results = rag.search("query")
print(f"Search took {time.time() - start:.3f}s")
```

## 🔄 Maintenance

### Regular Tasks

1. **Monitor usage**: Kiểm tra Pinecone dashboard
2. **Update data**: Upload dữ liệu mới định kỳ
3. **Clean old data**: Xóa dữ liệu cũ nếu cần
4. **Backup**: Export data nếu cần thiết

### Index Management

```python
# Xóa tất cả vectors (cẩn thận!)
rag.delete_all_vectors()

# Kiểm tra index stats
stats = rag.get_index_stats()
```

## 📚 Resources

- **Pinecone Docs**: https://docs.pinecone.io
- **Azure OpenAI Embeddings**: https://docs.microsoft.com/azure/cognitive-services/openai/
- **Project Repository**: https://github.com/Elevate-AI-Room-7/workshop-final

---

*Migration completed! 🎉*