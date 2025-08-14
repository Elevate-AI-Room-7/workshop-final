"""
AI Travel Assistant - Main Application
Combines RAG-only and Full-featured modes with Knowledge Base management
"""

import streamlit as st
import sys
import os
import pandas as pd
import json
from datetime import datetime
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
        try:
            agent = TravelPlannerAgent()
            st.session_state["travel_agent"] = agent
            
            # Debug info
            rag_type = type(agent.rag_system).__name__
            st.sidebar.info(f"🔧 RAG System: {rag_type}")
            
        except Exception as e:
            st.error(f"❌ Lỗi khởi tạo: {str(e)}")
            st.stop()

# Sidebar menu
st.sidebar.title("🌍 AI Travel Assistant")
st.sidebar.markdown("*Trợ lý du lịch thông minh với AI và RAG*")

# Menu selection
selected_page = st.sidebar.selectbox(
    "Chọn chức năng:",
    ["💬 Chat", "📚 Knowledge Base"],
    index=0
)

# Initialize session state for page management
if "current_action" not in st.session_state:
    st.session_state["current_action"] = "list"
if "selected_item_id" not in st.session_state:
    st.session_state["selected_item_id"] = None
if "page_number" not in st.session_state:
    st.session_state["page_number"] = 1

# Main content based on selected page
if selected_page == "💬 Chat":
    # Show welcome prompts only when no conversation yet
    if len(st.session_state["messages"]) == 0:
        st.markdown("""
        <div style="margin: 2rem 0; text-align: center;">
            <h4 style="color: #666; margin-bottom: 1.5rem;">✨ Tôi có thể giúp bạn với:</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Create 2x2 grid for feature prompts
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🌤️ Kiểm tra thời tiết", key="weather_prompt", use_container_width=True):
                st.session_state["messages"].append({
                    "role": "user", 
                    "content": "Kiểm tra thời tiết Hà Nội hôm nay"
                })
                st.rerun()
                
            if st.button("🏨 Đặt khách sạn", key="hotel_prompt", use_container_width=True):
                st.session_state["messages"].append({
                    "role": "user", 
                    "content": "Đặt khách sạn ở Đà Nẵng cho ngày 25/12/2025, 2 đêm"
                })
                st.rerun()
        
        with col2:
            if st.button("🗺️ Lên kế hoạch du lịch", key="planning_prompt", use_container_width=True):
                st.session_state["messages"].append({
                    "role": "user", 
                    "content": "Lập kế hoạch du lịch Sapa 3 ngày 2 đêm"
                })
                st.rerun()
                
            if st.button("🚗 Đặt xe", key="car_prompt", use_container_width=True):
                st.session_state["messages"].append({
                    "role": "user", 
                    "content": "Đặt xe từ Hà Nội đi Hạ Long ngày 25/12/2025"
                })
                st.rerun()

    # Chat input
    user_input = st.chat_input("Hỏi tôi về du lịch, thời tiết, đặt khách sạn hoặc đặt xe...")

    # Process user input
    if user_input:
        # Add user message
        st.session_state["messages"].append({
            "role": "user", 
            "content": user_input
        })
        
        # Detect if query might use RAG
        rag_keywords = [
            "gợi ý", "thông tin", "địa điểm", "du lịch", "nhà hàng", "khách sạn", 
            "hoạt động", "lịch trình", "kế hoạch", "điểm đến", "ăn uống", "tham quan",
            "hà nội", "hồ chí minh", "đà nẵng", "nha trang", "phú quốc", "sapa", 
            "hạ long", "huế", "hội an", "đà lạt", "cần thơ", "vịnh", "núi", "biển",
            "món ăn", "đặc sản", "văn hóa", "lễ hội", "chùa", "đền", "bảo tàng",
            "resort", "villa", "homestay", "booking", "giá", "tour", "package"
        ]
        likely_rag = any(keyword in user_input.lower() for keyword in rag_keywords)
        
        # Show appropriate spinner
        spinner_text = "🔍 Đang tìm kiếm..." if likely_rag else "🤔 Đang suy nghĩ..."
        with st.spinner(spinner_text):
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
                    # Check if no relevant info found and offer fallback
                    if result.get("no_relevant_info") and result.get("response") is None:
                        query = result.get("query", user_input)
                        fallback_message = f"Tôi không tìm thấy thông tin về **{query}** trong cơ sở dữ liệu. Bạn có muốn tôi trả lời dựa trên kiến thức chung không?"
                        
                        st.session_state["messages"].append({
                            "role": "assistant",
                            "content": fallback_message,
                            "sources": [],
                            "rag_used": False,
                            "need_fallback": True,
                            "fallback_query": query
                        })
                    else:
                        st.session_state["messages"].append({
                            "role": "assistant",
                            "content": result["response"],
                            "sources": result.get("sources", []),
                            "rag_used": result.get("rag_used", False),
                            "general_knowledge": result.get("general_knowledge", False),
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
            # Custom HTML container for user messages (right-aligned with human icon)
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; align-items: flex-end; margin: 1rem 0;">
                <div style="background-color: #007acc; color: white; padding: 12px 16px; 
                            border-radius: 18px 18px 5px 18px; max-width: 70%; 
                            box-shadow: 0 1px 2px rgba(0,0,0,0.1); margin-right: 8px;">
                    {message["content"]}
                </div>
                <div style="width: 32px; height: 32px; border-radius: 50%; background-color: #4CAF50; 
                            display: flex; align-items: center; justify-content: center; 
                            font-size: 16px; flex-shrink: 0;">
                    👤
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        elif message["role"] == "assistant":
            # Custom HTML container for assistant messages (left-aligned with AI icon)
            if message.get("error"):
                # Error messages with AI icon
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; align-items: flex-end; margin: 1rem 0;">
                    <div style="width: 32px; height: 32px; border-radius: 50%; background-color: #FF5722; 
                                display: flex; align-items: center; justify-content: center; 
                                font-size: 16px; flex-shrink: 0; margin-right: 8px;">
                        🤖
                    </div>
                    <div style="background-color: #ffebee; color: #c62828; padding: 12px 16px; 
                                border-radius: 18px 18px 18px 5px; max-width: 70%; 
                                box-shadow: 0 1px 2px rgba(0,0,0,0.1); border-left: 4px solid #f44336;">
                        ❌ {message["content"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; align-items: flex-end; margin: 1rem 0;">
                    <div style="width: 32px; height: 32px; border-radius: 50%; background-color: #2196F3; 
                                display: flex; align-items: center; justify-content: center; 
                                font-size: 16px; flex-shrink: 0; margin-right: 8px;">
                        🤖
                    </div>
                    <div style="background-color: #f0f2f6; color: #262730; padding: 12px 16px; 
                                border-radius: 18px 18px 18px 5px; max-width: 70%; 
                                box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                        {message["content"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show sources if RAG was used (debug info)
                sources = message.get("sources", [])
                rag_used = message.get("rag_used", False)
                    
                # Simplified condition for now - show sources if they exist
                if sources and not message.get("error") and not message.get("need_fallback"):
                    # Limit to 3 sources and add + if more
                    display_sources = sources[:3]
                    has_more = len(sources) > 3
                    
                    sources_text = ", ".join([f"`{source}`" for source in display_sources])
                    if has_more:
                        sources_text += f" +{len(sources) - 3}"
                    
                    st.markdown(f"""
                    <div style="margin-left: 40px; margin-top: 5px;">
                        <small style="color: #666; font-size: 12px;">
                            📚 <strong>Sources:</strong> {sources_text}
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show general knowledge indicator
                if message.get("general_knowledge"):
                    st.markdown("""
                    <div style="margin-left: 40px; margin-top: 5px;">
                        <small style="color: #666; font-size: 12px;">
                            🧠 <strong>Trả lời dựa trên kiến thức chung</strong>
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show fallback options if needed
                if message.get("need_fallback"):
                    st.markdown("""
                    <div style="margin-left: 40px; margin-top: 10px;">
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 1])
                    fallback_query = message.get("fallback_query", "")
                    
                    with col1:
                        if st.button("✅ Có, hãy trả lời", key=f"fallback_yes_{i}_{hash(fallback_query)}", use_container_width=True):
                            # Get general knowledge response
                            agent = st.session_state["travel_agent"]
                            result = agent.get_general_knowledge_response(fallback_query)
                            
                            if result["success"]:
                                st.session_state["messages"].append({
                                    "role": "assistant",
                                    "content": result["response"],
                                    "sources": [],
                                    "rag_used": False,
                                    "general_knowledge": True
                                })
                                st.rerun()
                    
                    with col2:
                        if st.button("❌ Không cần", key=f"fallback_no_{i}_{hash(fallback_query)}", use_container_width=True):
                            st.session_state["messages"].append({
                                "role": "assistant",
                                "content": "Được rồi! Bạn có thể hỏi tôi về chủ đề khác.",
                                "sources": [],
                                "rag_used": False
                            })
                            st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # TTS button for the latest message
                if i == len(st.session_state["messages"]) - 1 and not message.get("error"):
                    st.markdown("""
                    <div style="display: flex; justify-content: flex-start; margin-left: 40px;">
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        create_audio_button(
                            text=message["content"],
                            key=f"tts_{i}_{hash(message['content'][:20])}"
                        )
                    
                    st.markdown("</div>", unsafe_allow_html=True)

elif selected_page == "📚 Knowledge Base":
    # Get RAG system from agent
    rag_system = st.session_state["travel_agent"].rag_system
    
    # Knowledge Base header
    st.title("📚 Knowledge Base")
    st.markdown("*Quản lý cơ sở dữ liệu kiến thức du lịch*")
    
    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            stats = rag_system.get_index_stats()
            st.metric("📊 Records", stats.get('total_vectors', 0))
        except:
            st.metric("📊 Records", "0")
    
    with col2:
        st.metric("📐 Dimension", "1536")
    
    with col3:
        st.metric("🗃️ Database", "Pinecone")
    
    with col4:
        if st.button("➕ Tạo mới", type="primary", use_container_width=True):
            st.session_state["current_action"] = "create"
            st.rerun()
    
    st.markdown("---")
    
    # Handle different actions
    if st.session_state["current_action"] == "list":
        # List view with pagination
        st.subheader("📋 Danh sách Records")
        
        # Search bar
        search_query = st.text_input("🔍 Tìm kiếm", placeholder="Nhập từ khóa...")
        
        # Pagination settings
        items_per_page = 10
        page_number = st.session_state.get("page_number", 1)
        
        try:
            if search_query:
                # Search mode
                results = rag_system.search(search_query, top_k=50)  # Get more for pagination
            else:
                # Get all records (simulation - Pinecone doesn't have list all)
                results = rag_system.search("*", top_k=100)  # Get recent records
            
            if results:
                # Calculate pagination
                total_items = len(results)
                total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
                start_idx = (page_number - 1) * items_per_page
                end_idx = start_idx + items_per_page
                page_results = results[start_idx:end_idx]
                
                # Pagination controls
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    if st.button("⬅️ Trước", disabled=(page_number <= 1)):
                        st.session_state["page_number"] = max(1, page_number - 1)
                        st.rerun()
                
                with col2:
                    st.write(f"Trang {page_number}/{total_pages} - Hiển thị {len(page_results)}/{total_items} records")
                
                with col3:
                    if st.button("Sau ➡️", disabled=(page_number >= total_pages)):
                        st.session_state["page_number"] = min(total_pages, page_number + 1)
                        st.rerun()
                
                st.markdown("---")
                
                # Display items
                for result in page_results:
                    item_id = result.get('id', 'Unknown')
                    text = result.get('text', 'No content')
                    metadata = result.get('metadata', {})
                    score = result.get('score', 0)
                    
                    # Item container
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**🆔 ID:** {item_id}")
                            if search_query:
                                st.write(f"**🎯 Score:** {score:.3f}")
                            st.write(f"**📍 Location:** {metadata.get('location', 'N/A')}")
                            st.write(f"**📂 Category:** {metadata.get('category', 'N/A')}")
                            st.write(f"**⭐ Rating:** {metadata.get('rating', 'N/A')}")
                            
                            # Truncated text preview
                            preview_text = text[:150] + "..." if len(text) > 150 else text
                            st.write(f"**📝 Content:** {preview_text}")
                        
                        with col2:
                            # Action buttons
                            if st.button("👁️ View", key=f"view_{item_id}", use_container_width=True):
                                st.session_state["current_action"] = "view"
                                st.session_state["selected_item_id"] = item_id
                                st.rerun()
                            
                            if st.button("✏️ Edit", key=f"edit_{item_id}", use_container_width=True):
                                st.session_state["current_action"] = "edit"
                                st.session_state["selected_item_id"] = item_id
                                st.rerun()
                            
                            if st.button("🗑️ Delete", key=f"delete_{item_id}", use_container_width=True, type="secondary"):
                                st.session_state["current_action"] = "delete"
                                st.session_state["selected_item_id"] = item_id
                                st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("📭 Không có dữ liệu. Hãy tạo record đầu tiên!")
                
        except Exception as e:
            st.error(f"❌ Lỗi tải dữ liệu: {str(e)}")
    
    elif st.session_state["current_action"] == "create":
        # Create form
        st.subheader("➕ Tạo Record Mới")
        
        # Back button
        if st.button("⬅️ Quay lại danh sách"):
            st.session_state["current_action"] = "list"
            st.rerun()
        
        with st.form("create_form", clear_on_submit=True):
            new_id = st.text_input("🆔 ID", placeholder="unique-id-123")
            new_text = st.text_area("📝 Nội dung", placeholder="Thông tin du lịch...", height=120)
            
            # Metadata
            col1, col2 = st.columns(2)
            with col1:
                location = st.text_input("📍 Địa điểm", placeholder="Hà Nội")
                category = st.selectbox("📂 Danh mục", ["destination", "hotel", "restaurant", "activity", "transport"])
            with col2:
                rating = st.number_input("⭐ Đánh giá", min_value=0.0, max_value=5.0, value=0.0, step=0.1)
                price_range = st.selectbox("💰 Mức giá", ["$", "$$", "$$$", "$$$$"])
            
            submitted = st.form_submit_button("✅ Tạo Record", type="primary", use_container_width=True)
            
            if submitted:
                if new_id and new_text:
                    try:
                        # Debug info
                        st.write(f"🔧 Debug: RAG System type: {type(rag_system).__name__}")
                        st.write(f"🔧 Debug: Has upsert method: {hasattr(rag_system, 'upsert')}")
                        
                        metadata = {
                            "location": location,
                            "category": category,
                            "rating": rating,
                            "price_range": price_range,
                            "created_at": datetime.now().isoformat()
                        }
                        
                        embedding = rag_system.get_embedding(new_text)
                        metadata = rag_system._sanitize_metadata(metadata)
                        metadata["text"] = new_text
                        
                        # Check if upsert method exists before calling
                        if hasattr(rag_system, 'upsert'):
                            rag_system.upsert([(new_id, embedding, metadata)])
                        else:
                            st.error(f"❌ RAG system {type(rag_system).__name__} không có method upsert")
                            st.write(f"Available methods: {[m for m in dir(rag_system) if not m.startswith('_')]}")
                            raise AttributeError(f"'{type(rag_system).__name__}' object has no attribute 'upsert'")
                        
                        st.success(f"✅ Đã tạo record '{new_id}' thành công!")
                        st.session_state["current_action"] = "list"
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Lỗi tạo record: {str(e)}")
                else:
                    st.warning("⚠️ Vui lòng nhập đầy đủ ID và nội dung!")
    
    elif st.session_state["current_action"] == "view":
        # View detail
        item_id = st.session_state["selected_item_id"]
        st.subheader(f"👁️ Xem Record: {item_id}")
        
        # Back button
        if st.button("⬅️ Quay lại danh sách"):
            st.session_state["current_action"] = "list"
            st.rerun()
        
        try:
            # Search for the specific document
            search_results = rag_system.search(item_id, top_k=10)
            # Find exact match by ID
            record_found = None
            for result in search_results:
                if result.get('id') == item_id:
                    record_found = result
                    break
            
            if record_found:
                metadata = record_found.get('metadata', {})
                
                # Display details
                st.info(f"**🆔 ID:** {item_id}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**📍 Địa điểm:** {metadata.get('location', 'N/A')}")
                    st.write(f"**📂 Danh mục:** {metadata.get('category', 'N/A')}")
                with col2:
                    st.write(f"**⭐ Đánh giá:** {metadata.get('rating', 'N/A')}")
                    st.write(f"**💰 Mức giá:** {metadata.get('price_range', 'N/A')}")
                
                st.write(f"**📅 Tạo lúc:** {metadata.get('created_at', 'N/A')}")
                if metadata.get('updated_at'):
                    st.write(f"**📝 Cập nhật lúc:** {metadata.get('updated_at')}")
                
                st.markdown("**📝 Nội dung:**")
                st.text_area("", value=metadata.get('text', 'No content'), height=200, disabled=True)
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Chỉnh sửa", type="primary", use_container_width=True):
                        st.session_state["current_action"] = "edit"
                        st.rerun()
                with col2:
                    if st.button("🗑️ Xóa", type="secondary", use_container_width=True):
                        st.session_state["current_action"] = "delete"
                        st.rerun()
            else:
                st.error("❌ Không tìm thấy record!")
                
        except Exception as e:
            st.error(f"❌ Lỗi: {str(e)}")
    
    elif st.session_state["current_action"] == "edit":
        # Edit form
        item_id = st.session_state["selected_item_id"]
        st.subheader(f"✏️ Chỉnh sửa Record: {item_id}")
        
        # Back button
        if st.button("⬅️ Quay lại danh sách"):
            st.session_state["current_action"] = "list"
            st.rerun()
        
        try:
            # Search for the specific document
            search_results = rag_system.search(item_id, top_k=10)
            # Find exact match by ID
            record_found = None
            for result in search_results:
                if result.get('id') == item_id:
                    record_found = result
                    break
            
            if record_found:
                existing_metadata = record_found.get('metadata', {})
                
                with st.form("edit_form"):
                    updated_text = st.text_area(
                        "📝 Nội dung", 
                        value=existing_metadata.get('text', ''),
                        height=120
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        location = st.text_input("📍 Địa điểm", value=existing_metadata.get('location', ''))
                        category = st.selectbox(
                            "📂 Danh mục", 
                            ["destination", "hotel", "restaurant", "activity", "transport"],
                            index=["destination", "hotel", "restaurant", "activity", "transport"].index(
                                existing_metadata.get('category', 'destination')
                            ) if existing_metadata.get('category') in ["destination", "hotel", "restaurant", "activity", "transport"] else 0
                        )
                    with col2:
                        rating = st.number_input(
                            "⭐ Đánh giá", 
                            min_value=0.0, max_value=5.0, 
                            value=float(existing_metadata.get('rating', 0.0)), 
                            step=0.1
                        )
                        price_range = st.selectbox(
                            "💰 Mức giá", 
                            ["$", "$$", "$$$", "$$$$"],
                            index=["$", "$$", "$$$", "$$$$"].index(existing_metadata.get('price_range', '$')) if existing_metadata.get('price_range') in ["$", "$$", "$$$", "$$$$"] else 0
                        )
                    
                    submitted = st.form_submit_button("💾 Cập nhật", type="primary", use_container_width=True)
                    
                    if submitted:
                        try:
                            metadata = {
                                "location": location,
                                "category": category,
                                "rating": rating,
                                "price_range": price_range,
                                "updated_at": datetime.now().isoformat(),
                                "created_at": existing_metadata.get('created_at')
                            }
                            
                            embedding = rag_system.get_embedding(updated_text)
                            metadata = rag_system._sanitize_metadata(metadata)
                            metadata["text"] = updated_text
                            
                            rag_system.upsert([(item_id, embedding, metadata)])
                            
                            st.success(f"✅ Đã cập nhật record '{item_id}' thành công!")
                            st.session_state["current_action"] = "list"
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Lỗi cập nhật: {str(e)}")
            else:
                st.error("❌ Không tìm thấy record!")
                
        except Exception as e:
            st.error(f"❌ Lỗi: {str(e)}")
    
    elif st.session_state["current_action"] == "delete":
        # Delete confirmation
        item_id = st.session_state["selected_item_id"]
        st.subheader(f"🗑️ Xóa Record: {item_id}")
        
        # Back button
        if st.button("⬅️ Quay lại danh sách"):
            st.session_state["current_action"] = "list"
            st.rerun()
        
        try:
            # Search for the specific document
            search_results = rag_system.search(item_id, top_k=10)
            # Find exact match by ID
            record_found = None
            for result in search_results:
                if result.get('id') == item_id:
                    record_found = result
                    break
            
            if record_found:
                metadata = record_found.get('metadata', {})
                
                st.warning("⚠️ **Bạn có chắc chắn muốn xóa record này?**")
                
                # Show preview
                with st.container():
                    st.write(f"**🆔 ID:** {item_id}")
                    st.write(f"**📍 Địa điểm:** {metadata.get('location', 'N/A')}")
                    st.write(f"**📂 Danh mục:** {metadata.get('category', 'N/A')}")
                    preview_text = metadata.get('text', 'No content')[:200] + "..." if len(metadata.get('text', '')) > 200 else metadata.get('text', '')
                    st.write(f"**📝 Nội dung:** {preview_text}")
                
                # Confirmation
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("❌ Hủy", use_container_width=True):
                        st.session_state["current_action"] = "list"
                        st.rerun()
                
                with col2:
                    if st.button("🗑️ XÓA VĨNH VIỄN", type="primary", use_container_width=True):
                        try:
                            rag_system.delete([item_id])
                            st.success(f"✅ Đã xóa record '{item_id}' thành công!")
                            st.session_state["current_action"] = "list"
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Lỗi xóa: {str(e)}")
            else:
                st.error("❌ Không tìm thấy record!")
                
        except Exception as e:
            st.error(f"❌ Lỗi: {str(e)}")