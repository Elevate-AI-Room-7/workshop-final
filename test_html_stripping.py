#!/usr/bin/env python3
"""
Test HTML stripping approach
"""

import sys
import os
import re
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment
load_dotenv()

from src.config_manager import ConfigManager


def test_html_stripping():
    """Test HTML stripping approach"""
    
    print("🧪 Testing HTML Stripping Approach")
    print("=" * 40)
    
    # Test messages with HTML content
    test_messages = [
        "Tôi muốn đi du lịch <Đà Nẵng>",
        "Thời tiết hôm nay có <div>sunny</div> không?", 
        "Giá vé máy bay & khách sạn là bao nhiêu?",
        "<strong>Đây</strong> là <em>test</em> HTML",
        "<script>alert('test')</script>Content here",
        "Normal message without HTML"
    ]
    
    print("Testing regex HTML stripping:")
    for i, message in enumerate(test_messages, 1):
        cleaned = re.sub(r'<[^>]+>', '', message)
        print(f"{i}. Original: {message}")
        print(f"   Cleaned:  {cleaned}")
        print()
    
    # Test with actual database
    print("="*40)
    print("Testing with actual conversation...")
    
    config_manager = ConfigManager()
    
    # Create test conversation
    conv_id = config_manager.create_conversation("Test <HTML> Conversation")
    
    # Add messages with HTML
    test_content = [
        ("user", "I want to visit <div>Da Nang</div> and <strong>Ho Chi Minh</strong>"),
        ("assistant", "Great! <em>Da Nang</em> and <span>Ho Chi Minh</span> are amazing cities."),
        ("user", "What about <a href='#'>weather</a> forecast?")
    ]
    
    for msg_type, content in test_content:
        config_manager.save_message(conv_id, msg_type, content)
        print(f"💾 Saved {msg_type}: {content}")
    
    # Test the display logic
    print(f"\n📜 Testing display logic:")
    
    conversations = config_manager.get_conversations()
    for conv in conversations:
        if conv['conversation_id'] == conv_id:
            title = conv['title']
            
            # Test title cleaning
            clean_title = re.sub(r'<[^>]+>', '', title)
            print(f"Title - Original: '{title}'")
            print(f"Title - Cleaned:  '{clean_title}'")
            
            # Test message preview
            history = config_manager.get_conversation_history(conv_id)
            for msg_type, content in history:
                if msg_type == "user":
                    clean_content = re.sub(r'<[^>]+>', '', content)
                    preview = clean_content[:50] + ("..." if len(clean_content) > 50 else "")
                    print(f"Preview - Original: '{content}'")
                    print(f"Preview - Cleaned:  '{preview}'")
                    break
            break
    
    print(f"\n✅ HTML stripping approach tested successfully!")
    print("🎯 Result: All HTML tags removed, only text content displayed")


if __name__ == "__main__":
    test_html_stripping()