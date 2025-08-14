# AI Travel Assistant - Updated Smart Message Processing Flow

## 📋 Tổng quan
Sơ đồ này mô tả quy trình xử lý message ĐƯỢC CẬP NHẬT với smart tool detection và context rewriting trong AI Travel Assistant.

## 🔄 Updated Flow Diagram

```mermaid
graph TD
    A[👤 User Input] --> B[📝 Add to Session State]
    B --> C[🧠 Smart Analysis]
    
    C --> D[📝 Step 1: Context Rewriting<br/>Top 5 messages → Summary]
    D --> E[🔧 Step 2: Smart Tool Detection<br/>LLM-based intent classification]
    E --> F[⚡ Step 3: Execution Router]
    
    F --> G{🔀 Tool Selection}
    
    G -->|RAG| H[🔍 RAG Execution]
    G -->|WEATHER| I[🌤️ Weather Execution] 
    G -->|HOTEL| J[🏨 Hotel Execution]
    G -->|CAR| K[🚗 Car Execution]
    G -->|GENERAL| L[💬 General Execution]
    
    H --> H1[📚 Vector DB Search]
    H1 --> H2{📊 Process Results}
    H2 -->|Found| H3[✅ Extract Sources]
    H2 -->|Not Found| H4[❓ Fallback Handler]
    
    I --> I1[🏙️ Extract City]
    I1 --> I2[⏰ Detect Current/Forecast]
    I2 --> I3[🌐 Weather API Call]
    
    J --> J1[📋 Extract Hotel Details]
    J1 --> J2[🏨 Mock Hotel Booking]
    
    K --> K1[🚗 Extract Car Details]
    K1 --> K2[🚙 Mock Car Booking]
    
    L --> L1[💬 LLM General Response]
    
    H3 --> M[📦 Response Aggregator]
    I3 --> M
    J2 --> M
    K2 --> M
    L1 --> M
    
    M --> N[🎨 Enhanced UI Display<br/>Tool indicator + Sources + Context]
    N --> O[🔄 st.rerun()]
    
    H4 --> P[❓ Show Fallback Options]
    P --> N

    style A fill:#e1f5fe
    style N fill:#c8e6c9
    style O fill:#4caf50
    style H4 fill:#ffcdd2
    style C fill:#e3f2fd
```

## 🚀 Key Improvements in Updated Flow

### 1. 📝 **Context Rewriting (Step 1)**
```python
def _rewrite_conversation_context(self, user_input: str, chat_history: List) -> str:
    # Get last 5 messages (max)
    recent_messages = chat_history[-5:] if len(chat_history) > 5 else chat_history
    
    # LLM summarizes conversation context
    context_prompt = f"""
    Hãy tóm tắt cuộc hội thoại sau thành một đoạn ngắn gọn để hiểu ngữ cảnh:
    
    Lịch sử hội thoại: {recent_messages}
    Câu hỏi hiện tại: {user_input}
    
    Tóm tắt ngữ cảnh (1-2 câu):
    """
    
    return self.llm.predict(context_prompt)
```

### 2. 🧠 **Smart Tool Detection (Step 2)**
```python
def _detect_tool_intent(self, user_input: str, context: str) -> str:
    detection_prompt = f"""
    Phân loại ý định của người dùng và chọn công cụ phù hợp:
    
    Ngữ cảnh: {context}
    Câu hỏi: {user_input}
    
    Các công cụ có sẵn:
    1. RAG - Tra cứu thông tin dịch vụ du lịch, danh lam thắng cảnh địa phương
    2. WEATHER - Kiểm tra thời tiết hiện tại hoặc dự đoán thời tiết tương lai
    3. HOTEL - Đặt phòng khách sạn
    4. CAR - Đặt xe/vận chuyển
    5. GENERAL - Trò chuyện chung
    
    Quy tắc phân loại:
    - RAG: Hỏi về địa điểm, danh lam, ẩm thực, hoạt động du lịch, gợi ý điểm đến
    - WEATHER: Hỏi về thời tiết, nhiệt độ, trời mưa/nắng, dự báo thời tiết
    - HOTEL: Yêu cầu đặt phòng, tìm khách sạn, booking accommodation
    - CAR: Yêu cầu đặt xe, thuê xe, book transportation, di chuyển
    - GENERAL: Chào hỏi, cảm ơn, câu hỏi chung không liên quan du lịch
    
    Trả lời CHÍNH XÁC một trong: RAG, WEATHER, HOTEL, CAR, GENERAL
    """
    
    return self.llm.predict(detection_prompt).strip().upper()
```

