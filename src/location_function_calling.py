"""
Location Function Calling System using LangChain
Implements function calling to detect and request location information from users
"""

import json
from typing import Dict, Any, Optional, List
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage


@tool
def request_location_information(
    query_type: str, 
    context: str = "", 
    suggested_locations: List[str] = None
) -> Dict[str, Any]:
    """
    Request location information from user when location is missing or unclear.
    
    Args:
        query_type: Type of query needing location (weather, hotel, car, travel_plan)
        context: Additional context about the request
        suggested_locations: List of suggested locations based on context
        
    Returns:
        Dict with request message and suggestions
    """
    
    query_prompts = {
        "weather": {
            "message": "🏙️ **Tôi cần biết địa điểm để kiểm tra thời tiết.**\n\nBạn muốn xem thời tiết ở đâu?",
            "examples": ["Hà Nội", "Đà Nẵng", "Hồ Chí Minh", "Nha Trang", "Huế"]
        },
        "hotel": {
            "message": "🏨 **Tôi cần biết địa điểm để tìm khách sạn.**\n\nBạn muốn đặt khách sạn ở thành phố nào?",
            "examples": ["Hà Nội", "Đà Nẵng", "Hồ Chí Minh", "Hội An", "Sapa"]
        },
        "car": {
            "message": "🚗 **Tôi cần biết điểm đón và điểm đến để đặt xe.**\n\nBạn muốn đi từ đâu đến đâu?",
            "examples": ["Từ sân bay Nội Bài đến trung tâm Hà Nội", "Từ Hà Nội đi Hạ Long"]
        },
        "travel_plan": {
            "message": "🧳 **Tôi cần biết điểm đến để lập kế hoạch du lịch.**\n\nBạn muốn du lịch ở đâu?",
            "examples": ["Sapa", "Đà Lạt", "Phú Quốc", "Hạ Long", "Hội An"]
        }
    }
    
    prompt_info = query_prompts.get(query_type, query_prompts["weather"])
    
    # Use suggested locations if provided, otherwise use default examples
    examples = suggested_locations if suggested_locations else prompt_info["examples"]
    
    response_message = f"{prompt_info['message']}\n\n💡 **Gợi ý:** {', '.join(examples)}"
    
    if context:
        response_message += f"\n\n📝 **Ngữ cảnh:** {context}"
    
    return {
        "needs_location": True,
        "response": response_message,
        "query_type": query_type,
        "suggested_locations": examples,
        "tool_used": "LOCATION_REQUEST"
    }


@tool 
def extract_location_from_text(
    text: str,
    conversation_history: str = "",
    prioritize_provinces: bool = True
) -> Dict[str, Any]:
    """
    Extract location information from text using comprehensive location database.
    
    Args:
        text: Text to extract location from
        conversation_history: Previous conversation context
        prioritize_provinces: Whether to prioritize provinces over cities
        
    Returns:
        Dict with extracted location information
    """
    
    # Comprehensive Vietnam location database
    provinces = [
        "kiên giang", "an giang", "cà mau", "bạc liêu", "sóc trăng", 
        "đồng tháp", "tiền giang", "bến tre", "vĩnh long", "trà vinh",
        "hà giang", "cao bằng", "lào cai", "yên bái", "tuyên quang",
        "thái nguyên", "bắc kạn", "lang sơn", "quảng ninh", "hải phòng",
        "nam định", "thái bình", "hưng yên", "hà nam", "ninh bình",
        "thanh hóa", "nghệ an", "hà tĩnh", "quảng bình", "quảng trì",
        "quảng nam", "quảng ngãi", "bình định", "phú yên", "khánh hòa",
        "ninh thuận", "bình thuận", "kon tum", "gia lai", "đắk lắk",
        "đắk nông", "lâm đồng", "bình phước", "tây ninh", "bình dương",
        "đồng nai", "bà rịa vũng tầu", "long an"
    ]
    
    cities = [
        "hà nội", "hồ chí minh", "đà nẵng", "nha trang", "huế", "hội an", 
        "sapa", "đà lạt", "phú quốc", "cần thơ", "vũng tầu", "phan thiết",
        "hạ long", "ninh bình", "mù cang chải", "tam cốc", "bái đính",
        "sa pa", "mũi né", "côn đảo", "cát bà", "hòa bình"
    ]
    
    all_locations = provinces + cities
    
    # Normalize text for searching
    text_lower = text.lower().strip()
    history_lower = conversation_history.lower().strip()
    
    found_locations = []
    
    # Search in main text first (highest priority)
    for location in all_locations:
        if location in text_lower:
            priority = "province" if location in provinces else "city"
            found_locations.append({
                "location": location.title(),
                "source": "text",
                "priority": priority,
                "confidence": 0.9
            })
    
    # Search in conversation history (lower priority)
    if not found_locations and history_lower:
        for location in all_locations:
            if location in history_lower:
                priority = "province" if location in provinces else "city" 
                found_locations.append({
                    "location": location.title(),
                    "source": "history",
                    "priority": priority,
                    "confidence": 0.7
                })
    
    if found_locations:
        # Sort by confidence and priority
        if prioritize_provinces:
            found_locations.sort(key=lambda x: (
                x["confidence"], 
                x["priority"] == "province", 
                x["source"] == "text"
            ), reverse=True)
        else:
            found_locations.sort(key=lambda x: (
                x["confidence"],
                x["source"] == "text"
            ), reverse=True)
        
        best_match = found_locations[0]
        
        return {
            "location_found": True,
            "location": best_match["location"],
            "source": best_match["source"],
            "confidence": best_match["confidence"],
            "all_candidates": found_locations,
            "tool_used": "LOCATION_EXTRACTION"
        }
    
    return {
        "location_found": False,
        "location": None,
        "source": None,
        "confidence": 0.0,
        "all_candidates": [],
        "tool_used": "LOCATION_EXTRACTION"
    }


