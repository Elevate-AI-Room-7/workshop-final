"""
Travel Planner Agent - Unified agent for travel planning with RAG and tools
"""

import os
from typing import Dict, Any, List, Optional
from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import requests
import json
from .pinecone_rag_system import PineconeRAGSystem
from .config_manager import ConfigManager
from .suggestion_engine import SuggestionEngine, SuggestionContext, ToolType
from .location_function_calling import LocationFunctionCaller
from .conversational_car_booking import ConversationalCarBookingAgent
from .simple_car_booking import SimpleCarBooking
from .llm_car_booking import LLMCarBooking
from .llm_hotel_booking import LLMHotelBooking
from .llm_travel_planning import LLMTravelPlanning


class TravelPlannerAgent:
    """
    Unified Travel Planner Agent that combines:
    - Pinecone RAG system for travel knowledge
    - Weather information
    - Hotel booking functionality
    - Travel planning with database storage
    """
    
    def __init__(self, debug_mode: bool = False):
        self.openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.weather_api_key = os.getenv("WEATHER_API_KEY")
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        # Debug mode setting
        self.debug_mode = debug_mode or os.getenv("DEBUG_TRAVEL_AGENT", "false").lower() == "true"
        
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        
        # Initialize Pinecone RAG system
        self.rag_system = PineconeRAGSystem()
        
        # Initialize Suggestion Engine
        self.suggestion_engine = SuggestionEngine(self.config_manager)
        
        # Initialize function calling for location detection
        self.location_function_caller = LocationFunctionCaller(
            openai_api_key=self.openai_api_key,
            model="gpt-3.5-turbo"
        )
        
        # Initialize LLM car booking (preferred) với fallback
        self.llm_car_booking = LLMCarBooking()
        self.simple_car_booking = SimpleCarBooking()  # Fallback
        
        # Initialize LLM hotel booking (preferred)
        self.llm_hotel_booking = LLMHotelBooking()
        
        # Initialize LLM travel planning (simple demo)
        self.llm_travel_planning = LLMTravelPlanning()
        
        # Initialize conversational car booking agent (backup)
        self.car_booking_agent = ConversationalCarBookingAgent(
            openai_api_key=self.openai_api_key
        )
        
        # Initialize variables for tracking sources and fallback
        self.last_rag_sources = []
        self.no_relevant_info = False
        self.fallback_query = ""
        
        # Initialize LLM with configurable temperature
        self.llm = ChatOpenAI(
            model="GPT-4o-mini",
            temperature=self.config_manager.get_temperature(),
            openai_api_key=self.openai_api_key,
            base_url=self.openai_endpoint
        )
        
        # Setup tools and agent
        self.tools = self._setup_tools()
        self.agent = self._setup_agent()
        
        if self.debug_mode:
            print("🐛 DEBUG MODE ENABLED for TravelPlannerAgent")
        
    def _setup_tools(self) -> List[Tool]:
        """Setup all tools for the travel planner agent"""
        
        def rag_search_tool(query: str) -> str:
            """Search travel knowledge base using RAG"""
            try:
                result = self.rag_system.query(query)
                
                # Check if no relevant information was found
                if result.get('no_relevant_info') or result.get('answer') is None:
                    # Store that no relevant info was found
                    self.last_rag_sources = []
                    self.no_relevant_info = True
                    self.fallback_query = query
                    return f"RAG_NO_INFO: {query}"
                
                answer = result.get('answer', 'Không tìm thấy thông tin phù hợp.')
                sources = result.get('sources', [])
                
                # Store sources in class variable for access later
                self.last_rag_sources = sources
                self.no_relevant_info = False
                
                return answer
            except Exception as e:
                return f"Lỗi tìm kiếm: {str(e)}"
        
        def weather_tool(city: str) -> str:
            """Get weather information for a city"""
            try:
                url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.weather_api_key}&units=metric"
                response = requests.get(url, timeout=10)
                
                if response.status_code != 200:
                    return f"Không tìm thấy thông tin thời tiết cho {city}"
                
                data = response.json()
                weather_info = (
                    f"Thời tiết tại {city}:\n"
                    f"- Nhiệt độ: {data['main']['temp']}°C\n"
                    f"- Thời tiết: {data['weather'][0]['description']}\n"
                    f"- Độ ẩm: {data['main']['humidity']}%\n"
                    f"- Tốc độ gió: {data['wind']['speed']} m/s"
                )
                return weather_info
                
            except Exception as e:
                return f"Lỗi lấy thông tin thời tiết: {str(e)}"
        
        def hotel_booking_tool(input_str: str) -> str:
            """Book hotel (mock function)"""
            try:
                # Parse input: "city|date|nights"
                parts = input_str.split("|")
                city = parts[0] if len(parts) > 0 else "Unknown"
                date = parts[1] if len(parts) > 1 else "2025-12-01"
                nights = int(parts[2]) if len(parts) > 2 else 1
                
                # Mock booking
                booking_info = {
                    "city": city,
                    "date": date,
                    "nights": nights,
                    "hotel": "AI Grand Hotel",
                    "confirmation": f"CONFIRM-{city[:3].upper()}-{date.replace('-', '')}-{nights}",
                    "price": f"${nights * 120}"
                }
                
                result = (
                    f"✅ Đặt khách sạn thành công!\n"
                    f"🏨 Khách sạn: {booking_info['hotel']}\n"
                    f"📍 Thành phố: {booking_info['city']}\n"
                    f"📅 Ngày: {booking_info['date']}\n"
                    f"🌙 Số đêm: {booking_info['nights']}\n"
                    f"💰 Giá: {booking_info['price']}\n"
                    f"🔖 Mã xác nhận: {booking_info['confirmation']}"
                )
                
                return result
                
            except Exception as e:
                return f"Lỗi đặt khách sạn: {str(e)}"
        
        def car_booking_tool(input_str: str) -> str:
            """Book car/transportation (mock function)"""
            try:
                # Parse input: "pickup|destination|date|type"
                parts = input_str.split("|")
                pickup = parts[0] if len(parts) > 0 else "Unknown"
                destination = parts[1] if len(parts) > 1 else "Unknown"
                date = parts[2] if len(parts) > 2 else "2025-12-01"
                car_type = parts[3] if len(parts) > 3 else "4 chỗ"
                
                # Mock booking
                booking_info = {
                    "pickup": pickup,
                    "destination": destination,
                    "date": date,
                    "car_type": car_type,
                    "driver": "Nguyễn Văn An",
                    "confirmation": f"CAR-{pickup[:2].upper()}{destination[:2].upper()}-{date.replace('-', '')}",
                    "price": "500,000 VND"
                }
                
                result = (
                    f"✅ Đặt xe thành công!\n"
                    f"🚗 Loại xe: {booking_info['car_type']}\n"
                    f"📍 Điểm đón: {booking_info['pickup']}\n"
                    f"🎯 Điểm đến: {booking_info['destination']}\n"
                    f"📅 Ngày: {booking_info['date']}\n"
                    f"👨‍✈️ Tài xế: {booking_info['driver']}\n"
                    f"💰 Giá: {booking_info['price']}\n"
                    f"🔖 Mã xác nhận: {booking_info['confirmation']}"
                )
                
                return result
                
            except Exception as e:
                return f"Lỗi đặt xe: {str(e)}"
        
        return [
            Tool(
                name="TravelKnowledgeSearch",
                func=rag_search_tool,
                description="Tìm kiếm thông tin du lịch trong cơ sở dữ liệu. Input: câu hỏi về du lịch"
            ),
            Tool(
                name="WeatherInfo",
                func=weather_tool,
                description="Lấy thông tin thời tiết. Input: tên thành phố"
            ),
            Tool(
                name="BookHotel",
                func=hotel_booking_tool,
                description="Đặt khách sạn. Input format: 'city|date|nights' (ví dụ: 'Hanoi|2025-12-25|2')"
            ),
            Tool(
                name="BookCar",
                func=car_booking_tool,
                description="Đặt xe/vận chuyển. Input format: 'pickup|destination|date|type' (ví dụ: 'Hanoi|Halong|2025-12-25|7 chỗ')"
            )
        ]
    
    def _setup_agent(self):
        """Setup the conversational agent"""
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent="chat-conversational-react-description",
            verbose=False,
            max_iterations=3
        )
    
    def plan_travel(self, user_input: str, chat_history: List = None) -> Dict[str, Any]:
        """
        Main method to handle travel planning requests with smart tool detection
        
        Args:
            user_input: User's travel planning query
            chat_history: Previous conversation history
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Prepare chat history for agent
            if chat_history is None:
                chat_history = []
            
            if self.debug_mode:
                print(f"\n🚀 [DEBUG] Starting Travel Planning:")
                print(f"📝 User input: '{user_input}'")
                print(f"📚 Chat history: {len(chat_history)} messages")
            
            # Step 1: Rewrite top 5 last messages for context
            rewritten_context = self._rewrite_conversation_context(user_input, chat_history)
            
            # Step 2: Detect which tool to use based on intent
            detected_tool = self._detect_tool_intent(user_input, rewritten_context)
            
            if self.debug_mode:
                print(f"\n⚡ [DEBUG] Execution Route:")
                print(f"🔧 Selected tool: {detected_tool}")
                print(f"➡️  Routing to execution method...")
            
            # Step 3: Execute based on detected tool
            if detected_tool == "RAG":
                result = self._execute_rag_search(user_input, rewritten_context)
            elif detected_tool == "WEATHER":
                result = self._execute_weather_query(user_input, rewritten_context)
            elif detected_tool == "HOTEL":
                result = self._execute_hotel_booking(user_input, rewritten_context)
            elif detected_tool == "CAR":
                result = self._execute_car_booking(user_input, rewritten_context)
            elif detected_tool == "TRAVEL_PLAN":
                result = self._execute_travel_planning(user_input, rewritten_context, chat_history)
            else:
                # Default to general conversation
                result = self._execute_general_response(user_input, rewritten_context)
            
            # Step 4: Generate contextual suggestions
            if result.get('success', False) and result.get('response'):
                suggestions = self._generate_contextual_suggestions(
                    user_input, result, detected_tool, rewritten_context, chat_history
                )
                result['suggestions'] = suggestions
            
            if self.debug_mode:
                print(f"\n✅ [DEBUG] Execution Complete:")
                print(f"🎯 Success: {result.get('success', False)}")
                print(f"📄 Response length: {len(result.get('response', ''))}")
                print(f"💡 Suggestions generated: {len(result.get('suggestions', []))}")
                print(f"{'='*60}")
            
            return result
            
        except Exception as e:
            if self.debug_mode:
                print(f"\n❌ [ERROR] Travel planning failed: {str(e)}")
                import traceback
                traceback.print_exc()
            
            return {
                "success": False,
                "response": f"Xin lỗi, có lỗi xảy ra: {str(e)}",
                "error": str(e),
                "tool_used": "ERROR"
            }
    
    def _rewrite_conversation_context(self, user_input: str, chat_history: List) -> str:
        """
        Rewrite conversation context with enhanced location awareness
        """
        try:
            # Get configurable number of recent messages
            max_messages = self.config_manager.get_max_context_messages()
            recent_messages = chat_history[-max_messages:] if len(chat_history) > max_messages else chat_history
            
            if not recent_messages:
                return f"Người dùng hỏi: {user_input}"
            
            # Enhanced context prompt with location focus
            context_prompt = f"""
            Hãy phân tích cuộc hội thoại và tóm tắt ngữ cảnh, ĐẶC BIỆT chú ý các địa điểm được đề cập:
            
            Lịch sử hội thoại:
            """
            
            for role, content in recent_messages:
                if role == "user":
                    context_prompt += f"Người dùng: {content}\n"
                else:
                    # Only include first 100 chars of assistant response to avoid noise
                    short_content = content[:100] + "..." if len(content) > 100 else content
                    context_prompt += f"Trợ lý: {short_content}\n"
            
            context_prompt += f"""
            Câu hỏi hiện tại: {user_input}
            
            QUAN TRỌNG: Nếu có địa điểm nào được đề cập trong lịch sử hội thoại, 
            hãy ưu tiên ghi nhớ và đề cập trong tóm tắt ngữ cảnh.
            
            Tóm tắt ngữ cảnh (1-2 câu, bao gồm địa điểm nếu có):
            """
            
            # Get rewritten context
            rewritten = self.llm.predict(context_prompt)
            rewritten_clean = rewritten.strip()
            
            # Debug output
            if self.debug_mode:
                print(f"\n🔍 [DEBUG] Context Rewriting:")
                print(f"📝 User input: {user_input}")
                print(f"📚 Chat history: {len(recent_messages)} messages")
                print(f"🎯 Rewritten context: {rewritten_clean}")
                print(f"{'='*50}")
            
            return rewritten_clean
            
        except Exception as e:
            error_context = f"Người dùng hỏi: {user_input} (Lỗi xử lý ngữ cảnh: {str(e)})"
            if self.debug_mode:
                print(f"\n❌ [ERROR] Context rewriting failed: {str(e)}")
            return error_context
    
    def _detect_tool_intent(self, user_input: str, context: str) -> str:
        """
        Smart tool detection with enhanced context awareness
        """
        try:
            detection_prompt = f"""
            Phân tích ý định của người dùng dựa trên câu hỏi hiện tại và ngữ cảnh cuộc hội thoại:
            
            Ngữ cảnh hội thoại: {context}
            Câu hỏi hiện tại: {user_input}
            
            Các công cụ có sẵn:
            1. RAG - Tra cứu thông tin dịch vụ du lịch, danh lam thắng cảnh địa phương
            2. WEATHER - Kiểm tra thời tiết hiện tại hoặc dự đoán thời tiết tương lai
            3. HOTEL - Đặt phòng khách sạn
            4. CAR - Đặt xe/vận chuyển
            5. TRAVEL_PLAN - Lên kế hoạch du lịch chi tiết, lưu kế hoạch
            6. GENERAL - Trò chuyện chung, không cần công cụ đặc biệt
            
            Quy tắc phân loại (ĐẶC BIỆT chú ý ngữ cảnh):
            - RAG: Hỏi về địa điểm, danh lam, ẩm thực, hoạt động du lịch, "có gì", "làm gì"
            - WEATHER: Hỏi về thời tiết, nhiệt độ, trời mưa/nắng, dự báo (CHÚ Ý: nếu ngữ cảnh có địa điểm, thời tiết sẽ của địa điểm đó)
            - HOTEL: Yêu cầu đặt phòng, tìm khách sạn, booking accommodation
            - CAR: Yêu cầu đặt xe, thuê xe, book transportation, di chuyển
            - TRAVEL_PLAN: Lên kế hoạch du lịch, tạo itinerary, lưu kế hoạch, "lên kế hoạch", "tạo kế hoạch", "lưu kế hoạch"
            - GENERAL: Chào hỏi, cảm ơn, câu hỏi chung không liên quan du lịch
            
            QUAN TRỌNG: Nếu câu hỏi đơn giản như "thời tiết" nhưng ngữ cảnh có địa điểm, 
            vẫn chọn WEATHER vì người dùng muốn biết thời tiết của địa điểm đó.
            
            Trả lời CHÍNH XÁC một trong: RAG, WEATHER, HOTEL, CAR, TRAVEL_PLAN, GENERAL
            """
            
            detected = self.llm.predict(detection_prompt).strip().upper()
            
            # Debug output
            if self.debug_mode:
                print(f"\n🤖 [DEBUG] Tool Detection:")
                print(f"📝 User input: {user_input}")
                print(f"🎯 Context: {context}")
                print(f"🔧 Detected tool: {detected}")
            
            # Validate detection result
            valid_tools = ["RAG", "WEATHER", "HOTEL", "CAR", "TRAVEL_PLAN", "GENERAL"]
            if detected in valid_tools:
                if self.debug_mode:
                    print(f"✅ Valid tool selected: {detected}")
                return detected
            else:
                # Enhanced fallback with context awareness
                user_lower = user_input.lower()
                context_lower = context.lower()
                
                if self.debug_mode:
                    print(f"⚠️ Invalid tool '{detected}', using fallback logic")
                
                if any(keyword in user_lower for keyword in ["thời tiết", "weather", "mưa", "nắng", "nhiệt độ", "dự báo"]):
                    fallback = "WEATHER"
                elif any(keyword in user_lower for keyword in ["đặt phòng", "khách sạn", "hotel", "booking", "phòng"]):
                    fallback = "HOTEL"
                elif any(keyword in user_lower for keyword in ["đặt xe", "thuê xe", "car", "taxi", "di chuyển", "transport"]):
                    fallback = "CAR"
                elif any(keyword in user_lower for keyword in ["lên kế hoạch", "tạo kế hoạch", "kế hoạch du lịch", "itinerary", "lưu kế hoạch"]):
                    fallback = "TRAVEL_PLAN"
                elif any(keyword in user_lower for keyword in ["địa điểm", "danh lam", "thắng cảnh", "du lịch", "gợi ý", "tham quan", "có gì"]):
                    fallback = "RAG"
                else:
                    fallback = "GENERAL"
                
                if self.debug_mode:
                    print(f"🔄 Fallback tool: {fallback}")
                return fallback
                    
        except Exception as e:
            if self.debug_mode:
                print(f"\n❌ [ERROR] Tool detection failed: {str(e)}")
            # Final fallback to keyword-based detection
            user_lower = user_input.lower()
            if "thời tiết" in user_lower or "weather" in user_lower:
                return "WEATHER"
            elif "đặt phòng" in user_lower or "khách sạn" in user_lower:
                return "HOTEL"
            elif "đặt xe" in user_lower or "thuê xe" in user_lower:
                return "CAR"
            else:
                return "RAG"  # Default to RAG for travel queries
    
    def _execute_rag_search(self, user_input: str, context: str) -> Dict[str, Any]:
        """
        Execute RAG search for travel information
        """
        try:
            result = self.rag_system.query(user_input)
            
            if result.get('no_relevant_info') or result.get('answer') is None:
                return {
                    "success": True,
                    "response": None,
                    "sources": [],
                    "rag_used": True,
                    "no_relevant_info": True,
                    "query": user_input,
                    "tool_used": "RAG",
                    "context": context
                }
            
            return {
                "success": True,
                "response": result.get('answer'),
                "sources": result.get('sources', []),
                "rag_used": True,
                "tool_used": "RAG",
                "context": context
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": f"Lỗi tìm kiếm thông tin du lịch: {str(e)}",
                "error": str(e),
                "tool_used": "RAG"
            }
    
    def _execute_weather_query(self, user_input: str, context: str) -> Dict[str, Any]:
        """
        Execute weather query using LangChain function calling for location detection
        """
        try:
            # Use function calling for location detection
            location_result = self._detect_location_with_function_calling(
                user_query=user_input,
                query_type="weather",
                context=context
            )
            
            # Check if location was found
            if not location_result.get("location_found", False):
                # Return the function calling response (location request)
                return {
                    "success": True,
                    "response": location_result.get("response", "Tôi cần biết địa điểm để kiểm tra thời tiết."),
                    "sources": [],
                    "rag_used": False,
                    "tool_used": "WEATHER_LOCATION_REQUEST",
                    "weather_type": "location_missing",
                    "city": None,
                    "needs_location": True
                }
            
            # Extract the city from function calling result
            city = location_result.get("location")
            
            # Debug output
            if self.debug_mode:
                print(f"\n🌤️ [DEBUG] Weather Query:")
                print(f"📝 User input: {user_input}")
                print(f"🎯 Context: {context}")
                print(f"🏙️ Extracted city: {city}")
                
                # Detect if it's current weather or forecast
                is_forecast = self._detect_forecast_intent(user_input)
                print(f"⏰ Forecast request: {is_forecast}")
            else:
                is_forecast = self._detect_forecast_intent(user_input)
            
            if is_forecast:
                weather_info = self._get_weather_forecast(city)
            else:
                weather_info = self._get_current_weather(city)
            
            return {
                "success": True,
                "response": weather_info,
                "sources": [f"OpenWeatherMap API - {city}"],
                "rag_used": False,
                "tool_used": "WEATHER",
                "context": context,
                "weather_type": "forecast" if is_forecast else "current",
                "city": city
            }
            
        except Exception as e:
            if self.debug_mode:
                print(f"\n❌ [ERROR] Weather query failed: {str(e)}")
            return {
                "success": False,
                "response": f"Lỗi lấy thông tin thời tiết: {str(e)}",
                "error": str(e),
                "tool_used": "WEATHER"
            }
    
    def _execute_hotel_booking(self, user_input: str, context: str) -> Dict[str, Any]:
        """
        Execute enhanced LLM hotel booking with conversation state management
        """
        try:
            # Use the new LLM hotel booking system
            result = self.llm_hotel_booking.process(user_input, context)
            
            # Add sources info for compatibility
            result["sources"] = ["LLM Hotel Booking System"]
            result["rag_used"] = False
            
            return result
            
        except Exception as e:
            if self.debug_mode:
                print(f"🐛 [DEBUG] Hotel booking error: {str(e)}")
            
            return {
                "success": False,
                "response": f"Lỗi đặt khách sạn: {str(e)}",
                "error": str(e),
                "tool_used": "LLM_HOTEL_BOOKING"
            }
    
    def _execute_car_booking(self, user_input: str, context: str) -> Dict[str, Any]:
        """
        Execute simple car booking for demo
        """
        try:
            # Get conversation ID for maintaining state
            conversation_id = None
            try:
                import streamlit as st
                conversation_id = st.session_state.get('active_conversation_id', 'default')
            except:
                conversation_id = 'default'
            
            # Use LLM car booking (preferred)
            result = self.llm_car_booking.process(user_input)
            
            if self.debug_mode:
                print(f"\n🚗 [DEBUG] LLM Car Booking:")
                print(f"📝 User input: {user_input}")
                print(f"✅ Success: {result.get('success', False)}")
                print(f"🔧 Status: {result.get('status', 'unknown')}")
                print(f"🤖 Method: {result.get('extraction_method', 'unknown')}")
                print(f"🆕 New fields: {result.get('new_fields_detected', [])}")
            
            # Transform result to match expected format
            return {
                "success": result.get("success", True),
                "response": result.get("response", "Có lỗi xảy ra trong quá trình đặt xe."),
                "sources": ["Simple Car Booking Demo"],
                "rag_used": False,
                "tool_used": result.get("tool_used", "SIMPLE_CAR_BOOKING"),
                "booking_details": result.get("current_info", {}),
                "status": result.get("status", "unknown"),
                "missing_fields": result.get("missing_fields", []),
                "completion_rate": result.get("completion_rate", "0%"),
                "context": context
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": f"Lỗi đặt xe: {str(e)}",
                "error": str(e),
                "tool_used": "CAR"
            }
    
    def _execute_travel_planning(self, user_input: str, context: str, chat_history: List) -> Dict[str, Any]:
        """
        Execute simple LLM travel planning with conversation state management
        """
        try:
            # Use the new LLM travel planning system
            result = self.llm_travel_planning.process(user_input, context)
            
            # Add sources info for compatibility
            result["sources"] = ["LLM Travel Planning System"]
            result["rag_used"] = False
            
            return result
            
        except Exception as e:
            if self.debug_mode:
                print(f"🐛 [DEBUG] Travel planning error: {str(e)}")
            
            return {
                "success": False,
                "response": f"Lỗi lên kế hoạch du lịch: {str(e)}",
                "error": str(e),
                "tool_used": "LLM_TRAVEL_PLANNING"
            }
    
    def _execute_general_response(self, user_input: str, context: str) -> Dict[str, Any]:
        """
        Execute general conversation response with personalization
        """
        try:
            # Get personalized prompt based on agent configuration
            agent_name = self.config_manager.get_agent_name()
            personality = self.config_manager.get_personality()
            
            # Get user interests for personalization
            user_interests = self.config_manager.get_user_interests()
            interest_context = ""
            if user_interests:
                active_interests = [k for k, v in user_interests.items() if v]
                if active_interests:
                    interest_context = f"Người dùng quan tâm đến: {', '.join(active_interests)}. "
            
            prompt = f"""
            Bạn là {agent_name}, trợ lý du lịch với tính cách {personality}.
            
            {interest_context}
            
            Ngữ cảnh: {context}
            Câu hỏi: {user_input}
            
            Hãy trả lời một cách tự nhiên và hữu ích theo tính cách của bạn. 
            Nếu liên quan đến du lịch, hãy gợi ý người dùng hỏi cụ thể hơn về địa điểm, thời tiết, hoặc đặt dịch vụ.
            Nếu biết sở thích của người dùng, hãy đưa ra gợi ý phù hợp.
            
            Trả lời bằng tiếng Việt:
            """
            
            base_response = self.llm.predict(prompt)
            
            # Apply personalization
            personalized_response = self.config_manager.personalize_response(
                base_response, 
                {"tool_used": "GENERAL"}
            )
            
            return {
                "success": True,
                "response": personalized_response,
                "sources": [],
                "rag_used": False,
                "tool_used": "GENERAL",
                "context": context
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": f"Lỗi xử lý câu hỏi: {str(e)}",
                "error": str(e),
                "tool_used": "GENERAL"
            }
    
    # Helper methods
    def _extract_city_from_query(self, query: str) -> Optional[str]:
        """Extract city name from weather query - legacy method"""
        # Simple extraction - can be enhanced with NER
        cities = ["hà nội", "hồ chí minh", "đà nẵng", "nha trang", "huế", "hội an", "sapa", "đà lạt", "phú quốc", "cần thơ"]
        query_lower = query.lower()
        
        for city in cities:
            if city in query_lower:
                return city.title()
        
        return None  # No default city - require location to be specified
    
    def _extract_city_from_query_with_context(self, query: str, context: str, conversation_id: str = None) -> Optional[str]:
        """Extract city name from query with context awareness and conversation history"""
        # Separate provinces and cities to prioritize properly
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
            "sapa", "đà lạt", "phú quốc", "cần thơ", "vũng tầu", "phan thiết"
        ]
        
        # Combine all locations for comprehensive search
        all_locations = provinces + cities
        
        if self.debug_mode:
            print(f"\n🔍 [DEBUG] Enhanced City Extraction:")
            print(f"📝 Query: {query}")
            print(f"🎯 Context: {context}")
            print(f"🆔 Conversation ID: {conversation_id}")
        
        # Strategy: Find all matching locations, then prioritize
        found_locations = []
        
        # Check current query first (highest priority)
        query_lower = query.lower()
        for location in all_locations:
            if location in query_lower:
                found_locations.append(("query", location))
                if self.debug_mode:
                    print(f"🎯 Found in query: {location}")
        
        # Then check context 
        context_lower = context.lower()
        for location in all_locations:
            if location in context_lower:
                found_locations.append(("context", location))
                if self.debug_mode:
                    print(f"📚 Found in context: {location}")
        
        # If no location found in query/context, check conversation history
        if not found_locations and conversation_id:
            try:
                from .config_manager import ConfigManager
                config_manager = ConfigManager()
                conversation_location = config_manager.get_latest_conversation_location(conversation_id)
                if conversation_location:
                    found_locations.append(("conversation", conversation_location.lower()))
                    if self.debug_mode:
                        print(f"💬 Found in conversation history: {conversation_location}")
            except Exception as e:
                if self.debug_mode:
                    print(f"⚠️ Could not check conversation history: {str(e)}")
        
        if found_locations:
            # Prioritization logic:
            # 1. Direct query locations first
            # 2. Among context locations, prefer provinces over cities  
            # 3. Conversation history locations (fallback)
            # 4. Use the most specific match
            
            query_locations = [loc for source, loc in found_locations if source == "query"]
            context_locations = [loc for source, loc in found_locations if source == "context"]
            conversation_locations = [loc for source, loc in found_locations if source == "conversation"]
            
            if query_locations:
                # If found in query, use that
                selected = query_locations[0]
                if self.debug_mode:
                    print(f"🏙️ Selected from query: {selected}")
            elif context_locations:
                # If found in context, prefer provinces
                context_provinces = [loc for loc in context_locations if loc in provinces]
                if context_provinces:
                    selected = context_provinces[0]  # First province found
                    if self.debug_mode:
                        print(f"🏙️ Selected province from context: {selected}")
                else:
                    selected = context_locations[0]  # First city found
                    if self.debug_mode:
                        print(f"🏙️ Selected city from context: {selected}")
            elif conversation_locations:
                # Use conversation history location as fallback
                selected = conversation_locations[0]
                if self.debug_mode:
                    print(f"🏙️ Selected from conversation history: {selected}")
            else:
                selected = None  # No fallback
            
            return selected.title() if selected else None
        
        # No default fallback - return None when location not found
        if self.debug_mode:
            print(f"🏙️ No location found in query or context")
        return None
    
    def _detect_forecast_intent(self, query: str) -> bool:
        """Detect if user wants weather forecast vs current weather"""
        forecast_keywords = ["mai", "ngày mai", "tuần sau", "dự báo", "dự đoán", "tương lai", "sắp tới"]
        query_lower = query.lower()
        
        return any(keyword in query_lower for keyword in forecast_keywords)
    
    def _get_current_weather(self, city: str) -> str:
        """Get current weather"""
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.weather_api_key}&units=metric&lang=vi"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return f"Không tìm thấy thông tin thời tiết hiện tại cho {city}"
            
            data = response.json()
            weather_info = (
                f"🌤️ Thời tiết hiện tại tại {city}:\n"
                f"🌡️ Nhiệt độ: {data['main']['temp']}°C\n"
                f"☁️ Trời: {data['weather'][0]['description']}\n"
                f"💨 Độ ẩm: {data['main']['humidity']}%\n"
                f"🌬️ Tốc độ gió: {data['wind']['speed']} m/s"
            )
            return weather_info
            
        except Exception as e:
            return f"Lỗi lấy thông tin thời tiết hiện tại: {str(e)}"
    
    def _get_weather_forecast(self, city: str) -> str:
        """Get weather forecast"""
        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={self.weather_api_key}&units=metric&lang=vi"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return f"Không tìm thấy dự báo thời tiết cho {city}"
            
            data = response.json()
            # Get next 24 hours (8 forecasts * 3 hours each)
            forecasts = data['list'][:8]
            
            weather_info = f"🔮 Dự báo thời tiết {city} (24h tới):\n\n"
            
            for i, forecast in enumerate(forecasts):
                time = forecast['dt_txt'].split(' ')[1][:5]  # Get HH:MM
                temp = forecast['main']['temp']
                desc = forecast['weather'][0]['description']
                weather_info += f"⏰ {time}: {temp}°C - {desc}\n"
            
            return weather_info
            
        except Exception as e:
            return f"Lỗi lấy dự báo thời tiết: {str(e)}"
    
    def _extract_hotel_booking_details(self, query: str, context: str) -> Dict:
        """Extract hotel booking details from query with enhanced extraction"""
        details = {
            "customer_name": self._extract_customer_name(query, context),
            "customer_phone": self._extract_phone_number(query, context),
            "customer_email": self._extract_email(query, context),
            "hotel_name": self._extract_hotel_name(query, context),
            "location": self._extract_location_for_booking(query, "hotel", context),
            "check_in_date": self._extract_date(query, context),
            "check_out_date": None,  # Will be calculated from nights
            "nights": self._extract_nights(query, context),
            "guests": self._extract_guest_count(query, context),
            "rooms": self._extract_room_count(query, context),
            "room_type": self._extract_room_type(query, context),
            "special_requests": self._extract_special_requests(query, context),
            "query": query
        }
        
        # Calculate check-out date if check-in and nights are available
        if details["check_in_date"] and details["nights"]:
            try:
                from datetime import datetime, timedelta
                check_in = datetime.strptime(details["check_in_date"], "%Y-%m-%d")
                check_out = check_in + timedelta(days=int(details["nights"]))
                details["check_out_date"] = check_out.strftime("%Y-%m-%d")
            except:
                pass
        
        return details
    
    def _extract_car_booking_details(self, query: str, context: str) -> Dict:
        """Extract car booking details from query with enhanced extraction"""
        return {
            "customer_name": self._extract_customer_name(query, context),
            "customer_phone": self._extract_phone_number(query, context),
            "pickup_location": self._extract_pickup_location(query, context),
            "destination": self._extract_destination(query, context),
            "pickup_time": self._extract_pickup_time(query, context),
            "car_type": self._extract_car_type(query, context),
            "seats": self._extract_seat_count(query, context),
            "notes": self._extract_special_requests(query, context),
            "query": query
        }
    
    def _mock_hotel_booking(self, details: Dict) -> str:
        """Mock hotel booking"""
        confirmation = f"HOTEL-{details['city'][:3].upper()}-{details['date'].replace('-', '')}"
        
        return f"""✅ Đặt phòng khách sạn thành công!
        
