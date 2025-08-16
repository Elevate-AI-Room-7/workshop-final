"""
LLM-based Car Booking Function Calling
Sử dụng LLM để tự động detect thông tin thay vì regex manual
"""

import os
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage


@tool
def extract_booking_info_with_llm(user_input: str, current_booking: Dict[str, Any] = None, conversation_context: str = "") -> Dict[str, Any]:
    """
    Sử dụng LLM để trích xuất thông tin đặt xe từ user input
    
    Args:
        user_input: Input của user
        current_booking: Thông tin booking hiện tại (nếu có)
        
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
            return _extract_with_regex(user_input, conversation_context)
    except:
        # Fallback về regex nếu có lỗi
        return _extract_with_regex(user_input, conversation_context)
    
    # Template để extract thông tin
    extraction_prompt = ChatPromptTemplate.from_messages([
        ("system", """Bạn là một AI chuyên trích xuất thông tin đặt xe từ text tiếng Việt.

Từ input của user, hãy trích xuất các thông tin sau (nếu có):
- name: Tên khách hàng  
- phone: Số điện thoại (format: 0xxxxxxxxx)
- pickup: Điểm đón
- destination: Điểm đến  
- time: Thời gian (nếu có)

Trả về kết quả dưới dạng JSON với các key trên. Nếu không tìm thấy thông tin nào thì để giá trị rỗng "".

Ví dụ:
Input: "Tên Nguyễn Văn A, SĐT 0912345678, từ sân bay đến khách sạn"
Output: {{"name": "Nguyễn Văn A", "phone": "0912345678", "pickup": "sân bay", "destination": "khách sạn", "time": ""}}

Chỉ trả về JSON, không có text khác."""),
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
        print(f"LLM extraction failed: {e}, falling back to regex")
        return _extract_with_regex(user_input, conversation_context)


def _extract_with_regex(user_input: str, conversation_context: str = "") -> Dict[str, Any]:
    """Fallback regex extraction (simplified)"""
    import re
    
    info = {}
    text = user_input.lower()
    
    # Tên - pattern đơn giản
    name_patterns = [
        r'tên ([A-ZÀ-Ỹ][a-zà-ỹ]+(?: [A-ZÀ-Ỹ][a-zà-ỹ]+)*)',  # "Tên Hiển Võ"
        r'^([A-ZÀ-Ỹ][a-zà-ỹ]+(?: [A-ZÀ-Ỹ][a-zà-ỹ]+)*),',  # "Hiển Võ,"
        r'(?:tôi là |mình là )([A-ZÀ-Ỹ][a-zà-ỹ]+(?: [A-ZÀ-Ỹ][a-zà-ỹ]+)*)',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, user_input)
        if match:
            info['name'] = match.group(1)
            break
    
    # Số điện thoại
    phone_match = re.search(r'(0\d{8,9})', user_input)
    if phone_match:
        info['phone'] = phone_match.group(1)
    
    # Điểm đón
    pickup_match = re.search(r'(?:điểm đón[:\s]*|đón[:\s]*|từ )([^,]+?)(?:,|$)', text)
    if pickup_match:
        info['pickup'] = pickup_match.group(1).strip()
    
    # Điểm đến  
    dest_match = re.search(r'(?:điểm đến[:\s]*|đến[:\s]*|tới )([^,]+?)(?:,|$)', text)
    if dest_match:
        info['destination'] = dest_match.group(1).strip()
    
    # Smart default destination từ conversation context
    if not info.get('destination') and conversation_context:
        # Tìm địa danh trong context
        context_lower = conversation_context.lower()
        common_destinations = [
            'đà nẵng', 'hà nội', 'hồ chí minh', 'hải phòng', 'nha trang', 
            'đà lạt', 'huế', 'hội an', 'vũng tầu', 'cần thơ'
        ]
        
        for dest in common_destinations:
            if dest in context_lower and dest not in text:
                info['destination'] = f"{dest.title()} (địa danh được đề cập)"
                break
    
    return {
        "extracted_info": info,
        "new_fields": list(info.keys()),
        "method": "REGEX_FALLBACK"
    }


@tool
def validate_booking_complete(booking_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Kiểm tra thông tin đặt xe đã đầy đủ chưa
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
        "completion_rate": f"{((4 - len(missing_fields)) / 4) * 100:.0f}%",
        "method": "VALIDATION"
    }


@tool
def format_booking_preview(booking_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format booking information for preview/confirmation
    """
    
    preview = f"""🚗 THÔNG TIN ĐẶT XE

👤 Khách hàng: {booking_info.get('name', 'N/A')}
📞 Điện thoại: {booking_info.get('phone', 'N/A')}

📍 Điểm đón: {booking_info.get('pickup', 'N/A')}
🎯 Điểm đến: {booking_info.get('destination', 'N/A')} 
⏰ Thời gian: {booking_info.get('time', 'Sớm nhất có thể')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Vui lòng xác nhận thông tin trên

💬 Trả lời "xác nhận" hoặc "đồng ý" để đặt xe

🔄 Để thay đổi thông tin, nói: "Thay đổi [tên/sdt/điểm đón/điểm đến]" """
    
    # Clean HTML tags if any
    import re
    preview = re.sub(r'<[^>]+>', '', preview)
    
    return {
        "preview_message": preview.strip(),
        "status": "awaiting_confirmation", 
        "method": "PREVIEW_FORMATTING"
    }


