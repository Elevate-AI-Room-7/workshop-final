"""
LLM-based Simple Travel Planning for Demo
Tạo hệ thống lên kế hoạch du lịch đơn giản tương tự car/hotel booking
"""

import os
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage


@tool
def extract_travel_plan_info_with_llm(user_input: str, current_plan: Dict[str, Any] = None, conversation_context: str = "") -> Dict[str, Any]:
    """
    Sử dụng LLM để trích xuất thông tin kế hoạch du lịch từ user input
    
    Args:
        user_input: Input của user
        current_plan: Thông tin plan hiện tại (nếu có)
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
            return _extract_travel_plan_with_regex(user_input, conversation_context)
    except:
        # Fallback về regex nếu có lỗi
        return _extract_travel_plan_with_regex(user_input, conversation_context)
    
    # Template để extract thông tin travel plan
    extraction_prompt = ChatPromptTemplate.from_messages([
        ("system", """Bạn là AI chuyên trích xuất thông tin kế hoạch du lịch từ tiếng Việt và tiếng Anh.

NHIỆM VỤ: Trích xuất chính xác các thông tin sau cho kế hoạch du lịch đơn giản:
- destination: Điểm tham quan chính (tên thành phố/địa danh)
- itinerary: Lịch trình tham quan (danh sách các địa điểm theo thứ tự)
- car_booking_info: Thông tin đặt xe (pickup, destination, time)
- hotel_booking_info: Thông tin đặt phòng (hotel_name, location, nights)
- group_size: Số lượng người tham gia (số nguyên)
- duration: Thời lượng chuyến đi (số ngày)
- start_date: Ngày bắt đầu (format: YYYY-MM-DD)

HƯỚNG DẪN TRÍCH XUẤT:
1. Destination: Tìm tên thành phố/địa danh chính
   - VD: "Du lịch Đà Nẵng" → "Đà Nẵng"
2. Itinerary: Tìm danh sách địa điểm tham quan
   - VD: "tham quan Bà Nà Hills, Hội An, biển Mỹ Khê" → ["Bà Nà Hills", "Hội An", "biển Mỹ Khê"]
3. Car booking: Thông tin về di chuyển
   - VD: "xe từ sân bay đến khách sạn" → {"pickup": "sân bay", "destination": "khách sạn"}
4. Hotel booking: Thông tin về lưu trú
   - VD: "ở khách sạn Marriott 3 đêm" → {"hotel_name": "Marriott", "nights": "3"}
5. Group size: Số người
   - VD: "4 người", "gia đình 2 người lớn 1 trẻ em" → tổng số người
6. Duration: Thời lượng
   - VD: "3 ngày 2 đêm" → 3
7. Start date: Ngày khởi hành
   - VD: "từ 25/12" → "2025-12-25"

VÍ DỤ THỰC TẾ:
Input: "Lên kế hoạch du lịch Đà Nẵng 3 ngày, tham quan Bà Nà Hills và Hội An, 4 người"
Output: {"destination": "Đà Nẵng", "itinerary": ["Bà Nà Hills", "Hội An"], "car_booking_info": {}, "hotel_booking_info": {}, "group_size": "4", "duration": "3", "start_date": ""}

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
        
        # Merge với current plan nếu có
        if current_plan:
            for key, value in extracted_info.items():
                if value and (value != "" and value != {} and value != []):  # Chỉ update nếu có giá trị mới
                    current_plan[key] = value
            return {
                "extracted_info": current_plan,
                "new_fields": [k for k, v in extracted_info.items() if v and (v != "" and v != {} and v != [])],
                "method": "LLM"
            }
        else:
            # Loại bỏ các field rỗng
            cleaned_info = {}
            for k, v in extracted_info.items():
                if v and (v != "" and v != {} and v != []):
                    cleaned_info[k] = v
            return {
                "extracted_info": cleaned_info,
                "new_fields": list(cleaned_info.keys()),
                "method": "LLM"
            }
            
    except Exception as e:
        print(f"LLM travel plan extraction failed: {e}, falling back to regex")
        return _extract_travel_plan_with_regex(user_input, conversation_context)