🏨 Khách sạn: AI Grand Hotel {details['city']}
📍 Địa điểm: {details['city']}
📅 Ngày nhận phòng: {details['date']}
🌙 Số đêm: {details['nights']}
👥 Số khách: {details['guests']}
💰 Giá: ${details['nights'] * 120}
🎫 Mã xác nhận: {confirmation}

📞 Liên hệ: +84 123 456 789
📧 Email: booking@aigrandhotel.com"""
    
    def _mock_car_booking(self, details: Dict) -> str:
        """Mock car booking"""
        confirmation = f"CAR-{details['pickup_city'][:3].upper()}-{details['date'].replace('-', '')}"
        
        return f"""✅ Đặt xe thành công!
        
🚗 Loại xe: Toyota Vios (4 chỗ)
📍 Điểm đón: {details['pickup_city']}
🎯 Điểm đến: {details['destination']}
📅 Ngày: {details['date']}
⏰ Giờ: {details['time']}
💰 Giá: $50
🎫 Mã xác nhận: {confirmation}

📞 Tài xế: +84 987 654 321
🚗 Biển số: 30A-123.45"""

    def get_general_knowledge_response(self, query: str) -> Dict[str, Any]:
        """
        Get response using general LLM knowledge (no RAG)
        """
        try:
            prompt = f"""
            Bạn là trợ lý du lịch thông minh. Khách hàng hỏi về: "{query}"
            
            Tôi không tìm thấy thông tin cụ thể trong cơ sở dữ liệu của mình về câu hỏi này.
            
            Hãy trả lời dựa trên kiến thức chung của bạn về du lịch Việt Nam:
            - Đưa ra thông tin hữu ích và chính xác
            - Giữ giọng điệu thân thiện và chuyên nghiệp
            - Trả lời bằng tiếng Việt
            - Nếu không chắc chắn, hãy khuyên khách tìm hiểu thêm từ nguồn chính thức
            
            Trả lời:
            """
            
            response = self.llm.predict(prompt)
            
            return {
                "success": True,
                "response": response,
                "sources": [],
                "rag_used": False,
                "general_knowledge": True
            }
        except Exception as e:
            return {
                "success": False,
                "response": f"Xin lỗi, có lỗi xảy ra: {str(e)}",
                "error": str(e)
            }
    
    def get_rag_only_response(self, query: str) -> Dict[str, Any]:
        """
        Get response using only RAG system (no tools)
        """
        try:
            result = self.rag_system.query(query)
            return {
                "success": True,
                "response": result['answer'],
                "sources": len(result.get('source_documents', [])),
                "mode": "RAG Only"
            }
        except Exception as e:
            return {
                "success": False,
                "response": f"Lỗi RAG: {str(e)}",
                "error": str(e)
            }
    
    # Enhanced extraction helper functions
    def _extract_customer_name(self, query: str, context: str) -> str:
        """Extract customer name from query or context"""
        import re
        
        # Look for name patterns like "Tên tôi là X", "Tôi tên X", "Tôi là X"
        patterns = [
            r'(?:tên tôi là|tôi tên|tôi là|my name is)\s+([A-Za-zÀ-ỹ\s]+)',
            r'tên:\s*([A-Za-zÀ-ỹ\s]+)',
            r'họ tên:\s*([A-Za-zÀ-ỹ\s]+)'
        ]
        
        text = (query + " " + context).lower()
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                if len(name) > 1:
                    return name
        
        return ""  # Return empty if not found
    
    def _extract_phone_number(self, query: str, context: str) -> str:
        """Extract phone number from query or context"""
        import re
        
        text = query + " " + context
        
        # Vietnamese phone number patterns
        patterns = [
            r'(?:sđt|số điện thoại|phone|điện thoại)[:=\s]*([+84|84|0]?[3-9]\d{8,9})',
            r'([+84|84|0]?[3-9]\d{8,9})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean up the phone number
                phone = re.sub(r'[^\d+]', '', match)
                if len(phone) >= 9:
                    return phone
        
        return ""
    
    def _extract_email(self, query: str, context: str) -> str:
        """Extract email from query or context"""
        import re
        
        text = query + " " + context
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        match = re.search(pattern, text)
        return match.group() if match else ""
    
    def _extract_hotel_name(self, query: str, context: str) -> str:
        """Extract hotel name from query or context"""
        import re
        
        text = (query + " " + context).lower()
        
        # Look for hotel name patterns
        patterns = [
            r'khách sạn\s+([A-Za-zÀ-ỹ\s]+)',
            r'hotel\s+([A-Za-z\s]+)',
            r'(?:tại|ở)\s+([A-Za-zÀ-ỹ\s]*(?:hotel|resort|inn)[A-Za-zÀ-ỹ\s]*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                hotel = match.group(1).strip().title()
                if len(hotel) > 2:
                    return hotel
        
        return ""  # Will be requested later
    
    def _extract_date(self, query: str, context: str) -> str:
        """Extract check-in date from query"""
        import re
        from datetime import datetime, timedelta
        
        text = query + " " + context
        
        # Look for date patterns
        patterns = [
            r'ngày\s+(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) == 3:
                        day, month, year = match.groups()
                        date_obj = datetime(int(year), int(month), int(day))
                        return date_obj.strftime("%Y-%m-%d")
                    elif len(match.groups()) == 2:
                        day, month = match.groups()
                        year = datetime.now().year
                        date_obj = datetime(year, int(month), int(day))
                        return date_obj.strftime("%Y-%m-%d")
                except:
                    continue
        
        # Look for relative dates
        if any(word in text.lower() for word in ["hôm nay", "today"]):
            return datetime.now().strftime("%Y-%m-%d")
        elif any(word in text.lower() for word in ["ngày mai", "tomorrow"]):
            return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        return ""
    
    def _extract_nights(self, query: str, context: str) -> int:
        """Extract number of nights from query"""
        import re
        
        text = query + " " + context
        
        patterns = [
            r'(\d+)\s*đêm',
            r'(\d+)\s*nights?',
            r'(\d+)\s*ngày.*?(\d+)\s*đêm',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        
        return 1  # Default to 1 night
    
    def _extract_guest_count(self, query: str, context: str) -> int:
        """Extract number of guests from query"""
        import re
        
        text = query + " " + context
        
        patterns = [
            r'(\d+)\s*(?:người|khách|guests?)',
            r'(?:cho|for)\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        
        return 2  # Default to 2 guests
    
    def _extract_room_count(self, query: str, context: str) -> int:
        """Extract number of rooms from query"""
        import re
        
        text = query + " " + context
        
        patterns = [
            r'(\d+)\s*phòng',
            r'(\d+)\s*rooms?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        
        return 1  # Default to 1 room
    
    def _extract_room_type(self, query: str, context: str) -> str:
        """Extract room type from query"""
        text = (query + " " + context).lower()
        
        room_types = {
            "standard": ["standard", "tiêu chuẩn"],
            "deluxe": ["deluxe", "cao cấp"],
            "suite": ["suite", "hạng sang"],
            "family": ["family", "gia đình"],
            "single": ["single", "đơn"],
            "double": ["double", "đôi"],
            "twin": ["twin", "sinh đôi"]
        }
        
        for room_type, keywords in room_types.items():
            if any(keyword in text for keyword in keywords):
                return room_type
        
        return "standard"
    
    def _extract_pickup_location(self, query: str, context: str) -> str:
        """Extract pickup location from query"""
        import re
        
        text = query + " " + context
        
        patterns = [
            r'(?:đón tại|pickup at|from)\s+([A-Za-zÀ-ỹ\s,]+)',
            r'từ\s+([A-Za-zÀ-ỹ\s,]+)\s+(?:đến|to)',
            r'điểm đón:\s*([A-Za-zÀ-ỹ\s,]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) > 2:
                    return location
        
        # Try to extract from context using function calling
        location = self._extract_location_for_booking(query, "car", context)
        if location:
            return f"Sân bay {location}"  # Default to airport
        
        return ""
    
    def _extract_destination(self, query: str, context: str) -> str:
        """Extract destination from query"""
        import re
        
        text = query + " " + context
        
        patterns = [
            r'(?:đến|to|tới)\s+([A-Za-zÀ-ỹ\s,]+)',
            r'điểm đến:\s*([A-Za-zÀ-ỹ\s,]+)',
            r'(?:về|return to)\s+([A-Za-zÀ-ỹ\s,]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                destination = match.group(1).strip()
                if len(destination) > 2:
                    return destination
        
        # Try to extract using function calling as fallback
        location = self._extract_location_for_booking(query, "car", context)
        if location:
            return location
        
        return ""
    
    def _extract_pickup_time(self, query: str, context: str) -> str:
        """Extract pickup time from query"""
        import re
        
        text = query + " " + context
        
        patterns = [
            r'lúc\s+(\d{1,2}):(\d{2})',
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})\s*giờ\s*(\d{2})?',
            r'(\d{1,2})h(\d{2})?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    hour = int(match.group(1))
                    minute = int(match.group(2)) if match.group(2) else 0
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return f"{hour:02d}:{minute:02d}"
                except:
                    continue
        
        return ""
    
    def _extract_car_type(self, query: str, context: str) -> str:
        """Extract car type from query"""
        text = (query + " " + context).lower()
        
        car_types = {
            "4 chỗ": ["4 chỗ", "sedan", "4 seats"],
            "7 chỗ": ["7 chỗ", "suv", "7 seats"],
            "16 chỗ": ["16 chỗ", "minibus", "16 seats"],
            "taxi": ["taxi"],
            "grab": ["grab"],
            "luxury": ["luxury", "sang trọng"],
        }
        
        for car_type, keywords in car_types.items():
            if any(keyword in text for keyword in keywords):
                return car_type
        
        return "4 chỗ"  # Default
    
    def _extract_seat_count(self, query: str, context: str) -> int:
        """Extract seat count from query"""
        import re
        
        text = query + " " + context
        
        patterns = [
            r'(\d+)\s*chỗ',
            r'(\d+)\s*seats?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        
        return 4  # Default to 4 seats
    
    def _extract_special_requests(self, query: str, context: str) -> str:
        """Extract special requests from query"""
        import re
        
        text = query + " " + context
        
        patterns = [
            r'(?:yêu cầu|requests?|notes?|ghi chú)[:=\s]*(.+)',
            r'(?:đặc biệt|special)[:=\s]*(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                request = match.group(1).strip()
                if len(request) > 5:
                    return request
        
        return ""
    
    # Validation helper functions
    def _request_missing_hotel_info(self, missing_fields: list, current_details: dict) -> str:
        """Generate message requesting missing hotel booking information"""
        
        field_prompts = {
            'customer_name': "👤 Tên khách hàng",
            'customer_phone': "📞 Số điện thoại liên hệ",
            'hotel_name': "🏨 Tên khách sạn mong muốn",
            'location': "📍 Địa điểm (Ví dụ: Hà Nội, Đà Nẵng, Hồ Chí Minh...)",
            'check_in_date': "📅 Ngày nhận phòng (dd/mm/yyyy)",
            'nights': "🌙 Số đêm lưu trú"
        }
        
        current_info = []
        for key, value in current_details.items():
            if value and key in field_prompts:
                current_info.append(f"✅ {field_prompts[key]}: {value}")
        
        missing_info = []
        for field in missing_fields:
            if field in field_prompts:
                missing_info.append(f"❓ {field_prompts[field]}")
        
        message = "🏨 **Thông tin đặt phòng chưa đủ**\n\n"
        
        if current_info:
            message += "**Thông tin đã có:**\n" + "\n".join(current_info) + "\n\n"
        
        message += "**Cần bổ sung:**\n" + "\n".join(missing_info) + "\n\n"
        message += "💡 Vui lòng cung cấp thông tin còn thiếu để tôi có thể đặt phòng cho bạn."
        
        return message
    
    def _request_missing_car_info(self, missing_fields: list, current_details: dict) -> str:
        """Generate message requesting missing car booking information"""
        
        field_prompts = {
            'customer_name': "👤 Tên khách hàng",
            'customer_phone': "📞 Số điện thoại liên hệ",
            'pickup_location': "📍 Điểm đón",
            'destination': "🎯 Điểm đến",
            'pickup_time': "🕐 Thời gian đón (hh:mm)",
            'car_type': "🚗 Loại xe (4 chỗ, 7 chỗ, 16 chỗ)"
        }
        
        current_info = []
        for key, value in current_details.items():
            if value and key in field_prompts:
                current_info.append(f"✅ {field_prompts[key]}: {value}")
        
        missing_info = []
        for field in missing_fields:
            if field in field_prompts:
                missing_info.append(f"❓ {field_prompts[field]}")
        
        message = "🚗 **Thông tin đặt xe chưa đủ**\n\n"
        
        if current_info:
            message += "**Thông tin đã có:**\n" + "\n".join(current_info) + "\n\n"
        
        message += "**Cần bổ sung:**\n" + "\n".join(missing_info) + "\n\n"
        message += "💡 Vui lòng cung cấp thông tin còn thiếu để tôi có thể đặt xe cho bạn."
        
        return message
    
    # Confirmation helper functions
    def _generate_hotel_booking_confirmation(self, details: dict) -> str:
        """Generate hotel booking confirmation message"""
        
        message = f"""🏨 **XÁC NHẬN THÔNG TIN ĐẶT PHÒNG**

