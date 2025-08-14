"""
Configuration Sidebar Component
Allows users to customize agent settings and personal preferences
"""

import streamlit as st
from src.config_manager import ConfigManager

def render_config_sidebar():
    """Render configuration sidebar for agent and user settings"""
    
    # Initialize config manager
    if "config_manager" not in st.session_state:
        st.session_state["config_manager"] = ConfigManager()
    
    config_manager = st.session_state["config_manager"]
    
    st.sidebar.markdown("---")
    
    # Configuration section
    with st.sidebar.expander("⚙️ Cài đặt Agent", expanded=False):
        st.markdown("### 🤖 Thông tin Agent")
        
        # Agent basic settings
        current_name = config_manager.get_agent_name()
        new_name = st.text_input("Tên Agent", value=current_name, key="agent_name")
        
        current_personality = config_manager.get_personality()
        personality_options = ["friendly", "professional", "enthusiastic", "local_expert"]
        personality_labels = {
            "friendly": "🌟 Thân thiện",
            "professional": "💼 Chuyên nghiệp", 
            "enthusiastic": "🎉 Nhiệt tình",
            "local_expert": "🏘️ Chuyên gia địa phương"
        }
        
        new_personality = st.selectbox(
            "Tính cách",
            personality_options,
            index=personality_options.index(current_personality) if current_personality in personality_options else 0,
            format_func=lambda x: personality_labels.get(x, x),
            key="agent_personality"
        )
        
        current_avatar = config_manager.get_agent_avatar()
        avatar_options = ["🤖", "👩‍💼", "🧑‍🎓", "👨‍🏫", "🌟", "✨", "🎭", "🗺️"]
        new_avatar = st.selectbox(
            "Avatar", 
            avatar_options,
            index=avatar_options.index(current_avatar) if current_avatar in avatar_options else 0,
            key="agent_avatar"
        )
        
        st.markdown("### 🎨 Phong cách trả lời")
        
        current_tone = config_manager.get_response_tone()
        tone_options = ["casual", "formal"]
        tone_labels = {"casual": "Thoải mái", "formal": "Trang trọng"}
        new_tone = st.selectbox(
            "Giọng điệu",
            tone_options,
            index=tone_options.index(current_tone) if current_tone in tone_options else 0,
            format_func=lambda x: tone_labels.get(x, x),
            key="response_tone"
        )
        
        current_emoji = config_manager.agent_config.get('emoji_usage', 'moderate')
        emoji_options = ["minimal", "moderate", "high"]
        emoji_labels = {"minimal": "Ít", "moderate": "Vừa phải", "high": "Nhiều"}
        new_emoji = st.selectbox(
            "Sử dụng Emoji",
            emoji_options,
            index=emoji_options.index(current_emoji) if current_emoji in emoji_options else 1,
            format_func=lambda x: emoji_labels.get(x, x),
            key="emoji_usage"
        )
        
        st.markdown("### 🔧 Cài đặt nâng cao")
        
        current_temp = config_manager.get_temperature()
        new_temp = st.slider(
            "Độ sáng tạo (Temperature)",
            min_value=0.0,
            max_value=1.0,
            value=current_temp,
            step=0.1,
            key="temperature"
        )
        
        current_context = config_manager.get_max_context_messages()
        new_context = st.number_input(
            "Số tin nhắn ngữ cảnh",
            min_value=1,
            max_value=10,
            value=current_context,
            key="max_context"
        )
        
        # UI Settings
        st.markdown("### 🎨 Giao diện")
        
        show_tools = st.checkbox(
            "Hiển thị thông tin công cụ",
            value=config_manager.should_show_tool_indicators(),
            key="show_tools"
        )
        
        show_context = st.checkbox(
            "Hiển thị ngữ cảnh",
            value=config_manager.should_show_context_preview(),
            key="show_context"
        )
        
        enable_tts = st.checkbox(
            "Bật Text-to-Speech",
            value=config_manager.is_tts_enabled(),
            key="enable_tts"
        )
        
        # Save button
        if st.button("💾 Lưu cài đặt Agent", use_container_width=True):
            # Update agent config (flat structure based on database schema)
            new_config = config_manager.agent_config.copy()
            new_config['agent_name'] = new_name
            new_config['personality'] = new_personality
            new_config['avatar'] = new_avatar
            
            new_config['tone'] = new_tone
            new_config['emoji_usage'] = new_emoji
            
            new_config['creativity'] = new_temp
            new_config['context_messages'] = int(new_context)
            
            new_config['show_tool_info'] = show_tools
            new_config['show_context_preview'] = show_context
            new_config['enable_tts'] = enable_tts
            
            if config_manager.save_config('agent', new_config):
                st.success("✅ Đã lưu cài đặt!")
                # Refresh agent with new settings
                if "travel_agent" in st.session_state:
                    del st.session_state["travel_agent"]
                st.rerun()
            else:
                st.error("❌ Lỗi khi lưu cài đặt!")
    
    # User preferences section
    with st.sidebar.expander("👤 Sở thích cá nhân", expanded=False):
        st.markdown("### 🎯 Sở thích du lịch")
        
        # Travel interests
        current_interests = config_manager.get_user_interests()
        
        interest_nature = st.checkbox("🌿 Thiên nhiên", value=current_interests.get('nature', False))
        interest_culture = st.checkbox("🏛️ Văn hóa", value=current_interests.get('culture', False))
        interest_food = st.checkbox("🍜 Ẩm thực", value=current_interests.get('food', False))
        interest_adventure = st.checkbox("🏔️ Phiêu lưu", value=current_interests.get('adventure', False))
        interest_beach = st.checkbox("🏖️ Biển", value=current_interests.get('beach', False))
        interest_photography = st.checkbox("📸 Chụp ảnh", value=current_interests.get('photography', False))
        interest_shopping = st.checkbox("🛍️ Mua sắm", value=current_interests.get('shopping', False))
        
        st.markdown("### 💰 Ngân sách")
        
        current_budget = config_manager.get_user_budget_range('accommodation')
        budget_options = ["budget", "medium", "luxury", "flexible"]
        budget_labels = {"budget": "Tiết kiệm", "medium": "Trung bình", "luxury": "Cao cấp", "flexible": "Linh hoạt"}
        
        new_budget = st.selectbox(
            "Mức chi tiêu",
            budget_options,
            index=budget_options.index(current_budget) if current_budget in budget_options else 1,
            format_func=lambda x: budget_labels.get(x, x)
        )
        
        st.markdown("### 🍽️ Ăn uống")
        
        current_diet = config_manager.get_user_dietary_restrictions()
        
        is_vegetarian = st.checkbox("🥬 Ăn chay", value=current_diet.get('vegetarian', False))
        is_halal = st.checkbox("🕌 Halal", value=current_diet.get('halal', False))
        
        # Favorite cuisines
        cuisine_options = ["vietnamese", "asian", "international", "street_food", "fine_dining"]
        cuisine_labels = {
            "vietnamese": "Việt Nam",
            "asian": "Châu Á", 
            "international": "Quốc tế",
            "street_food": "Đường phố",
            "fine_dining": "Cao cấp"
        }
        
        current_cuisines = current_diet.get('favorite_cuisines', [])
        favorite_cuisines = st.multiselect(
            "Ẩm thực yêu thích",
            cuisine_options,
            default=current_cuisines,
            format_func=lambda x: cuisine_labels.get(x, x)
        )
        
        st.markdown("### ⚙️ Cài đặt cá nhân hóa")
        
        remember_prefs = st.checkbox(
            "Ghi nhớ sở thích",
            value=config_manager.should_remember_preferences()
        )
        
        proactive_suggestions = st.checkbox(
            "Gợi ý chủ động", 
            value=config_manager.should_give_proactive_suggestions()
        )
        
        # Bucket list
        st.markdown("### 🎯 Danh sách mơ ước")
        bucket_list = st.text_area(
            "Các điểm đến muốn ghé thăm (mỗi dòng một địa điểm)",
            value="\n".join(config_manager.get_user_bucket_list()),
            height=100
        )
        
        # Visited places
        st.markdown("### ✅ Đã từng đến")
        visited_places = st.text_area(
            "Các nơi đã đi (mỗi dòng một địa điểm)",
            value="\n".join(config_manager.get_user_visited_places()),
            height=80
        )
        
        # Save user preferences
        if st.button("💾 Lưu sở thích", use_container_width=True):
            user_updates = {
                "travel_preferences": {
                    "interests": {
                        "nature": interest_nature,
                        "culture": interest_culture,
                        "food": interest_food,
                        "adventure": interest_adventure,
                        "beach": interest_beach,
                        "photography": interest_photography,
                        "shopping": interest_shopping
                    },
                    "travel_style": {
                        "budget": new_budget
                    }
                },
                "dietary_restrictions": {
                    "vegetarian": is_vegetarian,
                    "halal": is_halal,
                    "favorite_cuisines": favorite_cuisines
                },
                "past_travels": {
                    "bucket_list": [place.strip() for place in bucket_list.split('\n') if place.strip()],
                    "visited_places": [place.strip() for place in visited_places.split('\n') if place.strip()]
                },
                "personalization_settings": {
                    "remember_preferences": remember_prefs,
                    "proactive_suggestions": proactive_suggestions
                }
            }
            
            if config_manager.update_user_preferences(user_updates):
                st.success("✅ Đã lưu sở thích!")
                st.rerun()
            else:
                st.error("❌ Lỗi khi lưu sở thích!")
        
        # Reset button
        if st.button("🔄 Reset về mặc định", use_container_width=True):
            if config_manager.reset_user_preferences():
                st.success("✅ Đã reset sở thích!")
                st.rerun()
            else:
                st.error("❌ Lỗi khi reset!")
    
    return config_manager