#!/usr/bin/env python3
"""
Test script for context awareness scenario:
User asks "Kiên Giang có gì?" then "Thời tiết"
"""

import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment
load_dotenv()

from src.travel_planner_agent import TravelPlannerAgent

def test_context_scenario():
    """Test the context awareness issue"""
    
    print("🧪 Testing Context Awareness Scenario")
    print("="*60)
    
    # Initialize agent with debug mode enabled
    try:
        agent = TravelPlannerAgent(debug_mode=True)
        print("✅ Agent initialized successfully with debug mode")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Simulate conversation
    chat_history = []
    
    # First message: "Kiên Giang có gì?"
    print(f"\n{'='*60}")
    print("👤 USER: Kiên Giang có gì?")
    print("="*60)
    
    result1 = agent.plan_travel("Kiên Giang có gì?", chat_history)
    
    if result1.get("success"):
        response1 = result1.get("response", "")
        print(f"🤖 AGENT: {response1[:200]}...")
        
        # Add to chat history
        chat_history.append(("user", "Kiên Giang có gì?"))
        chat_history.append(("assistant", response1))
    else:
        print(f"❌ First query failed: {result1.get('response', 'Unknown error')}")
        return
    
    # Second message: "Thời tiết"  
    print(f"\n{'='*60}")
    print("👤 USER: Thời tiết")
    print("="*60)
    
    result2 = agent.plan_travel("Thời tiết", chat_history)
    
    if result2.get("success"):
        response2 = result2.get("response", "")
        city_used = result2.get("city", "Unknown")
        weather_type = result2.get("weather_type", "Unknown")
        
        print(f"🤖 AGENT: {response2}")
        print(f"\n📊 ANALYSIS:")
        print(f"🏙️ City extracted: {city_used}")
        print(f"⏰ Weather type: {weather_type}")
        print(f"🔧 Tool used: {result2.get('tool_used')}")
        
        # Check if correct
        if "kiên giang" in city_used.lower():
            print("✅ SUCCESS: Correctly used Kiên Giang from context!")
        else:
            print("❌ FAILED: Should have used Kiên Giang from context")
            print(f"   Expected: Kiên Giang")
            print(f"   Got: {city_used}")
    else:
        print(f"❌ Second query failed: {result2.get('response', 'Unknown error')}")
    
    print(f"\n{'='*60}")
    print("🏁 Test completed")

if __name__ == "__main__":
    test_context_scenario()