👤 **Khách hàng:** {details.get('customer_name', 'N/A')}
📞 **Điện thoại:** {details.get('customer_phone', 'N/A')}
📧 **Email:** {details.get('customer_email', 'Không có')}

🏨 **Khách sạn:** {details.get('hotel_name', 'N/A')}
📍 **Địa điểm:** {details.get('location', 'N/A')}
🛏️ **Loại phòng:** {details.get('room_type', 'Standard')}
🚪 **Số phòng:** {details.get('rooms', 1)}

📅 **Nhận phòng:** {details.get('check_in_date', 'N/A')}
📅 **Trả phòng:** {details.get('check_out_date', 'N/A')}
🌙 **Số đêm:** {details.get('nights', 'N/A')}
👥 **Số khách:** {details.get('guests', 'N/A')}

"""
        
        if details.get('special_requests'):
            message += f"📝 **Yêu cầu đặc biệt:** {details['special_requests']}\n\n"
        
        message += """❓ **Thông tin trên có chính xác không?**

Trả lời "**Có**" hoặc "**Xác nhận**" để tiến hành đặt phòng.
Trả lời "**Không**" hoặc "**Sửa**" để điều chỉnh thông tin."""
        
        return message
    
    def _generate_car_booking_confirmation(self, details: dict) -> str:
        """Generate car booking confirmation message"""
        
        message = f"""🚗 **XÁC NHẬN THÔNG TIN ĐẶT XE**

