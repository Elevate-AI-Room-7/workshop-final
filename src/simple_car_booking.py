"""
Simple Car Booking Function Calling for Demo
Đơn giản chỉ để demo tính năng function calling của LangChain
"""

import re
from typing import Dict, Any, List
from langchain_core.tools import tool


@tool
def extract_car_info(user_input: str) -> Dict[str, Any]:
    """
    Trích xuất thông tin đặt xe từ input của user
    
    Args:
        user_input: Câu nói của người dùng
        
    Returns:
        Dict chứa thông tin đã trích xuất được
    """
    
    # Patterns đơn giản để trích xuất thông tin
    info = {}
    text = user_input.lower()
    
    # Tên khách hàng - Cải thiện pattern matching
    name_patterns = [
        r'tên (?:khách hàng[:\s]*|tôi là |của tôi là |)?([A-ZÀ-Ỹ][a-zà-ỹ]+(?: [A-ZÀ-Ỹ][a-zà-ỹ]+)*)',
        r'(?:tôi là |mình là |tên )([A-ZÀ-Ỹ][a-zà-ỹ]+(?: [A-ZÀ-Ỹ][a-zà-ỹ]+)*)',
        r'là ([A-ZÀ-Ỹ][a-zà-ỹ]+(?: [A-ZÀ-Ỹ][a-zà-ỹ]+)*)',
        r'^([A-ZÀ-Ỹ][a-zà-ỹ]+(?: [A-ZÀ-Ỹ][a-zà-ỹ]+)*),',  # Tên ở đầu câu, kết thúc bằng dấu phẩy
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, user_input)
        if match:
            info['name'] = match.group(1)
            break
    
    # Số điện thoại - Cải thiện pattern matching
    phone_patterns = [
        r'(?:số điện thoại[:\s]*|sdt[:\s]*|phone[:\s]*)(0\d{8,9})',
        r'(0\d{8,9})',
    ]
    
    for pattern in phone_patterns:
        phone_match = re.search(pattern, user_input.lower())
        if phone_match:
            # Lấy group 1 (số điện thoại)
            info['phone'] = phone_match.group(1)
            break
    
    # Điểm đón - Cải thiện pattern matching
    pickup_patterns = [
        r'điểm đón[:\s]*([^,\.]+?)(?:,|$)',  # "Điểm đón: Bx Miền Tây"
        r'(?:từ|đón tại|pickup) ([^đến,]+?)(?:\s+đến|\s+tới|,|$)',
        r'đón[:\s]*([^,\.]+?)(?:,|$)',
    ]
    
    for pattern in pickup_patterns:
        pickup_match = re.search(pattern, text)
        if pickup_match:
            info['pickup'] = pickup_match.group(1).strip()
            break
    
    # Điểm đến - Cải thiện pattern matching  
    dest_patterns = [
        r'điểm đến[:\s]*([^,\.]+?)(?:,|$)',  # "Điểm đến: Đà Nẵng"
        r'(?:đến|tới|to) ([^,\.]+)',
        r'đến[:\s]*([^,\.]+?)(?:,|$)',
    ]
    
    for pattern in dest_patterns:
        dest_match = re.search(pattern, text)
        if dest_match:
            info['destination'] = dest_match.group(1).strip()
            break
    
    # Thời gian
    time_match = re.search(r'(\d{1,2}:\d{2})', user_input)
    if time_match:
        info['time'] = time_match.group(1)
    elif 'mai' in text:
        info['time'] = 'ngày mai'
    elif 'hôm nay' in text:
        info['time'] = 'hôm nay'
    
    return {
        "extracted_info": info,
        "message": f"Đã trích xuất được {len(info)} thông tin"
    }


