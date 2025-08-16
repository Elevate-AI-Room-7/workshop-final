"""
LLM-based Hotel Booking Function Calling
Sử dụng LLM để tự động detect thông tin đặt khách sạn tương tự car booking
"""

import os
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage


@tool
def extract_hotel_booking_info_with_llm(user_input: str, current_booking: Dict[str, Any] = None, conversation_context: str = "") -> Dict[str, Any]:
    """
    Sử dụng LLM để trích xuất thông tin đặt khách sạn từ user input
    
    Args:
        user_input: Input của user
        current_booking: Thông tin booking hiện tại (nếu có)
        conversation_context: Context cuộc hội thoại
        
    Returns:
        Dict chứa thông tin đã trích xuất
    """
    
    # Khởi tạo LLM
    try:
        openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if openai_api_key and openai_endpoint:
            llm = ChatOpenAI(
                model="GPT-4o-mini",
                api_key=openai_api_key,
                base_url=openai_endpoint,
                temperature=0.1
            )
        else:
            # Fallback về regex nếu không có API key
            return _extract_hotel_with_regex(user_input, conversation_context)
    except:
        # Fallback về regex nếu có lỗi
        return _extract_hotel_with_regex(user_input, conversation_context)
    
    # Template để extract thông tin khách sạn với improved prompting
    extraction_prompt = ChatPromptTemplate.from_messages([
        ("system", """Bạn là AI chuyên trích xuất thông tin đặt khách sạn từ tiếng Việt và tiếng Anh.

NHIỆM VỤ: Trích xuất chính xác các thông tin sau:
- name: Tên khách hàng (họ tên đầy đủ)
- phone: Số điện thoại (0xxxxxxxxx)
- email: Địa chỉ email  
- hotel_name: Tên khách sạn (bao gồm brand như Marriott, Hilton, Sheraton, Lotte, InterContinental, etc.)
- location: Thành phố/địa điểm (Hà Nội, Đà Nẵng, HCMC, Nha Trang, Huế, Hội An, etc.)
- check_in_date: Ngày check-in (format: YYYY-MM-DD, default năm 2025)
- nights: Số đêm ở (số nguyên)
- guests: Số khách (số nguyên)
- room_type: Loại phòng

HƯỚNG DẪN TRÍCH XUẤT CHI TIẾT:
1. Tên khách sạn: Tìm brand names hoặc keywords "khách sạn", "hotel"
   - VD: "Marriott", "Hilton Đà Nẵng", "khách sạn Lotte", "Sheraton"
2. Địa điểm: Tìm tên thành phố Việt Nam
   - VD: "Đà Nẵng", "Hà Nội", "HCMC", "Sài Gòn", "Nha Trang"
3. Ngày checkin: Convert formats khác nhau
   - "25/12" → "2025-12-25", "20th December" → "2025-12-20"
4. Số đêm: Tìm "đêm", "nights", "ngày ở"
5. Số khách: Tìm "người", "guests", "khách"

VÍ DỤ THỰC TẾ:
Input: "Đặt Marriott Đà Nẵng 2 đêm từ 25/12"
Output: {"name": "", "phone": "", "email": "", "hotel_name": "Marriott", "location": "Đà Nẵng", "check_in_date": "2025-12-25", "nights": "2", "guests": "", "room_type": ""}

Input: "Book Hilton Hà Nội for 3 nights, 2 guests"  
Output: {"name": "", "phone": "", "email": "", "hotel_name": "Hilton", "location": "Hà Nội", "check_in_date": "", "nights": "3", "guests": "2", "room_type": ""}

CHỈ TRẢ VỀ JSON OBJECT, KHÔNG TEXT KHÁC."""),
        ("human", "Input: {user_input}")
    ])
    
    try:
        # Gọi LLM để extract
        chain = extraction_prompt | llm
        response = chain.invoke({"user_input": user_input})
        
        # Parse JSON response
        import json
        extracted_info = json.loads(response.content)
        
        # Merge với current booking nếu có
        if current_booking:
            for key, value in extracted_info.items():
                if value and value.strip():  # Chỉ update nếu có giá trị mới
                    current_booking[key] = value.strip()
            return {
                "extracted_info": current_booking,
                "new_fields": [k for k, v in extracted_info.items() if v and v.strip()],
                "method": "LLM"
            }
        else:
            # Loại bỏ các field rỗng
            cleaned_info = {k: v.strip() for k, v in extracted_info.items() if v and v.strip()}
            return {
                "extracted_info": cleaned_info,
                "new_fields": list(cleaned_info.keys()),
                "method": "LLM"
            }
            
    except Exception as e:
        print(f"LLM hotel extraction failed: {e}, falling back to regex")
        return _extract_hotel_with_regex(user_input, conversation_context)


