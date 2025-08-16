"""
Conversational Car Booking Agent using LangGraph
Provides smooth, natural conversation flow for car booking
"""

import json
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime, timedelta
from dataclasses import dataclass

# LangGraph imports with fallback
try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    from langgraph.prebuilt import ToolNode
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️ LangGraph not available, using simplified implementation")
    
    # Fallback definitions for when LangGraph is not available
    def add_messages(x, y):
        """Fallback function for add_messages"""
        if isinstance(x, list) and isinstance(y, list):
            return x + y
        return [x, y] if not isinstance(x, list) else x + [y]
    
    class StateGraph:
        def __init__(self, state_class):
            pass
    
    END = "END"

# LangChain imports
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


@dataclass
class CarBookingInfo:
    """Car booking information structure"""
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    pickup_location: Optional[str] = None
    destination: Optional[str] = None
    pickup_date: Optional[str] = None
    pickup_time: Optional[str] = None
    car_type: Optional[str] = None
    passengers: Optional[int] = None
    special_requests: Optional[str] = None
    
    def get_missing_fields(self) -> List[str]:
        """Get list of missing required fields"""
        required_fields = [
            'customer_name', 'customer_phone', 'pickup_location', 
            'destination', 'pickup_date', 'pickup_time'
        ]
        missing = []
        for field in required_fields:
            if not getattr(self, field):
                missing.append(field)
        return missing
    
    def get_completion_percentage(self) -> float:
        """Get completion percentage"""
        total_fields = 9
        filled_fields = sum(1 for field in self.__dict__.values() if field)
        return (filled_fields / total_fields) * 100


# LangGraph State Definition
class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    booking_info: CarBookingInfo
    current_step: str
    user_intent: str
    extraction_attempts: int


