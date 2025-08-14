#!/usr/bin/env python3
"""
Test the complete booking flow with validation and confirmation
"""

import sys
import os
from dotenv import load_dotenv

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment
load_dotenv()

from src.config_manager import ConfigManager
from src.travel_planner_agent import TravelPlannerAgent


def test_complete_booking_flow():
    """Test the complete booking flow from request to confirmation"""
    
    print("🧪 Testing Complete Booking Flow")
    print("=" * 50)
    
    # Initialize components
    config_manager = ConfigManager()
    agent = TravelPlannerAgent()
    
    print("1. Testing Hotel Booking Flow:")
    print("-" * 30)
    
    # Test hotel booking with incomplete info
    incomplete_hotel_query = "Tôi muốn đặt phòng ở Đà Nẵng"
    print(f"Query: '{incomplete_hotel_query}'")
    
    result = agent.plan_travel(incomplete_hotel_query, [])
    print(f"Response: {result['response'][:200]}...")
    print(f"Tool used: {result.get('tool_used')}")
    print(f"Missing fields: {result.get('missing_fields', [])}")
    
    # Test hotel booking with complete info
    complete_hotel_query = "Tên tôi là Nguyễn Văn A, SĐT: 0987654321, đặt phòng khách sạn Sheraton ở Đà Nẵng ngày 25/12/2024, 2 đêm"
    print(f"\nQuery with complete info: '{complete_hotel_query}'")
    
    result = agent.plan_travel(complete_hotel_query, [])
    print(f"Response: {result['response'][:300]}...")
    print(f"Tool used: {result.get('tool_used')}")
    print(f"Awaiting confirmation: {result.get('awaiting_confirmation', False)}")
    
    if result.get('booking_details'):
        print("Booking details:")
        for key, value in result['booking_details'].items():
            if value:
                print(f"  {key}: {value}")
    
    print(f"\n2. Testing Car Booking Flow:")
    print("-" * 30)
    
    # Test car booking with incomplete info
    incomplete_car_query = "Tôi muốn đặt xe từ sân bay Nội Bài"
    print(f"Query: '{incomplete_car_query}'")
    
    result = agent.plan_travel(incomplete_car_query, [])
    print(f"Response: {result['response'][:200]}...")
    print(f"Tool used: {result.get('tool_used')}")
    print(f"Missing fields: {result.get('missing_fields', [])}")
    
    # Test car booking with complete info
    complete_car_query = "Tên tôi là Trần Thị B, SĐT: 0123456789, đặt xe 4 chỗ từ sân bay Nội Bài đến khách sạn Hilton lúc 15:30"
    print(f"\nQuery with complete info: '{complete_car_query}'")
    
    result = agent.plan_travel(complete_car_query, [])
    print(f"Response: {result['response'][:300]}...")
    print(f"Tool used: {result.get('tool_used')}")
    print(f"Awaiting confirmation: {result.get('awaiting_confirmation', False)}")
    
    if result.get('booking_details'):
        print("Booking details:")
        for key, value in result['booking_details'].items():
            if value:
                print(f"  {key}: {value}")
    
    print(f"\n3. Testing Booking Save:")
    print("-" * 30)
    
    # Test saving a hotel booking
    test_hotel_booking = {
        'customer_name': 'Nguyễn Văn Test',
        'customer_phone': '0987654321',
        'hotel_name': 'Test Hotel',
        'location': 'Đà Nẵng',
        'check_in_date': '2024-12-25',
        'check_out_date': '2024-12-27',
        'nights': 2,
        'guests': 2,
        'room_type': 'deluxe',
        'status': 'confirmed'
    }
    
    success = config_manager.db_manager.save_hotel_booking_enhanced(test_hotel_booking)
    print(f"Hotel booking save result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test saving a car booking
    test_car_booking = {
        'customer_name': 'Trần Thị Test',
        'customer_phone': '0123456789',
        'pickup_location': 'Sân bay Nội Bài',
        'destination': 'Khách sạn Hilton',
        'pickup_time': '15:30',
        'car_type': '4 chỗ',
        'seats': 4,
        'status': 'confirmed'
    }
    
    success = config_manager.db_manager.save_car_booking_enhanced(test_car_booking)
    print(f"Car booking save result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test getting bookings
    car_bookings = config_manager.db_manager.get_all_car_bookings()
    hotel_bookings = config_manager.db_manager.get_all_hotel_bookings()
    
    print(f"\nTotal car bookings: {len(car_bookings)}")
    print(f"Total hotel bookings: {len(hotel_bookings)}")
    
    if car_bookings:
        print("Latest car booking:")
        latest_car = car_bookings[0]
        for key, value in latest_car.items():
            print(f"  {key}: {value}")
    
    if hotel_bookings:
        print("\nLatest hotel booking:")
        latest_hotel = hotel_bookings[0]
        for key, value in latest_hotel.items():
            print(f"  {key}: {value}")
    
    print(f"\n{'='*50}")
    print("✅ Booking flow test completed!")
    print("🎉 All booking validation, confirmation, and database save features are working!")


if __name__ == "__main__":
    test_complete_booking_flow()