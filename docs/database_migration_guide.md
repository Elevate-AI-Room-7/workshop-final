# 🗄️ Database Migration Guide

## 📋 Tổng quan

Hệ thống AI Travel Assistant đã được nâng cấp từ lưu trữ JSON sang SQLite database để cải thiện hiệu suất và quản lý dữ liệu tốt hơn.

## 🚀 Tính năng mới

### 1. **SQLite Database**
- Thay thế các file JSON cũ (agent_config.json, personality_templates.json, user_preferences.json)
- Lưu trữ cấu hình agent, template personality, sở thích người dùng
- Hỗ trợ booking (xe và khách sạn) 
- Quản lý lịch sử hội thoại

### 2. **Conversation Management**
- ✅ Tạo hội thoại mới với tiêu đề tùy chỉnh
- ✅ Chuyển đổi giữa các hội thoại
- ✅ Lưu trữ lịch sử tin nhắn tự động
- ✅ Hiển thị danh sách hội thoại trong sidebar

### 3. **Booking System**
- ✅ Lưu thông tin đặt xe với đầy đủ chi tiết
- ✅ Lưu thông tin đặt khách sạn
- ✅ Tracking trạng thái booking
- ✅ Lịch sử booking của người dùng

## 🗂️ Cấu trúc Database

### Tables Created:

#### 1. **agent_config**
- Cấu hình agent (tên, personality, avatar, settings)
- Thay thế: `config/agent_config.json`

#### 2. **personality_templates**  
- Template personality với greeting messages và response style
- Thay thế: `config/personality_templates.json`

#### 3. **user_preferences**
- Sở thích du lịch, budget, dietary restrictions, bucket list
- Thay thế: `config/user_preferences.json`

#### 4. **book_car** (MỚI)
- Thông tin đặt xe: pickup/dropoff, ngày giờ, loại xe, số người
- Tracking trạng thái booking

#### 5. **book_hotel** (MỚI)
- Thông tin đặt khách sạn: checkin/checkout, phòng, amenities
- Budget range và special requests

#### 6. **conversations** (MỚI)
- Quản lý các cuộc hội thoại với title và trạng thái
- Multi-conversation support

#### 7. **conversation_history** (MỚI)
- Lưu trữ từng tin nhắn với metadata
- Hỗ trợ search và filter

## 🔄 Migration Process

### Tự động Migration
- Database tự động tạo khi chạy app lần đầu
- Default personality templates được khởi tạo
- Không cần can thiệp thủ công

### File Changes
- ✅ `src/database_manager.py` - New database manager
- ✅ `src/config_manager.py` - Updated to use SQLite
- ✅ `components/conversation_manager.py` - New conversation UI
- ✅ `app.py` - Integrated database + conversation management

## 🎯 Sử dụng

### 1. Conversation Management
```python
# Trong sidebar
render_conversation_manager(config_manager)

# Tạo hội thoại mới
conversation_id = config_manager.create_conversation("Chuyến đi Đà Nẵng")

# Lưu tin nhắn
config_manager.save_message(conversation_id, "user", "Hello")
config_manager.save_message(conversation_id, "assistant", "Hi!", metadata={"tool": "RAG"})

# Lấy lịch sử
history = config_manager.get_conversation_history(conversation_id)
```

### 2. Booking Management  
```python
# Đặt xe
booking_id = config_manager.save_car_booking({
    "pickup_location": "Hà Nội",
    "dropoff_location": "Hạ Long", 
    "pickup_date": "2025-12-25",
    "car_type": "standard",
    "passengers": 4
})

# Đặt khách sạn
hotel_id = config_manager.save_hotel_booking({
    "location": "Đà Nẵng",
    "checkin_date": "2025-12-25",
    "checkout_date": "2025-12-27",
    "adults": 2,
    "room_type": "double"
})
```

### 3. Configuration Management
```python
# Lấy cấu hình (tự động từ database)
agent_name = config_manager.get_agent_name()
personality = config_manager.get_personality()

# Cập nhật sở thích
config_manager.update_user_preferences({
    "travel_interests": ["food", "culture", "photography"],
    "budget_preference": "medium"
})
```

## 📊 Performance Improvements

### Before (JSON)
- ❌ File I/O operations
- ❌ Full file read/write
- ❌ No indexing
- ❌ Limited search capability

### After (SQLite)
- ✅ Database indexes
- ✅ Efficient queries  
- ✅ Partial updates
- ✅ Advanced search & filter
- ✅ ACID transactions

## 🔧 Database Location

```
data/travel_assistant.db
```

## 🚨 Backward Compatibility

### JSON Files Status
- Các file JSON cũ vẫn tồn tại nhưng không được sử dụng
- Có thể xóa an toàn: `config/*.json`
- Data migration tự động khi khởi tạo

### Session State
- `st.session_state["messages"]` vẫn hoạt động cho UI
- Database lưu trữ persistent, session state lưu trữ temporary
- Khi chuyển conversation, session state được cập nhật từ database

## 🎮 UI Changes

### New Sidebar Features
- **💬 Quản lý Hội thoại**: Expandable section
- **🆕 Tạo hội thoại mới**: Với title tùy chỉnh  
- **📋 Hội thoại hiện có**: List với status và timestamps
- **🟢 Active indicator**: Hiển thị hội thoại đang hoạt động

### Chat Interface
- Tự động lưu tin nhắn khi gửi
- Load lịch sử khi chuyển conversation
- Metadata tracking (tool used, city, weather, etc.)

## 🛠️ Development

### Testing
```bash
# Test database manager
python src/database_manager.py

# Test config manager
python -c "from src.config_manager import ConfigManager; cm = ConfigManager(); print(cm.get_agent_name())"

# Run app
streamlit run app.py
```

### Database Schema
- Xem chi tiết trong `src/database_manager.py`
- Có thể extend thêm tables cho tính năng mới
- Built-in migration support

## 📈 Future Roadmap

### Planned Features
1. **User Management**: Multi-user support
2. **Export/Import**: Backup conversations
3. **Search**: Full-text search trong conversations  
4. **Analytics**: Conversation insights và usage stats
5. **Sync**: Cloud backup và sync across devices

### Database Optimization
- Thêm indexes cho performance
- Cleanup old conversations
- Compression cho large data

---

## ✅ Migration Completed

- ✅ SQLite database created
- ✅ All tables initialized  
- ✅ Config manager updated
- ✅ Conversation management added
- ✅ App integration completed
- ✅ Backward compatibility maintained

🎉 **Hệ thống đã sẵn sàng với tính năng database mới!**