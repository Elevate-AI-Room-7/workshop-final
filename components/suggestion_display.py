"""
Suggestion Display Component - UI components for displaying contextual suggestions
"""

import streamlit as st
from typing import List, Dict, Any, Optional


def render_suggestions(suggestions: List[Dict[str, Any]], 
                      key_prefix: str = "suggestion") -> Optional[str]:
    """
    Render suggestions as clickable buttons and return selected suggestion text
    
    Args:
        suggestions: List of suggestion dictionaries with 'text', 'category', 'tool_target', 'score'
        key_prefix: Unique prefix for streamlit component keys
        
    Returns:
        Selected suggestion text if any button was clicked, None otherwise
    """
    if not suggestions:
        return None
    
    # Filter out low quality suggestions
    filtered_suggestions = [s for s in suggestions if s.get('score', 0) > 0.3]
    if not filtered_suggestions:
        return None
    
    # Display suggestions header
    st.markdown("### 💡 Gợi ý câu hỏi liên quan")
    
    selected_suggestion = None
    
    # Create columns for better layout
    cols_per_row = 2
    rows = [filtered_suggestions[i:i + cols_per_row] 
            for i in range(0, len(filtered_suggestions), cols_per_row)]
    
    for row_idx, row_suggestions in enumerate(rows):
        cols = st.columns(len(row_suggestions))
        
        for col_idx, suggestion in enumerate(row_suggestions):
            with cols[col_idx]:
                # Create button with emoji based on tool target
                tool_emoji = _get_tool_emoji(suggestion.get('tool_target', 'GENERAL'))
                button_text = f"{tool_emoji} {suggestion['text']}"
                
                # Create button with custom styling
                button_key = f"{key_prefix}_{row_idx}_{col_idx}"
                
                if st.button(button_text, 
                           key=button_key,
                           help=f"Danh mục: {suggestion.get('category', 'N/A')} | "
                                f"Độ liên quan: {suggestion.get('score', 0):.2f}",
                           use_container_width=True):
                    selected_suggestion = suggestion['text']
                    
                    # Store selection in session state for feedback
                    if 'suggestion_feedback' not in st.session_state:
                        st.session_state.suggestion_feedback = {}
                    
                    st.session_state.suggestion_feedback[button_key] = {
                        'text': suggestion['text'],
                        'category': suggestion.get('category'),
                        'tool_target': suggestion.get('tool_target'),
                        'timestamp': st.session_state.get('current_time', '')
                    }
    
    # Add feedback section
    if filtered_suggestions:
        st.markdown("---")
        _render_suggestion_feedback(key_prefix)
    
    return selected_suggestion


def render_inline_suggestions(suggestions: List[Dict[str, Any]], 
                            max_display: int = 3,
                            key_prefix: str = "inline_suggestion") -> Optional[str]:
    """
    Render suggestions as inline chips/tags for compact display
    
    Args:
        suggestions: List of suggestion dictionaries
        max_display: Maximum number of suggestions to display
        key_prefix: Unique prefix for streamlit component keys
        
    Returns:
        Selected suggestion text if any was clicked
    """
    if not suggestions:
        return None
    
    # Filter and limit suggestions
    filtered_suggestions = [s for s in suggestions if s.get('score', 0) > 0.4][:max_display]
    if not filtered_suggestions:
        return None
    
    selected_suggestion = None
    
    # Display as horizontal layout
    st.markdown("**💡 Gợi ý:** ", help="Nhấn vào gợi ý để hỏi nhanh")
    
    cols = st.columns(len(filtered_suggestions))
    
    for idx, suggestion in enumerate(filtered_suggestions):
        with cols[idx]:
            tool_emoji = _get_tool_emoji(suggestion.get('tool_target', 'GENERAL'))
            
            # Create compact button
            button_key = f"{key_prefix}_{idx}"
            button_text = f"{tool_emoji} {suggestion['text']}"
            
            if st.button(button_text, 
                       key=button_key,
                       use_container_width=True):
                selected_suggestion = suggestion['text']
    
    return selected_suggestion


def render_suggestion_carousel(suggestions: List[Dict[str, Any]], 
                             key_prefix: str = "carousel") -> Optional[str]:
    """
    Render suggestions as a carousel/slider format
    
    Args:
        suggestions: List of suggestion dictionaries
        key_prefix: Unique prefix for streamlit component keys
        
    Returns:
        Selected suggestion text if any was selected
    """
    if not suggestions:
        return None
    
    filtered_suggestions = [s for s in suggestions if s.get('score', 0) > 0.3]
    if not filtered_suggestions:
        return None
    
    st.markdown("### 🎯 Khám phá thêm")
    
    # Create tabs for different categories
    categories = {}
    for suggestion in filtered_suggestions:
        category = suggestion.get('category', 'Khác')
        if category not in categories:
            categories[category] = []
        categories[category].append(suggestion)
    
    if len(categories) > 1:
        tab_names = list(categories.keys())
        tabs = st.tabs([_get_category_display_name(cat) for cat in tab_names])
        
        selected_suggestion = None
        
        for tab_idx, (category, tab) in enumerate(zip(tab_names, tabs)):
            with tab:
                for suggestion in categories[category]:
                    tool_emoji = _get_tool_emoji(suggestion.get('tool_target', 'GENERAL'))
                    button_text = f"{tool_emoji} {suggestion['text']}"
                    
                    button_key = f"{key_prefix}_{category}_{tab_idx}"
                    
                    if st.button(button_text, 
                               key=f"{button_key}_{suggestion['text'][:20]}",
                               use_container_width=True):
                        selected_suggestion = suggestion['text']
        
        return selected_suggestion
    else:
        # Single category, use simple layout
        return render_suggestions(filtered_suggestions, key_prefix)


