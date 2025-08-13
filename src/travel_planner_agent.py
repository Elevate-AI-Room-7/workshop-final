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
                return result.get('answer', 'Không tìm thấy thông tin phù hợp.')
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
            5. Đưa ra gợi ý hoạt động phù hợp
            
            Hãy sử dụng các tools có sẵn để:
            - TravelKnowledgeSearch: Tìm thông tin du lịch
            - WeatherInfo: Kiểm tra thời tiết
            - BookHotel: Đặt khách sạn khi khách hàng yêu cầu
            
            Trả lời bằng tiếng Việt, thân thiện và chi tiết.
            """
            
            # Run agent
            response = self.agent.run({
                "input": f"{system_prompt}\n\nYêu cầu của khách hàng: {user_input}",
                "chat_history": chat_history
            })
            
            return {
                "success": True,
                "response": response,
                "sources": "Travel knowledge base + Tools"
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