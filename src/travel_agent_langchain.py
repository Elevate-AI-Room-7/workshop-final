"""
Travel Assistant using LangChain Function Calling
"""
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from .travel_tools import TRAVEL_TOOLS
from .config_manager import ConfigManager
from .database_manager import DatabaseManager


class TravelAssistantLangChain:
    """
    Travel Assistant using LangChain function calling instead of manual tool detection
    """
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialize Travel Assistant with LangChain agent
        
        Args:
            debug_mode (bool): Enable debug output
        """
        self.debug_mode = debug_mode
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        
        # Initialize LLM
        self.llm = self._init_llm()
        
        # Create agent with tools
        self.agent = create_react_agent(
            model=self.llm,
            tools=TRAVEL_TOOLS
        )
        
        # Conversation memory
        self.conversation_history: List[Dict[str, Any]] = []
        
        if self.debug_mode:
            print("✅ TravelAssistantLangChain initialized successfully")
    
    def _init_llm(self) -> AzureChatOpenAI:
        """Initialize Azure OpenAI LLM"""
        try:
            # Get Azure OpenAI configuration
            azure_config = self.config_manager.get_azure_openai_config()
            
            if not azure_config or not all([
                azure_config.get('endpoint'),
                azure_config.get('api_key'),
                azure_config.get('deployment_name')
            ]):
                raise ValueError("Azure OpenAI configuration is incomplete")
            
            llm = AzureChatOpenAI(
                azure_endpoint=azure_config['endpoint'],
                api_key=azure_config['api_key'],
                azure_deployment=azure_config['deployment_name'],
                api_version="2024-07-01-preview",
                temperature=0.7,
                max_tokens=2000
            )
            
            if self.debug_mode:
                print("✅ Azure OpenAI LLM initialized successfully")
            
            return llm
            
        except Exception as e:
            if self.debug_mode:
                print(f"❌ Failed to initialize LLM: {str(e)}")
            raise
    
    def process_message(self, user_input: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process user message using LangChain agent
        
        Args:
            user_input (str): User's input message
            conversation_id (str, optional): Conversation ID for persistence
        
        Returns:
            Dict[str, Any]: Response with message and metadata
        """
        try:
            if self.debug_mode:
                print(f"\n🔄 Processing message: {user_input}")
            
            # Get conversation context
            context_messages = self._get_conversation_context(conversation_id)
            
            # Create system message with travel assistant instructions
            system_message = self._create_system_message()
            
            # Prepare messages for agent
            messages = [system_message] + context_messages + [HumanMessage(content=user_input)]
            
            # Invoke agent
            response = self.agent.invoke({"messages": messages})
            
            # Extract AI response
            ai_response = response["messages"][-1].content
            
            # Update conversation history
            self._update_conversation_history(user_input, ai_response, conversation_id)
            
            if self.debug_mode:
                print(f"✅ Response generated: {ai_response[:100]}...")
            
            return {
                "response": ai_response,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "tools_used": self._extract_tools_used(response["messages"]),
                "success": True
            }
            
        except Exception as e:
            error_msg = f"❌ Xin lỗi, có lỗi xảy ra khi xử lý yêu cầu của bạn: {str(e)}"
            
            if self.debug_mode:
                print(f"❌ Error processing message: {str(e)}")
            
            return {
                "response": error_msg,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "tools_used": [],
                "success": False,
                "error": str(e)
            }
    
    def _create_system_message(self) -> SystemMessage:
        """Create system message with travel assistant instructions"""
        system_prompt = """
Bạn là một trợ lý du lịch AI thông minh và thân thiện, chuyên hỗ trợ người dùng Việt Nam về mọi vấn đề liên quan đến du lịch.

**TÍNH CÁCH:**
- Thân thiện, nhiệt tình và chuyên nghiệp
- Sử dụng emoji phù hợp để tạo cảm giác gần gũi
- Trả lời bằng tiếng Việt tự nhiên và dễ hiểu
- Luôn cung cấp thông tin hữu ích và thực tế

**KHẢ NĂNG CỦA BẠN:**
🗺️ Tìm kiếm thông tin du lịch, danh lam thắng cảnh
🌤️ Kiểm tra thời tiết hiện tại và dự báo
🏨 Hỗ trợ đặt phòng khách sạn
🚗 Hỗ trợ đặt xe/dịch vụ vận chuyển
📋 Tạo kế hoạch du lịch chi tiết
💬 Trò chuyện chung về du lịch

**QUY TẮC QUAN TRỌNG:**
1. Luôn sử dụng các tools có sẵn khi phù hợp với yêu cầu của người dùng
2. Nếu không chắc chắn về thông tin, hãy thành thật nói và đề xuất cách tìm hiểu thêm
3. Cung cấp thông tin chi tiết và hữu ích
4. Luôn kết thúc bằng câu hỏi để tiếp tục hỗ trợ người dùng
5. Nếu người dùng cần thông tin cập nhật (thời tiết, giá cả), hãy sử dụng các tools để lấy thông tin mới nhất

**CÁCH SỬ DỤNG TOOLS:**
- Khi người dùng hỏi về địa điểm, danh lam thắng cảnh → dùng search_travel_information
- Khi hỏi về thời tiết → dùng get_weather_info
- Khi muốn đặt phòng khách sạn → dùng book_hotel
- Khi muốn đặt xe → dùng book_car_service
- Khi muốn lên kế hoạch du lịch → dùng create_travel_plan
- Câu chào hỏi, cảm ơn, câu hỏi chung → dùng general_conversation

Hãy luôn tự nhiên và hữu ích trong mọi tương tác!
"""
        return SystemMessage(content=system_prompt)
    
    def _get_conversation_context(self, conversation_id: Optional[str]) -> List:
        """Get conversation context from history"""
        if not conversation_id:
            return []
        
        try:
            # Get recent conversation history (last 10 messages)
            history = self.db_manager.get_conversation_history(conversation_id, limit=10)
            
            messages = []
            for record in history:
                messages.append(HumanMessage(content=record['user_message']))
                messages.append(AIMessage(content=record['assistant_response']))
            
            return messages[-10:]  # Keep last 10 messages for context
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ Could not load conversation context: {str(e)}")
            return []
    
    def _update_conversation_history(self, user_input: str, ai_response: str, conversation_id: Optional[str]):
        """Update conversation history in database"""
        try:
            if conversation_id:
                self.db_manager.save_conversation(
                    conversation_id=conversation_id,
                    user_message=user_input,
                    assistant_response=ai_response,
                    timestamp=datetime.now()
                )
            
            # Also keep in memory for current session
            self.conversation_history.append({
                "user_message": user_input,
                "assistant_response": ai_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep only last 20 messages in memory
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
                
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ Could not save conversation history: {str(e)}")
    
    def _extract_tools_used(self, messages: List) -> List[str]:
        """Extract tools that were used in the conversation"""
        tools_used = []
        
        for message in messages:
            if hasattr(message, 'additional_kwargs') and 'tool_calls' in message.additional_kwargs:
                for tool_call in message.additional_kwargs['tool_calls']:
                    tool_name = tool_call.get('function', {}).get('name', '')
                    if tool_name and tool_name not in tools_used:
                        tools_used.append(tool_name)
        
        return tools_used
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation summary"""
        try:
            history = self.db_manager.get_conversation_history(conversation_id)
            
            if not history:
                return {"summary": "Chưa có cuộc hội thoại nào", "message_count": 0}
            
            return {
                "summary": f"Cuộc hội thoại có {len(history)} tin nhắn",
                "message_count": len(history),
                "first_message": history[0]['user_message'] if history else None,
                "last_message": history[-1]['user_message'] if history else None
            }
            
        except Exception as e:
            if self.debug_mode:
                print(f"❌ Error getting conversation summary: {str(e)}")
            return {"summary": "Không thể tải thông tin cuộc hội thoại", "message_count": 0}
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation history"""
        try:
            self.db_manager.clear_conversation(conversation_id)
            # Also clear from memory
            self.conversation_history = []
            return True
        except Exception as e:
            if self.debug_mode:
                print(f"❌ Error clearing conversation: {str(e)}")
            return False
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available tools"""
        return [
            {"name": "search_travel_information", "description": "Tìm kiếm thông tin du lịch"},
            {"name": "get_weather_info", "description": "Kiểm tra thời tiết"},
            {"name": "book_hotel", "description": "Đặt phòng khách sạn"},
            {"name": "book_car_service", "description": "Đặt xe/vận chuyển"},
            {"name": "create_travel_plan", "description": "Tạo kế hoạch du lịch"},
            {"name": "general_conversation", "description": "Trò chuyện chung"}
        ]
    
    def plan_travel(self, user_input: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Legacy interface compatibility - delegates to process_message
        
        Args:
            user_input (str): User's input message
            conversation_id (str, optional): Conversation ID
        
        Returns:
            Dict[str, Any]: Response compatible with old interface
        """
        return self.process_message(user_input, conversation_id)
    
    @property
    def rag_system(self):
        """Property to access RAG system for backward compatibility"""
        from .travel_tools import _tools_manager
        return _tools_manager.get_rag_system()