def _extract_hotel_with_regex(user_input: str, conversation_context: str = "") -> Dict[str, Any]:
    """Enhanced fallback regex extraction cho hotel với improved patterns"""
    import re
    
    info = {}
    text = user_input.lower()
    original_text = user_input
    
    # Tên - enhanced patterns
    name_patterns = [
        r'tên ([A-ZÀ-Ỹ][a-zà-ỹ]+(?: [A-ZÀ-Ỹ][a-zà-ỹ]+)*)',  # "Tên Hiển Võ"
        r'^([A-ZÀ-Ỹ][a-zà-ỹ]+(?: [A-ZÀ-Ỹ][a-zà-ỹ]+)*),',  # "Hiển Võ,"
        r'(?:tôi là |mình là |i am |my name is )([A-ZÀ-Ỹ][a-zà-ỹ]+(?: [A-ZÀ-Ỹ][a-zà-ỹ]+)*)',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, original_text)
        if match:
            info['name'] = match.group(1)
            break
    
    # Số điện thoại - enhanced
    phone_match = re.search(r'(0\d{8,9})', original_text)
    if phone_match:
        info['phone'] = phone_match.group(1)
    
    # Email
    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', original_text)
    if email_match:
        info['email'] = email_match.group(1)
    
    # Hotel names - enhanced với brand recognition
    hotel_brand_patterns = [
        # Direct brand names
        r'\b(marriott|hilton|sheraton|intercontinental|lotte|hyatt|peninsula|regent|sofitel|novotel|pullman|mercure|accor)\b',
        # With hotel keyword
        r'(?:khách sạn|hotel)\s+([a-zà-ỹA-ZÀ-Ỹ0-9\s]+?)(?:\s+(?:ở|tại|in|at|,|$))',
        # Brand + location
        r'\b(marriott|hilton|sheraton|intercontinental|lotte|hyatt|peninsula|regent|sofitel|novotel|pullman|mercure)\s+([a-zà-ỹA-ZÀ-Ỹ\s]+)',
    ]
    
    for pattern in hotel_brand_patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 1:
                info['hotel_name'] = match.group(1).strip().title()
            else:
                info['hotel_name'] = f"{match.group(1).title()}"
            break
    
    # Location extraction - enhanced
    location_patterns = [
        # Specific Vietnamese cities
        r'\b(đà nẵng|hà nội|hồ chí minh|hcmc|sài gòn|nha trang|huế|hội an|đà lạt|vũng tầu|cần thơ|hải phòng|phú quốc|quy nhon)\b',
        # With prepositions
        r'(?:ở|tại|in|at)\s+([a-zà-ỹA-ZÀ-Ỹ\s]+?)(?:\s*[,.]|$)',
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text)
        if match:
            location = match.group(1).strip()
            # Normalize common city names
            city_mapping = {
                'hcmc': 'Hồ Chí Minh',
                'sài gòn': 'Hồ Chí Minh',
                'đà nẵng': 'Đà Nẵng',
                'hà nội': 'Hà Nội',
                'nha trang': 'Nha Trang'
            }
            info['location'] = city_mapping.get(location.lower(), location.title())
            break
    
    # Check-in date extraction - enhanced
    date_patterns = [
        r'(?:từ|from|checkin|check-in)\s*(?:ngày\s*)?(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{4}))?',
        r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',
        r'(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            if 'january' in match.group(0).lower() or 'february' in match.group(0).lower():
                # Handle English month names
                month_map = {
                    'january': '01', 'february': '02', 'march': '03', 'april': '04',
                    'may': '05', 'june': '06', 'july': '07', 'august': '08',
                    'september': '09', 'october': '10', 'november': '11', 'december': '12'
                }
                day = match.group(1).zfill(2)
                month_name = next(m for m in month_map.keys() if m in match.group(0).lower())
                month = month_map[month_name]
                info['check_in_date'] = f"2025-{month}-{day}"
            else:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3) if len(match.groups()) > 2 and match.group(3) else "2025"
                info['check_in_date'] = f"{year}-{month}-{day}"
            break
    
    # Số đêm - enhanced
    nights_patterns = [
        r'(\d+)\s*(?:đêm|night|nights)',
        r'(?:stay|ở)\s+(\d+)\s*(?:đêm|night|nights)',
        r'(\d+)\s*(?:ngày|days?)\s*(?:đêm|nights?)',
    ]
    
    for pattern in nights_patterns:
        match = re.search(pattern, text)
        if match:
            info['nights'] = match.group(1)
            break
    
    # Số khách - enhanced  
    guests_patterns = [
        r'(\d+)\s*(?:người|khách|guest|guests|pax)',
        r'(?:for|cho)\s+(\d+)\s*(?:người|khách|guest|guests|pax)',
        r'(\d+)\s*adults?',
    ]
    
    for pattern in guests_patterns:
        match = re.search(pattern, text)
        if match:
            info['guests'] = match.group(1)
            break
    
    # Smart default location từ conversation context
    if not info.get('location') and conversation_context:
        context_lower = conversation_context.lower()
        common_cities = [
            'đà nẵng', 'hà nội', 'hồ chí minh', 'hải phòng', 'nha trang', 
            'đà lạt', 'huế', 'hội an', 'vũng tầu', 'cần thơ'
        ]
        
        for city in common_cities:
            if city in context_lower and city not in text:
                info['location'] = f"{city.title()} (từ context)"
                break
    
    return {
        "extracted_info": info,
        "new_fields": list(info.keys()),
        "method": "ENHANCED_REGEX_FALLBACK"
    }


