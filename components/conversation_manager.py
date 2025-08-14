"""
Conversation Manager Component
Handles conversation creation, selection, and management in the sidebar
"""

import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime


def render_conversation_title_display(config_manager):
    """Display current conversation title in sidebar"""
    
    # Get current active conversation
    active_conversation_id = config_manager.get_active_conversation()
    
    if active_conversation_id:
        try:
            # Get all conversations to find the active one
            conversations = config_manager.get_conversations()
            current_conversation = None
            
            for conv in conversations:
                if conv['conversation_id'] == active_conversation_id:
                    current_conversation = conv
                    break
            
            if current_conversation:
                title = current_conversation['title']
                
                # Check if it's a new conversation that needs naming
                if title.startswith("New Chat") or title.startswith("Hội thoại mới") or title.startswith("Test Conversation"):
                    display_title = "New Chat"
                else:
                    display_title = title
                    
                # Display current conversation title
                st.sidebar.markdown("---")
                st.sidebar.markdown(f"**💬 Current:** {display_title}")
                
                # Show quick tip
                st.sidebar.markdown("*💡 Tip: Sử dụng '📜 Lịch sử hội thoại' để xem tất cả*")
            else:
                st.sidebar.markdown("---")
                st.sidebar.markdown("**💬 Current:** New Chat")
                
        except Exception as e:
            st.sidebar.markdown("---") 
            st.sidebar.markdown("**💬 Current:** New Chat")
    else:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**💬 Current:** New Chat")


def initialize_conversation_if_needed(config_manager):
    """Initialize default conversation if none exists"""
    
    # Check if there's an active conversation
    active_conversation_id = config_manager.get_active_conversation()
    
    if not active_conversation_id:
        # Create default conversation with temporary title (will be renamed by LLM)
        temp_title = f"New Chat {datetime.now().strftime('%H:%M')}"
        conversation_id = config_manager.create_conversation(temp_title)
        
        if conversation_id:
            st.session_state.active_conversation_id = conversation_id
            st.session_state.conversation_needs_naming = True  # Flag for auto-naming
            return conversation_id
    else:
        st.session_state.active_conversation_id = active_conversation_id
        return active_conversation_id
    
    return None


def save_user_message(config_manager, message: str):
    """Save user message to active conversation"""
    active_conversation_id = st.session_state.get('active_conversation_id')
    
    if active_conversation_id:
        config_manager.save_message(
            conversation_id=active_conversation_id,
            message_type="user", 
            content=message
        )


def save_assistant_message(config_manager, message: str, metadata: Dict = None):
    """Save assistant message to active conversation"""
    active_conversation_id = st.session_state.get('active_conversation_id')
    
    if active_conversation_id:
        config_manager.save_message(
            conversation_id=active_conversation_id,
            message_type="assistant",
            content=message,
            metadata=metadata or {}
        )


def load_conversation_history(config_manager, conversation_id: str) -> List[tuple]:
    """Load conversation history from database"""
    try:
        return config_manager.get_conversation_history(conversation_id)
    except Exception as e:
        st.error(f"Lỗi khi tải lịch sử hội thoại: {e}")
        return []