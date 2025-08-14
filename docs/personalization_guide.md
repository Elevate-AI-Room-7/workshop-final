# 🎯 Hướng dẫn Cá nhân hóa AI Travel Assistant

## 📋 Tổng quan
Hệ thống cá nhân hóa cho phép bạn tùy chỉnh AI agent theo phong cách riêng và thiết lập sở thích để nhận được gợi ý phù hợp nhất.

## 🤖 Cá nhân hóa Agent

### ⚙️ Truy cập Cài đặt
1. Mở sidebar bên trái
2. Click vào **"⚙️ Cài đặt Agent"**
3. Mở rộng để xem các tùy chọn

### 👤 Thông tin Agent
- **Tên Agent**: Đặt tên riêng cho trợ lý (VD: "Mai", "Linh", "An")
- **Tính cách**: Chọn 1 trong 4 phong cách:
  - 🌟 **Thân thiện**: Gần gũi, ấm áp
  - 💼 **Chuyên nghiệp**: Trang trọng, lịch sự  
  - 🎉 **Nhiệt tình**: Năng động, hào hứng
  - 🏘️ **Chuyên gia địa phương**: Kinh nghiệm thực tế
- **Avatar**: Chọn biểu tượng hiển thị (🤖, 👩‍💼, ✨, etc.)

### 🎨 Phong cách Trả lời
- **Giọng điệu**: Thoải mái vs Trang trọng
- **Sử dụng Emoji**: Ít / Vừa phải / Nhiều
- **Độ sáng tạo**: Slider từ 0.0-1.0 (Temperature)

### 🔧 Cài đặt Nâng cao
- **Số tin nhắn ngữ cảnh**: 1-10 tin nhắn gần nhất được phân tích
- **Hiển thị thông tin công cụ**: Bật/tắt tool indicators
- **Hiển thị ngữ cảnh**: Bật/tắt context preview
- **Text-to-Speech**: Bật/tắt đọc tin nhắn

## 👤 Sở thích Cá nhân

### 📍 Truy cập Sở thích
1. Trong sidebar, click **"👤 Sở thích cá nhân"**
2. Mở rộng để cấu hình

### 🎯 Sở thích Du lịch
Chọn các lĩnh vực bạn quan tâm:
- 🌿 **Thiên nhiên**: Rừng, núi, thác nước
- 🏛️ **Văn hóa**: Di tích lịch sử, bảo tàng
- 🍜 **Ẩm thực**: Đặc sản địa phương, street food
- 🏔️ **Phiêu lưu**: Leo núi, trekking, thể thao mạo hiểm
- 🏖️ **Biển**: Bãi biển, hoạt động nước
- 📸 **Chụp ảnh**: Góc ảnh đẹp, cảnh quan
- 🛍️ **Mua sắm**: Shopping mall, chợ địa phương

### 💰 Ngân sách
- **Tiết kiệm**: Ưu tiên chi phí thấp
- **Trung bình**: Cân bằng chất lượng/giá cả
- **Cao cấp**: Ưu tiên trải nghiệm premium
- **Linh hoạt**: Không giới hạn cụ thể

### 🍽️ Ăn uống
- **Chế độ ăn đặc biệt**: Ăn chay, Halal, etc.
- **Ẩm thực yêu thích**: 
  - Việt Nam: Phở, bún, bánh mì
  - Châu Á: Nhật, Hàn, Thái
  - Quốc tế: Âu, Mỹ, Ý
  - Đường phố: Street food, quán vỉa hè
  - Cao cấp: Fine dining, nhà hàng sang trọng

### 🎯 Danh sách Mơ ước (Bucket List)
- Nhập các điểm đến muốn ghé thăm
- Mỗi dòng một địa điểm
- Agent sẽ nhắc nhở và gợi ý

### ✅ Đã từng đến
- Liệt kê nơi đã đi
- Giúp agent tránh gợi ý trùng lặp
- Tham khảo kinh nghiệm cũ

### ⚙️ Cài đặt Cá nhân hóa
- **Ghi nhớ sở thích**: Lưu preferences cho lần sau
- **Gợi ý chủ động**: Agent tự động đưa ra suggestions

## 🎨 Trải nghiệm Cá nhân hóa

### 🏠 Màn hình Chính
- **Lời chào tùy chỉnh**: Theo tính cách agent và tên
- **Gợi ý riêng biệt**: Dựa trên sở thích đã chọn
- **UI động**: Thay đổi theo preferences

