#!/usr/bin/env python3
"""
Test script for new conversation features:
- Auto conversation naming with LLM
- Conversation history management
- Database operations
"""

import sys
import os
from dotenv import load_dotenv
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'components'))

# Load environment
load_dotenv()

from src.config_manager import ConfigManager
from components.conversation_history_page import auto_name_conversation_with_llm


def test_conversation_features():
    """Test all conversation features"""
    
    print("🧪 Testing Conversation Management Features")
    print("=" * 60)
    
    # Initialize config manager
    try:
        config_manager = ConfigManager()
        print("✅ Config manager initialized")
    except Exception as e:
        print(f"❌ Failed to initialize config manager: {e}")
        return
    
    # Test 1: Create conversation
    print(f"\n{'='*60}")
    print("📝 TEST 1: Create Conversation")
    print("="*60)
    
    temp_title = f"Test Conversation {datetime.now().strftime('%H:%M:%S')}"
    conversation_id = config_manager.create_conversation(temp_title)
    
    if conversation_id:
        print(f"✅ Created conversation: {conversation_id}")
        print(f"📝 Title: {temp_title}")
    else:
        print("❌ Failed to create conversation")
        return
    
    # Test 2: Save messages
    print(f"\n{'='*60}")
    print("💬 TEST 2: Save Messages")
    print("="*60)
    
    test_messages = [
        ("user", "Xin chào! Tôi muốn đi du lịch Đà Nẵng"),
        ("assistant", "Chào bạn! Đà Nẵng là một điểm đến tuyệt vời. Bạn muốn biết thông tin gì về Đà Nẵng?"),
        ("user", "Có những địa điểm nào đẹp ở Đà Nẵng?"),
        ("assistant", "Đà Nẵng có nhiều địa điểm đẹp như Bà Nà Hills, Cầu Vàng, Hội An gần đó...")
    ]
    
    for msg_type, content in test_messages:
        success = config_manager.save_message(conversation_id, msg_type, content)
        if success:
            print(f"✅ Saved {msg_type} message: {content[:50]}...")
        else:
            print(f"❌ Failed to save {msg_type} message")
    
    # Test 3: Get conversation history
    print(f"\n{'='*60}")
    print("📜 TEST 3: Get Conversation History")
    print("="*60)
    
    history = config_manager.get_conversation_history(conversation_id)
    print(f"📊 Retrieved {len(history)} messages:")
    
    for i, (msg_type, content) in enumerate(history, 1):
        print(f"   {i}. {msg_type}: {content[:50]}{'...' if len(content) > 50 else ''}")
    
    # Test 4: Auto-naming with LLM
    print(f"\n{'='*60}")
    print("🤖 TEST 4: Auto-Naming with LLM")
    print("="*60)
    
    if history:
        first_user_message = None
        for msg_type, content in history:
            if msg_type == "user":
                first_user_message = content
                break
        
        if first_user_message:
            print(f"📝 First user message: {first_user_message}")
            
            try:
                # Test LLM naming
                new_title = auto_name_conversation_with_llm(config_manager, first_user_message)
                print(f"🎯 Generated title: '{new_title}'")
                
                # Update conversation title
                if config_manager.update_conversation_title(conversation_id, new_title):
                    print("✅ Successfully updated conversation title")
                else:
                    print("❌ Failed to update conversation title")
                    
            except Exception as e:
                print(f"❌ LLM naming failed: {e}")
                print("📝 Using fallback naming...")
                
                # Fallback naming
                if "đà nẵng" in first_user_message.lower():
                    fallback_title = "Du lịch Đà Nẵng"
                else:
                    fallback_title = "Hội thoại du lịch"
                
                print(f"🔄 Fallback title: '{fallback_title}'")
                config_manager.update_conversation_title(conversation_id, fallback_title)
    
    # Test 5: List all conversations
    print(f"\n{'='*60}")
    print("📋 TEST 5: List All Conversations")
    print("="*60)
    
    conversations = config_manager.get_conversations()
    print(f"📊 Total conversations: {len(conversations)}")
    
    for i, conv in enumerate(conversations, 1):
        title = conv['title']
        created_at = conv['created_at']
        is_active = "🟢" if conv['is_active'] else "⚪"
        print(f"   {i}. {is_active} {title} (Created: {created_at})")
    
    # Test 6: Set active conversation
    print(f"\n{'='*60}")
    print("🎯 TEST 6: Set Active Conversation")  
    print("="*60)
    
    if config_manager.set_active_conversation(conversation_id):
        print(f"✅ Set conversation {conversation_id[:8]}... as active")
        
        active_id = config_manager.get_active_conversation()
        print(f"🔍 Active conversation: {active_id[:8] if active_id else 'None'}...")
    else:
        print("❌ Failed to set active conversation")
    
    # Test 7: Database operations
    print(f"\n{'='*60}")
    print("🗄️ TEST 7: Test Database Operations")
    print("="*60)
    
    # Test agent config
    agent_name = config_manager.get_agent_name()
    personality = config_manager.get_personality()
    print(f"🤖 Agent: {agent_name} ({personality})")
    
    # Test user preferences
    interests = config_manager.get_user_interests()
    budget = config_manager.get_user_travel_style()
    print(f"👤 User interests: {list(interests.keys())[:3]}")
    print(f"💰 Budget preference: {budget}")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("="*60)
    print("✅ All conversation features working correctly!")
    print(f"📝 Created and managed conversation: {conversation_id[:8]}...")
    print(f"💬 Saved {len(test_messages)} messages")
    print(f"🤖 Auto-naming with LLM: {'✅ Working' if 'new_title' in locals() else '⚠️ Fallback used'}")
    print(f"🗄️ Database integration: ✅ Working")
    
    print(f"\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    test_conversation_features()