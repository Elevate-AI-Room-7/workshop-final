"""
Conversation History Page Component
Displays conversation history with search, filter, and management capabilities
"""

import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid
import sys
import os

# Add utils to path
utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils')
if utils_path not in sys.path:
    sys.path.append(utils_path)

try:
    from html_cleaner import clean_html_for_display, clean_title
    HTML_CLEANER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import html_cleaner: {e}")
    HTML_CLEANER_AVAILABLE = False
    
    # Fallback cleaning functions
    import re
    def clean_html_for_display(content: str, max_length: int = 100) -> str:
        if not content:
            return ""
        # Remove script and style tags completely
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.IGNORECASE | re.DOTALL)
        # Remove all HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        # Clean whitespace and truncate
        content = re.sub(r'\s+', ' ', content).strip()
        return content[:max_length] + ("..." if len(content) > max_length else "")
    
    def clean_title(title: str) -> str:
        if not title:
            return ""
        # Remove all HTML tags
        clean = re.sub(r'<[^>]+>', '', title)
        return re.sub(r'\s+', ' ', clean).strip()


def render_conversation_history_page(config_manager):
    """Render the conversation history page"""
    
    st.title("📜 Lịch sử hội thoại")
    
    # Get all conversations
    conversations = config_manager.get_conversations()
    active_conversation_id = config_manager.get_active_conversation()
    
    # Header with stats and new conversation button
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"**Tổng cộng:** {len(conversations)} cuộc hội thoại")
    
    with col2:
        if st.button("🆕 Hội thoại mới", type="primary", use_container_width=True):
            # Create new conversation with temporary title
            temp_title = f"New Chat {datetime.now().strftime('%H:%M')}"
            conversation_id = config_manager.create_conversation(temp_title)
            
            if conversation_id:
                # Set as active and clear current messages
                st.session_state.active_conversation_id = conversation_id
                st.session_state.messages = []
                st.session_state.chat_history = []
                st.session_state.conversation_needs_naming = True  # Flag to rename on first message
                
                st.success("✅ Đã tạo hội thoại mới!")
                # Switch to chat page - use navigation state instead of switch_page
                st.session_state.selected_page = "💬 Chat"
                st.rerun()
    
    with col3:
        # Refresh button
        if st.button("🔄 Làm mới", use_container_width=True):
            st.rerun()
    
    if not conversations:
        # Empty state
        st.markdown("""
        <div style="text-align: center; padding: 3rem 0; color: #666;">
            <h3>📝 Chưa có hội thoại nào</h3>
            <p>Bắt đầu cuộc hội thoại đầu tiên của bạn bằng cách click "🆕 Hội thoại mới"</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Search and filter section
    with st.expander("🔍 Tìm kiếm & Lọc", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            search_query = st.text_input("Tìm kiếm theo tiêu đề:", placeholder="Nhập từ khóa...")
        
        with col2:
            # Date filter
            date_filter = st.selectbox(
                "Lọc theo thời gian:",
                ["Tất cả", "Hôm nay", "7 ngày qua", "30 ngày qua", "90 ngày qua"]
            )
    
    # Filter conversations based on search and date
    filtered_conversations = filter_conversations(conversations, search_query, date_filter)
    
    if search_query and not filtered_conversations:
        st.warning(f"🔍 Không tìm thấy hội thoại nào với từ khóa: **{search_query}**")
        return
    
    # Sort conversations by update time (newest first)
    sorted_conversations = sorted(filtered_conversations, key=lambda x: x['updated_at'], reverse=True)
    
    # Display conversations in a grid
    st.markdown("---")
    
    for i, conversation in enumerate(sorted_conversations):
        conversation_id = conversation['conversation_id']
        title = conversation['title']
        created_at = conversation['created_at']
        updated_at = conversation['updated_at']
        is_active = conversation['is_active']
        
        # Format dates
        try:
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            updated_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            
            created_str = created_date.strftime("%d/%m/%Y %H:%M")
            updated_str = updated_date.strftime("%d/%m/%Y %H:%M")
            
            # Time since last update
            time_diff = datetime.now() - updated_date.replace(tzinfo=None)
            if time_diff.days > 0:
                last_active = f"{time_diff.days} ngày trước"
            elif time_diff.seconds > 3600:
                last_active = f"{time_diff.seconds // 3600} giờ trước"
            elif time_diff.seconds > 60:
                last_active = f"{time_diff.seconds // 60} phút trước"
            else:
                last_active = "Vừa xong"
                
        except:
            created_str = updated_str = last_active = "N/A"
        
        # Get message count
        try:
            history = config_manager.get_conversation_history(conversation_id)
            message_count = len(history)
            
            # Get preview of first user message
            first_message = ""
            for msg_type, msg_content in history:
                if msg_type == "user":
                    # Clean HTML safely for preview with explicit debugging
                    raw_message = msg_content
                    first_message = clean_html_for_display(raw_message, 100)
                    
                    # Debug print to see what's happening
                    if "<" in raw_message or "<" in first_message:
                        print(f"[DEBUG] Raw message: '{raw_message}'")
                        print(f"[DEBUG] Cleaned message: '{first_message}'")
                    break
            
            if not first_message:
                first_message = "Chưa có tin nhắn người dùng"
        except:
            message_count = 0
            first_message = "Không có tin nhắn"
        
        # Create conversation card
        with st.container():
            # Status indicator
            status_color = "#4CAF50" if is_active else "#9E9E9E"
            status_text = "🟢 Đang hoạt động" if is_active else "⚪ Không hoạt động"
            
            # Clean all text content safely
            safe_title = clean_title(title)
            safe_first_message = first_message  # Already cleaned above
            safe_status_text = status_text  # Should not contain HTML
            safe_last_active = last_active   # Should not contain HTML
            safe_created_str = created_str   # Should not contain HTML
            
            # Use Streamlit native components instead of HTML to avoid rendering issues
            border_color = "#4CAF50" if is_active else "#E0E0E0"
            bg_color = "#F8FFF8" if is_active else "#FAFAFA"
            
            # Create a styled container using CSS injection
            st.markdown(f"""
            <div style="
                border: 2px solid {border_color}; 
                border-radius: 10px; 
                padding: 1rem; 
                margin: 0.5rem 0; 
                background-color: {bg_color};
            ">
            </div>
            """, unsafe_allow_html=True)
            
            # Use Streamlit components for content to avoid HTML parsing issues
            with st.container():
                # Title and status row
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### {safe_title}")
                with col2:
                    st.markdown(f"<span style='color: {status_color}; font-size: 0.8em;'>{safe_status_text}</span>", unsafe_allow_html=True)
                
                # Preview
                st.markdown(f"**Preview:** {safe_first_message}")
                
                # Statistics row  
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"📝 {message_count} tin nhắn")
                with col2:
                    st.markdown(f"🕒 {safe_last_active}")
                with col3:
                    st.markdown(f"📅 Tạo: {safe_created_str}")
                
                # Add some spacing
                st.markdown("---")
            
            # Action buttons
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                if st.button(
                    "💬 Mở hội thoại", 
                    key=f"open_{conversation_id}",
                    use_container_width=True,
                    type="primary" if not is_active else "secondary"
                ):
                    load_conversation(config_manager, conversation_id, title)
                    
            with col2:
                if st.button(
                    "📋 Chi tiết",
                    key=f"details_{conversation_id}",
                    use_container_width=True
                ):
                    show_conversation_details(config_manager, conversation_id, title, created_str, updated_str, message_count)
            
            with col3:
                if st.button(
                    "🗑️ Xóa",
                    key=f"delete_{conversation_id}",
                    use_container_width=True,
                    type="secondary"
                ):
                    if st.session_state.get(f"confirm_delete_{conversation_id}"):
                        # Actually delete
                        delete_conversation(config_manager, conversation_id)
                        st.rerun()
                    else:
                        # Show confirmation
                        st.session_state[f"confirm_delete_{conversation_id}"] = True
                        st.warning("⚠️ Click lại để xác nhận xóa")
                        
        st.markdown("---")


def filter_conversations(conversations: List[Dict], search_query: str, date_filter: str) -> List[Dict]:
    """Filter conversations based on search query and date range"""
    
    filtered = conversations.copy()
    
    # Search filter
    if search_query:
        search_lower = search_query.lower()
        filtered = [
            conv for conv in filtered 
            if search_lower in conv['title'].lower()
        ]
    
    # Date filter
    if date_filter != "Tất cả":
        now = datetime.now()
        
        if date_filter == "Hôm nay":
            cutoff = now - timedelta(days=1)
        elif date_filter == "7 ngày qua":
            cutoff = now - timedelta(days=7)
        elif date_filter == "30 ngày qua":
            cutoff = now - timedelta(days=30)
        elif date_filter == "90 ngày qua":
            cutoff = now - timedelta(days=90)
        else:
            cutoff = None
        
        if cutoff:
            filtered = [
                conv for conv in filtered
                if datetime.fromisoformat(conv['updated_at'].replace('Z', '+00:00')).replace(tzinfo=None) >= cutoff
            ]
    
    return filtered


def load_conversation(config_manager, conversation_id: str, title: str):
    """Load a conversation and switch to chat page"""
    
    try:
        # Set as active conversation
        if config_manager.set_active_conversation(conversation_id):
            # Load conversation history
            history = config_manager.get_conversation_history(conversation_id)
            
            # Convert to session state format
            messages = []
            for message_type, content in history:
                messages.append({
                    "role": message_type,
                    "content": content
                })
            
            # Update session state
            st.session_state.chat_history = history
            st.session_state.messages = messages
            st.session_state.active_conversation_id = conversation_id
            
            st.success(f"✅ Đã mở hội thoại: **{title}**")
            
            # Switch to chat page
            st.session_state.selected_page = "💬 Chat"
            st.rerun()
            
        else:
            st.error("❌ Không thể mở hội thoại")
            
    except Exception as e:
        st.error(f"❌ Lỗi khi mở hội thoại: {str(e)}")


def show_conversation_details(config_manager, conversation_id: str, title: str, created_str: str, updated_str: str, message_count: int):
    """Show detailed information about a conversation"""
    
    with st.expander(f"📋 Chi tiết: {title}", expanded=True):
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Clean HTML from display content
            safe_title = clean_title(title)
            
            st.markdown(f"**📝 Tiêu đề:** {safe_title}")
            st.markdown(f"**🆔 ID:** {conversation_id[:8]}...")
            st.markdown(f"**📅 Tạo lúc:** {created_str}")
            st.markdown(f"**🔄 Cập nhật:** {updated_str}")
        
        with col2:
            st.markdown(f"**💬 Tổng tin nhắn:** {message_count}")
            status_text = "🟢 Đang hoạt động" if st.session_state.get('active_conversation_id') == conversation_id else "⚪ Không hoạt động"
            st.markdown(f"**📊 Trạng thái:** {status_text}")
        
        # Show recent messages preview
        st.markdown("**📜 Tin nhắn gần đây:**")
        
        try:
            history = config_manager.get_conversation_history(conversation_id, limit=5)
            
            if history:
                for msg_type, content in history[-5:]:  # Last 5 messages
                    icon = "👤" if msg_type == "user" else "🤖"
                    # Clean HTML safely for display
                    preview = clean_html_for_display(content, 150)
                    st.markdown(f"**{icon} {msg_type.title()}:** {preview}")
            else:
                st.info("Chưa có tin nhắn nào")
                
        except Exception as e:
            st.error(f"Không thể tải tin nhắn: {str(e)}")


def delete_conversation(config_manager, conversation_id: str):
    """Delete a conversation"""
    
    try:
        if config_manager.delete_conversation(conversation_id):
            st.success("✅ Đã xóa hội thoại thành công!")
            
            # If deleted conversation was active, clear session state
            if st.session_state.get('active_conversation_id') == conversation_id:
                st.session_state.active_conversation_id = None
                st.session_state.messages = []
                st.session_state.chat_history = []
                
        else:
            st.error("❌ Không thể xóa hội thoại")
    except Exception as e:
        st.error(f"❌ Lỗi khi xóa hội thoại: {str(e)}")


def auto_name_conversation_with_llm(config_manager, first_message: str) -> str:
    """Automatically generate conversation title using LLM based on first user message"""
    
    try:
        # Get the travel agent for LLM access
        if "travel_agent" not in st.session_state:
            from src.travel_planner_agent import TravelPlannerAgent
            st.session_state["travel_agent"] = TravelPlannerAgent()
        
        agent = st.session_state["travel_agent"]
        
        # Prompt for title generation
        title_prompt = f"""
Hãy tạo một tiêu đề ngắn gọn (3-8 từ) cho cuộc hội thoại du lịch dựa trên tin nhắn đầu tiên của người dùng.

Tin nhắn của người dùng: "{first_message}"

Yêu cầu:
- Tiêu đề phải ngắn gọn, súc tích
- Phản ánh chính xác nội dung cuộc hội thoại
- Sử dụng tiếng Việt
- Không dùng dấu ngoặc kép
- Ví dụ: "Du lịch Đà Nẵng", "Thời tiết Hà Nội", "Đặt khách sạn Sapa"

Chỉ trả lời tiêu đề, không giải thích thêm.
"""
        
        # Use the agent's LLM to generate title
        import openai
        from openai import AzureOpenAI
        import os
        
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-15-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": title_prompt}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        title = response.choices[0].message.content.strip()
        
        # Fallback if title is too long or empty
        if not title or len(title) > 50:
            # Extract key terms from message for fallback
            if "thời tiết" in first_message.lower():
                title = "Thời tiết"
            elif "đặt" in first_message.lower() and ("khách sạn" in first_message.lower() or "hotel" in first_message.lower()):
                title = "Đặt khách sạn"
            elif "đặt" in first_message.lower() and "xe" in first_message.lower():
                title = "Đặt xe"
            elif any(place in first_message.lower() for place in ["hà nội", "hồ chí minh", "đà nẵng", "sapa", "hạ long"]):
                # Extract place name
                places = ["hà nội", "hồ chí minh", "đà nẵng", "sapa", "hạ long"]
                for place in places:
                    if place in first_message.lower():
                        title = f"Du lịch {place.title()}"
                        break
            else:
                title = "Hội thoại du lịch"
        
        return title
        
    except Exception as e:
        print(f"Error generating title: {e}")
        # Fallback to simple extraction
        if len(first_message) > 30:
            return first_message[:27] + "..."
        return first_message or "Hội thoại mới"


def update_conversation_title_if_needed(config_manager):
    """Update conversation title if it needs naming (after first user message)"""
    
    if st.session_state.get('conversation_needs_naming') and st.session_state.get('messages'):
        # Find first user message
        first_user_message = None
        for msg in st.session_state.messages:
            if msg['role'] == 'user':
                first_user_message = msg['content']
                break
        
        if first_user_message:
            # Generate title using LLM
            new_title = auto_name_conversation_with_llm(config_manager, first_user_message)
            
            # Update conversation title in database
            active_conversation_id = st.session_state.get('active_conversation_id')
            if active_conversation_id and new_title:
                try:
                    # Update the conversation title (this needs to be implemented in database_manager)
                    # For now, we'll store it in session state as a reminder
                    st.session_state.conversation_new_title = new_title
                    st.session_state.conversation_needs_naming = False
                    
                    # Update conversation title in database
                    config_manager.update_conversation_title(active_conversation_id, new_title)
                    
                    return new_title
                except Exception as e:
                    print(f"Error updating conversation title: {e}")
    
    return None