@tool
def detect_user_intent(user_input: str) -> Dict[str, Any]:
    """
    Detect user intent - confirmation, update request, or new info
    """
    text = user_input.lower().strip()
    
    # Confirmation patterns
    confirmation_patterns = [
        'xác nhận', 'đồng ý', 'ok', 'được', 'đặt xe', 'confirm', 'yes', 'đúng rồi', 'chính xác'
    ]
    
    # Update patterns
    update_patterns = [
        'thay đổi', 'sửa', 'update', 'đổi', 'chỉnh', 'không đúng', 'sai'
    ]
    
    # Field update patterns
    field_patterns = {
        'name': ['tên', 'name', 'khách hàng'],
        'phone': ['sdt', 'số điện thoại', 'phone', 'điện thoại'],
        'pickup': ['điểm đón', 'đón', 'pickup', 'từ'],
        'destination': ['điểm đến', 'đến', 'destination', 'tới']
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
        "method": "INTENT_DETECTION"
    }


@tool  
def confirm_booking_llm(booking_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Xác nhận đặt xe cuối cùng với formatting đẹp
    """
    booking_id = f"CAR{hash(str(booking_info)) % 10000:04d}"
    
    confirmation = f"""
🎉 **ĐẶT XE THÀNH CÔNG** 🎉

┌─────────────────────────────────────────────┐
│                    📋 CHI TIẾT ĐẶT XE                    │  
└─────────────────────────────────────────────┘

🔖 **Mã đặt xe:** {booking_id}
👤 **Khách hàng:** {booking_info.get('name', 'N/A')}
📞 **Điện thoại:** {booking_info.get('phone', 'N/A')}

🚩 **Lộ trình:**
   📍 Đón: {booking_info.get('pickup', 'N/A')}
   🎯 Đến: {booking_info.get('destination', 'N/A')}
   ⏰ Thời gian: {booking_info.get('time', 'Sớm nhất có thể')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ **Xe sẽ đến trong 15-20 phút**
📱 **Liên hệ tài xế:** 0901234567
📧 **Hỗ trợ:** support@taxiapp.com

🙏 **Cảm ơn bạn đã sử dụng dịch vụ!**
"""
    
    return {
        "booking_id": booking_id,
        "confirmation_message": confirmation.strip(),
        "status": "confirmed",
        "method": "FINAL_CONFIRMATION"
    }


class LLMCarBooking:
    """
    LLM-powered Car Booking System with confirmation flow
    """
    
    def __init__(self):
        self.current_booking = {}
        self.conversation_state = "gathering_info"  # gathering_info, awaiting_confirmation, confirmed
        self.conversation_context = ""  # Store conversation context
        self.tools = [extract_booking_info_with_llm, validate_booking_complete, format_booking_preview, detect_user_intent, confirm_booking_llm]
    
    def process(self, user_input: str, conversation_context: str = "") -> Dict[str, Any]:
        """
        Xử lý input với conversation state management
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
        """Handle info gathering state"""
        
        # Bước 1: Extract thông tin bằng LLM
        extraction_result = extract_booking_info_with_llm.invoke({
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
        validation_result = validate_booking_complete.invoke({
            "booking_info": self.current_booking
        })
        
        if validation_result["is_complete"]:
            # Bước 3: Show preview và chờ confirmation
            preview_result = format_booking_preview.invoke({
                "booking_info": self.current_booking
            })
            
            self.conversation_state = "awaiting_confirmation"
            
            return {
                "success": True,
                "response": preview_result["preview_message"],
                "tool_used": "LLM_CAR_BOOKING",
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
            
            # Gợi ý đã được bỏ theo yêu cầu người dùng
            
            # Clean any HTML tags that might have leaked
            import re
            response = re.sub(r'<[^>]+>', '', response)
            
            return {
                "success": True,
                "response": response,
                "tool_used": "LLM_CAR_BOOKING",
                "status": "gathering_info",
                "missing_fields": missing_fields,
                "completion_rate": completion_rate,
                "current_info": self.current_booking.copy(),
                "extraction_method": method,
                "new_fields_detected": new_fields,
                "suggestions": smart_suggestions if 'smart_suggestions' in locals() else []
            }
    
    def _handle_confirmation_state(self, user_input: str) -> Dict[str, Any]:
        """Handle confirmation state"""
        
        # Detect user intent
        intent_result = detect_user_intent.invoke({"user_input": user_input})
        intent = intent_result.get("intent", "new_info")
        
        if intent == "confirmation":
            # User confirmed - proceed with booking
            confirmation = confirm_booking_llm.invoke({
                "booking_info": self.current_booking
            })
            
            # Reset for new booking
            self.current_booking = {}
            self.conversation_state = "gathering_info"
            
            return {
                "success": True,
                "response": confirmation["confirmation_message"],
                "tool_used": "LLM_CAR_BOOKING",
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
                    'pickup': 'điểm đón',
                    'destination': 'điểm đến'
                }
                
                # Clear the field to be updated
                if update_field in self.current_booking:
                    del self.current_booking[update_field]
                
                self.conversation_state = "gathering_info"
                
                return {
                    "success": True,
                    "response": f"Được rồi! Vui lòng cung cấp {field_names.get(update_field, update_field)} mới:",
                    "tool_used": "LLM_CAR_BOOKING",
                    "status": "updating_info",
                    "updating_field": update_field,
                    "current_info": self.current_booking.copy()
                }
            else:
                return {
                    "success": True,
                    "response": "Bạn muốn thay đổi thông tin gì? (tên, số điện thoại, điểm đón, điểm đến)",
                    "tool_used": "LLM_CAR_BOOKING",
                    "status": "awaiting_confirmation",
                    "current_info": self.current_booking.copy()
                }
        else:
            # Treat as new info or try to extract update
            extraction_result = extract_booking_info_with_llm.invoke({
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
                preview_result = format_booking_preview.invoke({
                    "booking_info": self.current_booking
                })
                
                return {
                    "success": True,
                    "response": f"✅ Đã cập nhật: {', '.join(new_fields)}\n\n{preview_result['preview_message']}",
                    "tool_used": "LLM_CAR_BOOKING",
                    "status": "awaiting_confirmation",
                    "current_info": self.current_booking.copy(),
                    "updated_fields": new_fields
                }
            else:
                # No new info detected, ask for clarification
                return {
                    "success": True,
                    "response": "Tôi không hiểu yêu cầu của bạn. Vui lòng:\n- Trả lời **'xác nhận'** để đặt xe\n- Hoặc nói **'thay đổi [thông tin]'** để sửa thông tin",
                    "tool_used": "LLM_CAR_BOOKING", 
                    "status": "awaiting_confirmation",
                    "current_info": self.current_booking.copy()
                }