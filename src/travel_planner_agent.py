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


class TravelPlannerAgent:
    """
    Unified Travel Planner Agent that combines:
    - RAG system for travel knowledge
    - Weather information
    - Hotel booking functionality
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.weather_api_key = os.getenv("WEATHER_API_KEY")
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        # Initialize RAG system
        self.rag_system = PineconeRAGSystem()
        
        # Initialize variables for tracking sources and fallback
        self.last_rag_sources = []
        self.no_relevant_info = False
        self.fallback_query = ""
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="GPT-4o-mini",
            temperature=0.7,
            openai_api_key=self.openai_api_key,
            base_url=self.openai_endpoint
        )
        
        # Setup tools and agent
        self.tools = self._setup_tools()
        self.agent = self._setup_agent()
        
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
        Main method to handle travel planning requests
        
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
            
            # Create travel planning prompt
            system_prompt = """
            Bạn là AI Travel Planner chuyên nghiệp cho du lịch Việt Nam.
            
            Nhiệm vụ của bạn:
            1. Tư vấn điểm đến du lịch
            2. Lập kế hoạch chi tiết
            3. Cung cấp thông tin thời tiết khi cần
            4. Hỗ trợ đặt khách sạn
            5. Hỗ trợ đặt xe/vận chuyển
            6. Đưa ra gợi ý hoạt động phù hợp
            
            Hãy sử dụng các tools có sẵn để:
            - TravelKnowledgeSearch: Tìm thông tin du lịch
            - WeatherInfo: Kiểm tra thời tiết
            - BookHotel: Đặt khách sạn khi khách hàng yêu cầu
            - BookCar: Đặt xe/vận chuyển khi khách hàng yêu cầu
            
            Trả lời bằng tiếng Việt, thân thiện và chi tiết.
            """
            
            # Clear previous sources and reset flags
            self.last_rag_sources = []
            self.no_relevant_info = False
            self.fallback_query = ""
            
            # Run agent
            response = self.agent.run({
                "input": f"{system_prompt}\n\nYêu cầu của khách hàng: {user_input}",
                "chat_history": chat_history
            })
            
            # Check if RAG found no relevant info and suggest fallback
            if self.no_relevant_info and "RAG_NO_INFO:" in response:
                return {
                    "success": True,
                    "response": None,  # Signal that fallback is needed
                    "sources": [],
                    "rag_used": False,
                    "no_relevant_info": True,
                    "query": self.fallback_query
                }
            
            return {
                "success": True,
                "response": response,
                "sources": self.last_rag_sources,
                "rag_used": len(self.last_rag_sources) > 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": f"Xin lỗi, có lỗi xảy ra: {str(e)}",
                "error": str(e)
            }
    
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