def _extract_travel_plan_with_regex(user_input: str, conversation_context: str = "") -> Dict[str, Any]:
    """Enhanced fallback regex extraction cho travel plan"""
    import re
    
    info = {}
    text = user_input.lower()
    original_text = user_input
    
    # Destination extraction - main city/location
    destination_patterns = [
        r'du lịch\s+([a-zà-ỹA-ZÀ-Ỹ\s]+?)(?:\s*[,.]|$)',
        r'đi\s+([a-zà-ỹA-ZÀ-Ỹ\s]+?)(?:\s*[,.]|$)',
        r'travel\s+to\s+([a-zA-Z\s]+?)(?:\s*[,.]|$)',
        r'\b(đà nẵng|hà nội|hồ chí minh|hcmc|sài gòn|nha trang|huế|hội an|đà lạt|vũng tầu|hải phòng|phú quốc)\b',
    ]
    
    for pattern in destination_patterns:
        match = re.search(pattern, text)
        if match:
            destination = match.group(1).strip()
            # Normalize common city names
            city_mapping = {
                'hcmc': 'Hồ Chí Minh',
                'sài gòn': 'Hồ Chí Minh',
                'đà nẵng': 'Đà Nẵng',
                'hà nội': 'Hà Nội',
                'nha trang': 'Nha Trang'
            }
            info['destination'] = city_mapping.get(destination.lower(), destination.title())
            break
    
    # Itinerary extraction - enhanced list of places to visit
    itinerary_patterns = [
        r'tham quan\s+([^.]+?)(?:\s*[,.]|$)',
        r'visit\s+([^.]+?)(?:\s*[,.]|$)',
        r'đi\s+([^.]+?)(?:\s*[,.]|$)',
    ]
    
    for pattern in itinerary_patterns:
        match = re.search(pattern, text)
        if match:
            places_text = match.group(1).strip()
            # Enhanced splitting by multiple separators
            places = []
            # Split by common separators and clean up
            raw_places = re.split(r'[,và&\s]+(?:và\s+)?', places_text)
            for place in raw_places:
                place = place.strip()
                # Filter out non-place words
                if place and len(place) > 2 and not re.match(r'^\d+\s*(?:người|ngày)', place):
                    # Clean up common non-place words
                    if not any(word in place.lower() for word in ['người', 'ngày', 'đêm', 'cho', 'gia đình']):
                        places.append(place.title())
            
            if places:
                info['itinerary'] = places[:5]  # Limit to 5 places
            break
    
    # Group size extraction
    group_patterns = [
        r'(\d+)\s*(?:người|khách|guests?|pax)',
        r'(?:gia đình|family)\s*(\d+)',
        r'nhóm\s*(\d+)',
    ]
    
    for pattern in group_patterns:
        match = re.search(pattern, text)
        if match:
            info['group_size'] = match.group(1)
            break
    
    # Duration extraction
    duration_patterns = [
        r'(\d+)\s*(?:ngày|days?)',
        r'(\d+)\s*(?:ngày|days?)\s*(\d+)\s*(?:đêm|nights?)',  # "3 ngày 2 đêm"
    ]
    
    for pattern in duration_patterns:
        match = re.search(pattern, text)
        if match:
            info['duration'] = match.group(1)
            break
    
    # Start date extraction
    date_patterns = [
        r'(?:từ|from|bắt đầu)\s*(?:ngày\s*)?(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{4}))?',
        r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3) if len(match.groups()) > 2 and match.group(3) else "2025"
            info['start_date'] = f"{year}-{month}-{day}"
            break
    
    # Car booking info extraction (simple)
    car_info = {}
    car_patterns = [
        r'xe\s+từ\s+([^,\n]+?)\s+(?:đến|tới)\s+([^,\n]+)',
        r'(?:pickup|đón)\s+(?:from|từ)?\s*([^,\n]+?)(?:\s+(?:to|đến)\s+([^,\n]+))?',
    ]
    
    for pattern in car_patterns:
        match = re.search(pattern, text)
        if match:
            car_info['pickup'] = match.group(1).strip()
            if len(match.groups()) > 1 and match.group(2):
                car_info['destination'] = match.group(2).strip()
            break
    
    if car_info:
        info['car_booking_info'] = car_info
    
    # Hotel booking info extraction (simple)
    hotel_info = {}
    hotel_patterns = [
        r'(?:ở|stay)\s+(?:khách sạn|hotel)\s+([^,\n]+)',
        r'(?:khách sạn|hotel)\s+([a-zA-Z\s]+)',
    ]
    
    for pattern in hotel_patterns:
        match = re.search(pattern, text)
        if match:
            hotel_info['hotel_name'] = match.group(1).strip()
            break
    
    # Hotel nights
    nights_match = re.search(r'(\d+)\s*(?:đêm|nights?)', text)
    if nights_match:
        hotel_info['nights'] = nights_match.group(1)
    
    if hotel_info:
        info['hotel_booking_info'] = hotel_info
    
    # Smart default từ conversation context
    if not info.get('destination') and conversation_context:
        context_lower = conversation_context.lower()
        common_cities = [
            'đà nẵng', 'hà nội', 'hồ chí minh', 'nha trang', 'đà lạt', 'hội an'
        ]
        
        for city in common_cities:
            if city in context_lower:
                info['destination'] = city.title()
                break
    
    return {
        "extracted_info": info,
        "new_fields": list(info.keys()),
        "method": "ENHANCED_REGEX_FALLBACK"
    }