### 3. ⚡ **Specialized Tool Execution**

#### 🔍 **RAG Execution**
```python
def _execute_rag_search(self, user_input: str, context: str) -> Dict[str, Any]:
    result = self.rag_system.query(user_input)
    
    if result.get('no_relevant_info'):
        return {
            "success": True,
            "response": None,
            "no_relevant_info": True,
            "tool_used": "RAG",
            "context": context
        }
    
    return {
        "success": True,
        "response": result.get('answer'),
        "sources": result.get('sources', []),
        "rag_used": True,
        "tool_used": "RAG",
        "context": context
    }
```

#### 🌤️ **Enhanced Weather Execution**
```python
def _execute_weather_query(self, user_input: str, context: str) -> Dict[str, Any]:
    # Extract city from user input
    city = self._extract_city_from_query(user_input)
    
    # Detect if it's current weather or forecast
    is_forecast = self._detect_forecast_intent(user_input)
    
    if is_forecast:
        weather_info = self._get_weather_forecast(city)
    else:
        weather_info = self._get_current_weather(city)
    
    return {
        "success": True,
        "response": weather_info,
        "sources": [f"OpenWeatherMap API - {city}"],
        "tool_used": "WEATHER",
        "weather_type": "forecast" if is_forecast else "current",
        "city": city,
        "context": context
    }
```

#### 🏨 **Hotel Booking Execution**
```python
def _execute_hotel_booking(self, user_input: str, context: str) -> Dict[str, Any]:
    # Extract booking details
    booking_details = self._extract_hotel_booking_details(user_input, context)
    
    # Execute mock booking
    booking_result = self._mock_hotel_booking(booking_details)
    
    return {
        "success": True,
        "response": booking_result,
        "sources": ["AI Hotel Booking System"],
        "tool_used": "HOTEL",
        "booking_details": booking_details,
        "context": context
    }
```

#### 🚗 **Car Booking Execution**
```python
def _execute_car_booking(self, user_input: str, context: str) -> Dict[str, Any]:
    # Extract booking details
    booking_details = self._extract_car_booking_details(user_input, context)
    
    # Execute mock booking
    booking_result = self._mock_car_booking(booking_details)
    
    return {
        "success": True,
        "response": booking_result,
        "sources": ["AI Car Booking System"],
        "tool_used": "CAR",
        "booking_details": booking_details,
        "context": context
    }
```

### 4. 🎨 **Enhanced UI Display**

#### Tool Indicator Display
```python
# Show tool indicator
tool_icons = {
    "RAG": "🔍",
    "WEATHER": "🌤️", 
    "HOTEL": "🏨",
    "CAR": "🚗",
    "GENERAL": "💬"
}
tool_icon = tool_icons.get(tool_used, "🔧")

st.markdown(f"""
<small style="color: #666;">
    {tool_icon} <strong>Tool:</strong> {tool_used}
</small>
""")
```

#### Context Preview
```python
# Show context if available
context = message.get("context", "")
if context and len(context) > 10:
    st.markdown(f"""
    <small style="color: #888;">
        📝 <strong>Context:</strong> {context[:100]}{'...' if len(context) > 100 else ''}
    </small>
    """)
```

## 📊 Enhanced Data Flow

### Input Data Structure
```python
# Enhanced Input Processing
{
    "user_input": str,
    "chat_history": List[Tuple[str, str]],
    "rewritten_context": str,  # NEW
    "detected_tool": str       # NEW
}
```

### Enhanced Output Structure
```python
# Enhanced Response Structure
{
    "success": bool,
    "response": str,
    "sources": List[str],
    "rag_used": bool,
    "tool_used": str,           # NEW
    "context": str,             # NEW
    "weather_type": str,        # NEW (for weather)
    "city": str,                # NEW (for weather)
    "booking_details": Dict     # NEW (for bookings)
}
```

### Enhanced Session Message Structure
```python
# Enhanced Message Structure
{
    "role": "assistant",
    "content": str,
    "sources": List[str],
    "rag_used": bool,
    "tool_used": str,           # NEW
    "context": str,             # NEW
    "weather_type": str,        # NEW
    "city": str,                # NEW
    "booking_details": Dict     # NEW
}
```

## 🔧 Smart Detection Logic