### 💬 Trong Hội thoại
- **Phong cách trả lời**: Theo personality đã chọn
- **Gợi ý thông minh**: 
  - Yêu thích ẩm thực → Gợi ý món ăn
  - Thích chụp ảnh → Gợi ý góc ảnh
  - Quan tâm tự nhiên → Ưu tiên eco-tours
- **Ngữ cảnh cá nhân**: Sử dụng bucket list, nơi đã đi

### 🔍 Tool Detection
Agent sẽ:
- Hiểu rõ hơn ý định dựa trên sở thích
- Ưu tiên tools phù hợp với preferences
- Điều chỉnh responses theo personality

## 💾 Lưu và Quản lý

### Lưu Cài đặt
- Click **"💾 Lưu cài đặt Agent"** sau khi thay đổi
- Click **"💾 Lưu sở thích"** để cập nhật preferences
- Thay đổi áp dụng ngay lập tức

### Reset về Mặc định  
- **"🔄 Reset về mặc định"** trong phần sở thích
- Khôi phục settings ban đầu
- Không ảnh hưởng đến agent config

## 🎯 Ví dụ Thực tế

### Scenario 1: Người yêu ẩm thực
```json
{
  "agent": "Mai - Thân thiện",
  "interests": ["food", "culture"],
  "personality": "enthusiastic",
  "budget": "medium"
}
```
**Kết quả**: Agent sẽ nhiệt tình gợi ý các tour ẩm thực, kết hợp văn hóa địa phương, trong tầm giá vừa phải.

### Scenario 2: Photographer chuyên nghiệp
```json
{
  "agent": "An - Chuyên gia địa phương", 
  "interests": ["photography", "nature"],
  "personality": "local_expert",
  "budget": "flexible"
}
```
**Kết quả**: Agent như local expert, biết các góc chụp đẹp ít người biết, ưu tiên cảnh quan tự nhiên.

### Scenario 3: Gia đình tiết kiệm
```json
{
  "agent": "Linh - Chuyên nghiệp",
  "interests": ["culture", "beach"],
  "personality": "professional", 
  "budget": "budget"
}
```
**Kết quả**: Tư vấn chuyên nghiệp các địa điểm văn hóa và biển, tập trung vào option giá rẻ.

## 🔄 Vòng đời Cá nhân hóa

1. **Thiết lập ban đầu**: Cấu hình agent và sở thích
2. **Tương tác**: Chat và nhận gợi ý cá nhân hóa  
3. **Học hỏi**: Agent ghi nhớ preferences qua thời gian
4. **Tinh chỉnh**: Điều chỉnh settings khi cần
5. **Nâng cấp**: Thêm sở thích mới, cập nhật bucket list

## 🎊 Lợi ích

### Cho Người dùng
- ✅ Trải nghiệm cá nhân hóa 100%
- ✅ Gợi ý chính xác hơn
- ✅ Tiết kiệm thời gian tìm kiếm
- ✅ Khám phá điều mới phù hợp sở thích

### Cho Agent
- ✅ Hiểu người dùng sâu hơn
- ✅ Trả lời có ngữ cảnh
- ✅ Xây dựng mối quan hệ lâu dài
- ✅ Tăng độ hài lòng

## 🔧 Troubleshooting

### Agent không nhớ sở thích
- ✅ Check "Ghi nhớ sở thích" đã bật
- ✅ Đảm bảo đã click "💾 Lưu sở thích"
- ✅ Restart app nếu cần

### Gợi ý không phù hợp
- ✅ Kiểm tra lại interests đã chọn
- ✅ Cập nhật bucket list
- ✅ Thêm nơi đã đi để tránh trùng lặp

### Phong cách trả lời chưa đúng
- ✅ Chọn lại personality
- ✅ Điều chỉnh emoji usage
- ✅ Thay đổi temperature

## 📞 Hỗ trợ

Nếu gặp vấn đề với tính năng cá nhân hóa:
1. Kiểm tra file config trong thư mục `config/`
2. Reset về mặc định và thiết lập lại
3. Kiểm tra logs để debug

---

🎯 **Mục tiêu cuối cùng**: Tạo ra trợ lý du lịch hiểu bạn như một người bạn thân, đưa ra những gợi ý hoàn hảo cho từng chuyến đi!