👤 **Khách hàng:** {details.get('customer_name', 'N/A')}
📞 **Điện thoại:** {details.get('customer_phone', 'N/A')}

📍 **Điểm đón:** {details.get('pickup_location', 'N/A')}
🎯 **Điểm đến:** {details.get('destination', 'N/A')}
🕐 **Thời gian đón:** {details.get('pickup_time', 'N/A')}

🚗 **Loại xe:** {details.get('car_type', 'N/A')}
💺 **Số ghế:** {details.get('seats', 'N/A')}

"""
        
        if details.get('notes'):
            message += f"📝 **Ghi chú:** {details['notes']}\n\n"
        
        message += """❓ **Thông tin trên có chính xác không?**

Trả lời "**Có**" hoặc "**Xác nhận**" để tiến hành đặt xe.
Trả lời "**Không**" hoặc "**Sửa**" để điều chỉnh thông tin."""
        
        return message
    
    # Travel Planning helper methods
    def _extract_travel_plan_info(self, user_input: str, context: str, chat_history: List) -> Dict[str, Any]:
        """
        Extract travel plan information from user input, context, and chat history
        Based on the JSON schema provided by the user
        """
        travel_info = {}
        
        # Extract destination information
        travel_info['destination'] = self._extract_travel_destination(user_input, context, chat_history)
        
        # Extract dates and duration
        travel_info['dates'] = self._extract_travel_dates(user_input, context, chat_history)
        travel_info['duration'] = self._extract_travel_duration(user_input, context, chat_history)
        
        # Extract participants
        travel_info['participants'] = self._extract_travel_participants(user_input, context, chat_history)
        
        # Extract budget
        travel_info['budget'] = self._extract_travel_budget(user_input, context, chat_history)
        
        # Extract requirements (visa, health, etc.)
        travel_info['visa_requirements'] = self._extract_visa_requirements(user_input, context, chat_history)
        travel_info['health_requirements'] = self._extract_health_requirements(user_input, context, chat_history)
        
        # Extract optional preferences
        travel_info['travel_style'] = self._extract_travel_style(user_input, context, chat_history)
        travel_info['activities'] = self._extract_preferred_activities(user_input, context, chat_history)
        travel_info['accommodations'] = self._extract_accommodation_preferences(user_input, context, chat_history)
        travel_info['transportation'] = self._extract_transportation_preferences(user_input, context, chat_history)
        travel_info['meals'] = self._extract_meal_preferences(user_input, context, chat_history)
        travel_info['interests'] = self._extract_interests_from_config()
        
        return travel_info
    
    def _extract_travel_destination(self, user_input: str, context: str, chat_history: List) -> Dict[str, Any]:
        """Extract destination information"""
        import re
        
        text = user_input + " " + context
        
        # Look for destination patterns
        patterns = [
            r'(?:đến|tới|du lịch|ghé)\s+([A-Za-zÀ-ỹ\s,]+)',
            r'điểm đến:\s*([A-Za-zÀ-ỹ\s,]+)',
            r'(?:ở|tại)\s+([A-Za-zÀ-ỹ\s,]+)'
        ]
        
        destination_info = {}
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) > 2:
                    destination_info['primary'] = location
                    destination_info['country'] = self._determine_country(location)
                    destination_info['region'] = self._determine_region(location)
                    break
        
        return destination_info if destination_info else None
    
    def _extract_travel_dates(self, user_input: str, context: str, chat_history: List) -> Dict[str, Any]:
        """Extract travel dates"""
        import re
        from datetime import datetime, timedelta
        
        text = user_input + " " + context
        dates_info = {}
        
        # Look for date patterns
        patterns = [
            r'ngày\s+(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) == 3:
                        day, month, year = match.groups()
                        start_date = datetime(int(year), int(month), int(day))
                        dates_info['start_date'] = start_date.strftime("%Y-%m-%d")
                        dates_info['flexible'] = False
                        break
                    elif len(match.groups()) == 2:
                        day, month = match.groups()
                        year = datetime.now().year
                        date_obj = datetime(year, int(month), int(day))
                        dates_info['start_date'] = date_obj.strftime("%Y-%m-%d")
                        break
                except:
                    continue
        
        # Look for relative dates
        if not dates_info and any(word in text.lower() for word in ["tuần sau", "tháng sau", "sắp tới"]):
            dates_info['flexible'] = True
            dates_info['timeframe'] = "tương lai gần"
        
        return dates_info if dates_info else None
    
    def _extract_travel_duration(self, user_input: str, context: str, chat_history: List) -> Dict[str, Any]:
        """Extract travel duration"""
        import re
        
        text = user_input + " " + context
        duration_info = {}
        
        patterns = [
            r'(\d+)\s*ngày',
            r'(\d+)\s*tuần',
            r'(\d+)\s*tháng',
            r'(\d+)\s*days?',
            r'(\d+)\s*weeks?',
            r'(\d+)\s*months?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    number = int(match.group(1))
                    if 'ngày' in match.group() or 'days' in match.group():
                        duration_info['total_days'] = number
                        duration_info['unit'] = 'days'
                    elif 'tuần' in match.group() or 'weeks' in match.group():
                        duration_info['total_days'] = number * 7
                        duration_info['unit'] = 'weeks'
                    elif 'tháng' in match.group() or 'months' in match.group():
                        duration_info['total_days'] = number * 30
                        duration_info['unit'] = 'months'
                    break
                except:
                    continue
        
        return duration_info if duration_info else None
    
    def _extract_travel_participants(self, user_input: str, context: str, chat_history: List) -> Dict[str, Any]:
        """Extract travel participants information"""
        import re
        
        text = user_input + " " + context
        participants_info = {
            'adults': 1,  # Default
            'children': 0,
            'total': 1
        }
        
        # Look for participant patterns
        patterns = [
            r'(\d+)\s*(?:người|khách|people)',
            r'(?:gia đình|family)\s*(\d+)\s*(?:người|members)',
            r'(\d+)\s*(?:adults?|người lớn)',
            r'(\d+)\s*(?:children|trẻ em)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    number = int(match.group(1))
                    if 'adults' in match.group() or 'người lớn' in match.group():
                        participants_info['adults'] = number
                    elif 'children' in match.group() or 'trẻ em' in match.group():
                        participants_info['children'] = number
                    elif 'gia đình' in match.group() or 'family' in match.group():
                        participants_info['total'] = number
                        participants_info['type'] = 'family'
                    else:
                        participants_info['total'] = number
                    break
                except:
                    continue
        
        participants_info['total'] = participants_info['adults'] + participants_info['children']
        return participants_info
    
    def _extract_travel_budget(self, user_input: str, context: str, chat_history: List) -> Dict[str, Any]:
        """Extract budget information"""
        import re
        
        text = user_input + " " + context
        budget_info = {}
        
        # Look for budget patterns
        patterns = [
            r'(?:ngân sách|budget)\s*[:=]\s*([0-9,]+)\s*(?:đồng|vnd|usd|\$)',
            r'([0-9,]+)\s*(?:triệu|million)',
            r'([0-9,]+)\s*(?:nghìn|thousand)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = int(amount_str)
                    
                    if 'triệu' in match.group() or 'million' in match.group():
                        amount *= 1000000
                        budget_info['currency'] = 'VND'
                    elif 'nghìn' in match.group() or 'thousand' in match.group():
                        amount *= 1000
                        budget_info['currency'] = 'VND'
                    elif 'usd' in match.group() or '$' in match.group():
                        budget_info['currency'] = 'USD'
                    else:
                        budget_info['currency'] = 'VND'
                    
                    budget_info['total_amount'] = amount
                    budget_info['per_person'] = amount // max(1, self._get_participant_count(user_input, context))
                    break
                except:
                    continue
        
        # Check budget level from user config
        if not budget_info:
            budget_level = self.config_manager.get_user_budget_range('accommodation')
            if budget_level:
                budget_info['level'] = budget_level
                budget_info['flexible'] = True
        
        return budget_info if budget_info else None
    
    def _extract_visa_requirements(self, user_input: str, context: str, chat_history: List) -> Dict[str, Any]:
        """Extract visa requirements"""
        text = (user_input + " " + context).lower()
        
        visa_info = {}
        
        if any(word in text for word in ['visa', 'thị thực', 'hộ chiếu', 'passport']):
            visa_info['needs_visa'] = True
            
            if any(word in text for word in ['có sẵn', 'đã có', 'ready']):
                visa_info['status'] = 'ready'
            elif any(word in text for word in ['cần xin', 'chưa có', 'need to apply']):
                visa_info['status'] = 'need_to_apply'
            else:
                visa_info['status'] = 'unknown'
        
        return visa_info if visa_info else None
    
    def _extract_health_requirements(self, user_input: str, context: str, chat_history: List) -> Dict[str, Any]:
        """Extract health requirements"""
        text = (user_input + " " + context).lower()
        
        health_info = {}
        
        if any(word in text for word in ['vaccine', 'vắc xin', 'tiêm chủng', 'y tế', 'health']):
            health_info['needs_vaccination'] = True
            
            if any(word in text for word in ['đã tiêm', 'completed', 'done']):
                health_info['vaccination_status'] = 'completed'
            else:
                health_info['vaccination_status'] = 'needed'
        
        # Check for special health needs
        if any(word in text for word in ['dị ứng', 'allergy', 'bệnh', 'illness']):
            health_info['special_needs'] = True
        
        return health_info if health_info else None
    
    def _extract_travel_style(self, user_input: str, context: str, chat_history: List) -> str:
        """Extract travel style from user input or config"""
        text = (user_input + " " + context).lower()
        
        style_keywords = {
            'budget': ['tiết kiệm', 'rẻ', 'budget', 'cheap'],
            'luxury': ['sang trọng', 'cao cấp', 'luxury', 'premium'],
            'adventure': ['phiêu lưu', 'adventure', 'thám hiểm'],
            'cultural': ['văn hóa', 'culture', 'lịch sử'],
            'relaxation': ['thư giãn', 'nghỉ dưỡng', 'relaxation'],
            'family': ['gia đình', 'family']
        }
        
        for style, keywords in style_keywords.items():
            if any(keyword in text for keyword in keywords):
                return style
        
        # Get from user config
        user_interests = self.config_manager.get_user_interests()
        if user_interests:
            if user_interests.get('adventure'):
                return 'adventure'
            elif user_interests.get('culture'):
                return 'cultural'
            elif user_interests.get('beach'):
                return 'relaxation'
        
        return 'general'
    
    def _extract_preferred_activities(self, user_input: str, context: str, chat_history: List) -> List[str]:
        """Extract preferred activities"""
        text = (user_input + " " + context).lower()
        activities = []
        
        activity_keywords = {
            'sightseeing': ['tham quan', 'ngắm cảnh', 'sightseeing'],
            'food_tour': ['ẩm thực', 'food', 'đặc sản'],
            'shopping': ['mua sắm', 'shopping'],
            'photography': ['chụp ảnh', 'photography'],
            'outdoor': ['ngoài trời', 'outdoor', 'trekking'],
            'beach': ['biển', 'beach', 'bơi lội'],
            'cultural': ['văn hóa', 'cultural', 'bảo tàng', 'museum'],
            'nightlife': ['đêm', 'nightlife', 'bar']
        }
        
        for activity, keywords in activity_keywords.items():
            if any(keyword in text for keyword in keywords):
                activities.append(activity)
        
        # Get from user config
        user_interests = self.config_manager.get_user_interests()
        if user_interests:
            for interest, enabled in user_interests.items():
                if enabled and interest not in activities:
                    activities.append(interest)
        
        return activities
    
    def _extract_accommodation_preferences(self, user_input: str, context: str, chat_history: List) -> Dict[str, Any]:
        """Extract accommodation preferences"""
        text = (user_input + " " + context).lower()
        accommodation_info = {}
        
        if any(word in text for word in ['khách sạn', 'hotel']):
            accommodation_info['type'] = 'hotel'
        elif any(word in text for word in ['resort']):
            accommodation_info['type'] = 'resort'
        elif any(word in text for word in ['homestay']):
            accommodation_info['type'] = 'homestay'
        elif any(word in text for word in ['hostel']):
            accommodation_info['type'] = 'hostel'
        
        # Get budget level from user config
        budget_level = self.config_manager.get_user_budget_range('accommodation')
        if budget_level:
            accommodation_info['budget_level'] = budget_level
        
        return accommodation_info if accommodation_info else None
    
    def _extract_transportation_preferences(self, user_input: str, context: str, chat_history: List) -> Dict[str, Any]:
        """Extract transportation preferences"""
        text = (user_input + " " + context).lower()
        transport_info = {}
        
        if any(word in text for word in ['máy bay', 'flight', 'fly']):
            transport_info['primary'] = 'flight'
        elif any(word in text for word in ['tàu', 'train']):
            transport_info['primary'] = 'train'
        elif any(word in text for word in ['xe buýt', 'bus']):
            transport_info['primary'] = 'bus'
        elif any(word in text for word in ['xe hơi', 'car', 'ô tô']):
            transport_info['primary'] = 'car'
        
        return transport_info if transport_info else None
    
    def _extract_meal_preferences(self, user_input: str, context: str, chat_history: List) -> Dict[str, Any]:
        """Extract meal preferences"""
        meal_info = {}
        
        # Get dietary restrictions from user config
        dietary = self.config_manager.get_user_dietary_restrictions()
        if dietary:
            meal_info.update(dietary)
        
        text = (user_input + " " + context).lower()
        
        if any(word in text for word in ['ăn chay', 'vegetarian']):
            meal_info['vegetarian'] = True
        elif any(word in text for word in ['halal']):
            meal_info['halal'] = True
        
        return meal_info if meal_info else None
    
    def _extract_interests_from_config(self) -> List[str]:
        """Extract interests from user configuration"""
        user_interests = self.config_manager.get_user_interests()
        if user_interests:
            return [interest for interest, enabled in user_interests.items() if enabled]
        return []
    
    # Helper methods for travel planning
    def _determine_country(self, location: str) -> str:
        """Determine country from location"""
        vietnam_locations = [
            'hà nội', 'hồ chí minh', 'đà nẵng', 'nha trang', 'huế', 
            'hội an', 'sapa', 'đà lạt', 'phú quốc', 'cần thơ',
            'hạ long', 'ninh bình', 'mù cang chải'
        ]
        
        if any(vn_loc in location.lower() for vn_loc in vietnam_locations):
            return 'Việt Nam'
        
        # Add more country detection logic here
        return 'Unknown'
    
    def _determine_region(self, location: str) -> str:
        """Determine region from location"""
        north_locations = ['hà nội', 'sapa', 'hạ long', 'ninh bình']
        central_locations = ['huế', 'đà nẵng', 'hội an']
        south_locations = ['hồ chí minh', 'đà lạt', 'nha trang', 'phú quốc']
        
        location_lower = location.lower()
        
        if any(loc in location_lower for loc in north_locations):
            return 'Miền Bắc'
        elif any(loc in location_lower for loc in central_locations):
            return 'Miền Trung'
        elif any(loc in location_lower for loc in south_locations):
            return 'Miền Nam'
        
        return 'Unknown'
    
    def _get_participant_count(self, user_input: str, context: str) -> int:
        """Get participant count from text"""
        import re
        text = user_input + " " + context
        
        match = re.search(r'(\d+)\s*(?:người|khách)', text)
        if match:
            return int(match.group(1))
        return 1
    
    def _request_missing_travel_info(self, missing_fields: list, current_info: dict) -> str:
        """Generate message requesting missing travel information"""
        
        field_prompts = {
            'destination': "🎯 Điểm đến muốn du lịch",
            'dates': "📅 Thời gian du lịch (ngày bắt đầu)",
            'duration': "⏱️ Thời gian du lịch (số ngày/tuần)",
            'participants': "👥 Số người tham gia",
            'budget': "💰 Ngân sách dự kiến",
            'visa_requirements': "📋 Yêu cầu visa/thị thực",
            'health_requirements': "🏥 Yêu cầu sức khỏe/tiêm chủng"
        }
        
        current_info_display = []
        for key, value in current_info.items():
            if value and key in field_prompts:
                if isinstance(value, dict):
                    # Handle complex objects
                    if key == 'destination' and value.get('primary'):
                        current_info_display.append(f"✅ {field_prompts[key]}: {value['primary']}")
                    elif key == 'participants':
                        current_info_display.append(f"✅ {field_prompts[key]}: {value.get('total', 1)} người")
                    elif key == 'budget' and value.get('total_amount'):
                        current_info_display.append(f"✅ {field_prompts[key]}: {value['total_amount']:,} {value.get('currency', 'VND')}")
                else:
                    current_info_display.append(f"✅ {field_prompts[key]}: {value}")
        
        missing_info_display = []
        for field in missing_fields:
            if field in field_prompts:
                missing_info_display.append(f"❓ {field_prompts[field]}")
        
        message = "🧳 **Thông tin lên kế hoạch du lịch chưa đủ**\n\n"
        
        if current_info_display:
            message += "**Thông tin đã có:**\n" + "\n".join(current_info_display) + "\n\n"
        
        message += "**Cần bổ sung:**\n" + "\n".join(missing_info_display) + "\n\n"
        message += "💡 Vui lòng cung cấp thông tin còn thiếu để tôi có thể tạo kế hoạch du lịch chi tiết cho bạn."
        
        return message
    
    def _generate_travel_plan_confirmation(self, travel_info: dict) -> str:
        """Generate travel plan confirmation message"""
        
        message = f"""🧳 **XÁC NHẬN KẾ HOẠCH DU LỊCH**

