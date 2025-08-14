"""
Configuration Manager for AI Travel Assistant
Handles agent personalization, user preferences, and system settings
"""

import json
import os
from typing import Dict, Any, List
from datetime import datetime
import streamlit as st

class ConfigManager:
    """Manages all configuration settings for the travel assistant"""
    
    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        self.agent_config_path = os.path.join(self.config_dir, 'agent_config.json')
        self.personality_templates_path = os.path.join(self.config_dir, 'personality_templates.json')
        self.user_preferences_path = os.path.join(self.config_dir, 'user_preferences.json')
        
        # Load configurations
        self.agent_config = self._load_config(self.agent_config_path)
        self.personality_templates = self._load_config(self.personality_templates_path)
        self.user_preferences = self._load_config(self.user_preferences_path)
    
    def _load_config(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            st.error(f"Error loading config from {file_path}: {str(e)}")
            return {}
    
    def save_config(self, config_type: str, config_data: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        try:
            if config_type == 'agent':
                file_path = self.agent_config_path
                self.agent_config = config_data
            elif config_type == 'user':
                file_path = self.user_preferences_path
                self.user_preferences = config_data
            else:
                return False
            
            # Ensure directory exists
            os.makedirs(self.config_dir, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            st.error(f"Error saving config: {str(e)}")
            return False
    
    def get_agent_name(self) -> str:
        """Get agent display name"""
        return self.agent_config.get('agent_settings', {}).get('name', 'AI Assistant')
    
    def get_agent_full_name(self) -> str:
        """Get agent full name"""
        name = self.get_agent_name()
        return self.agent_config.get('agent_settings', {}).get('full_name', f'{name} - Trợ lý Du lịch AI')
    
    def get_agent_avatar(self) -> str:
        """Get agent avatar emoji"""
        return self.agent_config.get('agent_settings', {}).get('avatar', '🤖')
    
    def get_personality(self) -> str:
        """Get agent personality type"""
        return self.agent_config.get('agent_settings', {}).get('personality', 'friendly')
    
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
        emoji_usage = self.agent_config.get('response_style', {}).get('emoji_usage', 'moderate')
        
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
        emoji_usage = self.agent_config.get('response_style', {}).get('emoji_usage', 'moderate')
        return self.personality_templates.get('emoji_styles', {}).get(emoji_usage, {}).get('preferred_emojis', ['😊', '✅'])
    
    def get_response_tone(self) -> str:
        """Get response tone (casual/formal)"""
        return self.agent_config.get('response_style', {}).get('tone', 'casual')
    
    def get_max_context_messages(self) -> int:
        """Get maximum context messages for rewriting"""
        return self.agent_config.get('advanced_settings', {}).get('max_context_messages', 5)
    
    def get_temperature(self) -> float:
        """Get LLM temperature setting"""
        return self.agent_config.get('advanced_settings', {}).get('temperature', 0.7)
    
    def should_show_tool_indicators(self) -> bool:
        """Check if should show tool indicators"""
        return self.agent_config.get('ui_customization', {}).get('show_tool_indicators', True)
    
    def should_show_context_preview(self) -> bool:
        """Check if should show context preview"""
        return self.agent_config.get('ui_customization', {}).get('show_context_preview', True)
    
    def is_tts_enabled(self) -> bool:
        """Check if TTS is enabled"""
        return self.agent_config.get('ui_customization', {}).get('enable_tts', True)
    
    def get_primary_color(self) -> str:
        """Get primary theme color"""
        return self.agent_config.get('ui_customization', {}).get('primary_color', '#2196F3')
    
    def get_accent_color(self) -> str:
        """Get accent theme color"""
        return self.agent_config.get('ui_customization', {}).get('accent_color', '#4CAF50')
    
    def get_user_travel_style(self) -> str:
        """Get user's preferred travel style"""
        return self.user_preferences.get('travel_preferences', {}).get('travel_style', {}).get('budget', 'medium')
    
    def get_user_interests(self) -> Dict[str, bool]:
        """Get user's travel interests"""
        return self.user_preferences.get('travel_preferences', {}).get('interests', {})
    
    def get_user_budget_range(self, category: str) -> str:
        """Get user's budget preference for category"""
        return self.user_preferences.get('travel_preferences', {}).get('budget_preferences', {}).get(category, 'flexible')
    
    def get_user_dietary_restrictions(self) -> Dict[str, Any]:
        """Get user's dietary restrictions"""
        return self.user_preferences.get('dietary_restrictions', {})
    
    def get_user_visited_places(self) -> List[str]:
        """Get list of places user has visited"""
        return self.user_preferences.get('past_travels', {}).get('visited_places', [])
    
    def get_user_bucket_list(self) -> List[str]:
        """Get user's travel bucket list"""
        return self.user_preferences.get('past_travels', {}).get('bucket_list', [])
    
    def should_remember_preferences(self) -> bool:
        """Check if should remember user preferences"""
        return self.user_preferences.get('personalization_settings', {}).get('remember_preferences', True)
    
    def should_give_proactive_suggestions(self) -> bool:
        """Check if should give proactive suggestions"""
        return self.user_preferences.get('personalization_settings', {}).get('proactive_suggestions', True)
    
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
            # Deep merge updates into existing preferences
            def deep_merge(base_dict, update_dict):
                for key, value in update_dict.items():
                    if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                        deep_merge(base_dict[key], value)
                    else:
                        base_dict[key] = value
            
            deep_merge(self.user_preferences, updates)
            return self.save_config('user', self.user_preferences)
            
        except Exception as e:
            st.error(f"Error updating preferences: {str(e)}")
            return False
    
    def reset_user_preferences(self) -> bool:
        """Reset user preferences to default"""
        try:
            default_prefs = self._load_config(self.user_preferences_path)
            return self.save_config('user', default_prefs)
        except Exception:
            return False