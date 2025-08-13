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
        with st.chat_message("user"):
            st.write(message["content"])
    
    elif message["role"] == "assistant":
        with st.chat_message("assistant"):
            # Show error messages differently
            if message.get("error"):
                st.error(message["content"])
            else:
                st.write(message["content"])
                
                
                # TTS button for the latest message
                if i == len(st.session_state["messages"]) - 1 and not message.get("error"):
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        create_audio_button(
                            text=message["content"],
                            key=f"tts_{i}_{hash(message['content'][:20])}"
                        )

