"""
Car Booking Smart Suggestions
Tạo suggestions cho Điểm đón và Điểm đến dựa trên địa danh trong conversation
"""

from typing import Dict, List, Any
import re


def extract_location_from_context(conversation_context: str) -> str:
    """Extract main location being discussed"""
    
    context_lower = conversation_context.lower()
    
    # Vietnamese major destinations with their pickup/destination suggestions
    location_mapping = {
        'đà nẵng': {
            'city': 'Đà Nẵng',
            'pickup_suggestions': [
                'Sân bay Đà Nẵng',
                'Ga Đà Nẵng', 
                'Bến xe trung tâm Đà Nẵng',
                'Khách sạn trung tâm Đà Nẵng',
                'Cầu Rồng'
            ],
            'destination_suggestions': [
                'Bà Nà Hills',
                'Hội An',
                'Ngũ Hành Sơn',
                'Bán đảo Sơn Trà',
                'Biển Mỹ Khê',
                'Chùa Linh Ứng'
            ]
        },
        'hà nội': {
            'city': 'Hà Nội',
            'pickup_suggestions': [
                'Sân bay Nội Bài',
                'Ga Hà Nội',
                'Bến xe Mỹ Đình',
                'Hồ Hoàn Kiếm',
                'Phố cổ Hà Nội'
            ],
            'destination_suggestions': [
                'Hạ Long',
                'Sapa',
                'Ninh Bình',
                'Tam Cốc',
                'Chùa Một Cột',
                'Lăng Bác'
            ]
        },
        'hồ chí minh': {
            'city': 'Hồ Chí Minh',
            'pickup_suggestions': [
                'Sân bay Tân Sơn Nhất',
                'Ga Sài Gòn',
                'Bến xe Miền Đông',
                'Quận 1',
                'Chợ Bến Thành'
            ],
            'destination_suggestions': [
                'Củ Chi',
                'Vũng Tầu',
                'Mũi Né',
                'Đà Lạt',
                'Cần Thơ',
                'Nhà thờ Đức Bà'
            ]
        },
        'hải phòng': {
            'city': 'Hải Phòng',
            'pickup_suggestions': [
                'Ga Hải Phòng',
                'Bến xe Hải Phòng',
                'Cảng Hải Phòng',
                'Trung tâm Hải Phòng',
                'Chợ Sắt'
            ],
            'destination_suggestions': [
                'Cát Bà',
                'Vịnh Lan Hạ',
                'Đồ Sơn',
                'Núi Tuần Châu',
                'Chùa Hang',
                'Bãi biển Đồ Sơn'
            ]
        },
        'nha trang': {
            'city': 'Nha Trang',
            'pickup_suggestions': [
                'Sân bay Cam Ranh',
                'Ga Nha Trang',
                'Bến xe Nha Trang',
                'Trung tâm Nha Trang',
                'Chợ Đầm'
            ],
            'destination_suggestions': [
                'Vinpearl Land',
                'Tháp Bà Ponagar',
                'Bãi Dài',
                'Đảo Khỉ',
                'Suối nước nóng I-Resort',
                'Biển Nha Trang'
            ]
        }
    }
    
    # Find the main location being discussed
    for location_key, location_data in location_mapping.items():
        if location_key in context_lower:
            return location_data
    
    return None


def generate_car_booking_suggestions(conversation_context: str, missing_fields: List[str]) -> List[str]:
    """
    Generate smart suggestions cho điểm đón/điểm đến based on conversation context
    """
    
    suggestions = []
    location_data = extract_location_from_context(conversation_context)
    
    if not location_data:
        # Fallback generic suggestions
        if 'Điểm đón' in missing_fields:
            suggestions.extend([
                'Sân bay gần nhất',
                'Ga tàu chính',
                'Khách sạn của tôi'
            ])
        if 'Điểm đến' in missing_fields:
            suggestions.extend([
                'Trung tâm thành phố',
                'Điểm du lịch nổi tiếng',
                'Khách sạn đặt trước'
            ])
        return suggestions
    
    city = location_data['city']
    
    # Generate context-aware suggestions
    if 'Điểm đón' in missing_fields:
        pickup_options = location_data['pickup_suggestions'][:3]  # Top 3
        for option in pickup_options:
            suggestions.append(f"Đón tại {option}")
    
    if 'Điểm đến' in missing_fields:
        dest_options = location_data['destination_suggestions'][:3]  # Top 3
        for option in dest_options:
            suggestions.append(f"Đến {option}")
    
    return suggestions


def generate_smart_car_suggestions(conversation_context: str, current_booking: Dict[str, Any], missing_fields: List[str]) -> List[str]:
    """
    Generate comprehensive smart suggestions
    """
    
    suggestions = []
    
    # Add location-based suggestions
    location_suggestions = generate_car_booking_suggestions(conversation_context, missing_fields)
    suggestions.extend(location_suggestions)
    
    # Add specific field suggestions if still missing critical info
    if 'Tên khách hàng' in missing_fields:
        # Don't suggest names, let user provide
        pass
    
    if 'Số điện thoại' in missing_fields:
        # Don't suggest phone numbers, let user provide
        pass
    
    # If we have pickup but no destination, suggest popular destinations
    if current_booking.get('pickup') and 'Điểm đến' in missing_fields:
        location_data = extract_location_from_context(conversation_context)
        if location_data:
            popular_destinations = location_data['destination_suggestions'][:2]
            for dest in popular_destinations:
                suggestions.append(f"Đến {dest}")
    
    # If we have destination but no pickup, suggest common pickup points
    if current_booking.get('destination') and 'Điểm đón' in missing_fields:
        location_data = extract_location_from_context(conversation_context)
        if location_data:
            common_pickups = location_data['pickup_suggestions'][:2]
            for pickup in common_pickups:
                suggestions.append(f"Đón tại {pickup}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_suggestions = []
    for suggestion in suggestions:
        if suggestion not in seen:
            seen.add(suggestion)
            unique_suggestions.append(suggestion)
    
    # Limit to top 5 most relevant
    return unique_suggestions[:5]