def _get_tool_emoji(tool_target: str) -> str:
    """Get appropriate emoji for tool type"""
    emoji_map = {
        'RAG': '🗺️',
        'WEATHER': '🌤️', 
        'HOTEL': '🏨',
        'CAR': '🚗',
        'TRAVEL_PLAN': '📋',
        'GENERAL': '💬'
    }
    return emoji_map.get(tool_target, '❓')


def _get_category_display_name(category: str) -> str:
    """Get user-friendly display name for category"""
    category_map = {
        'weather_followup': '🌤️ Thời tiết',
        'accommodation': '🏨 Lưu trú',
        'transportation': '🚗 Di chuyển',
        'attractions': '🗺️ Địa điểm',
        'food': '🍜 Ẩm thực',
        'planning': '📋 Kế hoạch',
        'cross_tool': '🔗 Liên quan',
        'location_specific': '📍 Địa phương',
        'rag_attraction': '🏛️ Tham quan',
        'rag_food': '🍽️ Ẩm thực',
        'rag_hotel': '🏨 Khách sạn',
        'discovery': '🔍 Khám phá',
        'info': 'ℹ️ Thông tin'
    }
    return category_map.get(category, f"📌 {category.title()}")


def _render_suggestion_feedback(key_prefix: str):
    """Render feedback section for suggestions"""
    
    # Add rating for suggestion quality
    st.markdown("**📊 Các gợi ý có hữu ích không?**")
    
    feedback_cols = st.columns([1, 1, 1, 2])
    
    with feedback_cols[0]:
        if st.button("👍 Hữu ích", key=f"{key_prefix}_feedback_good"):
            st.session_state[f"{key_prefix}_feedback"] = "positive"
            st.success("Cảm ơn phản hồi!")
    
    with feedback_cols[1]:
        if st.button("👎 Không liên quan", key=f"{key_prefix}_feedback_bad"):
            st.session_state[f"{key_prefix}_feedback"] = "negative"
            st.info("Chúng tôi sẽ cải thiện gợi ý!")
    
    with feedback_cols[2]:
        if st.button("💡 Gợi ý khác", key=f"{key_prefix}_feedback_more"):
            st.session_state[f"{key_prefix}_feedback"] = "more"
            st.info("Hãy thử hỏi cụ thể hơn!")


def render_suggestion_stats(suggestions: List[Dict[str, Any]]):
    """Render statistics about suggestions for debugging"""
    if not suggestions:
        return
    
    if st.session_state.get('debug_mode', False):
        with st.expander("🔧 Debug: Suggestion Statistics"):
            st.write(f"**Total suggestions generated:** {len(suggestions)}")
            
            # Category breakdown
            categories = {}
            tool_targets = {}
            scores = []
            
            for suggestion in suggestions:
                category = suggestion.get('category', 'unknown')
                tool = suggestion.get('tool_target', 'unknown')
                score = suggestion.get('score', 0)
                
                categories[category] = categories.get(category, 0) + 1
                tool_targets[tool] = tool_targets.get(tool, 0) + 1
                scores.append(score)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Categories:**")
                for cat, count in categories.items():
                    st.write(f"- {cat}: {count}")
            
            with col2:
                st.write("**Tool Targets:**")
                for tool, count in tool_targets.items():
                    st.write(f"- {tool}: {count}")
            
            with col3:
                st.write("**Score Stats:**")
                if scores:
                    st.write(f"- Max: {max(scores):.2f}")
                    st.write(f"- Min: {min(scores):.2f}")
                    st.write(f"- Avg: {sum(scores)/len(scores):.2f}")


def handle_suggestion_click(suggestion_text: str) -> bool:
    """
    Handle when a suggestion is clicked
    
    Args:
        suggestion_text: The text of the clicked suggestion
        
    Returns:
        True if suggestion should be processed as new user input
    """
    if suggestion_text:
        # Store the suggestion in session state for processing
        st.session_state.suggestion_clicked = suggestion_text
        st.session_state.process_suggestion = True
        return True
    return False


def get_pending_suggestion() -> Optional[str]:
    """
    Get any pending suggestion that needs to be processed
    
    Returns:
        Suggestion text if there's a pending suggestion, None otherwise
    """
    if st.session_state.get('process_suggestion', False):
        suggestion = st.session_state.get('suggestion_clicked')
        # Clear the pending suggestion
        st.session_state.process_suggestion = False
        st.session_state.suggestion_clicked = None
        return suggestion
    return None


def clear_suggestions():
    """Clear any stored suggestion state"""
    keys_to_clear = [
        'suggestion_clicked', 
        'process_suggestion',
        'suggestion_feedback'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]