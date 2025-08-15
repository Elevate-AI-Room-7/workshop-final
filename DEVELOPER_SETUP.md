# 🚀 Developer Setup Guide

Hướng dẫn thiết lập môi trường phát triển cho AI Travel Assistant

## 📋 Yêu cầu hệ thống

- **Python**: 3.8 hoặc cao hơn
- **Git**: Để clone repository
- **Pinecone Account**: Để sử dụng vector database
- **Azure OpenAI**: Để sử dụng GPT và embedding models
- **OpenWeatherMap Account**: Để lấy thông tin thời tiết

## 🔧 Hướng dẫn thiết lập

### 1. Clone Repository

```bash
# Clone repository
git clone https://github.com/Elevate-AI-Room-7/workshop-final.git

# Di chuyển vào thư mục project
cd workshop-final
```

### 2. Tạo môi trường ảo

#### Trên Windows:

```powershell
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo
venv\Scripts\activate

# Kiểm tra Python version
python --version
```

#### Trên macOS/Linux:

```bash
# Tạo môi trường ảo
python3 -m venv venv

# Kích hoạt môi trường ảo
source venv/bin/activate

# Kiểm tra Python version
python --version
```

### 3. Cài đặt thư viện

```bash
# Cập nhật pip
pip install --upgrade pip

# Cài đặt tất cả dependencies
pip install -r requirements.txt

# Kiểm tra cài đặt
pip list
```

### 4. Cấu hình môi trường

#### 4.1. Tạo file `.env`

```bash
# Copy file .env.example thành .env
cp .env.example .env

# Windows CMD
copy .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

#### 4.2. Cấu hình các API Keys

Mở file `.env` và điền các thông tin sau:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_MODEL=GPT-4o-mini

# Azure OpenAI Embeddings Configuration
AZURE_OPENAI_EMBEDDING_API_KEY=your_embedding_api_key
AZURE_OPENAI_EMBEDDING_ENDPOINT=https://your-embedding-resource.openai.azure.com/
AZURE_OPENAI_EMBED_MODEL=text-embedding-3-small

# Weather API (OpenWeatherMap)
WEATHER_API_KEY=your_weather_api_key

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=travel-agency
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1

# TTS Settings
HF_TTS_DEFAULT_LANGUAGE=vietnamese
HF_TTS_AUTO_PLAY=true
HF_TTS_VOLUME=1.0
```

## 🔑 Hướng dẫn lấy API Keys

### 1. Azure OpenAI

1. **Truy cập Azure Portal**: https://portal.azure.com
2. **Tạo Azure OpenAI Resource**:
   - Tìm kiếm "OpenAI" trong Azure Portal
   - Chọn "Create" để tạo resource mới
   - Chọn region và pricing tier
3. **Deploy Models**:
   - Vào Azure OpenAI Studio: https://oai.azure.com
   - Deploy `GPT-4o-mini` model cho chat
   - Deploy `text-embedding-3-small` model cho embeddings
4. **Lấy Keys và Endpoints**:
   - Vào "Keys and Endpoint" trong Azure OpenAI resource
   - Copy `Key 1` làm `AZURE_OPENAI_API_KEY`
   - Copy `Endpoint` làm `AZURE_OPENAI_ENDPOINT`
   - Nếu dùng riêng embedding resource, lấy thêm embedding keys

### 2. Pinecone

1. **Đăng ký tài khoản**: https://www.pinecone.io
2. **Tạo Project**:
   - Login vào Pinecone console
   - Tạo project mới
3. **Lấy API Key**:
   - Vào "API Keys" tab
   - Copy API key làm `PINECONE_API_KEY`
4. **Cấu hình Index**:
   - Index name: `travel-agency` (hoặc tùy chỉnh)
   - Cloud: `aws`
   - Region: `us-east-1`

### 3. OpenWeatherMap

1. **Đăng ký tài khoản**: https://openweathermap.org/api
2. **Lấy API Key**:
   - Vào "My API keys" trong dashboard
   - Copy API key làm `WEATHER_API_KEY`

## 📊 Migrate Database lên Pinecone

Sau khi cấu hình xong, chạy script để upload dữ liệu mẫu lên Pinecone:

### 1. Kiểm tra kết nối

```bash
# Kiểm tra kết nối Pinecone
python scripts/test_pinecone_connection.py

# Kiểm tra tất cả credentials
python scripts/test_credentials.py
```

### 2. Upload dữ liệu mẫu

```bash
# Chạy script tạo và upload dữ liệu
python scripts/generate_sample_data.py
```

Script này sẽ:
- Tạo ~90 records dữ liệu du lịch cho 10 tỉnh thành Việt Nam
- Upload tất cả vào Pinecone index
- Hiển thị progress và kết quả

### 3. Alternative: Sử dụng run script

```bash
# Chạy qua wrapper script
python scripts/run_data_generation.py
```

## 🚀 Chạy ứng dụng

```bash
# Kích hoạt môi trường ảo (nếu chưa)
# Windows
venv\Scripts\activate
# macOS/Linux  
source venv/bin/activate

# Chạy Streamlit app
streamlit run app.py

# Hoặc chỉ định port
streamlit run app.py --server.port 8505
```

Mở trình duyệt và truy cập: http://localhost:8501 (hoặc port đã chỉ định)

## 🔧 Troubleshooting

### Lỗi thường gặp:

1. **Import Error**:
   ```bash
   # Đảm bảo đã kích hoạt virtual environment
   # Cài đặt lại dependencies
   pip install -r requirements.txt
   ```

2. **Pinecone Connection Error**:
   ```bash
   # Chạy test script để kiểm tra
   python scripts/test_pinecone_connection.py
   ```

3. **Azure OpenAI Error**:
   ```bash
   # Kiểm tra credentials
   python scripts/test_credentials.py
   ```

4. **SSL Certificate Error**:
   ```env
   # Thêm vào .env file (chỉ dùng trong development)
   VERIFY_SSL=False
   ```

### Debugging:

```bash
# Chạy với debug mode
streamlit run app.py --logger.level debug

# Kiểm tra logs trong terminal
```

## 📚 Cấu trúc Project

```
workshop-final/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .env                  # Your environment variables (create this)
├── src/
│   ├── pinecone_rag_system.py   # Pinecone vector database
│   ├── travel_planner_agent.py  # Main AI agent
│   └── utils/
│       └── tts.py              # Text-to-speech utilities
├── scripts/
│   ├── generate_sample_data.py  # Upload sample data to Pinecone
│   ├── test_pinecone_connection.py  # Test Pinecone connection
│   └── test_credentials.py      # Test all API credentials
└── components/             # Streamlit components
```

## 🎯 Tiếp theo

Sau khi setup xong, bạn có thể:

1. **Test ứng dụng**: Thử chat với AI về du lịch Việt Nam
2. **Upload thêm dữ liệu**: Sử dụng Knowledge Base tab để upload JSON files
3. **Customize**: Chỉnh sửa prompts và logic trong `src/travel_planner_agent.py`
4. **Deploy**: Chuẩn bị deploy lên cloud platforms

## 🆘 Hỗ trợ

Nếu gặp vấn đề, hãy:
1. Kiểm tra logs trong terminal
2. Chạy test scripts để debug
3. Kiểm tra file `.env` có đúng format không
4. Đảm bảo tất cả API keys đều hợp lệ và có quyền truy cập

---

*Happy coding! 🎉*