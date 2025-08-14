#!/usr/bin/env python3
"""
Test the Streamlit HTML rendering issue specifically
"""

import sys
import os
from dotenv import load_dotenv

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

# Load environment
load_dotenv()

from src.config_manager import ConfigManager
from utils.html_cleaner import clean_html_content, clean_html_for_display, clean_title


def test_streamlit_html_issue():
    """Test if the issue is with how Streamlit processes HTML"""
    
    print("🧪 Testing Streamlit HTML Issue")
    print("=" * 40)
    
    config_manager = ConfigManager()
    
    # Create test data with HTML
    conv_id = config_manager.create_conversation("Test <div>Conversation</div>")
    config_manager.save_message(conv_id, "user", "I want <strong>hotel</strong> in <div>Da Nang</div>")
    config_manager.save_message(conv_id, "assistant", "Sure! I can help with <em>hotel booking</em>")
    
    # Simulate the exact logic from conversation_history_page.py
    conversations = config_manager.get_conversations()
    
    for conversation in conversations:
        if conversation['conversation_id'] == conv_id:
            conversation_id = conversation['conversation_id']
            title = conversation['title']
            is_active = conversation['is_active']
            
            # Get message history (same as in the actual code)
            try:
                history = config_manager.get_conversation_history(conversation_id)
                message_count = len(history)
                
                # Get preview of first user message (exact same logic)
                first_message = ""
                for msg_type, msg_content in history:
                    if msg_type == "user":
                        raw_message = msg_content
                        first_message = clean_html_for_display(raw_message, 100)
                        
                        print(f"Raw message: '{raw_message}'")
                        print(f"Cleaned message: '{first_message}'")
                        break
                
                if not first_message:
                    first_message = "Chưa có tin nhắn người dùng"
                    
            except Exception as e:
                print(f"Error: {e}")
                message_count = 0
                first_message = "Không có tin nhắn"
            
            # Clean all content (exact same as in code)
            safe_title = clean_title(title)
            safe_first_message = first_message  # Already cleaned above
            safe_status_text = "🟢 Đang hoạt động" if is_active else "⚪ Không hoạt động"
            
            print(f"\nCleaned data for display:")
            print(f"Title: '{title}' → '{safe_title}'")
            print(f"First message: '{safe_first_message}'")
            print(f"Status: '{safe_status_text}'")
            
            # Test the HTML generation (exact same structure)
            border_color = "#4CAF50" if is_active else "#E0E0E0"
            bg_color = "#F8FFF8" if is_active else "#FAFAFA" 
            status_color = "#4CAF50" if is_active else "#9E9E9E"
            
            html_content = f"""
            <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; background-color: {bg_color};">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                    <h4 style="margin: 0; color: #333; font-size: 1.1em;">{safe_title}</h4>
                    <span style="color: {status_color}; font-size: 0.8em; font-weight: 500; white-space: nowrap; margin-left: 1rem;">{safe_status_text}</span>
                </div>
                <div style="color: #666; font-size: 0.85em; margin-bottom: 0.5rem;">
                    <strong>Preview:</strong> {safe_first_message}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8em; color: #888;">
                    <span>📝 {message_count} tin nhắn</span>
                    <span>🕒 Vừa xong</span>
                    <span>📅 Tạo: 14/08/2025</span>
                </div>
            </div>
            """
            
            print(f"\nGenerated HTML:")
            print(html_content)
            
            # Check if there are any remaining HTML tags in the variables
            variables_to_check = [safe_title, safe_first_message, safe_status_text]
            html_found = False
            
            for i, var in enumerate(variables_to_check):
                if "<" in str(var):
                    print(f"❌ HTML found in variable {i}: '{var}'")
                    html_found = True
            
            if not html_found:
                print("✅ No HTML tags found in any variables")
                print("📋 The issue might be with Streamlit's HTML rendering")
            
            break


if __name__ == "__main__":
    test_streamlit_html_issue()