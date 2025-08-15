#!/usr/bin/env python3
"""
Debug script to test HTML cleaning in actual conversation history
"""

import sys
import os
from dotenv import load_dotenv

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'components'))

# Load environment
load_dotenv()

from src.config_manager import ConfigManager


def debug_html_display():
    """Debug the actual HTML display in conversation history"""
    
    print("🔍 Debugging HTML Display in Conversation History")
    print("=" * 55)
    
    # Create config manager
    config_manager = ConfigManager()
    
    # Create test conversation with HTML content
    conv_id = config_manager.create_conversation("Debug <HTML> Test")
    
    # Add test messages
    test_messages = [
        ("user", "I want to visit <div>Da Nang</div> and <strong>Ho Chi Minh</strong>"),
        ("assistant", "Great choice! <em>Da Nang</em> is beautiful."),
        ("user", "<script>alert('test')</script>What about weather?")
    ]
    
    for msg_type, content in test_messages:
        config_manager.save_message(conv_id, msg_type, content)
        print(f"💾 Saved: {content}")
    
    # Test the import and functions used in conversation_history_page.py
    print(f"\n🧪 Testing import path:")
    
    # Simulate the same import as in conversation_history_page.py
    utils_path = os.path.join(os.path.dirname(__file__), 'utils')
    print(f"Utils path: {utils_path}")
    print(f"Utils exists: {os.path.exists(utils_path)}")
    
    if utils_path not in sys.path:
        sys.path.append(utils_path)
    
    try:
        from html_cleaner import clean_html_for_display, clean_title
        print("✅ Import successful")
        
        # Test the exact logic used in conversation history
        print(f"\n🔄 Testing conversation display logic:")
        
        conversations = config_manager.get_conversations()
        for conv in conversations:
            if conv['conversation_id'] == conv_id:
                title = conv['title']
                print(f"Original title: '{title}'")
                
                # Test title cleaning
                safe_title = clean_title(title)
                print(f"Cleaned title: '{safe_title}'")
                
                # Test message preview
                history = config_manager.get_conversation_history(conv_id)
                for msg_type, msg_content in history:
                    if msg_type == "user":
                        print(f"Original message: '{msg_content}'")
                        
                        # Apply the exact same logic as in conversation_history_page.py
                        first_message = clean_html_for_display(msg_content, 100)
                        print(f"Cleaned preview: '{first_message}'")
                        break
                break
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        
        # Test fallback cleaning
        import re
        print(f"\n🔄 Testing fallback cleaning:")
        
        test_content = "I want <div>test</div> content"
        cleaned = re.sub(r'<[^>]+>', '', test_content)
        print(f"Original: '{test_content}'")
        print(f"Fallback cleaned: '{cleaned}'")
    
    # Check if the problem is in the display itself
    print(f"\n🖼️ Testing HTML card rendering:")
    
    # Simulate the card HTML generation
    test_title = "Test <HTML> Title"
    test_preview = "Message with <div>content</div>"
    
    # Clean them
    try:
        from html_cleaner import clean_title, clean_html_for_display
        safe_title = clean_title(test_title)
        safe_preview = clean_html_for_display(test_preview, 50)
    except:
        import re
        safe_title = re.sub(r'<[^>]+>', '', test_title)
        safe_preview = re.sub(r'<[^>]+>', '', test_preview)
    
    print(f"Card title: '{safe_title}'")
    print(f"Card preview: '{safe_preview}'")
    
    # Generate sample HTML that would be used in Streamlit
    card_html = f"""
    <div style="border: 1px solid #ccc; padding: 1rem;">
        <h4>{safe_title}</h4>
        <div>Preview: {safe_preview}</div>
    </div>
    """
    
    print(f"\nGenerated HTML:")
    print(card_html)
    
    if "<" in safe_title or "<" in safe_preview:
        print("❌ PROBLEM: HTML tags still present in cleaned content!")
    else:
        print("✅ SUCCESS: No HTML tags in cleaned content")


if __name__ == "__main__":
    debug_html_display()