### 1. 🏙️ **City Extraction**
```python
def _extract_city_from_query(self, query: str) -> str:
    cities = ["hà nội", "hồ chí minh", "đà nẵng", "nha trang", "huế", 
              "hội an", "sapa", "đà lạt", "phú quốc", "cần thơ"]
    query_lower = query.lower()
    
    for city in cities:
        if city in query_lower:
            return city.title()
    
    return "Hà Nội"  # Default city
```

### 2. ⏰ **Forecast Detection**
```python
def _detect_forecast_intent(self, query: str) -> bool:
    forecast_keywords = ["mai", "ngày mai", "tuần sau", "dự báo", 
                        "dự đoán", "tương lai", "sắp tới"]
    query_lower = query.lower()
    
    return any(keyword in query_lower for keyword in forecast_keywords)
```

### 3. 🌤️ **Enhanced Weather Responses**

#### Current Weather
```python
def _get_current_weather(self, city: str) -> str:
    # OpenWeatherMap API call
    return f"""🌤️ Thời tiết hiện tại tại {city}:
🌡️ Nhiệt độ: {temp}°C
☁️ Trời: {description}
💨 Độ ẩm: {humidity}%
🌬️ Tốc độ gió: {wind_speed} m/s"""
```

#### Weather Forecast
```python
def _get_weather_forecast(self, city: str) -> str:
    # 24-hour forecast from API
    return f"""🔮 Dự báo thời tiết {city} (24h tới):

⏰ 08:00: 25°C - Nắng ít mây
⏰ 11:00: 28°C - Nắng
⏰ 14:00: 30°C - Nắng gắt
⏰ 17:00: 27°C - Có mây
..."""
```

### 4. 🏨 **Enhanced Booking Responses**

#### Hotel Booking
```python
def _mock_hotel_booking(self, details: Dict) -> str:
    return """✅ Đặt phòng khách sạn thành công!

🏨 Khách sạn: AI Grand Hotel {city}
📍 Địa điểm: {city}
📅 Ngày nhận phòng: {date}
🌙 Số đêm: {nights}
👥 Số khách: {guests}
💰 Giá: ${price}
🎫 Mã xác nhận: {confirmation}

📞 Liên hệ: +84 123 456 789
📧 Email: booking@aigrandhotel.com"""
```

#### Car Booking
```python
def _mock_car_booking(self, details: Dict) -> str:
    return """✅ Đặt xe thành công!

🚗 Loại xe: Toyota Vios (4 chỗ)
📍 Điểm đón: {pickup_city}
🎯 Điểm đến: {destination}
📅 Ngày: {date}
⏰ Giờ: {time}
💰 Giá: $50
🎫 Mã xác nhận: {confirmation}

📞 Tài xế: +84 987 654 321
🚗 Biển số: 30A-123.45"""
```

## 🎯 Flow Outcomes

### ✅ **Success Cases**
1. **RAG Found Info**: Display response + sources + context
2. **Current Weather**: Display real-time weather data 
3. **Weather Forecast**: Display 24h forecast
4. **Hotel Booking**: Show booking confirmation details
5. **Car Booking**: Show transportation booking details
6. **General Chat**: LLM conversation with travel suggestions

### ❓ **Enhanced Fallback Cases**
1. **No Relevant RAG Info**: Smart fallback with context
2. **Weather API Errors**: Graceful error with city info
3. **Booking Errors**: Clear error messages with retry options

### 🔧 **Smart Features**
1. **Context Awareness**: Top 5 messages rewritten for better understanding
2. **Intent Detection**: LLM-based tool selection
3. **City Recognition**: Automatic city extraction from queries
4. **Time Detection**: Current vs forecast weather detection
5. **Rich UI**: Tool indicators, context previews, booking details
6. **Unified Response**: Consistent response format across all tools

## 📈 Performance Improvements

### 🚀 **Efficiency Gains**
- **Single LLM Call** for tool detection vs multiple keyword checks
- **Context Summarization** reduces token usage in subsequent calls
- **Specialized Execution** paths reduce unnecessary processing
- **Rich Metadata** reduces need for additional queries

### 🎨 **User Experience Enhancements**
- **Tool Transparency**: Users see which tool was used
- **Context Awareness**: System understands conversation flow
- **Smart Detection**: More accurate tool selection
- **Rich Responses**: Enhanced formatting and details

---
*Generated: 2025-08-14*  
*Updated flow with smart tool detection and context rewriting*