# AI Travel Assistant - Message Processing Flow

## 📋 Tổng quan
Sơ đồ này mô tả quy trình xử lý message từ user trong AI Travel Assistant, từ khi user nhập tin nhắn cho đến khi hiển thị kết quả.

## 🔄 Flow Diagram

```mermaid
graph TD
    A[👤 User Input] --> B[📝 Add to Session State]
    B --> C[🔍 RAG Keywords Detection]
    C --> D[📊 Prepare Chat History]
    D --> E[🤖 TravelPlannerAgent.plan_travel()]
    
    E --> F[🛠️ Agent Initialize Tools]
    F --> G[📋 System Prompt Creation]
    G --> H[🏃‍♂️ Agent.run()]
    
    H --> I{🔧 Tool Selection}
    
    I -->|Travel Query| J[🔍 RAG Search Tool]
    I -->|Weather Query| K[🌤️ Weather API Tool]
    I -->|Hotel Booking| L[🏨 Hotel Booking Tool]
    I -->|Car Booking| M[🚗 Car Booking Tool]
    
    J --> N{📚 RAG Results}
    N -->|Found Info| O[✅ Extract Sources & Answer]
    N -->|No Relevant Info| P[❌ Set Fallback Flag]
    
    K --> Q[🌐 OpenWeather API Call]
    L --> R[📋 Mock Hotel Booking]
    M --> S[📋 Mock Car Booking]
    
    O --> T[📤 Return Success Response]
    P --> U[📤 Return No-Info Response]
    Q --> T
    R --> T
    S --> T
    
    T --> V{🔄 Response Processing}
    V -->|Success + Has Info| W[💬 Add Assistant Message]
    V -->|Success + No Info| X[❓ Add Fallback Options]
    V -->|Error| Y[❌ Add Error Message]
    
    W --> Z[🎨 Display in Chat UI]
    X --> AA[🔘 Show Fallback Buttons]
    Y --> Z
    
    AA --> AB{👆 User Choice}
    AB -->|Yes - General Knowledge| AC[🧠 Get General LLM Response]
    AB -->|No| AD[✋ Skip to Next Question]
    
    AC --> W
    AD --> Z
    
    Z --> AE[🔄 st.rerun()]
    AE --> AF[📱 UI Update Complete]

    style A fill:#e1f5fe
    style Z fill:#c8e6c9
    style AF fill:#4caf50
    style Y fill:#ffcdd2
    style P fill:#fff3e0
```

## 📊 Detailed Flow Steps

### 1. 📝 Input Processing (app.py:175-180)
```python
# User input được capture từ st.chat_input()
user_input = st.chat_input("...")
if user_input:
    st.session_state["messages"].append({
        "role": "user", 
        "content": user_input
    })
```

### 2. 🔍 RAG Detection (app.py:182-194)
```python
# Detect nếu query có thể sử dụng RAG
rag_keywords = ["gợi ý", "thông tin", "địa điểm", ...]
likely_rag = any(keyword in user_input.lower() for keyword in rag_keywords)
spinner_text = "🔍 Đang tìm kiếm..." if likely_rag else "🤔 Đang suy nghĩ..."
```

### 3. 📊 Chat History Preparation (app.py:199-206)
```python
chat_history = []
for msg in st.session_state["messages"][:-1]:
    if msg["role"] == "user":
        chat_history.append(("user", msg["content"]))
    elif msg["role"] == "assistant":
        chat_history.append(("assistant", msg["content"]))
```

### 4. 🤖 Agent Processing (travel_planner_agent.py:201-272)

#### 4.1 System Prompt Creation
```python
system_prompt = """
Bạn là AI Travel Planner chuyên nghiệp cho du lịch Việt Nam.
Nhiệm vụ: Tư vấn điểm đến, lập kế hoạch, thông tin thời tiết, đặt khách sạn/xe
Tools: TravelKnowledgeSearch, WeatherInfo, BookHotel, BookCar
"""
```

#### 4.2 Tool Definitions
- **🔍 RAG Search Tool** (`rag_search_tool()` - line 51-73)
- **🌤️ Weather Tool** (`weather_tool()` - line 75-95) 
- **🏨 Hotel Booking Tool** (`hotel_booking_tool()` - line 97-129)
- **🚗 Car Booking Tool** (`car_booking_tool()` - line 131-163)

#### 4.3 Agent Execution
```python
response = self.agent.run({
    "input": f"{system_prompt}\n\nYêu cầu của khách hàng: {user_input}",
    "chat_history": chat_history
})
```

### 5. 🛠️ Tool Processing Details

#### 🔍 RAG Search Tool Flow
```python
def rag_search_tool(query: str) -> str:
    result = self.rag_system.query(query)
    
    if result.get('no_relevant_info') or result.get('answer') is None:
        self.no_relevant_info = True
        self.fallback_query = query
        return f"RAG_NO_INFO: {query}"
    
    self.last_rag_sources = result.get('sources', [])
    return result.get('answer')
```