@tool
def check_booking_complete(booking_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Kiểm tra xem thông tin đặt xe đã đầy đủ chưa
    
    Args:
        booking_info: Thông tin đặt xe hiện tại
        
    Returns:
        Dict với kết quả kiểm tra và các field còn thiếu
    """
    
    required_fields = ['name', 'phone', 'pickup', 'destination']
    missing_fields = []
    
    for field in required_fields:
        if field not in booking_info or not booking_info[field]:
            missing_fields.append(field)
    
    field_names = {
        'name': 'Tên khách hàng',
        'phone': 'Số điện thoại', 
        'pickup': 'Điểm đón',
        'destination': 'Điểm đến'
    }
    
    is_complete = len(missing_fields) == 0
    
    return {
        "is_complete": is_complete,
        "missing_fields": [field_names[field] for field in missing_fields],
        "completion_rate": f"{((4 - len(missing_fields)) / 4) * 100:.0f}%"
    }


@tool
def confirm_booking(booking_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Xác nhận đặt xe khi thông tin đã đầy đủ
    
    Args:
        booking_info: Thông tin đặt xe đầy đủ
        
    Returns:
        Dict với thông tin xác nhận
    """
    
    booking_id = f"CAR{hash(str(booking_info)) % 10000:04d}"
    
    confirmation = f"""
🚗 **ĐẶT XE THÀNH CÔNG**

📋 **Mã đặt xe:** {booking_id}
👤 **Khách hàng:** {booking_info.get('name', 'N/A')}
📞 **Điện thoại:** {booking_info.get('phone', 'N/A')}
📍 **Điểm đón:** {booking_info.get('pickup', 'N/A')}
🎯 **Điểm đến:** {booking_info.get('destination', 'N/A')}
⏰ **Thời gian:** {booking_info.get('time', 'Sớm nhất có thể')}

✅ **Xe sẽ đến trong 15-20 phút**
📱 **Liên hệ tài xế:** 0901234567
"""
    
    return {
        "booking_id": booking_id,
        "confirmation_message": confirmation.strip(),
        "status": "confirmed"
    }


class SimpleCarBooking:
    """
    Class đơn giản để demo function calling cho đặt xe
    """
    
    def __init__(self):
        self.current_booking = {}
        self.tools = [extract_car_info, check_booking_complete, confirm_booking]
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """
        Xử lý input của user và trả về response
        """
        
        # Bước 1: Trích xuất thông tin từ input
        extraction_result = extract_car_info.invoke({"user_input": user_input})
        extracted_info = extraction_result.get("extracted_info", {})
        
        # Bước 2: Cập nhật thông tin booking hiện tại
        self.current_booking.update(extracted_info)
        
        # Bước 3: Kiểm tra xem đã đủ thông tin chưa
        check_result = check_booking_complete.invoke({"booking_info": self.current_booking})
        
        if check_result["is_complete"]:
            # Bước 4: Xác nhận đặt xe nếu đã đầy đủ
            confirmation = confirm_booking.invoke({"booking_info": self.current_booking})
            
            # Reset booking sau khi confirm
            self.current_booking = {}
            
            return {
                "success": True,
                "response": confirmation["confirmation_message"],
                "tool_used": "SIMPLE_CAR_BOOKING",
                "status": "confirmed",
                "booking_id": confirmation["booking_id"]
            }
        else:
            # Yêu cầu thông tin còn thiếu
            missing_fields = check_result["missing_fields"]
            completion_rate = check_result["completion_rate"]
            
            if len(missing_fields) == 1:
                response = f"Cảm ơn bạn! Tôi cần thêm thông tin: **{missing_fields[0]}**"
            else:
                response = f"Cảm ơn bạn! Tôi cần thêm thông tin:\n"
                for i, field in enumerate(missing_fields, 1):
                    response += f"{i}. {field}\n"
            
            response += f"\n📊 Hoàn thành: {completion_rate}"
            
            return {
                "success": True,
                "response": response,
                "tool_used": "SIMPLE_CAR_BOOKING", 
                "status": "gathering_info",
                "missing_fields": missing_fields,
                "completion_rate": completion_rate,
                "current_info": self.current_booking.copy()
            }