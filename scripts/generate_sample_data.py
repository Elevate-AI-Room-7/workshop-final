#!/usr/bin/env python3
"""
Script để tạo dữ liệu mẫu cho Pinecone
Tạo dữ liệu du lịch cho 10 tỉnh thành Việt Nam
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

try:
    from pinecone_rag_system import PineconeRAGSystem
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"🔧 Script directory: {script_dir}")
    print(f"🔧 Project root: {project_root}")
    print(f"🔧 Src path: {src_path}")
    print(f"🔧 Python path: {sys.path[:3]}")
    raise

# Sample data cho 10 tỉnh thành
PROVINCES_DATA = {
    "hanoi": {
        "name": "Hà Nội",
        "attractions": [
            "Hồ Hoàn Kiếm với Đền Ngọc Sơn là biểu tượng của Hà Nội. Hồ nằm ở trung tâm thành phố, là nơi tập thể dục buổi sáng của người dân và điểm check-in yêu thích của du khách.",
            "Phố cổ Hà Nội với 36 phố phường mang đậm nét văn hóa truyền thống. Mỗi phố có một nghề riêng như phố Hàng Bạc, phố Hàng Mã, phố Hàng Bồ.",
            "Văn Miếu - Quốc Tử Giám là trường đại học đầu tiên của Việt Nam, được xây dựng từ năm 1070. Đây là nơi thờ Khổng Tử và các bậc hiền tài."
        ],
        "foods": [
            "Phở Hà Nội nổi tiếng với nước dùng trong, thịt bò tái và bánh phở mềm. Các quán phở nổi tiếng: Phở Thìn, Phở Bát Đàn, Phở Suông.",
            "Bún chả Hà Nội gồm bún tươi, chả nướng và nước mắm chua ngọt. Quán bún chả Đắc Kim và bún chả Hương Liên rất được ưa chuộng.",
            "Bánh mì pate Hà Nội với bánh giòn, pate béo ngậy và rau sống tươi mát. Bánh mì phố cổ và bánh mì Hàng Cân là những địa chỉ quen thuộc."
        ],
        "hotels": [
            "Khách sạn Metropole Hanoi là khách sạn 5 sao lịch sử với kiến trúc Pháp cổ điển, nằm ở vị trí trung tâm. Giá phòng từ 200-500 USD/đêm.",
            "JW Marriott Hotel Hanoi là khách sạn cao cấp với view đẹp ra hồ Hoàn Kiếm. Có spa, gym và nhà hàng sang trọng. Giá từ 150-300 USD/đêm.",
            "Hanoi La Siesta Hotel & Spa là khách sạn boutique với dịch vụ tốt và vị trí thuận tiện ở phố cổ. Giá phòng từ 80-150 USD/đêm."
        ]
    },
    "hochiminh": {
        "name": "Hồ Chí Minh",
        "attractions": [
            "Dinh Độc Lập (Dinh Thống Nhất) là công trình kiến trúc quan trọng, từng là nơi làm việc của Tổng thống Việt Nam Cộng Hòa. Hiện là bảo tàng với nhiều hiện vật lịch sử.",
            "Chợ Bến Thành là biểu tượng của Sài Gòn với kiến trúc đặc trưng. Đây là nơi mua sắm quà lưu niệm, thưởng thức ẩm thực địa phương.",
            "Nhà thờ Đức Bà Sài Gòn được xây dựng theo phong cách Gothic Pháp, là một trong những công trình kiến trúc tôn giáo đẹp nhất Việt Nam."
        ],
        "foods": [
            "Phở Sài Gòn có hương vị ngọt đậm đà, ăn kèm với giá đỗ và rau thơm. Phở Hùng, Phở Lệ và Phở 2000 là những quán nổi tiếng.",
            "Bánh mì Sài Gòn với nhân đa dạng: chả cá, xíu mại, thịt nướng. Bánh mì Hòa Mã và bánh mì Như Lan được du khách yêu thích.",
            "Cơm tấm Sài Gòn gồm cơm tấm, sườn nướng, chả trứng và nước mắm pha. Cơm tấm Ba Ghiền và cơm tấm Kiều Giang rất nổi tiếng."
        ],
        "hotels": [
            "Park Hyatt Saigon là khách sạn 5 sao sang trọng ở trung tâm Quận 1, với thiết kế hiện đại và dịch vụ đẳng cấp. Giá từ 300-600 USD/đêm.",
            "Hotel Continental Saigon là khách sạn lịch sử với kiến trúc Pháp cổ điển, nằm gần Nhà hát Thành phố. Giá từ 100-200 USD/đêm.",
            "Sheraton Saigon Hotel & Towers với view đẹp ra sông Sài Gòn, có nhiều tiện ích cao cấp. Giá phòng từ 150-300 USD/đêm."
        ]
    },
    "danang": {
        "name": "Đà Nẵng",
        "attractions": [
            "Bãi biển Mỹ Khê được CNN bình chọn là một trong 6 bãi biển đẹp nhất hành tinh. Bãi cát trắng mịn, nước biển trong xanh và sóng êm.",
            "Cầu Rồng là biểu tượng của Đà Nẵng, có hình dáng con rồng uốn lượn qua sông Hàn. Vào cuối tuần, rồng sẽ phun lửa và nước vào 21h.",
            "Bà Nà Hills với cầu Vàng nổi tiếng thế giới, được nâng đỡ bởi đôi bàn tay khổng lồ. Khu du lịch có cáp treo, làng Pháp và nhiều trò chơi."
        ],
        "foods": [
            "Mì Quảng Đà Nẵng với nước dùng đậm đà, bánh tráng nướng và tôm thịt. Mì Quảng Ba Mua và Mì Quảng Bà Vị là địa chỉ nổi tiếng.",
            "Bánh xèo Đà Nẵng có vỏ giòn vàng, nhân tôm thịt và giá đỗ, ăn kèm rau sống và nước chấm. Bánh xèo Bà Dưỡng rất được ưa chuộng.",
            "Cao lầu Hội An là món đặc sản với sợi bánh dai, thịt xá xíu và rau sống. Chỉ có thể ăn món này tại Hội An do nguồn nước đặc biệt."
        ],
        "hotels": [
            "InterContinental Danang Sun Peninsula Resort là resort 5 sao trên bán đảo Sơn Trà với view biển tuyệt đẹp. Giá từ 400-800 USD/đêm.",
            "Pullman Danang Beach Resort nằm trên bãi biển Mỹ Khê với thiết kế hiện đại và nhiều tiện ích. Giá từ 200-400 USD/đêm.",
            "Fusion Maia Da Nang là resort all-spa với concept độc đáo, mỗi villa đều có spa riêng. Giá từ 300-600 USD/đêm."
        ]
    },
    "nhatrang": {
        "name": "Nha Trang",
        "attractions": [
            "Vinpearl Land Nha Trang là khu vui chơi giải trí lớn trên đảo Hòn Tre, có cáp treo vượt biển dài nhất thế giới. Gồm công viên nước, thủy cung và các trò chơi.",
            "Tháp Bà Ponagar là quần thể kiến trúc Chăm cổ xưa, thờ nữ thần Ponagar. Tháp được xây dựng từ thế kỷ 8-13 với kiến trúc độc đáo.",
            "Bãi biển Nha Trang dài 6km với cát trắng mịn và nước biển trong xanh. Là nơi lý tưởng để tắm biển, lặn ngắm san hô và các hoạt động thể thao biển."
        ],
        "foods": [
            "Bánh căn Nha Trang là món đặc sản với vỏ giòn, nhân tôm băm, ăn kèm nước mắm ngọt. Bánh căn Đinh Tiên Hoàng và Nguyễn Thiện Thuật nổi tiếng.",
            "Nem nướng Ninh Hòa với thịt nướng thơm lừng, cuốn bánh tráng với rau sống và chấm tương. Nem nướng Cô Ba và nem nướng Xứ Huế được ưa chuộng.",
            "Bún chả cá Nha Trang với nước dùng chua cay, chả cá dai giòn và bún tươi. Bún chả cá 123 Hoàng Văn Thụ và bún chả cá Dì Hai rất nổi tiếng."
        ],
        "hotels": [
            "JW Marriott Nha Trang Ocean Resort & Spa là resort 5 sao view biển với thiết kế sang trọng và spa đẳng cấp. Giá từ 250-500 USD/đêm.",
            "Melia Nha Trang Bay Resort & Spa nằm ở vị trí trung tâm với view đẹp ra vịnh Nha Trang. Giá từ 150-300 USD/đêm.",
            "Sunrise Nha Trang Beach Hotel & Spa là khách sạn 4 sao với vị trí đắc địa ngay bãi biển. Giá từ 80-160 USD/đêm."
        ]
    },
    "dalat": {
        "name": "Đà Lạt",
        "attractions": [
            "Hồ Xuân Hương là trung tâm của Đà Lạt, có hình lưỡi liềm độc đáo. Quanh hồ có nhiều khách sạn, nhà hàng và các hoạt động như đạp xe, đi dạo.",
            "Dinh Bảo Đại (Dinh 3) là nơi nghỉ dưỡng của vua Bảo Đại với kiến trúc Pháp cổ điển. Hiện là bảo tàng trưng bày đồ dùng cá nhân của hoàng gia.",
            "Đèo Prenn với thác nước đẹp và cây cầu treo thú vị. Du khách có thể đi cáp treo ngắm cảnh và chụp ảnh với khung cảnh núi rừng Đà Lạt."
        ],
        "foods": [
            "Bánh tráng nướng Đà Lạt với lớp bánh giòn, trứng gà và các loại gia vị đặc trưng. Bánh tráng nướng chợ đêm Đà Lạt rất nổi tiếng.",
            "Nem nướng Đà Lạt với thịt nướng thơm, bánh tráng và rau địa phương như rau rừng. Nem nướng chợ Đà Lạt và nem nướng Trần Phú được ưa chuộng.",
            "Sữa đậu nành nóng Đà Lạt thích hợp cho thời tiết se lạnh của thành phố. Các quán sữa đậu nành ở chợ đêm và chợ Đà Lạt rất đông khách."
        ],
        "hotels": [
            "Dalat Palace Luxury Hotel & Golf Club là khách sạn 5 sao lịch sử với kiến trúc Pháp cổ điển và sân golf đẹp. Giá từ 200-400 USD/đêm.",
            "Ana Mandara Villas Dalat Resort & Spa là resort villa sang trọng với không gian riêng tư và thiết kế độc đáo. Giá từ 150-300 USD/đêm.",
            "Swiss-Belresort Tuyen Lam Dalat với view hồ Tuyền Lâm tuyệt đẹp và không khí trong lành. Giá từ 100-200 USD/đêm."
        ]
    },
    "hue": {
        "name": "Huế",
        "attractions": [
            "Đại Nội Huế là quần thể cung đình nhà Nguyễn với kiến trúc hoàng gia độc đáo. Gồm Hoàng thành, Tử cấm thành và nhiều cung điện, đền đài.",
            "Chùa Thiên Mụ là ngôi chùa cổ nhất Huế, nằm bên sông Hương với tháp Phước Duyên 7 tầng làm biểu tượng. Chùa có giá trị văn hóa tâm linh cao.",
            "Lăng Khải Định là lăng tẩm của vua Khải Định với kiến trúc pha trộn Đông Tây độc đáo. Trang trí bằng sành sứ và kiếng màu rất tinh xảo."
        ],
        "foods": [
            "Bún bò Huế có nước dùng cay nồng đặc trưng, thịt bò và chả cua. Bún bò Bà Tuần và bún bò Đông Ba là những quán nổi tiếng nhất.",
            "Cơm âm phủ Huế là món cơm trộn với nhiều loại rau, thịt và nước mắm đặc biệt. Cơm âm phủ Hạnh và cơm âm phủ Mười rất được ưa chuộng.",
            "Bánh bèo Huế là món nhỏ với bánh bèo nhỏ, tôm khô và nước mắm chua ngọt. Bánh bèo Nam Phổ và bánh bèo Bà Bích nổi tiếng."
        ],
        "hotels": [
            "La Residence Hue Hotel & Spa là khách sạn 5 sao bên sông Hương với kiến trúc Art Deco độc đáo. Giá từ 150-350 USD/đêm.",
            "Imperial Hotel Hue là khách sạn 4 sao trung tâm với thiết kế hiện đại và dịch vụ tốt. Giá từ 80-150 USD/đêm.",
            "Indochine Palace Hue là khách sạn sang trọng với không gian cổ điển và vị trí thuận tiện. Giá từ 100-200 USD/đêm."
        ]
    },
    "hoian": {
        "name": "Hội An",
        "attractions": [
            "Phố cổ Hội An là Di sản Văn hóa Thế giới với kiến trúc cổ kính được bảo tồn nguyên vẹn. Về đêm, phố cổ được thắp sáng bằng đèn lồng rất lãng mạn.",
            "Chùa cầu Nhật Bản (Lai Viễn Kiều) là biểu tượng của Hội An, được xây dựng từ thế kỷ 16 bởi cộng đồng người Nhật. Kiến trúc độc đáo kết hợp chùa và cầu.",
            "Rừng dừa Bảy Mẫu là khu sinh thái với rừng dừa nước xanh mướt. Du khách có thể đi thúng chai, câu cua và thưởng thức hải sản tươi sống."
        ],
        "foods": [
            "Cao lầu Hội An là món đặc sản chỉ có ở Hội An với sợi bánh dai, thịt xá xíu và rau sống. Cao lầu Thanh và cao lầu Bà Lê rất nổi tiếng.",
            "White Rose (Bánh vạc) là món dimsum Hội An với vỏ bánh mỏng, nhân tôm và hành lá. Chỉ có một gia đình ở Hội An biết làm món này.",
            "Cơm gà Hội An với gà luộc thơm ngon, cơm được nấu bằng nước luộc gà và rau sống. Cơm gà Bà Buội và cơm gà Phố Cổ rất được ưa chuộng."
        ],
        "hotels": [
            "Four Seasons Resort The Nam Hai là resort 5 sao siêu sang với villa riêng biệt và bãi biển đẹp. Giá từ 800-1500 USD/đêm.",
            "Anantara Hoi An Resort là resort sang trọng bên sông Thu Bồn với thiết kế truyền thống Việt Nam. Giá từ 300-600 USD/đêm.",
            "Victoria Hoi An Beach Resort & Spa nằm trên bãi biển Cửa Đại với không gian yên tĩnh và thiết kế cổ điển. Giá từ 150-300 USD/đêm."
        ]
    },
    "sapa": {
        "name": "Sapa",
        "attractions": [
            "Ruộng bậc thang Sapa được UNESCO công nhận là Di sản thiên nhiên thế giới. Đẹp nhất vào mùa lúa chín (tháng 9-10) với màu vàng óng ánh.",
            "Fansipan là đỉnh núi cao nhất Đông Dương (3.143m), được gọi là 'nóc nhà Đông Dương'. Du khách có thể leo núi hoặc đi cáp treo lên đỉnh.",
            "Thác Bạc (Silver Falls) cao 200m là thác nước đẹp nhất Sapa. Đường đến thác đi qua các bản làng dân tộc với cảnh quan thiên nhiên tuyệt đẹp."
        ],
        "foods": [
            "Thịt lợn cắp nách Sapa là đặc sản với lợn nhỏ nướng nguyên con, da giòn thịt thơm. Thường ăn kèm rau rừng và rượu cần.",
            "Cá tầm nướng Sapa với thịt cá chắc, ngọt và thơm. Ăn kèm bánh tráng và rau sống, chấm mắm tôm chua cay đặc trưng.",
            "Rau rừng Sapa gồm nhiều loại rau dại như su su non, măng tre, lá lốt. Có vị đắng thanh đặc trưng của vùng núi cao."
        ],
        "hotels": [
            "Hotel de la Coupole - MGallery Sapa là khách sạn 5 sao với kiến trúc Pháp cổ điển và view núi tuyệt đẹp. Giá từ 200-400 USD/đêm.",
            "Victoria Sapa Resort & Spa là resort sang trọng với thiết kế độc đáo và dịch vụ đẳng cấp quốc tế. Giá từ 150-300 USD/đêm.",
            "Amazing Sapa Hotel với vị trí trung tâm thị trấn Sapa và view đẹp ra thung lũng. Giá từ 50-100 USD/đêm."
        ]
    },
    "phuquoc": {
        "name": "Phú Quốc",
        "attractions": [
            "Bãi Sao Phú Quốc là bãi biển đẹp nhất đảo với cát trắng mịn như bột và nước biển trong xanh như ngọc. Lý tưởng cho hoạt động bơi lội và lặn ngắm san hô.",
            "Cáp treo Hòn Thơm là cáp treo vượt biển dài nhất thế giới, kết nối đất liền với đảo Hòn Thơm. Trên đảo có nhiều hoạt động vui chơi và ăn uống.",
            "Chợ đêm Dinh Cậu là nơi thưởng thức hải sản tươi sống và đặc sản Phú Quốc. Có nhiều món ngon như cua rang me, ghẹ nướng và ốc hương."
        ],
        "foods": [
            "Nước mắm Phú Quốc là đặc sản nổi tiếng thế giới với chất lượng cao nhất. Được làm từ cá cơm tươi ngon theo phương pháp truyền thống.",
            "Gỏi cá trích Phú Quốc với cá tươi, rau sống và nước mắm đặc biệt. Món ăn có vị chua cay đặc trưng của vùng biển đảo.",
            "Hàu nướng mỡ hành Phú Quốc với hàu tươi béo ngậy, nướng với mỡ hành thơm lừng. Ăn kèm bánh tráng nướng và rau sống."
        ],
        "hotels": [
            "JW Marriott Phu Quoc Emerald Bay Resort & Spa là resort 5 sao với kiến trúc độc đáo như lâu đài cổ tích. Giá từ 300-700 USD/đêm.",
            "InterContinental Phu Quoc Long Beach Resort nằm trên bãi biển Trường với thiết kế hiện đại và nhiều tiện ích. Giá từ 250-500 USD/đêm.",
            "Salinda Resort Phu Quoc Island là resort sang trọng với villa riêng biệt và không gian yên tĩnh. Giá từ 200-400 USD/đêm."
        ]
    },
    "cantho": {
        "name": "Cần Thơ",
        "attractions": [
            "Chợ nổi Cái Răng là chợ nổi lớn nhất miền Tây, hoạt động từ sáng sớm đến 9h. Du khách có thể mua trái cây tươi ngon và trải nghiệm văn hóa sông nước.",
            "Vườn cò Bằng Lăng là khu bảo tồn thiên nhiên với hàng nghìn con cò trắng về đậu mỗi chiều. Cảnh quan thơ mộng với sông nước và cây cầu tre.",
            "Nhà cổ Bình Thủy là biệt thự cổ 100 tuổi với kiến trúc Pháp - Việt độc đáo. Được sử dụng làm bối cảnh quay phim 'Người tình' của Marguerite Duras."
        ],
        "foods": [
            "Bánh xèo miền Tây Cần Thơ có size lớn, vỏ giòn vàng và nhân tôm thịt phong phú. Ăn kèm rau sống và nước chấm chua ngọt đặc trưng.",
            "Lẩu mắm miền Tây với nước dùng đậm đà từ mắm cá linh, nhiều loại rau rừng và cá kèo. Món ăn đặc trưng của vùng sông nước.",
            "Cơm dẻo Cần Thơ là món cơm tám xôi dẻo, ăn kèm thịt nướng và nước mắm ngọt. Cơm dẻo Tám Xôi và cơm dẻo Bà Hàng rất nổi tiếng."
        ],
        "hotels": [
            "Victoria Can Tho Resort là resort 4 sao bên sông Hậu với thiết kế kiểu Pháp cổ điển và vườn nhiệt đới. Giá từ 100-200 USD/đêm.",
            "Muong Thanh Luxury Can Tho Hotel là khách sạn cao cấp ở trung tâm thành phố với view sông đẹp. Giá từ 60-120 USD/đêm.",
            "TTC Hotel Can Tho là khách sạn 4 sao với vị trí thuận tiện và dịch vụ chất lượng. Giá từ 50-100 USD/đêm."
        ]
    }
}

def create_sample_records() -> List[Dict[str, Any]]:
    """Tạo danh sách records mẫu cho Pinecone"""
    records = []
    record_id = 1
    
    for province_key, province_data in PROVINCES_DATA.items():
        province_name = province_data["name"]
        
        # Tạo records cho attractions
        for i, attraction in enumerate(province_data["attractions"]):
            records.append({
                "id": f"{province_key}-attraction-{i+1:02d}",
                "text": attraction,
                "metadata": {
                    "location": province_name,
                    "category": "destination",
                    "rating": round(4.2 + (i * 0.2), 1),
                    "price_range": "$" if i == 0 else "$$",
                    "created_at": datetime.now().isoformat(),
                    "province_key": province_key
                }
            })
        
        # Tạo records cho foods
        for i, food in enumerate(province_data["foods"]):
            records.append({
                "id": f"{province_key}-food-{i+1:02d}",
                "text": food,
                "metadata": {
                    "location": province_name,
                    "category": "restaurant",
                    "rating": round(4.5 + (i * 0.1), 1),
                    "price_range": "$" if i < 2 else "$$",
                    "created_at": datetime.now().isoformat(),
                    "province_key": province_key
                }
            })
        
        # Tạo records cho hotels
        for i, hotel in enumerate(province_data["hotels"]):
            price_ranges = ["$$$$", "$$$", "$$"]
            records.append({
                "id": f"{province_key}-hotel-{i+1:02d}",
                "text": hotel,
                "metadata": {
                    "location": province_name,
                    "category": "hotel",
                    "rating": round(4.8 - (i * 0.1), 1),
                    "price_range": price_ranges[i] if i < len(price_ranges) else "$$",
                    "created_at": datetime.now().isoformat(),
                    "province_key": province_key
                }
            })
    
    return records

def main():
    """Hàm chính để upload dữ liệu vào Pinecone"""
    print("🚀 Bắt đầu tạo dữ liệu mẫu cho Pinecone...")
    
    try:
        # Khởi tạo RAG system
        print("📦 Khởi tạo Pinecone RAG system...")
        rag_system = PineconeRAGSystem()
        
        # Tạo dữ liệu mẫu
        print("📝 Tạo dữ liệu mẫu...")
        records = create_sample_records()
        print(f"✅ Đã tạo {len(records)} records")
        
        # In thống kê
        stats = {}
        for record in records:
            category = record["metadata"]["category"]
            location = record["metadata"]["location"]
            
            if category not in stats:
                stats[category] = {}
            if location not in stats[category]:
                stats[category][location] = 0
            stats[category][location] += 1
        
        print("\n📊 Thống kê dữ liệu:")
        for category, locations in stats.items():
            print(f"  {category.title()}:")
            for location, count in locations.items():
                print(f"    - {location}: {count} records")
        
        # Upload dữ liệu
        print("\n⬆️  Upload dữ liệu vào Pinecone...")
        uploaded_count = 0
        
        for record in records:
            try:
                # Lấy embedding
                embedding = rag_system.get_embedding(record["text"])
                
                # Sanitize metadata
                metadata = rag_system._sanitize_metadata(record["metadata"])
                metadata["text"] = record["text"]
                
                # Upsert vào Pinecone
                rag_system.index.upsert([(record["id"], embedding, metadata)])
                uploaded_count += 1
                
                if uploaded_count % 10 == 0:
                    print(f"  📤 Đã upload {uploaded_count}/{len(records)} records...")
                    
            except Exception as e:
                print(f"❌ Lỗi upload record {record['id']}: {str(e)}")
                continue
        
        print(f"\n✅ Hoàn thành! Đã upload {uploaded_count}/{len(records)} records vào Pinecone")
        
        # Kiểm tra kết quả
        try:
            stats = rag_system.get_index_stats()
            print(f"📊 Tổng số records trong database: {stats.get('total_vectors', 0)}")
        except Exception as e:
            print(f"⚠️  Không thể lấy thống kê: {str(e)}")
        
        # Test tìm kiếm
        print("\n🔍 Test tìm kiếm mẫu:")
        test_queries = [
            "địa điểm tham quan Hà Nội",
            "món ăn đặc sản Huế", 
            "khách sạn Đà Nẵng",
            "bãi biển Phú Quốc"
        ]
        
        for query in test_queries:
            try:
                results = rag_system.search(query, top_k=2)
                print(f"  🔎 Query: '{query}' → {len(results)} kết quả")
                for result in results[:1]:
                    print(f"     - {result.get('id', 'Unknown')}: {result.get('text', '')[:80]}...")
            except Exception as e:
                print(f"     ❌ Lỗi search '{query}': {str(e)}")
                
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        return 1
    
    print("\n🎉 Script hoàn thành thành công!")
    return 0

if __name__ == "__main__":
    exit(main())