🎯 **Điểm đến:** {travel_info.get('destination', {}).get('primary', 'N/A')}
🌍 **Quốc gia:** {travel_info.get('destination', {}).get('country', 'N/A')}

📅 **Thời gian:** {travel_info.get('dates', {}).get('start_date', 'N/A')}
⏱️ **Thời lượng:** {travel_info.get('duration', {}).get('total_days', 'N/A')} ngày

👥 **Số người:** {travel_info.get('participants', {}).get('total', 1)}
👩‍👩‍👧‍👦 **Người lớn:** {travel_info.get('participants', {}).get('adults', 1)}
👶 **Trẻ em:** {travel_info.get('participants', {}).get('children', 0)}

💰 **Ngân sách:** {travel_info.get('budget', {}).get('total_amount', 'N/A'):,} {travel_info.get('budget', {}).get('currency', 'VND')}

"""
        
        # Add optional information if available
        if travel_info.get('travel_style'):
            message += f"🎨 **Phong cách du lịch:** {travel_info['travel_style']}\n"
        
        if travel_info.get('activities'):
            message += f"🎯 **Hoạt động yêu thích:** {', '.join(travel_info['activities'])}\n"
        
        if travel_info.get('accommodations'):
            message += f"🏨 **Lưu trú:** {travel_info['accommodations'].get('type', 'N/A')}\n"
        
        if travel_info.get('visa_requirements'):
            visa_status = travel_info['visa_requirements'].get('status', 'unknown')
            message += f"📋 **Visa:** {visa_status}\n"
        
        if travel_info.get('health_requirements'):
            health_status = travel_info['health_requirements'].get('vaccination_status', 'unknown')
            message += f"🏥 **Y tế:** {health_status}\n"
        
        message += f"""
