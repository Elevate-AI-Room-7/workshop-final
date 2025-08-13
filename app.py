import streamlit as st
import requests
import openai
import os
from dotenv import load_dotenv
import json
from pinecone import Pinecone, ServerlessSpec
from gtts import gTTS
import io
from openai import AzureOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
st.set_page_config(
    page_title="🌍 AI Travel Assistant with HuggingFace TTS",
    page_icon="🤗",
    layout="wide"
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

client = openai.OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=os.getenv("AZURE_OPENAI_ENDPOINT")
)


PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
AZURE_EMBEDDING_KEY = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY", os.getenv("AZURE_OPENAI_API_KEY"))
AZURE_EMBEDDING_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
EMBED_MODEL = os.getenv("AZURE_EMBED_MODEL", "text-embedding-3-small")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "travel-agency")

pc = Pinecone(
    api_key=PINECONE_API_KEY
)

# Remove duplicate INDEX_NAME assignment and auto-delete
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(name=INDEX_NAME, dimension=1536, metric="cosine", spec=ServerlessSpec(
        cloud='aws',
        region='us-east-1'
    ))
    st.info(f"Created Pinecone index: {INDEX_NAME}")

index = pc.Index(INDEX_NAME)

def get_embedding(text: str):
    emb_client = AzureOpenAI(
        api_key=AZURE_EMBEDDING_KEY,
        azure_endpoint=AZURE_EMBEDDING_ENDPOINT,
        api_version="2024-07-01-preview"
    )
    resp = emb_client.embeddings.create(model=EMBED_MODEL, input=text)
    return resp.data[0].embedding

def sanitize_metadata(metadata):
    """Convert metadata to Pinecone-compatible types (string, number, boolean, list of strings)"""
    sanitized = {}
    for k, v in metadata.items():
        if isinstance(v, (str, int, float, bool)):
            sanitized[k] = v
        elif isinstance(v, list):
            # Convert all list items to strings
            sanitized[k] = [str(item) for item in v]
        elif isinstance(v, dict):
            # Convert dict to JSON string
            sanitized[k] = json.dumps(v, ensure_ascii=False)
        else:
            # Convert any other type to string
            sanitized[k] = str(v)
    return sanitized

def load_knowledge_to_pinecone(json_path: str):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        vectors = []
        for entry in data:
            _id = entry.get("id")
            text = entry.get("text")
            metadata = entry.get("metadata", {})
            if not _id or not text:
                continue
            emb = get_embedding(text)
            # Sanitize metadata for Pinecone compatibility
            metadata = sanitize_metadata(metadata)
            metadata["text"] = text  # store for retrieval display
            vectors.append((_id, emb, metadata))
        if vectors:
            index.upsert(vectors)
            st.success(f"Upserted {len(vectors)} vectors into {INDEX_NAME}")
            return True
        st.warning("No vectors to upsert")
        return False
    except Exception as e:
        st.error(f"Load knowledge failed: {e}")
        return False

def query_pinecone(user_input, top_k=5):
    query_embedding = get_embedding(user_input)
    results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    print(results, "result query pinecone")
    if results.get("matches") and len(results["matches"]) > 0:
        # Return the top matched text only
        top_text = results["matches"][0]["metadata"].get("text", "")
        return top_text
    return "Không tìm thấy thông tin phù hợp."

DATASET_PATH = os.getenv("TRAVEL_DATASET", "destination_knowledge_extended_dataset.json")

def ensure_index_loaded():
    try:
        stats = index.describe_index_stats()
        total_count = stats.get('total_vector_count', 0)
        st.sidebar.info(f"Current vectors in index: {total_count}")
        if total_count == 0:
            st.info("Loading dataset to Pinecone...")
            load_knowledge_to_pinecone(DATASET_PATH)
    except Exception as e:
        st.error(f"Error checking index: {e}")
        load_knowledge_to_pinecone(DATASET_PATH)

ensure_index_loaded()

def search_faq(query: str):
    matches = query_pinecone(query, top_k=1)
    return [m.get('metadata', {}).get('text', '') for m in matches]

