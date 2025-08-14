"""
AI Travel Assistant - Simplified Stable Version
"""

import streamlit as st
import sys
import os
import traceback
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="🌍 AI Travel Assistant",
    page_icon="🤖",
    layout="wide"
)

def initialize_agent():
    """Initialize travel agent with proper error handling"""
    try:
        from src.travel_planner_agent import TravelPlannerAgent
        
        with st.spinner("🔄 Initializing AI Travel Assistant..."):
            agent = TravelPlannerAgent()
            return agent, None
    except Exception as e:
        error_msg = f"Failed to initialize: {str(e)}"
        st.error(f"❌ {error_msg}")
        with st.expander("Show error details"):
            st.code(traceback.format_exc())
        return None, error_msg

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "travel_agent" not in st.session_state:
    st.session_state["travel_agent"] = None
    st.session_state["agent_error"] = None

# Try to initialize agent only once
if st.session_state["travel_agent"] is None and st.session_state["agent_error"] is None:
    agent, error = initialize_agent()
    st.session_state["travel_agent"] = agent
    st.session_state["agent_error"] = error
    
    if agent:
        # Show success info in sidebar
        st.sidebar.success("✅ AI Assistant Ready")
        try:
            stats = agent.rag_system.get_index_stats()
            st.sidebar.info(f"📚 Records: {stats.get('total_vectors', 0)}")
        except:
            st.sidebar.info("📚 Records: Unknown")

# Main UI
st.title("🌍 AI Travel Assistant")
st.markdown("*Your intelligent travel companion*")

# Check if agent is ready
if st.session_state["travel_agent"] is None:
    if st.session_state["agent_error"]:
        st.error("⚠️ AI Assistant is not available. Please check the error above.")
        if st.button("🔄 Try Again"):
            st.session_state["agent_error"] = None
            st.rerun()
        st.stop()
    else:
        st.info("🔄 Initializing AI Assistant...")
        st.stop()

# Chat interface
st.subheader("💬 Chat")

# Quick action buttons
if len(st.session_state["messages"]) == 0:
    st.markdown("### ✨ Try these examples:")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🌤️ Weather in Hanoi", use_container_width=True):
            st.session_state["messages"].append({
                "role": "user", 
                "content": "Kiểm tra thời tiết Hà Nội hôm nay"
            })
            st.rerun()
            
        if st.button("🏨 Hotels in Da Nang", use_container_width=True):
            st.session_state["messages"].append({
                "role": "user", 
                "content": "Gợi ý khách sạn ở Đà Nẵng"
            })
            st.rerun()
    
    with col2:
        if st.button("🗺️ Plan Sapa trip", use_container_width=True):
            st.session_state["messages"].append({
                "role": "user", 
                "content": "Lập kế hoạch du lịch Sapa 3 ngày 2 đêm"
            })
            st.rerun()
            
        if st.button("🍜 Food in Hue", use_container_width=True):
            st.session_state["messages"].append({
                "role": "user", 
                "content": "Món ăn đặc sản Huế"
            })
            st.rerun()

# Display conversation
for i, message in enumerate(st.session_state["messages"]):
    if message["role"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])
    elif message["role"] == "assistant":
        with st.chat_message("assistant"):
            if message.get("error"):
                st.error(message["content"])
            else:
                st.write(message["content"])
                
                # Show sources if available
                sources = message.get("sources", [])
                if sources:
                    with st.expander(f"📚 Sources ({len(sources)})"):
                        for source in sources[:5]:  # Show max 5 sources
                            st.text(f"• {source}")

# Chat input
user_input = st.chat_input("Ask me about travel, weather, hotels...")

if user_input:
    # Add user message
    st.session_state["messages"].append({
        "role": "user", 
        "content": user_input
    })
    
    # Process with agent
    with st.spinner("🤔 Thinking..."):
        try:
            agent = st.session_state["travel_agent"]
            
            # Prepare chat history
            chat_history = []
            for msg in st.session_state["messages"][:-1]:  # Exclude current message
                if msg["role"] == "user":
                    chat_history.append(("user", msg["content"]))
                elif msg["role"] == "assistant" and not msg.get("error"):
                    chat_history.append(("assistant", msg["content"]))
            
            # Get response
            result = agent.plan_travel(user_input, chat_history)
            
            # Add response
            if result["success"]:
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": result["response"],
                    "sources": result.get("sources", []),
                    "rag_used": result.get("rag_used", False)
                })
            else:
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error: {result['response']}",
                    "error": True
                })
                
        except Exception as e:
            st.session_state["messages"].append({
                "role": "assistant",
                "content": f"❌ Error processing your request: {str(e)}",
                "error": True
            })
    
    # Rerun to show new messages
    st.rerun()

# Sidebar stats
with st.sidebar:
    st.markdown("---")
    st.subheader("📊 System Info")
    
    if st.session_state["travel_agent"]:
        try:
            stats = st.session_state["travel_agent"].rag_system.get_index_stats()
            st.metric("Database", stats.get('database', 'ChromaDB'))
            st.metric("Records", stats.get('total_vectors', 0))
            st.metric("Dimension", stats.get('dimension', 1536))
        except Exception as e:
            st.write("📊 Stats unavailable")
    
    st.markdown("---")
    st.caption("🤖 Powered by Claude & ChromaDB")
    
    # Reset button
    if st.button("🗑️ Clear Chat"):
        st.session_state["messages"] = []
        st.rerun()