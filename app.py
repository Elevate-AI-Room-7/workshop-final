"""
AI Travel Assistant - Main Application
Combines RAG-only and Full-featured modes
"""

import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.travel_planner_agent import TravelPlannerAgent
from src.utils.tts import create_audio_button

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="🌍 AI Travel Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for chat styling
st.markdown("""
<style>
/* Force reload CSS */
.main .block-container {
    max-width: 100% !important;
}

/* User message styling - align right with stronger selectors */
div[data-testid="stChatMessage"]:has([data-testid="chat-message-user"]),
.stChatMessage[data-testid="chat-message-user"],
[data-testid="chat-message-user"] {
    display: flex !important;
    flex-direction: row-reverse !important;
    justify-content: flex-start !important;
    margin: 0.5rem 0 !important;
}

div[data-testid="stChatMessage"]:has([data-testid="chat-message-user"]) > div,
.stChatMessage[data-testid="chat-message-user"] > div,
[data-testid="chat-message-user"] > div {
    background-color: #007acc !important;
    color: white !important;
    border-radius: 18px 18px 5px 18px !important;
    margin-left: 20% !important;
    margin-right: 10px !important;
    padding: 12px 16px !important;
    max-width: 70% !important;
}

/* Assistant message styling - align left with stronger selectors */
div[data-testid="stChatMessage"]:has([data-testid="chat-message-assistant"]),
.stChatMessage[data-testid="chat-message-assistant"],
[data-testid="chat-message-assistant"] {
    display: flex !important;
    flex-direction: row !important;
    justify-content: flex-start !important;
    margin: 0.5rem 0 !important;
}

div[data-testid="stChatMessage"]:has([data-testid="chat-message-assistant"]) > div,
.stChatMessage[data-testid="chat-message-assistant"] > div,
[data-testid="chat-message-assistant"] > div {
    background-color: #f0f2f6 !important;
    color: #262730 !important;
    border-radius: 18px 18px 18px 5px !important;
    margin-right: 20% !important;
    margin-left: 10px !important;
    padding: 12px 16px !important;
    max-width: 70% !important;
}

/* Alternative approach with direct element targeting */
.element-container:has([data-testid="chat-message-user"]) {
    display: flex !important;
    justify-content: flex-end !important;
}

.element-container:has([data-testid="chat-message-assistant"]) {
    display: flex !important;
    justify-content: flex-start !important;
}

/* Chat message content */
.stChatMessage > div:first-child {
    border: none !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "travel_agent" not in st.session_state:
    with st.spinner("🔄 Đang khởi tạo AI Travel Assistant..."):
        st.session_state["travel_agent"] = TravelPlannerAgent()

# Main UI
st.title("🤖 AI Travel Assistant")
st.markdown("*Trợ lý du lịch thông minh với AI và RAG*")


# Chat input
user_input = st.chat_input("Hỏi tôi về du lịch, thời tiết, hoặc đặt khách sạn...")

# Process user input
if user_input:
    # Add user message
    st.session_state["messages"].append({
        "role": "user", 
        "content": user_input
    })
    
    # Show processing spinner
    with st.spinner("🤔 Đang suy nghĩ..."):
        try:
            agent = st.session_state["travel_agent"]
            
            # Prepare chat history
            chat_history = []
            for msg in st.session_state["messages"][:-1]:  # Exclude current message
                if msg["role"] == "user":
                    chat_history.append(("user", msg["content"]))
                elif msg["role"] == "assistant":
                    chat_history.append(("assistant", msg["content"]))
            
            # Always use full features mode
            result = agent.plan_travel(user_input, chat_history)
            
            # Add assistant response
            if result["success"]:
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": result["response"],
                    "sources": result.get("sources", ""),
                    "mode": result.get("mode", "full")
                })
            else:
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": result["response"],
                    "error": True
                })
                
        except Exception as e:
            st.session_state["messages"].append({
                "role": "assistant",
                "content": f"❌ Xin lỗi, có lỗi xảy ra: {str(e)}",
                "error": True
            })
    
    # Rerun to show new messages
    st.rerun()

# Display conversation
for i, message in enumerate(st.session_state["messages"]):
    if message["role"] == "user":
        # Custom HTML container for user messages (right-aligned)
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin: 1rem 0;">
            <div style="background-color: #007acc; color: white; padding: 12px 16px; 
                        border-radius: 18px 18px 5px 18px; max-width: 70%; 
                        box-shadow: 0 1px 2px rgba(0,0,0,0.1); margin-left: 20%;">
                {message["content"]}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    elif message["role"] == "assistant":
        # Custom HTML container for assistant messages (left-aligned)
        if message.get("error"):
            st.error(message["content"])
        else:
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; margin: 1rem 0;">
                <div style="background-color: #f0f2f6; color: #262730; padding: 12px 16px; 
                            border-radius: 18px 18px 18px 5px; max-width: 70%; 
                            box-shadow: 0 1px 2px rgba(0,0,0,0.1); margin-right: 20%;">
                    {message["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # TTS button for the latest message
            if i == len(st.session_state["messages"]) - 1 and not message.get("error"):
                col1, col2 = st.columns([1, 4])
                with col1:
                    create_audio_button(
                        text=message["content"],
                        key=f"tts_{i}_{hash(message['content'][:20])}"
                    )