❓ **Thông tin kế hoạch trên có chính xác không?**

Trả lời "**Có**" hoặc "**Xác nhận**" để lưu kế hoạch du lịch.
Trả lời "**Không**" hoặc "**Sửa**" để điều chỉnh thông tin.
"""
        
        return message
    
    def _generate_contextual_suggestions(self, user_input: str, result: Dict[str, Any], 
                                       detected_tool: str, context: str, 
                                       chat_history: List) -> List[Dict[str, str]]:
        """
        Generate contextual suggestions based on user interaction and result
        
        Args:
            user_input: User's original query
            result: Agent's response result
            detected_tool: Tool that was used (RAG, WEATHER, etc.)
            context: Conversation context
            chat_history: Previous conversation history
            
        Returns:
            List of suggestion dictionaries with text and target tool
        """
        try:
            # Get user interests from config
            user_interests = []
            if self.config_manager:
                interests = self.config_manager.get_user_interests()
                if interests:
                    user_interests = [k for k, v in interests.items() if v]
            
            # Extract location from various sources with enhanced detection
            location = None
            
            # Try function calling location detection first (most accurate)
            try:
                location_result = self._detect_location_with_function_calling(
                    user_query=user_input,
                    query_type=detected_tool.lower(),
                    context=context
                )
                if location_result.get("location_found", False):
                    location = location_result.get("location")
            except:
                pass
            
            # Fallback to existing methods
            if not location:
                location = (
                    result.get('city') or  # From weather queries
                    self._extract_location_from_text(user_input) or
                    self._extract_location_from_text(context)
                )
            
            # Create suggestion context
            suggestion_context = SuggestionContext(
                tool_used=ToolType(detected_tool),
                user_query=user_input,
                agent_response=result.get('response', ''),
                location=location,
                rag_sources=result.get('sources'),
                booking_details=result.get('booking_details'),
                chat_history=chat_history,
                user_interests=user_interests
            )
            
            # Generate suggestions using the suggestion engine
            suggestions = self.suggestion_engine.generate_suggestions(suggestion_context)
            
            # Convert suggestions to format expected by UI
            formatted_suggestions = []
            for suggestion in suggestions:
                formatted_suggestions.append({
                    'text': suggestion.text,
                    'category': suggestion.category,
                    'tool_target': suggestion.tool_target.value,
                    'score': suggestion.total_score()
                })
            
            if self.debug_mode:
                print(f"\n💡 [DEBUG] Generated {len(formatted_suggestions)} suggestions:")
                for i, sugg in enumerate(formatted_suggestions, 1):
                    print(f"  {i}. {sugg['text']} (→ {sugg['tool_target']}, score: {sugg['score']:.2f})")
            
            return formatted_suggestions
            
        except Exception as e:
            if self.debug_mode:
                print(f"\n❌ [ERROR] Suggestion generation failed: {str(e)}")
            return []
    
    def _extract_location_from_text(self, text: str) -> str:
        """Extract location from text using simple pattern matching - consistent with suggestion engine"""
        if not text:
            return None
            
        # Vietnamese location patterns
        vietnam_locations = [
            "hà nội", "hồ chí minh", "đà nẵng", "nha trang", "huế", "hội an",
            "sapa", "đà lạt", "phú quốc", "cần thơ", "vũng tầu", "phan thiết",
            "hạ long", "ninh bình", "mù cang chải", "tam cốc", "bái đính"
        ]
        
        text_lower = text.lower()
        for location in vietnam_locations:
            if location in text_lower:
                return location.title()
        
        return None
    
    def _detect_location_with_function_calling(
        self, 
        user_query: str, 
        query_type: str, 
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Use LangChain function calling to detect location or request it from user
        
        Args:
            user_query: User's query text
            query_type: Type of query (weather, hotel, car, travel_plan)
            context: Additional context
            
        Returns:
            Dict with location information or request message
        """
        try:
            # Get conversation history for context
            conversation_history = ""
            try:
                import streamlit as st
                conversation_id = st.session_state.get('active_conversation_id')
                if conversation_id:
                    from .config_manager import ConfigManager
                    config_manager = ConfigManager()
                    history = config_manager.get_conversation_history(conversation_id)
                    # Convert history to text
                    conversation_history = " ".join([
                        entry[1] for entry in history[-5:] if len(entry) >= 2  # Last 5 messages
                    ])
            except:
                pass
            
            # Use function calling to detect location
            result = self.location_function_caller.detect_and_handle_location(
                user_query=user_query,
                query_type=query_type,
                conversation_history=conversation_history,
                context=context
            )
            
            if self.debug_mode:
                print(f"\n🔧 [DEBUG] Function Calling Location Detection:")
                print(f"📝 Query: {user_query}")
                print(f"🎯 Type: {query_type}")
                print(f"✅ Success: {result.get('success', False)}")
                print(f"📍 Location Found: {result.get('location_found', False)}")
                print(f"🏙️ Location: {result.get('location', 'None')}")
                print(f"🔧 Tool Used: {result.get('tool_used', 'Unknown')}")
            
            return result
            
        except Exception as e:
            if self.debug_mode:
                print(f"\n❌ [ERROR] Function calling failed: {str(e)}")
            
            # Fallback to original method
            return self._fallback_location_detection(user_query, query_type, context)
    
    def _fallback_location_detection(
        self, 
        user_query: str, 
        query_type: str, 
        context: str = ""
    ) -> Dict[str, Any]:
        """Fallback location detection using original methods"""
        
        conversation_id = self._get_conversation_id()
        location = self._extract_city_from_query_with_context(user_query, context, conversation_id)
        
        if location:
            return {
                "success": True,
                "location_found": True,
                "location": location,
                "confidence": 0.8,
                "tool_used": "FALLBACK_EXTRACTION"
            }
        else:
            # Generate location request message
            query_prompts = {
                "weather": "🏙️ **Tôi cần biết địa điểm để kiểm tra thời tiết.**\n\nBạn muốn xem thời tiết ở đâu? (Ví dụ: Hà Nội, Đà Nẵng, Hồ Chí Minh...)",
                "hotel": "🏨 **Tôi cần biết địa điểm để tìm khách sạn.**\n\nBạn muốn đặt khách sạn ở thành phố nào? (Ví dụ: Hà Nội, Đà Nẵng, Hồ Chí Minh...)",
                "car": "🚗 **Tôi cần biết điểm đón và điểm đến để đặt xe.**\n\nBạn muốn đi từ đâu đến đâu?",
                "travel_plan": "🧳 **Tôi cần biết điểm đến để lập kế hoạch du lịch.**\n\nBạn muốn du lịch ở đâu?"
            }
            
            message = query_prompts.get(query_type, query_prompts["weather"])
            
            return {
                "success": True,
                "location_found": False,
                "needs_location": True,
                "response": message,
                "tool_used": "FALLBACK_REQUEST"
            }
    
    def _extract_location_for_booking(self, query: str, booking_type: str, context: str = "") -> Optional[str]:
        """
        Extract location for booking using function calling with fallback
        
        Args:
            query: User query text
            booking_type: Type of booking (hotel, car, travel_plan)
            context: Additional context
            
        Returns:
            Location if found, None otherwise
        """
        try:
            # Use function calling to detect location
            location_result = self._detect_location_with_function_calling(
                user_query=query,
                query_type=booking_type,
                context=context
            )
            
            if location_result.get("location_found", False):
                return location_result.get("location")
            else:
                # No location found - return None so booking validation can handle
                return None
                
        except Exception as e:
            if self.debug_mode:
                print(f"\n❌ [ERROR] Location extraction for booking failed: {str(e)}")
            
            # Fallback to original method
            conversation_id = self._get_conversation_id()
            return self._extract_city_from_query_with_context(query, context, conversation_id)
    
    def _get_conversation_id(self) -> Optional[str]:
        """Get current conversation ID from session state"""
        try:
            import streamlit as st
            return st.session_state.get('active_conversation_id')
        except:
            return None