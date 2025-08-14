"""
AI Travel Assistant - Debug Version with Comprehensive Logging
"""

import streamlit as st
import sys
import os
import pandas as pd
import json
import traceback
import logging
from datetime import datetime
from dotenv import load_dotenv

# Setup comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('streamlit_debug.log')
    ]
)
logger = logging.getLogger(__name__)

logger.info("🚀 Starting Streamlit app with debug logging...")

# Add src to path for imports
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.append(src_path)
logger.info(f"📁 Added src path: {src_path}")

try:
    logger.info("🔧 Loading environment variables...")
    load_dotenv()
    logger.info("✅ Environment variables loaded")
except Exception as e:
    logger.error(f"❌ Failed to load environment: {e}")

# Page configuration
try:
    logger.info("⚙️ Configuring Streamlit page...")
    st.set_page_config(
        page_title="🌍 AI Travel Assistant - Debug",
        page_icon="🔧",
        layout="wide"
    )
    logger.info("✅ Page configuration complete")
except Exception as e:
    logger.error(f"❌ Page config failed: {e}")

# Debug info panel
st.title("🔧 AI Travel Assistant - Debug Mode")
st.markdown("*Debug version with comprehensive logging*")

debug_container = st.container()
with debug_container:
    col1, col2, col3 = st.columns(3)
    with col1:
        debug_status = st.empty()
        debug_status.info("🔍 Initializing...")
    with col2:
        import_status = st.empty()
        import_status.warning("⏳ Importing modules...")
    with col3:
        agent_status = st.empty()
        agent_status.warning("⏳ Creating agent...")

# Step 1: Test imports
try:
    logger.info("📦 Testing imports...")
    
    logger.debug("Importing TravelPlannerAgent...")
    from src.travel_planner_agent import TravelPlannerAgent
    logger.info("✅ TravelPlannerAgent imported successfully")
    
    logger.debug("Importing TTS utils...")
    from src.utils.tts import create_audio_button
    logger.info("✅ TTS utils imported successfully")
    
    import_status.success("✅ Imports OK")
    
