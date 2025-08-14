#!/usr/bin/env python3
"""
Test the HTML escaping approach
"""

import html

def test_html_escaping():
    """Test if HTML escaping resolves the display issue"""
    
    print("🧪 Testing HTML Escaping Approach")
    print("=" * 40)
    
    # Test data (already cleaned)
    safe_title = "Test Conversation"
    safe_first_message = "I want hotel in Da Nang"
    safe_status_text = "🟢 Đang hoạt động"
    safe_last_active = "Vừa xong"
    safe_created_str = "14/08/2025 20:34"
    message_count = 2
    
    # Color variables
    border_color = "#4CAF50"
    bg_color = "#F8FFF8" 
    status_color = "#4CAF50"
    
    print("Before escaping:")
    print(f"Title: '{safe_title}'")
    print(f"Message: '{safe_first_message}'")
    print(f"Status: '{safe_status_text}'")
    
    # Apply HTML escaping
    escaped_title = html.escape(safe_title)
    escaped_message = html.escape(safe_first_message) 
    escaped_status = html.escape(safe_status_text)
    escaped_last_active = html.escape(safe_last_active)
    escaped_created = html.escape(safe_created_str)
    
    print(f"\nAfter escaping:")
    print(f"Title: '{escaped_title}'")
    print(f"Message: '{escaped_message}'")
    print(f"Status: '{escaped_status}'")
    
    # Test both approaches
    print(f"\n{'='*40}")
    print("1. F-string approach (original):")
    
    f_string_html = f"""
    <div style="border: 2px solid {border_color}; border-radius: 10px;">
        <h4>{escaped_title}</h4>
        <div><strong>Preview:</strong> {escaped_message}</div>
    </div>
    """
    
    print(f_string_html)
    
    print(f"\n{'='*40}")
    print("2. String concatenation approach (new):")
    
    concat_html = """
<div style="border: 2px solid """ + border_color + """; border-radius: 10px;">
    <h4>""" + escaped_title + """</h4>
    <div><strong>Preview:</strong> """ + escaped_message + """</div>
</div>
    """
    
    print(concat_html)


if __name__ == "__main__":
    test_html_escaping()