# ====== PROMPT TEMPLATE ======
travel_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "Bạn là trợ lý du lịch thông minh về du lịch. "
        "Sử dụng thông tin sau để trả lời câu hỏi bằng tiếng việt:\n\n"
        "Ngữ cảnh: {context}\n\n"
        "Câu hỏi: {question}\n\n"
        "Hãy trả lời ngắn gọn, chính xác và hữu ích dựa theo ngữ cảnh."
        "Nếu không có thông tin trong ngữ cảnh, hãy nói rõ là không có thông tin.\n\n"
    )
)
def speak(text, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        st.audio(mp3_fp, format='audio/mp3')
    except Exception as e:
        st.error(f"❌ Error during TTS: {e}")
def fetch_weather(city: str, unit: str = "metric"):
    """Lấy thông tin thời tiết"""
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units={unit}"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return {"error": "City not found"}
        data = resp.json()
        return {
            "city": city,
            "temperature": data["main"]["temp"],
            "weather": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"]
        }
    except Exception as e:
        return {"error": f"Weather API error: {str(e)}"}


def book_hotel(city: str, date: str, nights: int = 1):
    """Đặt khách sạn (mock function)"""
    return {
        "city": city,
        "date": date,
        "nights": nights,
        "hotel": "AI Grand Hotel",
        "confirmation": f"CONFIRM-{city[:3].upper()}-{date.replace('-', '')}-{nights}"
    }

# ====== LANGCHAIN TOOLS & AGENT SETUP ======
def weather_tool_func(city: str):
    """Wrapper for weather function"""
    result = fetch_weather(city)
    if "error" in result:
        return f"Weather error: {result['error']}"
    return f"Weather in {result['city']}: {result['temperature']}°C, {result['weather']}, humidity {result['humidity']}%, wind {result['wind_speed']} m/s"

def hotel_tool_func(input_str: str):
    """Parse input and book hotel"""
    # Simple parsing - in production, use proper NLP
    parts = input_str.split("|")
    city = parts[0] if len(parts) > 0 else "Unknown"
    date = parts[1] if len(parts) > 1 else "2025-12-01"
    nights = int(parts[2]) if len(parts) > 2 else 1
    result = book_hotel(city, date, nights)
    return f"Hotel booked: {result['hotel']} in {result['city']} for {result['nights']} nights. Confirmation: {result['confirmation']}"


weather_tool = Tool(
    name="WeatherTool",
    func=weather_tool_func,
    description="Get weather information for a city. Input: city name"
)

hotel_tool = Tool(
    name="BookHotel",
    func=hotel_tool_func,
    description="Book hotel. Input format: 'city|date|nights' (e.g., 'Hanoi|2025-12-25|2')"
)

# Initialize LangChain LLM
llm = ChatOpenAI(
    model="GPT-4o-mini",
    temperature=0.7,
    openai_api_key=OPENAI_API_KEY,
    base_url=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# ====== STREAMLIT UI ======
st.title("🤖 AI Travel Chatbot with Pinecone RAG & LangChain Agent")


if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": "You are a travel assistant. Use function calling when needed."}
    ]

def chat(user_input, chat_history):
    context = query_pinecone(user_input)
    prompt = travel_prompt.format(context=context, question=user_input)
    print(prompt, "Promt context")
    agent = initialize_agent(
        tools=[weather_tool,hotel_tool],
        llm=llm,
        agent="chat-conversational-react-description",
        verbose=False
    )
    result = agent.run(   {
        "input": prompt,
        "chat_history": chat_history
    })
    print(result, "result from agent")
    return result,chat_history

user_input = st.chat_input("Hỏi tôi về thời tiết, đặt khách sạn hoặc lập kế hoạch...")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.spinner("Processing with LangChain Agent..."):
        try:
            # Use LangChain agent instead of OpenAI function calling
            chat_history = []
            for msg in st.session_state["messages"]:
                if msg["role"] == "user":
                    chat_history.append(("user", msg["content"]))
                elif msg["role"] == "assistant" and msg.get("content"):
                    chat_history.append(("assistant", msg["content"]))
            result,chat_history = chat(user_input, chat_history)
            
            st.session_state["messages"].append({"role": "assistant", "content": result})
        except Exception as e:
            error_msg = f"Agent error: {str(e)}"
            st.session_state["messages"].append({"role": "assistant", "content": error_msg})

# Display conversation
for m in st.session_state["messages"][1:]:  # Skip system message
    if m["role"] == "user":
        st.chat_message("user").write(m["content"])
    elif m["role"] == "assistant" and m.get("content"):
        with st.chat_message("assistant"):
            st.write(m["content"])
            # Add TTS button
            if st.button("🔊 Play Audio", key=f"tts_{hash(m['content'][:20])}"):
                speak(m["content"], lang='vi')