@tool
def validate_travel_plan_complete(plan_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Kiểm tra thông tin kế hoạch du lịch đã đầy đủ chưa
    """
    required_fields = ['destination', 'itinerary', 'group_size', 'duration']
    missing_fields = []
    
    for field in required_fields:
        if field not in plan_info or not plan_info[field]:
            missing_fields.append(field)
    
    field_names = {
        'destination': 'Điểm tham quan chính',
        'itinerary': 'Lịch trình các địa điểm',
        'group_size': 'Số lượng người',
        'duration': 'Thời lượng (số ngày)',
        'start_date': 'Ngày khởi hành',
        'car_booking_info': 'Thông tin đặt xe',
        'hotel_booking_info': 'Thông tin đặt phòng'
    }
    
    is_complete = len(missing_fields) == 0
    
    return {
        "is_complete": is_complete,
        "missing_fields": [field_names[field] for field in missing_fields],
        "completion_rate": f"{((4 - len(missing_fields)) / 4) * 100:.0f}%",
        "method": "TRAVEL_PLAN_VALIDATION"
    }


@tool
def format_travel_plan_preview(plan_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format travel plan information for preview/confirmation
    """
    
    # Format itinerary
    itinerary_text = "Chưa có"
    if plan_info.get('itinerary') and isinstance(plan_info['itinerary'], list):
        itinerary_list = []
        for i, place in enumerate(plan_info['itinerary'], 1):
            itinerary_list.append(f"   {i}. {place}")
        itinerary_text = "\n".join(itinerary_list)
    elif plan_info.get('itinerary'):
        itinerary_text = str(plan_info['itinerary'])
    
    # Format car booking
    car_info_text = "Chưa có"
    if plan_info.get('car_booking_info') and isinstance(plan_info['car_booking_info'], dict):
        car_info = plan_info['car_booking_info']
        if car_info.get('pickup') or car_info.get('destination'):
            car_info_text = f"Từ {car_info.get('pickup', 'N/A')} đến {car_info.get('destination', 'N/A')}"
    
    # Format hotel booking
    hotel_info_text = "Chưa có"
    if plan_info.get('hotel_booking_info') and isinstance(plan_info['hotel_booking_info'], dict):
        hotel_info = plan_info['hotel_booking_info']
        if hotel_info.get('hotel_name') or hotel_info.get('nights'):
            hotel_info_text = f"{hotel_info.get('hotel_name', 'Khách sạn')} - {hotel_info.get('nights', 'N/A')} đêm"
    
    preview = f"""🧳 THÔNG TIN KẾ HOẠCH DU LỊCH

🎯 Điểm tham quan: {plan_info.get('destination', 'N/A')}
📅 Thời lượng: {plan_info.get('duration', 'N/A')} ngày
👥 Số người: {plan_info.get('group_size', 'N/A')} người
🗓️ Ngày khởi hành: {plan_info.get('start_date', 'Chưa xác định')}

📍 LỊCH TRÌNH THAM QUAN:
{itinerary_text}

🚗 THÔNG TIN ĐẶT XE:
{car_info_text}

🏨 THÔNG TIN ĐẶT PHÒNG:
{hotel_info_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Vui lòng xác nhận thông tin kế hoạch trên

💬 Trả lời "xác nhận" hoặc "đồng ý" để lưu kế hoạch

🔄 Để thay đổi thông tin, nói: "Thay đổi [destination/itinerary/group_size/duration]" """
    
    # Clean HTML tags if any
    import re
    preview = re.sub(r'<[^>]+>', '', preview)
    
    return {
        "preview_message": preview.strip(),
        "status": "awaiting_confirmation", 
        "method": "TRAVEL_PLAN_PREVIEW_FORMATTING"
    }


@tool
def detect_travel_plan_user_intent(user_input: str) -> Dict[str, Any]:
    """
    Detect user intent cho travel planning - confirmation, update request, or new info
    """
    text = user_input.lower().strip()
    
    # Confirmation patterns
    confirmation_patterns = [
        'xác nhận', 'đồng ý', 'ok', 'được', 'lưu kế hoạch', 'confirm', 'yes', 'đúng rồi', 'chính xác'
    ]
    
    # Update patterns
    update_patterns = [
        'thay đổi', 'sửa', 'update', 'đổi', 'chỉnh', 'không đúng', 'sai'
    ]
    
    # Field update patterns for travel plan
    field_patterns = {
        'destination': ['điểm tham quan', 'destination', 'nơi đi', 'địa điểm chính'],
        'itinerary': ['lịch trình', 'itinerary', 'địa điểm', 'tham quan'],
        'group_size': ['số người', 'group size', 'nhóm', 'số lượng'],
        'duration': ['thời lượng', 'duration', 'số ngày', 'ngày'],
        'start_date': ['ngày khởi hành', 'start date', 'ngày đi', 'ngày bắt đầu']
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
        "method": "TRAVEL_PLAN_INTENT_DETECTION"
    }


@tool  
def confirm_travel_plan_llm(plan_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Xác nhận kế hoạch du lịch cuối cùng với formatting đẹp
    """
    plan_id = f"TRIP{hash(str(plan_info)) % 10000:04d}"
    
    # Format itinerary for confirmation
    itinerary_text = "Các địa điểm sẽ được xác định chi tiết"
    if plan_info.get('itinerary') and isinstance(plan_info['itinerary'], list):
        itinerary_list = []
        for i, place in enumerate(plan_info['itinerary'], 1):
            itinerary_list.append(f"     {i}. {place}")
        itinerary_text = "\n".join(itinerary_list)
    
    confirmation = f"""
🎉 **TẠO KẾ HOẠCH DU LỊCH THÀNH CÔNG** 🎉

┌─────────────────────────────────────────────┐
│                  📋 CHI TIẾT KẾ HOẠCH                   │  
└─────────────────────────────────────────────┘

🔖 **Mã kế hoạch:** {plan_id}
🎯 **Điểm tham quan:** {plan_info.get('destination', 'N/A')}
📅 **Thời lượng:** {plan_info.get('duration', 'N/A')} ngày
👥 **Số người:** {plan_info.get('group_size', 'N/A')} người
🗓️ **Ngày khởi hành:** {plan_info.get('start_date', 'Sẽ xác định sau')}

📍 **Lịch trình tham quan:**
{itinerary_text}

🚗 **Thông tin đặt xe:**
     {plan_info.get('car_booking_info', {}).get('pickup', 'Sẽ sắp xếp') if plan_info.get('car_booking_info') else 'Sẽ sắp xếp theo lịch trình'}

🏨 **Thông tin đặt phòng:**
     {plan_info.get('hotel_booking_info', {}).get('hotel_name', 'Sẽ đề xuất phù hợp') if plan_info.get('hotel_booking_info') else 'Sẽ đề xuất phù hợp với ngân sách'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ **Kế hoạch đã được lưu thành công**
📧 **Xem chi tiết:** Vào trang Quản lý kế hoạch
📞 **Hỗ trợ:** support@travelapp.com

🙏 **Chúc bạn có chuyến đi thú vị!**
"""
    
    return {
        "plan_id": plan_id,
        "confirmation_message": confirmation.strip(),
        "status": "confirmed",
        "method": "TRAVEL_PLAN_FINAL_CONFIRMATION"
    }


class LLMTravelPlanning:
    """
    LLM-powered Simple Travel Planning System cho demo
    """
    
    def __init__(self):
        self.current_plan = {}
        self.conversation_state = "gathering_info"  # gathering_info, awaiting_confirmation, confirmed
        self.conversation_context = ""  # Store conversation context
        self.tools = [
            extract_travel_plan_info_with_llm, 
            validate_travel_plan_complete, 
            format_travel_plan_preview, 
            detect_travel_plan_user_intent, 
            confirm_travel_plan_llm
        ]
    
    def process(self, user_input: str, conversation_context: str = "") -> Dict[str, Any]:
        """
        Xử lý input với conversation state management cho travel planning
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
        """Handle travel plan info gathering state"""
        
        # Bước 1: Extract thông tin bằng LLM
        extraction_result = extract_travel_plan_info_with_llm.invoke({
            "user_input": user_input,
            "current_plan": self.current_plan.copy(),
            "conversation_context": self.conversation_context
        })
        
        # Cập nhật plan info
        extracted_info = extraction_result.get("extracted_info", {})
        method = extraction_result.get("method", "UNKNOWN")
        new_fields = extraction_result.get("new_fields", [])
        
        self.current_plan.update(extracted_info)
        
        # Bước 2: Validate completeness
        validation_result = validate_travel_plan_complete.invoke({
            "plan_info": self.current_plan
        })
        
        if validation_result["is_complete"]:
            # Bước 3: Show preview và chờ confirmation
            preview_result = format_travel_plan_preview.invoke({
                "plan_info": self.current_plan
            })
            
            self.conversation_state = "awaiting_confirmation"
            
            return {
                "success": True,
                "response": preview_result["preview_message"],
                "tool_used": "LLM_TRAVEL_PLANNING",
                "status": "awaiting_confirmation",
                "current_info": self.current_plan.copy(),
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
                "tool_used": "LLM_TRAVEL_PLANNING",
                "status": "gathering_info",
                "missing_fields": missing_fields,
                "completion_rate": completion_rate,
                "current_info": self.current_plan.copy(),
                "extraction_method": method,
                "new_fields_detected": new_fields
            }
    
    def _handle_confirmation_state(self, user_input: str) -> Dict[str, Any]:
        """Handle travel plan confirmation state"""
        
        # Detect user intent
        intent_result = detect_travel_plan_user_intent.invoke({"user_input": user_input})
        intent = intent_result.get("intent", "new_info")
        
        if intent == "confirmation":
            # User confirmed - proceed with saving plan
            confirmation = confirm_travel_plan_llm.invoke({
                "plan_info": self.current_plan
            })
            
            # Reset for new plan
            self.current_plan = {}
            self.conversation_state = "gathering_info"
            
            return {
                "success": True,
                "response": confirmation["confirmation_message"],
                "tool_used": "LLM_TRAVEL_PLANNING",
                "status": "confirmed",
                "plan_id": confirmation["plan_id"]
            }
            
        elif intent == "update_request":
            # User wants to update something
            update_field = intent_result.get("update_field")
            
            if update_field:
                field_names = {
                    'destination': 'điểm tham quan chính',
                    'itinerary': 'lịch trình các địa điểm',
                    'group_size': 'số lượng người',
                    'duration': 'thời lượng (số ngày)',
                    'start_date': 'ngày khởi hành'
                }
                
                # Clear the field to be updated
                if update_field in self.current_plan:
                    del self.current_plan[update_field]
                
                self.conversation_state = "gathering_info"
                
                return {
                    "success": True,
                    "response": f"Được rồi! Vui lòng cung cấp {field_names.get(update_field, update_field)} mới:",
                    "tool_used": "LLM_TRAVEL_PLANNING",
                    "status": "updating_info",
                    "updating_field": update_field,
                    "current_info": self.current_plan.copy()
                }
            else:
                return {
                    "success": True,
                    "response": "Bạn muốn thay đổi thông tin gì? (điểm tham quan, lịch trình, số người, thời lượng, ngày khởi hành)",
                    "tool_used": "LLM_TRAVEL_PLANNING",
                    "status": "awaiting_confirmation",
                    "current_info": self.current_plan.copy()
                }
        else:
            # Treat as new info or try to extract update
            extraction_result = extract_travel_plan_info_with_llm.invoke({
                "user_input": user_input,
                "current_plan": self.current_plan.copy(),
                "conversation_context": self.conversation_context
            })
            
            extracted_info = extraction_result.get("extracted_info", {})
            new_fields = extraction_result.get("new_fields", [])
            
            if new_fields:
                # Update the plan info
                self.current_plan.update(extracted_info)
                
                # Show updated preview
                preview_result = format_travel_plan_preview.invoke({
                    "plan_info": self.current_plan
                })
                
                return {
                    "success": True,
                    "response": f"✅ Đã cập nhật: {', '.join(new_fields)}\n\n{preview_result['preview_message']}",
                    "tool_used": "LLM_TRAVEL_PLANNING",
                    "status": "awaiting_confirmation",
                    "current_info": self.current_plan.copy(),
                    "updated_fields": new_fields
                }
            else:
                # No new info detected, ask for clarification
                return {
                    "success": True,
                    "response": "Tôi không hiểu yêu cầu của bạn. Vui lòng:\n- Trả lời **'xác nhận'** để lưu kế hoạch\n- Hoặc nói **'thay đổi [thông tin]'** để sửa thông tin",
                    "tool_used": "LLM_TRAVEL_PLANNING", 
                    "status": "awaiting_confirmation",
                    "current_info": self.current_plan.copy()
                }