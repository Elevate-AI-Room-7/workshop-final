"""
Travel Assistant Tools using LangChain function calling
"""
from typing import Dict, Any, Optional
from langchain_core.tools import tool
import requests
import json
from datetime import datetime

# Import existing modules
from .pinecone_rag_system import PineconeRAGSystem
from .config_manager import ConfigManager


class TravelToolsManager:
    """Manager class for travel tools"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.rag_system = None
        self._init_rag_system()
    
    def _init_rag_system(self):
        """Initialize RAG system"""
        try:
            self.rag_system = PineconeRAGSystem()
        except Exception as e:
            print(f"Warning: Could not initialize RAG system: {e}")
    
    def get_rag_system(self):
        """Get RAG system instance"""
        return self.rag_system
    
    def get_weather_api_key(self):
        """Get weather API key from config"""
        return self.config_manager.get_weather_api_key()


# Global instance
_tools_manager = TravelToolsManager()


@tool
def search_travel_information(query: str, location: Optional[str] = None) -> str:
    """
    Tra cứu thông tin du lịch, danh lam thắng cảnh, ẩm thực, hoạt động du lịch.
    
    Args:
        query (str): Câu hỏi hoặc thông tin cần tìm kiếm
        location (str, optional): Địa điểm cụ thể nếu có
    
    Returns:
        str: Thông tin du lịch liên quan
    """
    try:
        rag_system = _tools_manager.get_rag_system()
        if not rag_system:
            return "❌ Hệ thống RAG chưa được khởi tạo. Vui lòng thử lại sau."
        
        # Combine query with location if provided
        search_query = f"{query} {location}" if location else query
        
        # Perform RAG search
        results = rag_system.search(search_query, top_k=3)
        
        if not results:
            return f"Không tìm thấy thông tin về '{search_query}'. Vui lòng thử với từ khóa khác."
        
        # Format results
        response = f"📍 **Thông tin về {search_query}:**\n\n"
        for i, result in enumerate(results, 1):
            response += f"**{i}. {result.get('title', 'Thông tin du lịch')}**\n"
            response += f"{result.get('content', result.get('text', 'Không có nội dung'))}\n\n"
        
        return response
        
    except Exception as e:
        return f"❌ Lỗi khi tìm kiếm thông tin: {str(e)}"


@tool
def get_weather_info(city: str, days: Optional[int] = 1) -> str:
    """
    Lấy thông tin thời tiết hiện tại hoặc dự báo thời tiết.
    
    Args:
        city (str): Tên thành phố cần kiểm tra thời tiết
        days (int, optional): Số ngày dự báo (1-7 ngày), mặc định là 1 ngày
    
    Returns:
        str: Thông tin thời tiết
    """
    try:
        api_key = _tools_manager.get_weather_api_key()
        if not api_key:
            return "❌ Không tìm thấy API key cho dịch vụ thời tiết. Vui lòng cấu hình trong settings."
        
        # WeatherAPI.com endpoint
        if days == 1:
            url = f"http://api.weatherapi.com/v1/current.json"
            params = {
                'key': api_key,
                'q': city,
                'lang': 'vi'
            }
        else:
            url = f"http://api.weatherapi.com/v1/forecast.json"
            params = {
                'key': api_key,
                'q': city,
                'days': min(days, 7),  # Max 7 days
                'lang': 'vi'
            }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if days == 1:
                # Current weather
                current = data['current']
                location = data['location']
                
                weather_info = f"🌤️ **Thời tiết hiện tại tại {location['name']}, {location['country']}:**\n\n"
                weather_info += f"🌡️ **Nhiệt độ:** {current['temp_c']}°C (cảm giác như {current['feelslike_c']}°C)\n"
                weather_info += f"☁️ **Tình trạng:** {current['condition']['text']}\n"
                weather_info += f"💨 **Gió:** {current['wind_kph']} km/h hướng {current['wind_dir']}\n"
                weather_info += f"💧 **Độ ẩm:** {current['humidity']}%\n"
                weather_info += f"👁️ **Tầm nhìn:** {current['vis_km']} km\n"
                weather_info += f"📊 **Áp suất:** {current['pressure_mb']} mb\n"
                
                return weather_info
            else:
                # Forecast weather
                location = data['location']
                forecast = data['forecast']['forecastday']
                
                weather_info = f"📅 **Dự báo thời tiết {days} ngày tại {location['name']}, {location['country']}:**\n\n"
                
                for day_data in forecast:
                    date = datetime.strptime(day_data['date'], '%Y-%m-%d').strftime('%d/%m/%Y')
                    day = day_data['day']
                    
                    weather_info += f"📆 **{date}:**\n"
                    weather_info += f"   🌡️ Nhiệt độ: {day['mintemp_c']}°C - {day['maxtemp_c']}°C\n"
                    weather_info += f"   ☁️ Tình trạng: {day['condition']['text']}\n"
                    weather_info += f"   🌧️ Khả năng mưa: {day['daily_chance_of_rain']}%\n\n"
                
                return weather_info
        else:
            return f"❌ Không thể lấy thông tin thời tiết cho '{city}'. Vui lòng kiểm tra tên thành phố."
            
    except requests.RequestException as e:
        return f"❌ Lỗi kết nối khi lấy thông tin thời tiết: {str(e)}"
    except Exception as e:
        return f"❌ Lỗi khi lấy thông tin thời tiết: {str(e)}"


@tool
def book_hotel(city: str, checkin_date: str, checkout_date: str, guests: int = 2, room_type: Optional[str] = None) -> str:
    """
    Hỗ trợ đặt phòng khách sạn.
    
    Args:
        city (str): Thành phố muốn đặt phòng
        checkin_date (str): Ngày check-in (định dạng: DD/MM/YYYY)
        checkout_date (str): Ngày check-out (định dạng: DD/MM/YYYY)
        guests (int): Số khách (mặc định 2)
        room_type (str, optional): Loại phòng mong muốn
    
    Returns:
        str: Thông tin đặt phòng
    """
    try:
        # Validate dates
        try:
            checkin = datetime.strptime(checkin_date, '%d/%m/%Y')
            checkout = datetime.strptime(checkout_date, '%d/%m/%Y')
            
            if checkout <= checkin:
                return "❌ Ngày check-out phải sau ngày check-in."
            
            if checkin < datetime.now():
                return "❌ Ngày check-in phải từ hôm nay trở đi."
                
        except ValueError:
            return "❌ Định dạng ngày không đúng. Vui lòng sử dụng định dạng DD/MM/YYYY."
        
        # Calculate nights
        nights = (checkout - checkin).days
        
        booking_info = f"🏨 **Yêu cầu đặt phòng khách sạn:**\n\n"
        booking_info += f"📍 **Địa điểm:** {city}\n"
        booking_info += f"📅 **Check-in:** {checkin_date}\n"
        booking_info += f"📅 **Check-out:** {checkout_date}\n"
        booking_info += f"🌙 **Số đêm:** {nights} đêm\n"
        booking_info += f"👥 **Số khách:** {guests} người\n"
        
        if room_type:
            booking_info += f"🛏️ **Loại phòng:** {room_type}\n"
        
        booking_info += f"\n✅ **Yêu cầu đặt phòng đã được ghi nhận!**\n"
        booking_info += f"📞 Chúng tôi sẽ liên hệ với bạn để xác nhận đặt phòng và thanh toán.\n"
        booking_info += f"💡 **Gợi ý:** Để có giá tốt nhất, hãy đặt phòng sớm và so sánh giá từ nhiều nguồn khác nhau."
        
        # TODO: Integrate with actual hotel booking API
        # For now, this is a mock response
        
        return booking_info
        
    except Exception as e:
        return f"❌ Lỗi khi đặt phòng khách sạn: {str(e)}"


@tool
def book_car_service(pickup_location: str, destination: str, pickup_time: str, service_type: str = "taxi") -> str:
    """
    Hỗ trợ đặt xe/dịch vụ vận chuyển.
    
    Args:
        pickup_location (str): Địa điểm đón
        destination (str): Địa điểm đến
        pickup_time (str): Thời gian đón (định dạng: DD/MM/YYYY HH:MM)
        service_type (str): Loại dịch vụ (taxi, car, bike)
    
    Returns:
        str: Thông tin đặt xe
    """
    try:
        # Validate pickup time
        try:
            pickup_dt = datetime.strptime(pickup_time, '%d/%m/%Y %H:%M')
            
            if pickup_dt < datetime.now():
                return "❌ Thời gian đón phải từ hiện tại trở đi."
                
        except ValueError:
            return "❌ Định dạng thời gian không đúng. Vui lòng sử dụng định dạng DD/MM/YYYY HH:MM."
        
        # Validate service type
        valid_services = ["taxi", "car", "bike", "xe máy", "ô tô"]
        if service_type.lower() not in valid_services:
            service_type = "taxi"  # Default fallback
        
        booking_info = f"🚗 **Yêu cầu đặt xe:**\n\n"
        booking_info += f"📍 **Điểm đón:** {pickup_location}\n"
        booking_info += f"🎯 **Điểm đến:** {destination}\n"
        booking_info += f"⏰ **Thời gian đón:** {pickup_time}\n"
        booking_info += f"🚙 **Loại dịch vụ:** {service_type.title()}\n"
        
        # Estimate travel time (mock calculation)
        estimated_time = "20-30 phút"  # This would be calculated by a real service
        
        booking_info += f"\n✅ **Yêu cầu đặt xe đã được ghi nhận!**\n"
        booking_info += f"⏱️ **Thời gian di chuyển ước tính:** {estimated_time}\n"
        booking_info += f"📞 Tài xế sẽ liên hệ với bạn trước 15 phút.\n"
        booking_info += f"💡 **Lưu ý:** Vui lòng có mặt tại điểm đón đúng giờ."
        
        # TODO: Integrate with actual car booking API
        # For now, this is a mock response
        
        return booking_info
        
    except Exception as e:
        return f"❌ Lỗi khi đặt xe: {str(e)}"


@tool
def create_travel_plan(destination: str, duration_days: int, interests: Optional[str] = None, budget: Optional[str] = None) -> str:
    """
    Tạo kế hoạch du lịch chi tiết.
    
    Args:
        destination (str): Điểm đến du lịch
        duration_days (int): Số ngày du lịch
        interests (str, optional): Sở thích/hoạt động mong muốn
        budget (str, optional): Ngân sách (thấp/trung bình/cao)
    
    Returns:
        str: Kế hoạch du lịch chi tiết
    """
    try:
        if duration_days <= 0 or duration_days > 30:
            return "❌ Số ngày du lịch phải từ 1 đến 30 ngày."
        
        # Get travel information from RAG
        rag_system = _tools_manager.get_rag_system()
        travel_info = ""
        
        if rag_system:
            try:
                search_query = f"du lịch {destination} {interests if interests else ''}"
                results = rag_system.search(search_query, top_k=2)
                if results:
                    travel_info = "\n".join([result.get('content', result.get('text', ''))[:300] + "..." 
                                           for result in results])
            except:
                travel_info = ""
        
        plan = f"✈️ **KẾ HOẠCH DU LỊCH {destination.upper()}**\n\n"
        plan += f"📅 **Thời gian:** {duration_days} ngày\n"
        plan += f"📍 **Điểm đến:** {destination}\n"
        
        if interests:
            plan += f"🎯 **Sở thích:** {interests}\n"
        if budget:
            plan += f"💰 **Ngân sách:** {budget}\n"
        
        plan += f"\n📋 **LỊCH TRÌNH CHI TIẾT:**\n\n"
        
        # Generate daily itinerary
        for day in range(1, duration_days + 1):
            plan += f"**📆 Ngày {day}:**\n"
            
            if day == 1:
                plan += f"- 🛬 **Sáng:** Đến {destination}, check-in khách sạn\n"
                plan += f"- 🍽️ **Trưa:** Thưởng thức ẩm thực địa phương\n"
                plan += f"- 🏛️ **Chiều:** Tham quan các điểm nổi tiếng gần trung tâm\n"
                plan += f"- 🌃 **Tối:** Khám phá phố đi bộ, chợ đêm\n"
            elif day == duration_days:
                plan += f"- 🎁 **Sáng:** Mua sắm quà lưu niệm\n"
                plan += f"- 🍜 **Trưa:** Thưởng thức món ăn yêu thích cuối cùng\n"
                plan += f"- ✈️ **Chiều:** Check-out, ra sân bay/nhà ga\n"
            else:
                if interests and "ẩm thực" in interests.lower():
                    plan += f"- 🍳 **Sáng:** Tour ẩm thực địa phương\n"
                    plan += f"- 🏮 **Trưa:** Tham gia lớp nấu ăn\n"
                elif interests and "văn hóa" in interests.lower():
                    plan += f"- 🏛️ **Sáng:** Tham quan bảo tàng, di tích lịch sử\n"
                    plan += f"- 🎭 **Trưa:** Xem biểu diễn văn hóa dân gian\n"
                elif interests and "thiên nhiên" in interests.lower():
                    plan += f"- 🌄 **Sáng:** Trekking, ngắm cảnh thiên nhiên\n"
                    plan += f"- 🏊 **Trưa:** Hoạt động thể thao ngoài trời\n"
                else:
                    plan += f"- 🗺️ **Sáng:** Tham quan danh lam thắng cảnh\n"
                    plan += f"- 🛍️ **Trưa:** Mua sắm, thư giãn\n"
                
                plan += f"- 🌅 **Chiều:** Ngắm hoàng hôn, chụp ảnh\n"
                plan += f"- 🍽️ **Tối:** Thưởng thức ẩm thực đặc sản\n"
            
            plan += f"\n"
        
        plan += f"💡 **GỢI Ý THÊM:**\n"
        plan += f"- 📱 Tải app bản đồ offline\n"
        plan += f"- 💳 Chuẩn bị tiền mặt và thẻ\n"
        plan += f"- 🎒 Đóng gói phù hợp với thời tiết\n"
        plan += f"- 📋 Kiểm tra thông tin visa/hộ chiếu\n"
        
        if travel_info:
            plan += f"\n📖 **THÔNG TIN THAM KHẢO:**\n{travel_info[:500]}...\n"
        
        plan += f"\n✅ **Kế hoạch đã được tạo thành công!**\n"
        plan += f"💾 Bạn có muốn lưu kế hoạch này không?"
        
        return plan
        
    except Exception as e:
        return f"❌ Lỗi khi tạo kế hoạch du lịch: {str(e)}"


@tool 
def general_conversation(message: str) -> str:
    """
    Xử lý các cuộc trò chuyện chung, chào hỏi, cảm ơn.
    
    Args:
        message (str): Tin nhắn từ người dùng
    
    Returns:
        str: Phản hồi thân thiện
    """
    try:
        message_lower = message.lower()
        
        # Greetings
        if any(greeting in message_lower for greeting in ["xin chào", "hello", "hi", "chào"]):
            return "👋 Xin chào! Tôi là trợ lý du lịch AI. Tôi có thể giúp bạn:\n\n🗺️ Tìm kiếm thông tin du lịch\n🌤️ Kiểm tra thời tiết\n🏨 Đặt phòng khách sạn\n🚗 Đặt xe di chuyển\n📋 Tạo kế hoạch du lịch\n\nBạn cần tôi hỗ trợ gì?"
        
        # Thanks
        elif any(thanks in message_lower for thanks in ["cảm ơn", "thank", "thanks", "cám ơn"]):
            return "😊 Rất vui được giúp đỡ bạn! Nếu có thêm câu hỏi về du lịch, đừng ngần ngại hỏi nhé. Chúc bạn có những chuyến đi tuyệt vời! ✈️"
        
        # Goodbye
        elif any(bye in message_lower for bye in ["tạm biệt", "bye", "goodbye", "chào tạm biệt"]):
            return "👋 Tạm biệt! Chúc bạn có những chuyến du lịch thật tuyệt vời. Hẹn gặp lại! 🌟"
        
        # Help
        elif any(help_word in message_lower for help_word in ["giúp", "help", "hướng dẫn", "hỗ trợ"]):
            return "🤖 **HƯỚNG DẪN SỬ DỤNG:**\n\n📍 **Tìm thông tin du lịch:** 'Có gì hay ở Đà Nẵng?'\n🌤️ **Xem thời tiết:** 'Thời tiết Hà Nội hôm nay'\n🏨 **Đặt phòng:** 'Đặt phòng khách sạn ở Sài Gòn từ 15/01 đến 20/01'\n🚗 **Đặt xe:** 'Đặt taxi từ sân bay về trung tâm lúc 14:00'\n📋 **Lập kế hoạch:** 'Lên kế hoạch du lịch Phú Quốc 3 ngày'\n\nHãy nói chuyện tự nhiên, tôi sẽ hiểu và hỗ trợ bạn!"
        
        # Default friendly response
        else:
            return f"😊 Tôi hiểu bạn muốn nói về: \"{message}\"\n\nTuy nhiên, tôi chuyên hỗ trợ về du lịch. Bạn có muốn tôi giúp tìm thông tin du lịch, kiểm tra thời tiết, đặt phòng khách sạn, hoặc lên kế hoạch du lịch không?"
        
    except Exception as e:
        return f"😊 Xin chào! Tôi là trợ lý du lịch AI. Tôi có thể giúp bạn với các vấn đề về du lịch. Bạn cần hỗ trợ gì?"


# Export all tools
TRAVEL_TOOLS = [
    search_travel_information,
    get_weather_info, 
    book_hotel,
    book_car_service,
    create_travel_plan,
    general_conversation
]