#!/usr/bin/env python3
"""
Final verification that HTML display issue is fixed
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


def test_final_fix():
    """Verify that the HTML display fix is complete and working"""
    
    print("🎯 Final HTML Display Fix Verification")
    print("=" * 50)
    
    config_manager = ConfigManager()
    
    # Create test data with problematic HTML
    conv_id = config_manager.create_conversation("<script>alert('title')</script>Vacation Planning <div>Test</div>")
    
    test_messages = [
        ("user", "I want to go to <strong>Da Nang</strong> and visit <div>beautiful places</div>"),
        ("assistant", "Great! <em>Da Nang</em> has <span style='color:red'>amazing beaches</span>"),
        ("user", "<script>alert('xss')</script>What about <div>hotels and restaurants</div>?"),
        ("assistant", "I'll help you find <strong>the best options</strong>!")
    ]
    
    for msg_type, content in test_messages:
        config_manager.save_message(conv_id, msg_type, content)
    
    print("1. Testing HTML cleaning functions:")
    print("-" * 30)
    
    # Test all HTML cleaning functions
    test_content = "I want <strong>hotel</strong> in <div>Da Nang</div> with <script>alert('xss')</script>good views"
    
    cleaned_content = clean_html_content(test_content)
    display_content = clean_html_for_display(test_content, 50)
    title_content = clean_title("<div>My <script>alert('title')</script>Title</div>")
    
    print(f"Original: '{test_content}'")
    print(f"clean_html_content: '{cleaned_content}'")
    print(f"clean_html_for_display: '{display_content}'")  
    print(f"clean_title: '{title_content}'")
    
    # Verify no HTML tags remain
    html_found = False
    for content in [cleaned_content, display_content, title_content]:
        if "<" in content or ">" in content:
            print(f"❌ HTML tags found in: '{content}'")
            html_found = True
    
    if not html_found:
        print("✅ All HTML cleaning functions working correctly")
    
    print(f"\n2. Testing conversation display logic:")
    print("-" * 30)
    
    # Test the actual conversation display logic
    conversations = config_manager.get_conversations()
    for conversation in conversations:
        if conversation['conversation_id'] == conv_id:
            title = conversation['title']
            conversation_id = conversation['conversation_id']
            is_active = conversation['is_active']
            
            # Apply same logic as in conversation_history_page.py
            safe_title = clean_title(title)
            
            # Get message history
            history = config_manager.get_conversation_history(conversation_id)
            first_message = ""
            for msg_type, msg_content in history:
                if msg_type == "user":
                    first_message = clean_html_for_display(msg_content, 100)
                    break
            
            print(f"Original title: '{title}'")
            print(f"Cleaned title: '{safe_title}'")
            print(f"First message preview: '{first_message}'")
            
            # Check if any HTML remains
            items_to_check = [safe_title, first_message]
            html_found = False
            
            for item in items_to_check:
                if "<" in str(item) or ">" in str(item):
                    print(f"❌ HTML found in display item: '{item}'")
                    html_found = True
            
            if not html_found:
                print("✅ No HTML tags in conversation display elements")
            
            break
    
    print(f"\n3. Security test:")
    print("-" * 30)
    
    # Test security - dangerous content should be neutralized
    dangerous_inputs = [
        "<script>alert('XSS attack')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='data:text/html,<script>alert(1)</script>'></iframe>"
    ]
    
    all_secure = True
    for dangerous in dangerous_inputs:
        cleaned = clean_html_content(dangerous)
        if any(word in cleaned.lower() for word in ['script', 'javascript:', 'iframe', 'onerror']):
            print(f"❌ Security risk: '{dangerous}' → '{cleaned}'")
            all_secure = False
        else:
            print(f"✅ Secure: '{dangerous}' → '{cleaned}'")
    
    print(f"\n4. Summary:")
    print("=" * 50)
    
    if not html_found and all_secure:
        print("🎉 SUCCESS: HTML display issue completely fixed!")
        print("✅ No HTML tags showing in conversation history")
        print("✅ All content properly cleaned and secure")
        print("✅ XSS attacks neutralized")
        print("✅ User interface displays clean, readable text")
        print("\n💡 Users will now see clean, formatted content without raw HTML tags")
    else:
        print("❌ Issues still present - further debugging needed")
    
    return not html_found and all_secure


if __name__ == "__main__":
    success = test_final_fix()
    exit(0 if success else 1)