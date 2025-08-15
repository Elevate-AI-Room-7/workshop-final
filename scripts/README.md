# 📜 Scripts Documentation

## 🗂️ Available Scripts

### 1. `generate_sample_data.py` - Tạo dữ liệu mẫu cho Pinecone

**Purpose**: Tạo dữ liệu du lịch mẫu cho 10 tỉnh thành Việt Nam và upload vào Pinecone.

**Data Coverage**:
- **10 Tỉnh thành**: Hà Nội, TP.HCM, Đà Nẵng, Nha Trang, Đà Lạt, Huế, Hội An, Sapa, Phú Quốc, Cần Thơ
- **3 Categories**: Attractions, Foods, Hotels  
- **Total Records**: ~90 records (9 records per province)

**Usage**:
```bash
# From project root directory
cd /path/to/workshop-final

# Run the script
python scripts/generate_sample_data.py
```

**Sample Output**:
```
🚀 Bắt đầu tạo dữ liệu mẫu cho ChromaDB...
📦 Khởi tạo ChromaDB RAG system...
📝 Tạo dữ liệu mẫu...
✅ Đã tạo 90 records

📊 Thống kê dữ liệu:
  Destination:
    - Hà Nội: 3 records
    - TP.HCM: 3 records
    ...
  Restaurant:
    - Hà Nội: 3 records
    - TP.HCM: 3 records
    ...
  Hotel:
    - Hà Nội: 3 records
    - TP.HCM: 3 records
    ...

⬆️  Upload dữ liệu vào ChromaDB...
  📤 Đã upload 10/90 records...
  📤 Đã upload 20/90 records...
  ...
✅ Hoàn thành! Đã upload 90/90 records vào ChromaDB

🔍 Test tìm kiếm mẫu:
  🔎 Query: 'địa điểm tham quan Hà Nội' → 2 kết quả
     - hanoi-attraction-01: Hồ Hoàn Kiếm với Đền Ngọc Sơn là biểu tượng của Hà Nội...

🎉 Script hoàn thành thành công!
```

**Data Structure Example**:
```json
{
  "id": "hanoi-attraction-01",
  "text": "Hồ Hoàn Kiếm với Đền Ngọc Sơn là biểu tượng của Hà Nội...",
  "metadata": {
    "location": "Hà Nội",
    "category": "destination", 
    "rating": 4.2,
    "price_range": "$",
    "created_at": "2024-12-XX",
    "province_key": "hanoi"
  }
}
```

**Requirements**:
- ChromaDB RAG system đã được setup
- Environment variables đã configured (.env file)
- Azure OpenAI API key cho embeddings

**Error Handling**:
- Script sẽ continue nếu một record upload fail
- Hiển thị progress và error details
- Test search functionality sau khi upload

### 2. `fix_pinecone.bat` / `fix_pinecone.sh` - Legacy Pinecone Setup

**Note**: Deprecated scripts cho Pinecone setup. Hiện tại project sử dụng ChromaDB.

## 🔧 Development Scripts

### Running Scripts

**Option 1: Direct Python**
```bash
python scripts/generate_sample_data.py
```

**Option 2: From project root**
```bash
# Ensure src is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python scripts/generate_sample_data.py
```

**Option 3: With virtual environment**
```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

python scripts/generate_sample_data.py
```

### Script Development Guidelines

1. **Error Handling**: Always include try-catch blocks
2. **Progress Reporting**: Show progress for long operations
3. **Validation**: Validate inputs and environment setup
4. **Logging**: Use clear, informative messages
5. **Testing**: Include basic functionality tests

### Common Issues & Solutions

**Issue**: `ModuleNotFoundError: No module named 'rag_system'`
**Solution**: Run script from project root directory or add src to PYTHONPATH

**Issue**: ChromaDB connection error
**Solution**: Check if ChromaDB service is running and accessible

**Issue**: Azure OpenAI API error
**Solution**: Verify API keys and endpoints in .env file

**Issue**: Permission denied
**Solution**: Make script executable with `chmod +x script_name.py`

## 📊 Data Statistics

After running `generate_sample_data.py`, you will have:

| Category | Records per Province | Total Records |
|----------|---------------------|---------------|
| Attractions | 3 | 30 |
| Foods | 3 | 30 |
| Hotels | 3 | 30 |
| **Total** | **9** | **90** |

**Provinces Covered**:
1. Hà Nội - Capital city attractions, phở, luxury hotels
2. TP.HCM - Historical sites, street food, business hotels  
3. Đà Nẵng - Beaches, Mi Quang, beach resorts
4. Nha Trang - Islands, seafood, beachfront hotels
5. Đà Lạt - Mountains, local specialties, boutique hotels
6. Huế - Imperial sites, royal cuisine, heritage hotels
7. Hội An - Ancient town, cao lau, luxury resorts
8. Sapa - Terraces, mountain food, eco lodges
9. Phú Quốc - Islands, seafood, beach resorts
10. Cần Thơ - Mekong Delta, river food, riverside hotels

---

**Last Updated**: December 2024
**Maintainer**: AI Development Team