@tool
def extract_booking_details(text: str, current_info: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Extract car booking details from user text using advanced NLP
    
    Args:
        text: User input text
        current_info: Current booking information
        
    Returns:
        Dict with extracted booking details
    """
    import re
    from datetime import datetime, timedelta
    
    if current_info is None:
        current_info = {}
    
    extracted = {}
    text_lower = text.lower()
    
    # Extract names (Vietnamese patterns)
    name_patterns = [
        r'tên (?:tôi là |của tôi là )?([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]+(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]+)*)',
        r'(?:tôi là |mình là |họ tên |họ và tên )([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]+(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]+)*)',
        r'([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]+(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]+)+)(?:\s+đây|$)'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted['customer_name'] = match.group(1).strip()
            break
    
    # Extract phone numbers
    phone_patterns = [
        r'(?:số điện thoại|sdt|phone|số|điện thoại)[\s:]*(\+?84?[0-9]{8,10})',
        r'(\+?84?[0-9]{8,10})',
        r'(?:^|\s)(0[0-9]{8,9})(?:\s|$)'
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(1).strip()
            # Normalize phone number
            if phone.startswith('+84'):
                phone = '0' + phone[3:]
            elif phone.startswith('84'):
                phone = '0' + phone[2:]
            extracted['customer_phone'] = phone
            break
    
    # Extract locations
    location_patterns = [
        r'(?:từ|đón tại|pickup)\s+([A-Za-zÀ-ỹ\s,]+?)(?:\s+(?:đến|to|tới)|$)',
        r'(?:đến|tới|to)\s+([A-Za-zÀ-ỹ\s,]+?)(?:\s|$)',
        r'địa chỉ[\s:]*([A-Za-zÀ-ỹ\s,0-9]+)'
    ]
    
    # Try to extract pickup and destination
    pickup_match = re.search(r'(?:từ|đón tại|pickup)\s+([A-Za-zÀ-ỹ\s,]+?)(?:\s+(?:đến|to|tới)|$)', text, re.IGNORECASE)
    if pickup_match:
        extracted['pickup_location'] = pickup_match.group(1).strip()
    
    dest_match = re.search(r'(?:đến|tới|to)\s+([A-Za-zÀ-ỹ\s,]+?)(?:\s|$)', text, re.IGNORECASE)
    if dest_match:
        extracted['destination'] = dest_match.group(1).strip()
    
    # Extract dates
    date_patterns = [
        r'(?:ngày|date)\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
        r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
        r'(?:hôm nay|today)',
        r'(?:ngày mai|tomorrow)',
        r'(?:thứ\s+\w+|monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text_lower)
        if match:
            if 'hôm nay' in match.group() or 'today' in match.group():
                extracted['pickup_date'] = datetime.now().strftime('%Y-%m-%d')
            elif 'ngày mai' in match.group() or 'tomorrow' in match.group():
                extracted['pickup_date'] = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            elif match.group(1) if len(match.groups()) > 0 else None:
                # Try to parse date
                try:
                    date_str = match.group(1)
                    if '/' in date_str:
                        parts = date_str.split('/')
                    else:
                        parts = date_str.split('-')
                    
                    if len(parts) == 3:
                        day, month, year = parts
                        if len(year) == 2:
                            year = '20' + year
                        extracted['pickup_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    pass
            break
    
    # Extract times
    time_patterns = [
        r'(?:lúc|vào|at)\s*(\d{1,2}):(\d{2})',
        r'(\d{1,2}):(\d{2})',
        r'(\d{1,2})\s*(?:giờ|h)',
        r'(?:sáng|morning)\s*(\d{1,2})',
        r'(?:chiều|afternoon)\s*(\d{1,2})',
        r'(?:tối|evening)\s*(\d{1,2})'
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) >= 2:
                hour, minute = match.group(1), match.group(2)
                extracted['pickup_time'] = f"{hour.zfill(2)}:{minute}"
            else:
                hour = match.group(1)
                if 'chiều' in pattern or 'afternoon' in pattern:
                    hour = str(int(hour) + 12)
                elif 'tối' in pattern or 'evening' in pattern:
                    hour = str(int(hour) + 18)
                extracted['pickup_time'] = f"{hour.zfill(2)}:00"
            break
    
    # Extract car type
    car_types = {
        '4 chỗ': '4 chỗ',
        '7 chỗ': '7 chỗ', 
        '16 chỗ': '16 chỗ',
        'sedan': '4 chỗ',
        'suv': '7 chỗ',
        'minivan': '16 chỗ',
        'xe ôm': 'xe ôm',
        'grab': '4 chỗ'
    }
    
    for key, value in car_types.items():
        if key in text_lower:
            extracted['car_type'] = value
            break
    
    # Extract passenger count
    passenger_match = re.search(r'(\d+)\s*(?:người|passenger|khách)', text_lower)
    if passenger_match:
        extracted['passengers'] = int(passenger_match.group(1))
    
    # Extract special requests
    request_patterns = [
        r'(?:ghi chú|note|yêu cầu)[\s:]*(.+)',
        r'(?:cần|muốn|đề nghị)[\s:]*(.+)'
    ]
    
    for pattern in request_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted['special_requests'] = match.group(1).strip()
            break
    
    return {
        "extracted_info": extracted,
        "confidence": min(len(extracted) * 0.2, 1.0),
        "tool_used": "ADVANCED_EXTRACTION"
    }


@tool  
def validate_booking_info(booking_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate booking information and provide specific feedback
    
    Args:
        booking_info: Current booking information
        
    Returns:
        Validation result with specific missing fields and suggestions
    """
    
    missing_fields = []
    suggestions = {}
    
    field_display_names = {
        'customer_name': 'Tên khách hàng',
        'customer_phone': 'Số điện thoại',
        'pickup_location': 'Điểm đón', 
        'destination': 'Điểm đến',
        'pickup_date': 'Ngày đón',
        'pickup_time': 'Giờ đón'
    }
    
    required_fields = ['customer_name', 'customer_phone', 'pickup_location', 'destination', 'pickup_date', 'pickup_time']
    
    for field in required_fields:
        if not booking_info.get(field):
            missing_fields.append(field)
            
            # Provide specific suggestions for each field
            if field == 'customer_name':
                suggestions[field] = "Vui lòng cho biết tên của bạn (ví dụ: Nguyễn Văn An)"
            elif field == 'customer_phone':
                suggestions[field] = "Vui lòng cung cấp số điện thoại (ví dụ: 0912345678)"
            elif field == 'pickup_location':
                suggestions[field] = "Vui lòng cho biết địa điểm đón (ví dụ: Sân bay Nội Bài, 123 Trần Hưng Đạo)"
            elif field == 'destination':
                suggestions[field] = "Vui lòng cho biết điểm đến (ví dụ: Hà Nội, Khách sạn ABC)"
            elif field == 'pickup_date':
                suggestions[field] = "Vui lòng cho biết ngày đón (ví dụ: hôm nay, ngày mai, 25/12/2024)"
            elif field == 'pickup_time':
                suggestions[field] = "Vui lòng cho biết giờ đón (ví dụ: 8:00, 14:30, 8 giờ sáng)"
    
    # Calculate completion percentage
    total_fields = len(required_fields)
    completed_fields = total_fields - len(missing_fields)
    completion_percentage = (completed_fields / total_fields) * 100
    
    return {
        "is_complete": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "missing_display_names": [field_display_names[field] for field in missing_fields],
        "suggestions": suggestions,
        "completion_percentage": completion_percentage,
        "tool_used": "VALIDATION"
    }


@tool
def format_booking_summary(booking_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format booking information into a user-friendly summary
    
    Args:
        booking_info: Complete booking information
        
    Returns:
        Formatted summary for confirmation
    """
    
    summary_lines = []
    
    # Header
    summary_lines.append("🚗 **THÔNG TIN ĐẶT XE**")
    summary_lines.append("─" * 30)
    
    # Customer info
    if booking_info.get('customer_name'):
        summary_lines.append(f"👤 **Khách hàng:** {booking_info['customer_name']}")
    if booking_info.get('customer_phone'):
        summary_lines.append(f"📞 **Điện thoại:** {booking_info['customer_phone']}")
    
    # Trip info
    if booking_info.get('pickup_location'):
        summary_lines.append(f"📍 **Điểm đón:** {booking_info['pickup_location']}")
    if booking_info.get('destination'):
        summary_lines.append(f"🎯 **Điểm đến:** {booking_info['destination']}")
    
    # Time info
    if booking_info.get('pickup_date'):
        summary_lines.append(f"📅 **Ngày đón:** {booking_info['pickup_date']}")
    if booking_info.get('pickup_time'):
        summary_lines.append(f"⏰ **Giờ đón:** {booking_info['pickup_time']}")
    
    # Vehicle info
    if booking_info.get('car_type'):
        summary_lines.append(f"🚙 **Loại xe:** {booking_info['car_type']}")
    if booking_info.get('passengers'):
        summary_lines.append(f"👥 **Số hành khách:** {booking_info['passengers']}")
    
    # Special requests
    if booking_info.get('special_requests'):
        summary_lines.append(f"📝 **Ghi chú:** {booking_info['special_requests']}")
    
    summary_lines.append("─" * 30)
    summary_lines.append("✅ Vui lòng xác nhận thông tin trên có chính xác không?")
    summary_lines.append("💬 Trả lời 'đồng ý' hoặc 'xác nhận' để hoàn tất đặt xe")
    
    return {
        "formatted_summary": "\n".join(summary_lines),
        "tool_used": "FORMATTING"
    }


class ConversationalCarBookingAgent:
    """
    Conversational Car Booking Agent using LangChain/LangGraph
    """
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key
        self.use_langgraph = LANGGRAPH_AVAILABLE and openai_api_key
        
        # Initialize LLM
        if openai_api_key:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                api_key=openai_api_key,
                temperature=0.3
            )
        
        # Define tools
        self.tools = [
            extract_booking_details,
            validate_booking_info,
            format_booking_summary
        ]
        
        # Initialize conversation system
        if self.use_langgraph:
            self._setup_langgraph()
        else:
            self._setup_simple_conversation()
    
    def _setup_langgraph(self):
        """Setup LangGraph-based conversation flow"""
        
        # Create the state graph
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("extract_info", self._extract_info_node)
        workflow.add_node("validate_info", self._validate_info_node) 
        workflow.add_node("request_missing", self._request_missing_node)
        workflow.add_node("confirm_booking", self._confirm_booking_node)
        workflow.add_node("tools", ToolNode(self.tools))
        
        # Set entry point
        workflow.set_entry_point("extract_info")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "extract_info",
            self._should_validate,
            {
                "validate": "validate_info",
                "tools": "tools"
            }
        )
        
        workflow.add_conditional_edges(
            "validate_info", 
            self._check_completeness,
            {
                "complete": "confirm_booking",
                "incomplete": "request_missing"
            }
        )
        
        workflow.add_edge("request_missing", END)
        workflow.add_edge("confirm_booking", END)
        workflow.add_edge("tools", "validate_info")
        
        # Compile the graph
        memory = MemorySaver()
        self.app = workflow.compile(checkpointer=memory)
    
    def _setup_simple_conversation(self):
        """Setup simple conversation flow without LangGraph"""
        self.conversation_state = {
            "booking_info": CarBookingInfo(),
            "current_step": "initial",
            "extraction_attempts": 0
        }
    
    def process_user_input(self, user_input: str, conversation_id: str = "default") -> Dict[str, Any]:
        """
        Process user input and return conversational response
        
        Args:
            user_input: User's message
            conversation_id: Conversation identifier
            
        Returns:
            Response with conversational message and booking status
        """
        
        if self.use_langgraph:
            return self._process_with_langgraph(user_input, conversation_id)
        else:
            return self._process_simple(user_input)
    
    def _process_with_langgraph(self, user_input: str, conversation_id: str) -> Dict[str, Any]:
        """Process using LangGraph workflow"""
        
        # Create initial state
        state = {
            "messages": [HumanMessage(content=user_input)],
            "booking_info": CarBookingInfo(),
            "current_step": "extract_info",
            "user_intent": "booking",
            "extraction_attempts": 0
        }
        
        # Configure with conversation ID
        config = {"configurable": {"thread_id": conversation_id}}
        
        # Run the workflow
        result = self.app.invoke(state, config)
        
        # Extract response from result
        if result.get("messages"):
            last_message = result["messages"][-1]
            if hasattr(last_message, 'content'):
                response = last_message.content
            else:
                response = str(last_message)
        else:
            response = "Có lỗi xảy ra trong quá trình xử lý."
        
        return {
            "success": True,
            "response": response,
            "booking_info": result.get("booking_info", CarBookingInfo()).__dict__,
            "current_step": result.get("current_step", "unknown"),
            "tool_used": "CONVERSATIONAL_CAR_BOOKING"
        }
    
    def _process_simple(self, user_input: str) -> Dict[str, Any]:
        """Process using simple conversation flow"""
        
        # Extract information using tools
        extraction_result = extract_booking_details.invoke({
            "text": user_input,
            "current_info": self.conversation_state["booking_info"].__dict__
        })
        
        # Update booking info
        extracted_info = extraction_result.get("extracted_info", {})
        for key, value in extracted_info.items():
            setattr(self.conversation_state["booking_info"], key, value)
        
        # Validate current info
        validation_result = validate_booking_info.invoke({
            "booking_info": self.conversation_state["booking_info"].__dict__
        })
        
        # Generate response based on completeness
        if validation_result["is_complete"]:
            # Format summary for confirmation
            summary_result = format_booking_summary.invoke({
                "booking_info": self.conversation_state["booking_info"].__dict__
            })
            response = summary_result["formatted_summary"]
            current_step = "confirmation"
        else:
            # Request missing information
            response = self._generate_missing_info_request(validation_result)
            current_step = "information_gathering"
        
        return {
            "success": True,
            "response": response,
            "booking_info": self.conversation_state["booking_info"].__dict__,
            "current_step": current_step,
            "completion_percentage": validation_result.get("completion_percentage", 0),
            "tool_used": "CONVERSATIONAL_CAR_BOOKING"
        }
    
    def _generate_missing_info_request(self, validation_result: Dict[str, Any]) -> str:
        """Generate conversational request for missing information"""
        
        missing_fields = validation_result["missing_display_names"]
        suggestions = validation_result["suggestions"]
        completion = validation_result["completion_percentage"]
        
        if len(missing_fields) == 1:
            field = validation_result["missing_fields"][0]
            suggestion = suggestions.get(field, "")
            response = f"Cảm ơn bạn! Tôi cần thêm thông tin: **{missing_fields[0]}**\n\n{suggestion}"
        elif len(missing_fields) <= 3:
            response = f"Cảm ơn bạn! Tôi cần thêm một số thông tin:\n\n"
            for i, field in enumerate(missing_fields, 1):
                original_field = validation_result["missing_fields"][i-1]
                suggestion = suggestions.get(original_field, "")
                response += f"{i}. **{field}**: {suggestion}\n"
        else:
            response = f"Cảm ơn bạn! Tôi cần thêm thông tin về:\n\n"
            for i, field in enumerate(missing_fields[:3], 1):
                response += f"{i}. {field}\n"
            response += f"\nVui lòng cung cấp từng thông tin một cách tự nhiên."
        
        # Add progress indicator
        response += f"\n\n📊 **Tiến độ:** {completion:.0f}% hoàn thành"
        
        return response
    
    # LangGraph node functions (placeholder implementations)
    def _extract_info_node(self, state: ConversationState):
        # Implementation for LangGraph node
        pass
    
    def _validate_info_node(self, state: ConversationState):
        # Implementation for LangGraph node
        pass
    
    def _request_missing_node(self, state: ConversationState):
        # Implementation for LangGraph node
        pass
    
    def _confirm_booking_node(self, state: ConversationState):
        # Implementation for LangGraph node
        pass
    
    def _should_validate(self, state: ConversationState):
        # Decision logic for LangGraph
        return "validate"
    
    def _check_completeness(self, state: ConversationState):
        # Decision logic for LangGraph
        return "incomplete"