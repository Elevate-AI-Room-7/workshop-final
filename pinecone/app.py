import streamlit as st
import os
from dotenv import load_dotenv
from rag_system import TravelRAGSystemPinecone
from gtts import gTTS
import io
import logging

logging.basicConfig(level=logging.INFO)

# Cấu hình trang
st.set_page_config(
    page_title="🌍 AI Travel Assistant with RAG",
    page_icon="🤖",
    layout="wide"
)

# Load environment variables
load_dotenv()


@st.cache_resource
def init_rag_system():
    """Khởi tạo RAG system với Pinecone caching"""
    rag = TravelRAGSystemPinecone()
    rag.setup_retrieval_chain()
    return rag


# Initialize RAG system
rag_system = init_rag_system()


def speak(text, lang='vi'):
    """Text-to-Speech"""
    try:
        tts = gTTS(text=text, lang=lang)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        st.audio(mp3_fp, format='audio/mp3')
    except Exception as e:
        st.error(f"❌ Lỗi TTS: {e}")


# Streamlit UI
st.title("🤖 AI Travel Assistant với RAG & Pinecone")
st.markdown("*Hệ thống tư vấn du lịch thông minh sử dụng RAG với Pinecone*")

# Sidebar thông tin
with st.sidebar:
    st.header("🛠️ Thông tin hệ thống")
    st.write("**Chế độ:** RAG Only")
    st.write("**Vector Store:** Pinecone")
    st.write("**Framework:** Langchain")
    st.write("**LLM:** Azure OpenAI GPT-4o-mini")
    st.write("**Embeddings:** text-embedding-3-small")

    st.header("📊 Số liệu Vector Store")
    try:
        if rag_system.index:
            stats = rag_system.index.describe_index_stats()
            st.write(f"**Total Vectors:** {stats.total_vector_count}")
            st.write(f"**Dimension:** {stats.dimension}")
    except:
        st.write("**Status:** Initializing...")

    st.header("✨ Tính năng")
    st.write("🔍 Tìm kiếm thông tin du lịch")
    st.write("📍 Tư vấn điểm đến")
    st.write("🏨 Thông tin khách sạn")
    st.write("🎯 Gợi ý hoạt động")
    st.write("🔊 Text-to-Speech")

    # Reset button
    if st.button("🔄 Reset Vector Store"):
        rag_system.delete_all_vectors()
        st.success("Vector store đã được reset!")
        st.rerun()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": """Bạn là trợ lý du lịch thông minh cho Việt Nam.
Sử dụng RAG system với Pinecone để tư vấn du lịch."""}
    ]

# Chat interface - chỉ input box
user_input = st.chat_input("Hỏi tôi về du lịch Việt Nam...")

# Xử lý tin nhắn người dùng
if user_input:
    # Thêm tin nhắn người dùng
    st.session_state["messages"].append(
        {"role": "user", "content": user_input}
    )

    # Hiển thị trạng thái đang xử lý
    with st.spinner("🔍 Đang tìm kiếm thông tin trong cơ sở dữ liệu..."):
        try:
            # Chỉ sử dụng RAG
            result = rag_system.query(user_input)
            response = result['answer']
            sources = len(result.get('source_documents', []))

            # Thêm phản hồi vào session state
            st.session_state["messages"].append({
                "role": "assistant",
                "content": response,
                "sources": sources
            })

        except Exception as e:
            st.session_state["messages"].append({
                "role": "assistant",
                "content": f"❌ Xin lỗi, có lỗi xảy ra: {str(e)}"
            })

    # Rerun để hiển thị tin nhắn mới
    st.rerun()

# Hiển thị cuộc trò chuyện
st.subheader("💬 Cuộc trò chuyện")

for i, message in enumerate(st.session_state["messages"]):
    if message["role"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])

    elif message["role"] == "assistant" and message.get("content"):
        with st.chat_message("assistant"):
            st.write(message["content"])

            # Hiển thị số sources
            if message.get("sources"):
                st.caption(
                    f"📚 Tìm thấy {message['sources']} nguồn tham khảo từ vector store")

            # Text-to-speech cho tin nhắn cuối
            if i == len(st.session_state["messages"]) - 1:
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("🔊 Nghe", key=f"tts_{i}"):
                        speak(message["content"])

# Thông tin hướng dẫn
# st.info("ℹ️ **Chế độ RAG Only:** Hệ thống chỉ sử dụng cơ sở dữ liệu du lịch từ Pinecone để trả lời câu hỏi của bạn")

# Gợi ý câu hỏi mẫu
with st.expander("💡 Câu hỏi mẫu"):
    st.write("• Gợi ý điểm du lịch ở Đà Nẵng")
    st.write("• Những món ăn đặc sản ở Huế")
    st.write("• Khách sạn tốt ở Hội An")
    st.write("• Hoạt động vui chơi ở Phú Quốc")
    st.write("• Lịch trình 3 ngày ở Sapa")

# Footer
st.markdown("---")
st.markdown("🚀 **RAG Travel Assistant** - Powered by Pinecone & Langchain")
