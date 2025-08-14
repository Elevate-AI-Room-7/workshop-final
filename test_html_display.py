#!/usr/bin/env python3
"""
Test different approaches to prevent HTML display in Streamlit
"""

import sys
import os
import html
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment
load_dotenv()

from src.config_manager import ConfigManager


def test_html_display_approaches():
    """Test different approaches to handle HTML in text"""
    
    print("🧪 Testing HTML Display Approaches")
    print("=" * 45)
    
    test_content = "Hello <div>world</div> & <strong>test</strong>"
    
    print(f"Original content: {test_content}")
    
    # Approach 1: html.escape()
    escaped = html.escape(test_content)
    print(f"1. html.escape(): {escaped}")
    
    # Approach 2: Manual replacement
    manual = test_content.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
    print(f"2. Manual replace: {manual}")
    
    # Approach 3: Strip HTML tags completely
    import re
    stripped = re.sub(r'<[^>]+>', '', test_content)
    print(f"3. Strip tags: {stripped}")
    
    # Approach 4: Double escaping (for HTML inside HTML)
    double_escaped = html.escape(html.escape(test_content))
    print(f"4. Double escape: {double_escaped}")
    
    print(f"\n{'='*45}")
    print("Testing with actual conversation data...")
    
    # Test with real data
    config_manager = ConfigManager()
    
    # Create test conversation with HTML
    conv_id = config_manager.create_conversation("HTML Test <Conversation>")
    config_manager.save_message(conv_id, "user", "I want <div>content</div> here")
    
    # Get data back
    history = config_manager.get_conversation_history(conv_id)
    
    for msg_type, content in history:
        if msg_type == "user":
            print(f"\nOriginal: {content}")
            print(f"Escaped: {html.escape(content)}")
            print(f"Stripped: {re.sub(r'<[^>]+>', '', content)}")
            
            # Test HTML snippet construction
            escaped_content = html.escape(content)
            html_snippet = f'<div>Preview: {escaped_content}</div>'
            print(f"HTML snippet: {html_snippet}")
            break


if __name__ == "__main__":
    test_html_display_approaches()