@tool
def validate_hotel_booking_complete(booking_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Kiểm tra thông tin đặt khách sạn đã đầy đủ chưa
    """
    required_fields = ['name', 'phone', 'hotel_name', 'location', 'check_in_date', 'nights']
    missing_fields = []
    
    for field in required_fields:
        if field not in booking_info or not booking_info[field]:
            missing_fields.append(field)
    
    field_names = {
        'name': 'Tên khách hàng',
        'phone': 'Số điện thoại', 
        'hotel_name': 'Tên khách sạn',
        'location': 'Địa điểm',
        'check_in_date': 'Ngày check-in',
        'nights': 'Số đêm'
    }
    
    is_complete = len(missing_fields) == 0
    
    return {
        "is_complete": is_complete,
        "missing_fields": [field_names[field] for field in missing_fields],
        "completion_rate": f"{((6 - len(missing_fields)) / 6) * 100:.0f}%",
        "method": "HOTEL_VALIDATION"
    }


@tool
def format_hotel_booking_preview(booking_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format hotel booking information for preview/confirmation
    """
    
    # Calculate check-out date
    check_out_date = "N/A"
    if booking_info.get('check_in_date') and booking_info.get('nights'):
        try:
            from datetime import datetime, timedelta
            check_in = datetime.strptime(booking_info['check_in_date'], '%Y-%m-%d')
            nights = int(booking_info['nights'])
            check_out = check_in + timedelta(days=nights)
            check_out_date = check_out.strftime('%Y-%m-%d')
        except:
            pass
    
    preview = f"""🏨 THÔNG TIN ĐẶT PHÒNG

👤 Khách hàng: {booking_info.get('name', 'N/A')}
📞 Điện thoại: {booking_info.get('phone', 'N/A')}
📧 Email: {booking_info.get('email', 'Không có')}

🏨 Khách sạn: {booking_info.get('hotel_name', 'N/A')}
📍 Địa điểm: {booking_info.get('location', 'N/A')}

📅 Check-in: {booking_info.get('check_in_date', 'N/A')}
📅 Check-out: {check_out_date}
🌙 Số đêm: {booking_info.get('nights', 'N/A')}
👥 Số khách: {booking_info.get('guests', '2')}
🛏️ Loại phòng: {booking_info.get('room_type', 'Standard')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Vui lòng xác nhận thông tin trên

💬 Trả lời "xác nhận" hoặc "đồng ý" để đặt phòng

🔄 Để thay đổi thông tin, nói: "Thay đổi [tên/sdt/khách sạn/địa điểm/ngày/số đêm]" """
    
    # Clean HTML tags if any
    import re
    preview = re.sub(r'<[^>]+>', '', preview)
    
    return {
        "preview_message": preview.strip(),
        "status": "awaiting_confirmation", 
        "method": "HOTEL_PREVIEW_FORMATTING"
    }


@tool
def detect_hotel_user_intent(user_input: str) -> Dict[str, Any]:
    """
    Detect user intent cho hotel booking - confirmation, update request, or new info
    """
    text = user_input.lower().strip()
    
    # Confirmation patterns
    confirmation_patterns = [
        'xác nhận', 'đồng ý', 'ok', 'được', 'đặt phòng', 'confirm', 'yes', 'đúng rồi', 'chính xác'
    ]
    
    # Update patterns
    update_patterns = [
        'thay đổi', 'sửa', 'update', 'đổi', 'chỉnh', 'không đúng', 'sai'
    ]
    
    # Field update patterns for hotel
    field_patterns = {
        'name': ['tên', 'name', 'khách hàng'],
        'phone': ['sdt', 'số điện thoại', 'phone', 'điện thoại'],
        'hotel_name': ['khách sạn', 'hotel', 'tên khách sạn'],
        'location': ['địa điểm', 'location', 'thành phố', 'nơi'],
        'check_in_date': ['ngày', 'check-in', 'check in', 'ngày đến'],
        'nights': ['đêm', 'nights', 'số đêm']
    }
    
    intent = "new_info"  # default
    update_field = None
    
    # Check for confirmation
    if any(pattern in text for pattern in confirmation_patterns):
        intent = "confirmation"
    
    # Check for update request
    elif any(pattern in text for pattern in update_patterns):
        intent = "update_request"
        
        # Try to detect which field to update
        for field, patterns in field_patterns.items():
            if any(pattern in text for pattern in patterns):
                update_field = field
                break
    
    return {
        "intent": intent,
        "update_field": update_field,
        "confidence": 0.8 if intent != "new_info" else 0.3,
        "method": "HOTEL_INTENT_DETECTION"
    }


@tool  
def confirm_hotel_booking_llm(booking_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Xác nhận đặt khách sạn cuối cùng với formatting đẹp
    """
    booking_id = f"HOTEL{hash(str(booking_info)) % 10000:04d}"
    
    # Calculate check-out date
    check_out_date = "N/A"
    if booking_info.get('check_in_date') and booking_info.get('nights'):
        try:
            from datetime import datetime, timedelta
            check_in = datetime.strptime(booking_info['check_in_date'], '%Y-%m-%d')
            nights = int(booking_info['nights'])
            check_out = check_in + timedelta(days=nights)
            check_out_date = check_out.strftime('%Y-%m-%d')
        except:
            pass
    
    confirmation = f"""
🎉 **ĐẶT PHÒNG THÀNH CÔNG** 🎉

┌─────────────────────────────────────────────┐
│                   📋 CHI TIẾT ĐẶT PHÒNG                   │  
└─────────────────────────────────────────────┘

🔖 **Mã đặt phòng:** {booking_id}
👤 **Khách hàng:** {booking_info.get('name', 'N/A')}
📞 **Điện thoại:** {booking_info.get('phone', 'N/A')}
📧 **Email:** {booking_info.get('email', 'Không có')}

🏨 **Khách sạn:** {booking_info.get('hotel_name', 'N/A')}
📍 **Địa điểm:** {booking_info.get('location', 'N/A')}

📅 **Check-in:** {booking_info.get('check_in_date', 'N/A')}
📅 **Check-out:** {check_out_date}
🌙 **Số đêm:** {booking_info.get('nights', 'N/A')}
👥 **Số khách:** {booking_info.get('guests', '2')}
🛏️ **Loại phòng:** {booking_info.get('room_type', 'Standard')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ **Phòng đã được giữ chỗ**
🕐 **Check-in:** 14:00
🕐 **Check-out:** 12:00
📧 **Email xác nhận:** booking@hotel.com

🙏 **Cảm ơn bạn đã đặt phòng!**
"""
    
    return {
        "booking_id": booking_id,
        "confirmation_message": confirmation.strip(),
        "status": "confirmed",
        "method": "HOTEL_FINAL_CONFIRMATION"
    }


class LLMHotelBooking:
    """
    LLM-powered Hotel Booking System với conversation state management
    """
    
    def __init__(self):
        self.current_booking = {}
        self.conversation_state = "gathering_info"  # gathering_info, awaiting_confirmation, confirmed
        self.conversation_context = ""  # Store conversation context
        self.tools = [
            extract_hotel_booking_info_with_llm, 
            validate_hotel_booking_complete, 
            format_hotel_booking_preview, 
            detect_hotel_user_intent, 
            confirm_hotel_booking_llm
        ]
    
    def process(self, user_input: str, conversation_context: str = "") -> Dict[str, Any]:
        """
        Xử lý input với conversation state management cho hotel booking
        """
        
        # Update conversation context
        if conversation_context:
            self.conversation_context = conversation_context
        else:
            self.conversation_context += " " + user_input
        
        # Handle different conversation states
        if self.conversation_state == "awaiting_confirmation":
            return self._handle_confirmation_state(user_input)
        else:
            return self._handle_gathering_state(user_input)
    
    def _handle_gathering_state(self, user_input: str) -> Dict[str, Any]:
        """Handle hotel info gathering state"""
        
        # Bước 1: Extract thông tin bằng LLM
        extraction_result = extract_hotel_booking_info_with_llm.invoke({
            "user_input": user_input,
            "current_booking": self.current_booking.copy(),
            "conversation_context": self.conversation_context
        })
        
        # Cập nhật booking info
        extracted_info = extraction_result.get("extracted_info", {})
        method = extraction_result.get("method", "UNKNOWN")
        new_fields = extraction_result.get("new_fields", [])
        
        self.current_booking.update(extracted_info)
        
        # Bước 2: Validate completeness
        validation_result = validate_hotel_booking_complete.invoke({
            "booking_info": self.current_booking
        })
        
        if validation_result["is_complete"]:
            # Bước 3: Show preview và chờ confirmation
            preview_result = format_hotel_booking_preview.invoke({
                "booking_info": self.current_booking
            })
            
            self.conversation_state = "awaiting_confirmation"
            
            return {
                "success": True,
                "response": preview_result["preview_message"],
                "tool_used": "LLM_HOTEL_BOOKING",
                "status": "awaiting_confirmation",
                "current_info": self.current_booking.copy(),
                "extraction_method": method,
                "new_fields_detected": new_fields
            }
        else:
            # Yêu cầu thông tin còn thiếu
            missing_fields = validation_result["missing_fields"]
            completion_rate = validation_result["completion_rate"]
            
            if len(missing_fields) == 1:
                response = f"Cảm ơn bạn! Tôi cần thêm thông tin:\n\n{missing_fields[0]}"
            else:
                response = f"Cảm ơn bạn! Tôi cần thêm thông tin:\n\n"
                for i, field in enumerate(missing_fields, 1):
                    response += f"{i}. {field}\n"
            
            if new_fields:
                response += f"\n✅ Đã nhận: {', '.join(new_fields)}"
            
            # Clean any HTML tags that might have leaked
            import re
            response = re.sub(r'<[^>]+>', '', response)
            
            return {
                "success": True,
                "response": response,
                "tool_used": "LLM_HOTEL_BOOKING",
                "status": "gathering_info",
                "missing_fields": missing_fields,
                "completion_rate": completion_rate,
                "current_info": self.current_booking.copy(),
                "extraction_method": method,
                "new_fields_detected": new_fields
            }
    
    def _handle_confirmation_state(self, user_input: str) -> Dict[str, Any]:
        """Handle hotel booking confirmation state"""
        
        # Detect user intent
        intent_result = detect_hotel_user_intent.invoke({"user_input": user_input})
        intent = intent_result.get("intent", "new_info")
        
        if intent == "confirmation":
            # User confirmed - proceed with booking
            confirmation = confirm_hotel_booking_llm.invoke({
                "booking_info": self.current_booking
            })
            
            # Reset for new booking
            self.current_booking = {}
            self.conversation_state = "gathering_info"
            
            return {
                "success": True,
                "response": confirmation["confirmation_message"],
                "tool_used": "LLM_HOTEL_BOOKING",
                "status": "confirmed",
                "booking_id": confirmation["booking_id"]
            }
            
        elif intent == "update_request":
            # User wants to update something
            update_field = intent_result.get("update_field")
            
            if update_field:
                field_names = {
                    'name': 'tên khách hàng',
                    'phone': 'số điện thoại', 
                    'hotel_name': 'tên khách sạn',
                    'location': 'địa điểm',
                    'check_in_date': 'ngày check-in',
                    'nights': 'số đêm'
                }
                
                # Clear the field to be updated
                if update_field in self.current_booking:
                    del self.current_booking[update_field]
                
                self.conversation_state = "gathering_info"
                
                return {
                    "success": True,
                    "response": f"Được rồi! Vui lòng cung cấp {field_names.get(update_field, update_field)} mới:",
                    "tool_used": "LLM_HOTEL_BOOKING",
                    "status": "updating_info",
                    "updating_field": update_field,
                    "current_info": self.current_booking.copy()
                }
            else:
                return {
                    "success": True,
                    "response": "Bạn muốn thay đổi thông tin gì? (tên, số điện thoại, khách sạn, địa điểm, ngày check-in, số đêm)",
                    "tool_used": "LLM_HOTEL_BOOKING",
                    "status": "awaiting_confirmation",
                    "current_info": self.current_booking.copy()
                }
        else:
            # Treat as new info or try to extract update
            extraction_result = extract_hotel_booking_info_with_llm.invoke({
                "user_input": user_input,
                "current_booking": self.current_booking.copy(),
                "conversation_context": self.conversation_context
            })
            
            extracted_info = extraction_result.get("extracted_info", {})
            new_fields = extraction_result.get("new_fields", [])
            
            if new_fields:
                # Update the booking info
                self.current_booking.update(extracted_info)
                
                # Show updated preview
                preview_result = format_hotel_booking_preview.invoke({
                    "booking_info": self.current_booking
                })
                
                return {
                    "success": True,
                    "response": f"✅ Đã cập nhật: {', '.join(new_fields)}\n\n{preview_result['preview_message']}",
                    "tool_used": "LLM_HOTEL_BOOKING",
                    "status": "awaiting_confirmation",
                    "current_info": self.current_booking.copy(),
                    "updated_fields": new_fields
                }
            else:
                # No new info detected, ask for clarification
                return {
                    "success": True,
                    "response": "Tôi không hiểu yêu cầu của bạn. Vui lòng:\n- Trả lời **'xác nhận'** để đặt phòng\n- Hoặc nói **'thay đổi [thông tin]'** để sửa thông tin",
                    "tool_used": "LLM_HOTEL_BOOKING", 
                    "status": "awaiting_confirmation",
                    "current_info": self.current_booking.copy()
                }