#### 🌤️ Weather Tool Flow
```python
def weather_tool(city: str) -> str:
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    response = requests.get(url)
    # Format weather data
    return formatted_weather_info
```

### 6. 📤 Response Processing (app.py:210-246)

#### 6.1 Success Response with Info
```python
if result["success"] and result.get("response"):
    st.session_state["messages"].append({
        "role": "assistant",
        "content": result["response"],
        "sources": result.get("sources", []),
        "rag_used": result.get("rag_used", False)
    })
```

#### 6.2 Success Response without Relevant Info (Fallback)
```python
if result.get("no_relevant_info") and result.get("response") is None:
    fallback_message = f"Tôi không tìm thấy thông tin về **{query}** trong cơ sở dữ liệu..."
    st.session_state["messages"].append({
        "role": "assistant",
        "content": fallback_message,
        "need_fallback": True,
        "fallback_query": query
    })
```

#### 6.3 Error Response
```python
else:
    st.session_state["messages"].append({
        "role": "assistant",
        "content": result["response"],
        "error": True
    })
```

### 7. 🎨 UI Display Processing

#### 7.1 Normal Message Display (app.py:271-354)
```python
for message in st.session_state["messages"]:
    if message["role"] == "user":
        # User message with right alignment
    elif message["role"] == "assistant":
        # Assistant message with sources display
        sources = message.get("sources", [])
        if sources:
            # Show sources with expandable section
```

#### 7.2 Fallback Options Display (app.py:356-390)
```python
if message.get("need_fallback"):
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("✅ Có, hãy trả lời"):
            # Call get_general_knowledge_response()
    with col2:
        if st.button("❌ Không cần"):
            # Add skip message
```

## 📈 Data Flow Summary

### Input Data Structure
```python
# User Input
user_input: str

# Chat History
chat_history: List[Tuple[str, str]] = [
    ("user", "message1"),
    ("assistant", "response1"),
    ...
]
```

### Output Data Structure
```python
# Success Response
{
    "success": True,
    "response": "AI generated response",
    "sources": ["source1", "source2"],
    "rag_used": True/False,
    "mode": "full"
}

# No Relevant Info Response
{
    "success": True,
    "response": None,
    "sources": [],
    "rag_used": False,
    "no_relevant_info": True,
    "query": "original query"
}

# Error Response
{
    "success": False,
    "response": "Error message",
    "error": "detailed error"
}
```

### Session State Message Structure
```python
# User Message
{
    "role": "user",
    "content": "user input text"
}

# Assistant Message (Success)
{
    "role": "assistant",
    "content": "response text",
    "sources": ["source1", "source2"],
    "rag_used": True,
    "general_knowledge": False
}

# Assistant Message (Fallback)
{
    "role": "assistant",
    "content": "fallback prompt text",
    "sources": [],
    "rag_used": False,
    "need_fallback": True,
    "fallback_query": "original query"
}

# Assistant Message (Error)
{
    "role": "assistant",
    "content": "error message",
    "error": True
}
```

## 🔧 Key Components

### 1. TravelPlannerAgent Class
- **File**: `src/travel_planner_agent.py`
- **Main Method**: `plan_travel(user_input, chat_history)`
- **Tools**: RAG Search, Weather, Hotel Booking, Car Booking
- **LLM**: AzureChatOpenAI with LangChain AgentExecutor

### 2. RAG System
- **Interface**: Via `rag_search_tool()` function
- **Backend**: Pinecone vector database (current commit)
- **Query Method**: `rag_system.query(query)`
- **Fallback**: General knowledge when no relevant info found

### 3. External APIs
- **Weather**: OpenWeatherMap API
- **Embeddings**: Azure OpenAI text-embedding-3-small
- **Chat**: Azure OpenAI GPT-4o-mini

### 4. UI Framework
- **Frontend**: Streamlit with custom CSS
- **State Management**: `st.session_state`
- **Real-time Updates**: `st.rerun()`

## 🎯 Processing Outcomes

### ✅ Success Cases
1. **RAG Found Info**: Display response + sources
2. **Weather Query**: Display weather data
3. **Booking Request**: Show booking confirmation
4. **General Knowledge**: LLM response without RAG

### ❓ Fallback Cases
1. **No Relevant RAG Info**: Offer general knowledge option
2. **API Errors**: Graceful error messages
3. **Tool Failures**: Error handling with details

### ❌ Error Cases
1. **Network Issues**: Connection error messages
2. **Invalid Input**: Input validation errors
3. **System Errors**: Technical error messages

---
*Generated: 2025-08-14*  
*Source: AI Travel Assistant codebase analysis*