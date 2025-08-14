"""
Travel Planner Agent - Unified agent for travel planning with RAG and tools
"""

import os
from typing import Dict, Any, List
from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import requests
import json
from .pinecone_rag_system import PineconeRAGSystem
from .config_manager import ConfigManager


class TravelPlannerAgent:
    """
    Unified Travel Planner Agent that combines:
    - RAG system for travel knowledge
    - Weather information
    - Hotel booking functionality
    """
    
    def __init__(self, debug_mode: bool = False):
        self.openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.weather_api_key = os.getenv("WEATHER_API_KEY")
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        # Debug mode setting
        self.debug_mode = debug_mode or os.getenv("DEBUG_TRAVEL_AGENT", "false").lower() == "true"
        
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        
        # Initialize RAG system
        self.rag_system = PineconeRAGSystem()
        
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
            else:
                # Default to general conversation
                result = self._execute_general_response(user_input, rewritten_context)
            
            if self.debug_mode:
                print(f"\n✅ [DEBUG] Execution Complete:")
                print(f"🎯 Success: {result.get('success', False)}")
                print(f"📄 Response length: {len(result.get('response', ''))}")
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
            5. GENERAL - Trò chuyện chung, không cần công cụ đặc biệt
            
            Quy tắc phân loại (ĐẶC BIỆT chú ý ngữ cảnh):
            - RAG: Hỏi về địa điểm, danh lam, ẩm thực, hoạt động du lịch, "có gì", "làm gì"
            - WEATHER: Hỏi về thời tiết, nhiệt độ, trời mưa/nắng, dự báo (CHÚ Ý: nếu ngữ cảnh có địa điểm, thời tiết sẽ của địa điểm đó)
            - HOTEL: Yêu cầu đặt phòng, tìm khách sạn, booking accommodation
            - CAR: Yêu cầu đặt xe, thuê xe, book transportation, di chuyển
            - GENERAL: Chào hỏi, cảm ơn, câu hỏi chung không liên quan du lịch
            
            QUAN TRỌNG: Nếu câu hỏi đơn giản như "thời tiết" nhưng ngữ cảnh có địa điểm, 
            vẫn chọn WEATHER vì người dùng muốn biết thời tiết của địa điểm đó.
            
            Trả lời CHÍNH XÁC một trong: RAG, WEATHER, HOTEL, CAR, GENERAL
            """
            
            detected = self.llm.predict(detection_prompt).strip().upper()
            
            # Debug output
            if self.debug_mode:
                print(f"\n🤖 [DEBUG] Tool Detection:")
                print(f"📝 User input: {user_input}")
                print(f"🎯 Context: {context}")
                print(f"🔧 Detected tool: {detected}")
            
            # Validate detection result
            valid_tools = ["RAG", "WEATHER", "HOTEL", "CAR", "GENERAL"]
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
        Execute weather query with context-aware city extraction
        """
        try:
            # Extract city from user input AND context
            city = self._extract_city_from_query_with_context(user_input, context)
            
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
        Execute hotel booking with validation and confirmation
        """
        try:
            # Extract booking details
            booking_details = self._extract_hotel_booking_details(user_input, context)
            
            # Check if required information is complete
            required_fields = ['customer_name', 'customer_phone', 'hotel_name', 'location', 'check_in_date', 'nights']
            missing_fields = [field for field in required_fields if not booking_details.get(field)]
            
            if missing_fields:
                # Request missing information
                missing_info = self._request_missing_hotel_info(missing_fields, booking_details)
                return {
                    "success": False,
                    "response": missing_info,
                    "sources": ["AI Hotel Booking System"],
                    "rag_used": False,
                    "tool_used": "HOTEL_VALIDATION",
                    "booking_details": booking_details,
                    "missing_fields": missing_fields
                }
            
            # All information complete - show confirmation
            confirmation_message = self._generate_hotel_booking_confirmation(booking_details)
            
            return {
                "success": True,
                "response": confirmation_message,
                "sources": ["AI Hotel Booking System"],
                "rag_used": False,
                "tool_used": "HOTEL_CONFIRMATION",
                "context": context,
                "booking_details": booking_details,
                "awaiting_confirmation": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": f"Lỗi đặt khách sạn: {str(e)}",
                "error": str(e),
                "tool_used": "HOTEL"
            }
    
    def _execute_car_booking(self, user_input: str, context: str) -> Dict[str, Any]:
        """
        Execute car booking with validation and confirmation
        """
        try:
            # Extract booking details
            booking_details = self._extract_car_booking_details(user_input, context)
            
            # Check if required information is complete
            required_fields = ['customer_name', 'customer_phone', 'pickup_location', 'destination', 'pickup_time', 'car_type']
            missing_fields = [field for field in required_fields if not booking_details.get(field)]
            
            if missing_fields:
                # Request missing information
                missing_info = self._request_missing_car_info(missing_fields, booking_details)
                return {
                    "success": False,
                    "response": missing_info,
                    "sources": ["AI Car Booking System"],
                    "rag_used": False,
                    "tool_used": "CAR_VALIDATION",
                    "booking_details": booking_details,
                    "missing_fields": missing_fields
                }
            
            # All information complete - show confirmation
            confirmation_message = self._generate_car_booking_confirmation(booking_details)
            
            return {
                "success": True,
                "response": confirmation_message,
                "sources": ["AI Car Booking System"],
                "rag_used": False,
                "tool_used": "CAR_CONFIRMATION",
                "context": context,
                "booking_details": booking_details,
                "awaiting_confirmation": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": f"Lỗi đặt xe: {str(e)}",
                "error": str(e),
                "tool_used": "CAR"
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
    def _extract_city_from_query(self, query: str) -> str:
        """Extract city name from weather query - legacy method"""
        # Simple extraction - can be enhanced with NER
        cities = ["hà nội", "hồ chí minh", "đà nẵng", "nha trang", "huế", "hội an", "sapa", "đà lạt", "phú quốc", "cần thơ"]
        query_lower = query.lower()
        
        for city in cities:
            if city in query_lower:
                return city.title()
        
        return "Hà Nội"  # Default city
    
    def _extract_city_from_query_with_context(self, query: str, context: str) -> str:
        """Extract city name from query with context awareness - prioritizes provinces over cities"""
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
        
        # Strategy: Find all matching locations, then prioritize
        found_locations = []
        
        # Check current query first
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
        
        if found_locations:
            # Prioritization logic:
            # 1. Direct query locations first
            # 2. Among context locations, prefer provinces over cities
            # 3. Use the most specific match
            
            query_locations = [loc for source, loc in found_locations if source == "query"]
            context_locations = [loc for source, loc in found_locations if source == "context"]
            
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
            else:
                selected = "hà nội"  # Fallback
            
            return selected.title()
        
        # Default fallback
        default_city = "Hà Nội"
        if self.debug_mode:
            print(f"🏙️ No location found, using default: {default_city}")
        return default_city
    
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
            "location": self._extract_city_from_query(query),
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
        
        # Try to extract from context if available
        city = self._extract_city_from_query(query)
        if city:
            return f"Sân bay {city}"  # Default to airport
        
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
            'location': "📍 Địa điểm (thành phố)",
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