class LocationFunctionCaller:
    """
    LangChain-based function calling system for location detection
    """
    
    def __init__(self, openai_api_key: str = None, model: str = "gpt-3.5-turbo"):
        """Initialize the function calling system"""
        
        self.use_agent = False
        self.agent_executor = None
        
        # Only initialize agent if API key is available
        if openai_api_key:
            try:
                self.llm = ChatOpenAI(
                    model=model,
                    api_key=openai_api_key,
                    temperature=0.1  # Low temperature for consistent results
                )
                self.use_agent = True
            except Exception as e:
                print(f"⚠️ Could not initialize OpenAI agent: {str(e)}")
                self.use_agent = False
        
        # Define available tools
        self.tools = [
            request_location_information,
            extract_location_from_text
        ]
        
        # Initialize agent components only if using agent
        if self.use_agent:
            # Create the function calling prompt
            self.prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""Bạn là trợ lý du lịch thông minh chuyên xử lý thông tin địa điểm.

Nhiệm vụ của bạn:
1. Phân tích yêu cầu của người dùng để xác định xem có cần thông tin địa điểm không
2. Trích xuất địa điểm từ văn bản nếu có
3. Yêu cầu người dùng cung cấp địa điểm nếu thiếu và cần thiết

Quy tắc xử lý:
- Luôn ưu tiên địa điểm được đề cập trực tiếp trong câu hỏi
- Nếu không có địa điểm trong câu hỏi, kiểm tra lịch sử hội thoại
- Nếu vẫn không có, yêu cầu người dùng cung cấp
- KHÔNG BAO GIỜ tự động chọn địa điểm mặc định

Loại yêu cầu cần địa điểm:
- weather: Kiểm tra thời tiết
- hotel: Đặt khách sạn  
- car: Đặt xe di chuyển
- travel_plan: Lập kế hoạch du lịch"""),
                
                HumanMessage(content="{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])
            
            # Create the agent
            self.agent = create_openai_functions_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self.prompt
            )
            
            # Create agent executor
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=False,
                handle_parsing_errors=True,
                max_iterations=3
            )
    
    def detect_and_handle_location(
        self, 
        user_query: str,
        query_type: str,
        conversation_history: str = "",
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Main method to detect location or request it from user
        
        Args:
            user_query: User's query text
            query_type: Type of query (weather, hotel, car, travel_plan)
            conversation_history: Previous conversation context
            context: Additional context
            
        Returns:
            Dict with location information or request message
        """
        
        # Prepare input for the agent
        full_context = f"Conversation History: {conversation_history}\nContext: {context}" if conversation_history or context else ""
        
        agent_input = f"""
Phân tích yêu cầu sau:

Câu hỏi: "{user_query}"
Loại yêu cầu: {query_type}
Ngữ cảnh: {full_context}

Hãy xử lý theo quy trình:
1. Trích xuất địa điểm từ câu hỏi bằng extract_location_from_text
2. Nếu không tìm thấy địa điểm, sử dụng request_location_information để yêu cầu người dùng cung cấp
"""
        
        # If no agent available, use direct tool calls
        if not self.use_agent or self.agent_executor is None:
            return self._fallback_location_detection(user_query, query_type, conversation_history)
        
        try:
            # Execute the agent
            result = self.agent_executor.invoke({
                "input": agent_input
            })
            
            # Parse the result
            output = result.get("output", "")
            
            # Try to extract structured information from the output
            return self._parse_agent_output(output, user_query, query_type)
            
        except Exception as e:
            # Fallback to direct tool usage
            return self._fallback_location_detection(user_query, query_type, conversation_history)
    
    def _parse_agent_output(self, output: str, user_query: str, query_type: str) -> Dict[str, Any]:
        """Parse agent output to extract structured location information"""
        
        # Try to extract location information from output
        if "location_found" in output.lower() and "true" in output.lower():
            # Location was found
            return {
                "success": True,
                "location_found": True,
                "response": output,
                "tool_used": "FUNCTION_CALLING_EXTRACTION"
            }
        elif "needs_location" in output.lower() and "true" in output.lower():
            # Location request needed
            return {
                "success": True,
                "location_found": False,
                "needs_location": True,
                "response": output,
                "tool_used": "FUNCTION_CALLING_REQUEST"
            }
        else:
            # Parse the text output
            return {
                "success": True,
                "location_found": False,
                "response": output,
                "tool_used": "FUNCTION_CALLING_RESPONSE"
            }
    
    def _fallback_location_detection(
        self, 
        user_query: str, 
        query_type: str, 
        conversation_history: str = ""
    ) -> Dict[str, Any]:
        """Fallback method using direct tool calls"""
        
        try:
            # Try to extract location directly
            extraction_result = extract_location_from_text.invoke({
                "text": user_query,
                "conversation_history": conversation_history
            })
            
            if extraction_result["location_found"]:
                return {
                    "success": True,
                    "location_found": True,
                    "location": extraction_result["location"],
                    "confidence": extraction_result["confidence"],
                    "response": f"Đã xác định địa điểm: {extraction_result['location']}",
                    "tool_used": "FALLBACK_EXTRACTION"
                }
            else:
                # Request location from user
                request_result = request_location_information.invoke({
                    "query_type": query_type,
                    "context": user_query
                })
                
                return {
                    "success": True,
                    "location_found": False,
                    "needs_location": True,
                    "response": request_result["response"],
                    "suggested_locations": request_result["suggested_locations"],
                    "tool_used": "FALLBACK_REQUEST"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "Có lỗi xảy ra khi xử lý thông tin địa điểm.",
                "tool_used": "FALLBACK_ERROR"
            }