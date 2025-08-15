"""
Configuration Manager for AI Travel Assistant
Handles agent personalization, user preferences, and system settings
Now using SQLite database instead of JSON files
"""

import os
from typing import Dict, Any, List
from datetime import datetime
import streamlit as st
from .database_manager import DatabaseManager

class ConfigManager:
    """Manages all configuration settings for the travel assistant using SQLite database"""
    
    def __init__(self, db_path: str = None):
        # Initialize database manager
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'travel_assistant.db')
        
        self.db_manager = DatabaseManager(db_path)
        
        # Initialize default data if needed
        self.db_manager.initialize_default_data()
        
        # Load current configurations (cached for performance)
        self._agent_config = None
        self._personality_templates = None
        self._user_preferences = None
    
    @property
    def agent_config(self) -> Dict[str, Any]:
        """Get agent configuration (cached)"""
        if self._agent_config is None:
            self._agent_config = self.db_manager.get_agent_config()
        return self._agent_config
    
    @property  
    def personality_templates(self) -> Dict[str, Any]:
        """Get personality templates (cached)"""
        if self._personality_templates is None:
            self._personality_templates = self.db_manager.get_personality_templates()
        return self._personality_templates
    
    @property
    def user_preferences(self) -> Dict[str, Any]:
        """Get user preferences (cached)"""
        if self._user_preferences is None:
            self._user_preferences = self.db_manager.get_user_preferences()
        return self._user_preferences
    
    def refresh_cache(self):
        """Refresh cached configurations"""
        self._agent_config = None
        self._personality_templates = None
        self._user_preferences = None
    
    def save_config(self, config_type: str, config_data: Dict[str, Any]) -> bool:
        """Save configuration to database"""
        try:
            if config_type == 'agent':
                success = self.db_manager.save_agent_config(config_data)
                if success:
                    self._agent_config = None  # Clear cache
                return success
            elif config_type == 'user':
                success = self.db_manager.save_user_preferences(config_data)
                if success:
                    self._user_preferences = None  # Clear cache
                return success
            else:
                return False
        except Exception as e:
            st.error(f"Error saving config: {str(e)}")
            return False
    
    def get_agent_name(self) -> str:
        """Get agent display name"""
        return self.agent_config.get('agent_name', 'AI Assistant')
    
    def get_agent_full_name(self) -> str:
        """Get agent full name"""
        name = self.get_agent_name()
        return f'{name} - Trợ lý Du lịch AI'
    
    def get_agent_avatar(self) -> str:
        """Get agent avatar emoji"""
        return self.agent_config.get('avatar', '🤖')
    
    def get_personality(self) -> str:
        """Get agent personality type"""
        return self.agent_config.get('personality', 'friendly')
    
    def get_greeting_message(self) -> str:
        """Get random greeting message based on personality"""
        personality = self.get_personality()
        agent_name = self.get_agent_name()
        
        greetings = self.personality_templates.get('personalities', {}).get(personality, {}).get('greeting_messages', [
            f"Chào bạn! Mình là {agent_name}, trợ lý du lịch của bạn. Mình có thể giúp gì cho bạn hôm nay? 😊"
        ])
        
        import random
        greeting = random.choice(greetings)
        return greeting.format(agent_name=agent_name)
    
    def get_response_template(self, template_type: str) -> str:
        """Get response template based on personality"""
        personality = self.get_personality()
        templates = self.personality_templates.get('personalities', {}).get(personality, {}).get('response_templates', {})
        
        defaults = {
            'success': "Tôi đã tìm thấy thông tin cho bạn:",
            'no_info': "Tôi không tìm thấy thông tin cụ thể về điều này. Bạn có muốn tôi tư vấn dựa trên kiến thức chung không?",
            'error': "Xin lỗi, có lỗi xảy ra:",
            'booking_success': "Đặt chỗ thành công:",
            'weather': "Thông tin thời tiết:"
        }
        
        return templates.get(template_type, defaults.get(template_type, ""))
    
    def get_conversation_starter(self) -> str:
        """Get random conversation starter"""
        personality = self.get_personality()
        starters = self.personality_templates.get('personalities', {}).get(personality, {}).get('conversation_starters', [
            "Bạn có kế hoạch du lịch gì không?"
        ])
        
        import random
        return random.choice(starters)
    
    def should_use_emoji(self) -> bool:
        """Check if should use emoji based on settings"""
        emoji_usage = self.agent_config.get('emoji_usage', 'moderate')
        
        if emoji_usage == 'minimal':
            return False
        elif emoji_usage == 'moderate':
            import random
            return random.random() < 0.3
        else:  # high
            import random
            return random.random() < 0.6
    
    def get_preferred_emojis(self) -> List[str]:
        """Get list of preferred emojis"""
        emoji_usage = self.agent_config.get('emoji_usage', 'moderate')
        return self.personality_templates.get('emoji_styles', {}).get(emoji_usage, {}).get('preferred_emojis', ['😊', '✅'])
    
    def get_response_tone(self) -> str:
        """Get response tone (casual/formal)"""
        return self.agent_config.get('tone', 'casual')
    
    def get_max_context_messages(self) -> int:
        """Get maximum context messages for rewriting"""
        return self.agent_config.get('context_messages', 5)
    
    def get_temperature(self) -> float:
        """Get LLM temperature setting"""
        return self.agent_config.get('creativity', 0.7)
    
    def should_show_tool_indicators(self) -> bool:
        """Check if should show tool indicators"""
        return self.agent_config.get('show_tool_info', True)
    
    def should_show_context_preview(self) -> bool:
        """Check if should show context preview"""
        return self.agent_config.get('show_context_preview', True)
    
    def is_tts_enabled(self) -> bool:
        """Check if TTS is enabled"""
        return self.agent_config.get('enable_tts', False)
    
    def get_primary_color(self) -> str:
        """Get primary theme color"""
        return '#2196F3'  # Default color
    
    def get_accent_color(self) -> str:
        """Get accent theme color"""
        return '#4CAF50'  # Default color
    
    def get_user_travel_style(self) -> str:
        """Get user's preferred travel style"""
        return self.user_preferences.get('budget_preference', 'medium')
    
    def get_user_interests(self) -> Dict[str, bool]:
        """Get user's travel interests"""
        interests_list = self.user_preferences.get('travel_interests', [])
        # Convert list to dict format for backward compatibility
        interests_dict = {}
        for interest in interests_list:
            interests_dict[interest] = True
        return interests_dict
    
    def get_user_budget_range(self, category: str) -> str:
        """Get user's budget preference for category"""
        return self.user_preferences.get('budget_preference', 'flexible')
    
    def get_user_dietary_restrictions(self) -> Dict[str, Any]:
        """Get user's dietary restrictions"""
        restrictions_list = self.user_preferences.get('dietary_restrictions', [])
        # Convert to dict format
        restrictions_dict = {}
        for restriction in restrictions_list:
            restrictions_dict[restriction] = True
        return restrictions_dict
    
    def get_user_visited_places(self) -> List[str]:
        """Get list of places user has visited"""
        return self.user_preferences.get('visited_places', [])
    
    def get_user_bucket_list(self) -> List[str]:
        """Get user's travel bucket list"""
        return self.user_preferences.get('bucket_list', [])
    
    def should_remember_preferences(self) -> bool:
        """Check if should remember user preferences"""
        return self.user_preferences.get('remember_preferences', True)
    
    def should_give_proactive_suggestions(self) -> bool:
        """Check if should give proactive suggestions"""
        return self.user_preferences.get('proactive_suggestions', True)
    
    def personalize_response(self, base_response: str, context: Dict[str, Any] = None) -> str:
        """Personalize response based on user preferences and agent personality"""
        if not self.should_remember_preferences():
            return base_response
        
        # Apply personality tone
        tone = self.get_response_tone()
        personality = self.get_personality()
        
        # Add personal touches based on user interests
        interests = self.get_user_interests()
        if context and context.get('tool_used') == 'RAG':
            # Add interest-based suggestions
            if interests.get('food', False) and 'ăn' not in base_response.lower():
                base_response += "\n\n💡 *Bạn có muốn mình gợi ý thêm về ẩm thực địa phương không?*"
            elif interests.get('photography', False) and 'chụp' not in base_response.lower():
                base_response += "\n\n📸 *Tip: Đây cũng là điểm chụp ảnh rất đẹp đấy!*"
        
        # Add emoji if enabled
        if self.should_use_emoji():
            emojis = self.get_preferred_emojis()
            import random
            if not any(emoji in base_response for emoji in emojis):
                emoji = random.choice(emojis)
                base_response += f" {emoji}"
        
        return base_response
    
    def get_personalized_suggestions(self) -> List[str]:
        """Get personalized travel suggestions based on user profile"""
        if not self.should_give_proactive_suggestions():
            return []
        
        interests = self.get_user_interests()
        visited_places = self.get_user_visited_places()
        bucket_list = self.get_user_bucket_list()
        
        suggestions = []
        
        # Interest-based suggestions
        if interests.get('nature', False):
            suggestions.append("🌿 Khám phá các vườn quốc gia tuyệt đẹp")
        if interests.get('culture', False):
            suggestions.append("🏛️ Tìm hiểu văn hóa địa phương độc đáo")
        if interests.get('food', False):
            suggestions.append("🍜 Trải nghiệm ẩm thực đường phố authentic")
        if interests.get('beach', False):
            suggestions.append("🏖️ Thư giãn tại những bãi biển hoang sơ")
        
        # Bucket list reminders
        for place in bucket_list[:2]:  # Show max 2
            suggestions.append(f"✨ Lên kế hoạch cho {place} trong bucket list")
        
        return suggestions[:3]  # Return max 3 suggestions
    
    def update_user_preferences(self, updates: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            # Get current preferences
            current_prefs = self.user_preferences.copy()
            
            # Update with new values
            current_prefs.update(updates)
            
            # Save to database
            success = self.save_config('user', current_prefs)
            if success:
                self.refresh_cache()
            return success
            
        except Exception as e:
            st.error(f"Error updating preferences: {str(e)}")
            return False
    
    def reset_user_preferences(self) -> bool:
        """Reset user preferences to default"""
        try:
            default_prefs = self.db_manager._get_default_user_preferences()
            success = self.save_config('user', default_prefs)
            if success:
                self.refresh_cache()
            return success
        except Exception:
            return False
    
    # ===== NEW DATABASE-SPECIFIC METHODS =====
    
    def get_conversation_history(self, conversation_id: str, limit: int = None) -> List[tuple]:
        """Get conversation history"""
        return self.db_manager.get_conversation_history(conversation_id, limit)
    
    def save_message(self, conversation_id: str, message_type: str, content: str, metadata: Dict = None) -> bool:
        """Save message to conversation history"""
        return self.db_manager.save_message(conversation_id, message_type, content, metadata)
    
    def create_conversation(self, title: str) -> str:
        """Create new conversation"""
        return self.db_manager.create_conversation(title)
    
    def get_conversations(self) -> List[Dict]:
        """Get all conversations"""
        return self.db_manager.get_conversations()
    
    def get_active_conversation(self) -> str:
        """Get active conversation ID"""
        return self.db_manager.get_active_conversation()
    
    def set_active_conversation(self, conversation_id: str) -> bool:
        """Set active conversation"""
        return self.db_manager.set_active_conversation(conversation_id)
    
    def save_car_booking(self, booking: Dict[str, Any]) -> int:
        """Save car booking"""
        return self.db_manager.save_car_booking(booking)
    
    def save_hotel_booking(self, booking: Dict[str, Any]) -> int:
        """Save hotel booking"""
        return self.db_manager.save_hotel_booking(booking)
    
    def get_user_bookings(self, booking_type: str = 'all') -> Dict[str, List]:
        """Get user bookings"""
        return self.db_manager.get_user_bookings('default', booking_type)
    
    def update_conversation_title(self, conversation_id: str, new_title: str) -> bool:
        """Update conversation title"""
        return self.db_manager.update_conversation_title(conversation_id, new_title)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation"""
        return self.db_manager.delete_conversation(conversation_id)
    
    # ===== SUGGESTION ENGINE CONFIGURATION =====
    
    def get_suggestion_enabled(self) -> bool:
        """Check if suggestion system is enabled"""
        return self.agent_config.get('enable_suggestions', True)
    
    def get_max_suggestions(self) -> int:
        """Get maximum number of suggestions to display"""
        return self.agent_config.get('max_suggestions', 5)
    
    def get_suggestion_min_score(self) -> float:
        """Get minimum relevance score for suggestions"""
        return self.agent_config.get('suggestion_min_score', 0.3)
    
    def get_suggestion_diversity_factor(self) -> float:
        """Get diversity factor for suggestion selection"""
        return self.agent_config.get('suggestion_diversity_factor', 0.7)
    
    def should_show_cross_tool_suggestions(self) -> bool:
        """Check if cross-tool suggestions should be shown"""
        return self.agent_config.get('show_cross_tool_suggestions', True)
    
    def should_show_location_suggestions(self) -> bool:
        """Check if location-based suggestions should be shown"""
        return self.agent_config.get('show_location_suggestions', True)
    
    def should_show_rag_suggestions(self) -> bool:
        """Check if RAG-based suggestions should be shown"""
        return self.agent_config.get('show_rag_suggestions', True)
    
    def get_suggestion_display_mode(self) -> str:
        """Get suggestion display mode (inline, full, carousel)"""
        return self.agent_config.get('suggestion_display_mode', 'inline')
    
    def should_collect_suggestion_feedback(self) -> bool:
        """Check if suggestion feedback should be collected"""
        return self.agent_config.get('collect_suggestion_feedback', True)
    
    def get_suggestion_templates_config(self) -> Dict[str, Any]:
        """Get suggestion templates configuration"""
        return self.agent_config.get('suggestion_templates', {})
    
    def update_suggestion_config(self, config_updates: Dict[str, Any]) -> bool:
        """Update suggestion-related configuration"""
        try:
            current_config = self.agent_config.copy()
            
            # Update suggestion-related keys
            suggestion_keys = [
                'enable_suggestions', 'max_suggestions', 'suggestion_min_score',
                'suggestion_diversity_factor', 'show_cross_tool_suggestions',
                'show_location_suggestions', 'show_rag_suggestions',
                'suggestion_display_mode', 'collect_suggestion_feedback',
                'suggestion_templates'
            ]
            
            for key, value in config_updates.items():
                if key in suggestion_keys:
                    current_config[key] = value
            
            # Save updated config
            success = self.save_config('agent', current_config)
            if success:
                self.refresh_cache()
            return success
            
        except Exception as e:
            st.error(f"Error updating suggestion config: {str(e)}")
            return False