except Exception as e:
    logger.error(f"❌ Import failed: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    import_status.error(f"❌ Import failed: {str(e)}")
    st.error("Import failed. Check logs for details.")
    st.stop()

# Initialize session state with debugging
logger.info("🔧 Initializing session state...")

if "messages" not in st.session_state:
    logger.debug("Creating messages session state")
    st.session_state["messages"] = []

if "travel_agent" not in st.session_state:
    logger.debug("Creating travel_agent session state")
    st.session_state["travel_agent"] = None

if "agent_initialized" not in st.session_state:
    logger.debug("Creating agent_initialized session state")
    st.session_state["agent_initialized"] = False

if "initialization_error" not in st.session_state:
    logger.debug("Creating initialization_error session state")
    st.session_state["initialization_error"] = None

logger.info("✅ Session state initialized")

# Step 2: Agent initialization with detailed logging
if not st.session_state["agent_initialized"] and st.session_state["initialization_error"] is None:
    logger.info("🤖 Starting agent initialization...")
    debug_status.info("🤖 Creating agent...")
    
    try:
        with st.spinner("🔄 Initializing AI Travel Assistant..."):
            logger.debug("About to create TravelPlannerAgent instance...")
            
            # Create agent with step-by-step logging
            agent = TravelPlannerAgent()
            logger.info("✅ TravelPlannerAgent instance created")
            
            # Test basic functionality
            logger.debug("Testing agent basic functionality...")
            if hasattr(agent, 'rag_system'):
                logger.info(f"✅ RAG system available: {type(agent.rag_system).__name__}")
                
                # Test RAG system stats
                try:
                    logger.debug("Getting RAG system stats...")
                    stats = agent.rag_system.get_index_stats()
                    logger.info(f"✅ RAG stats: {stats}")
                    
                    # Update sidebar
                    st.sidebar.success(f"🔧 Vector Database: ChromaDB")
                    st.sidebar.info(f"📚 Records: {stats.get('total_vectors', 0)}")
                    
                except Exception as stats_error:
                    logger.error(f"❌ Stats error: {stats_error}")
            
            # Test a simple query
            logger.debug("Testing simple query...")
            test_result = agent.plan_travel("test", [])
            logger.info(f"✅ Test query result: {test_result.get('success', False)}")
            
            # Store in session state
            st.session_state["travel_agent"] = agent
            st.session_state["agent_initialized"] = True
            logger.info("✅ Agent stored in session state")
            
            debug_status.success("✅ Agent ready")
            agent_status.success("✅ Agent OK")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Agent initialization failed: {error_msg}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        
        st.session_state["initialization_error"] = error_msg
        debug_status.error(f"❌ Failed: {error_msg[:50]}...")
        agent_status.error("❌ Agent failed")
        
        # Show detailed error
        st.error(f"❌ Agent initialization failed: {error_msg}")
        with st.expander("🔍 Show full error details"):
            st.code(traceback.format_exc())
        
        # Reset button
        if st.button("🔄 Retry Initialization"):
            logger.info("🔄 User requested retry")
            st.session_state["initialization_error"] = None
            st.session_state["agent_initialized"] = False
            st.rerun()
        
        st.stop()

# Step 3: Main chat interface (only if agent is ready)
if st.session_state["agent_initialized"]:
    logger.info("🎯 Rendering main chat interface...")
    
    st.markdown("---")
    st.subheader("💬 Chat Interface")
    
    # Quick test buttons
    if len(st.session_state["messages"]) == 0:
        st.markdown("### ✨ Test the assistant:")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🌤️ Test Weather", use_container_width=True):
                logger.info("User clicked weather test button")
                st.session_state["messages"].append({
                    "role": "user", 
                    "content": "Kiểm tra thời tiết Hà Nội hôm nay"
                })
                st.rerun()
        
        with col2:
            if st.button("🏨 Test Hotels", use_container_width=True):
                logger.info("User clicked hotels test button")
                st.session_state["messages"].append({
                    "role": "user", 
                    "content": "Gợi ý khách sạn ở Đà Nẵng"
                })
                st.rerun()

    # Display messages
    logger.debug(f"Displaying {len(st.session_state['messages'])} messages")
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
                    
                    # Show sources
                    sources = message.get("sources", [])
                    if sources:
                        with st.expander(f"📚 Sources ({len(sources)})"):
                            for source in sources[:3]:
                                st.text(f"• {source}")

    # Chat input
    user_input = st.chat_input("Type your message...")
    
    if user_input:
        logger.info(f"📝 User input received: {user_input[:50]}...")
        
        # Add user message
        st.session_state["messages"].append({
            "role": "user", 
            "content": user_input
        })
        
        # Process with detailed logging
        with st.spinner("🤔 Processing your request..."):
            try:
                logger.debug("Getting agent from session state...")
                agent = st.session_state["travel_agent"]
                
                logger.debug("Preparing chat history...")
                chat_history = []
                for msg in st.session_state["messages"][:-1]:
                    if msg["role"] == "user":
                        chat_history.append(("user", msg["content"]))
                    elif msg["role"] == "assistant" and not msg.get("error"):
                        chat_history.append(("assistant", msg["content"]))
                
                logger.info(f"🔄 Processing query with {len(chat_history)} history items...")
                
                # Get response
                result = agent.plan_travel(user_input, chat_history)
                logger.info(f"✅ Query processed, success: {result.get('success', False)}")
                
                # Add response
                if result["success"]:
                    response_content = {
                        "role": "assistant",
                        "content": result["response"],
                        "sources": result.get("sources", []),
                        "rag_used": result.get("rag_used", False)
                    }
                    st.session_state["messages"].append(response_content)
                    logger.info(f"✅ Added successful response with {len(result.get('sources', []))} sources")
                else:
                    error_content = {
                        "role": "assistant",
                        "content": f"Sorry, I encountered an error: {result['response']}",
                        "error": True
                    }
                    st.session_state["messages"].append(error_content)
                    logger.error(f"❌ Added error response: {result['response']}")
                
            except Exception as e:
                logger.error(f"❌ Chat processing error: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": f"❌ Processing error: {str(e)}",
                    "error": True
                })
        
        logger.info("🔄 Rerunning app to show new messages")
        st.rerun()

# Debug sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("🔧 Debug Info")
    
    st.write(f"**Session State Keys:** {list(st.session_state.keys())}")
    st.write(f"**Messages Count:** {len(st.session_state.get('messages', []))}")
    st.write(f"**Agent Ready:** {st.session_state.get('agent_initialized', False)}")
    
    if st.session_state.get("initialization_error"):
        st.error(f"**Error:** {st.session_state['initialization_error'][:100]}...")
    
    if st.button("🗑️ Clear All Data"):
        logger.info("🗑️ User requested data clear")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    if st.button("📄 Show Debug Log"):
        if os.path.exists('streamlit_debug.log'):
            with open('streamlit_debug.log', 'r') as f:
                log_content = f.read()
            st.text_area("Debug Log", log_content, height=200)

logger.info("🎯 App render complete")