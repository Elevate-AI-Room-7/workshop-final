"""
Hotel Booking Management Page
Displays and manages hotel booking records
"""

import streamlit as st
from typing import Dict, List
from datetime import datetime
import sys
import os

# Add utils to path for HTML cleaning
utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils')
if utils_path not in sys.path:
    sys.path.append(utils_path)

try:
    from html_cleaner import clean_html_for_display, clean_title
except ImportError:
    import re
    def clean_html_for_display(content: str, max_length: int = 100) -> str:
        if not content:
            return ""
        content = re.sub(r'<[^>]+>', '', content)
        content = re.sub(r'\s+', ' ', content).strip()
        return content[:max_length] + ("..." if len(content) > max_length else "")
    
    def clean_title(title: str) -> str:
        if not title:
            return ""
        return re.sub(r'<[^>]+>', '', title).strip()


def render_hotel_booking_page(config_manager):
    """Render the hotel booking management page"""
    
    st.title("🏨 Quản lý đặt phòng")
    
    # Get all hotel bookings
    try:
        hotel_bookings = config_manager.db_manager.get_all_hotel_bookings()
    except Exception as e:
        st.error(f"❌ Không thể tải danh sách đặt phòng: {str(e)}")
        return
    
    # Header with stats
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"**Tổng cộng:** {len(hotel_bookings)} lượt đặt phòng")
    
    with col2:
        if st.button("🔄 Làm mới", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("🆕 Đặt phòng mới", use_container_width=True, type="primary"):
            # Add a new booking message to chat
            st.session_state.messages = st.session_state.get("messages", [])
            st.session_state.messages.append({
                "role": "user",
                "content": "Tôi muốn đặt phòng khách sạn"
            })
            st.session_state.selected_page = "💬 Chat"
            st.rerun()
    
    if not hotel_bookings:
        # Empty state
        st.markdown("""
        <div style="text-align: center; padding: 3rem 0; color: #666;">
            <h3>🏨 Chưa có đặt phòng nào</h3>
            <p>Khi bạn đặt phòng qua chat, thông tin sẽ hiển thị tại đây</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Filter and search section
    with st.expander("🔍 Tìm kiếm & Lọc", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            search_query = st.text_input("Tìm kiếm theo tên khách hàng:", placeholder="Nhập tên...")
        
        with col2:
            status_filter = st.selectbox(
                "Lọc theo trạng thái:",
                ["Tất cả", "confirmed", "pending", "cancelled"]
            )
    
    # Filter bookings
    filtered_bookings = filter_hotel_bookings(hotel_bookings, search_query, status_filter)
    
    if search_query and not filtered_bookings:
        st.warning(f"🔍 Không tìm thấy đặt phòng nào với từ khóa: **{search_query}**")
        return
    
    # Sort bookings by created date (newest first)
    sorted_bookings = sorted(filtered_bookings, 
                           key=lambda x: x.get('created_at', ''), 
                           reverse=True)
    
    # Display bookings
    st.markdown("---")
    
    for booking in sorted_bookings:
        display_hotel_booking_card(booking)
        st.markdown("---")


def filter_hotel_bookings(bookings: List[Dict], search_query: str, status_filter: str) -> List[Dict]:
    """Filter hotel bookings based on search and status"""
    
    filtered = bookings.copy()
    
    # Search filter
    if search_query:
        search_lower = search_query.lower()
        filtered = [
            booking for booking in filtered 
            if search_lower in booking.get('customer_name', '').lower()
            or search_lower in booking.get('hotel_name', '').lower()
            or search_lower in booking.get('location', '').lower()
        ]
    
    # Status filter
    if status_filter != "Tất cả":
        filtered = [
            booking for booking in filtered
            if booking.get('status', '') == status_filter
        ]
    
    return filtered


def display_hotel_booking_card(booking: Dict):
    """Display a single hotel booking card"""
    
    # Clean data for display
    booking_id = booking.get('id', 'N/A')
    customer_name = clean_title(booking.get('customer_name', 'N/A'))
    hotel_name = clean_html_for_display(booking.get('hotel_name', 'N/A'), 50)
    location = clean_html_for_display(booking.get('location', 'N/A'), 50)
    check_in = booking.get('check_in_date', 'N/A')
    check_out = booking.get('check_out_date', 'N/A')
    room_type = booking.get('room_type', 'N/A')
    guests = booking.get('guests', 'N/A')
    status = booking.get('status', 'pending')
    created_at = booking.get('created_at', 'N/A')
    
    # Status styling
    status_colors = {
        'confirmed': '#4CAF50',
        'pending': '#FF9800', 
        'cancelled': '#F44336'
    }
    status_icons = {
        'confirmed': '✅',
        'pending': '⏳',
        'cancelled': '❌'
    }
    
    status_color = status_colors.get(status, '#9E9E9E')
    status_icon = status_icons.get(status, '⚪')
    status_text = f"{status_icon} {status.title()}"
    
    # Format date
    try:
        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        created_str = created_date.strftime("%d/%m/%Y %H:%M")
    except:
        created_str = "N/A"
    
    # Create card using Streamlit components
    with st.container():
        # Header row
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### 🏨 Đặt phòng #{booking_id}")
            st.markdown(f"**👤 Khách hàng:** {customer_name}")
        
        with col2:
            st.markdown(f"<div style='text-align: right; color: {status_color}; font-weight: 500;'>{status_text}</div>", 
                       unsafe_allow_html=True)
        
        # Booking details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**🏨 Khách sạn:** {hotel_name}")
            st.markdown(f"**📍 Địa điểm:** {location}")
        
        with col2:
            st.markdown(f"**📅 Nhận phòng:** {check_in}")
            st.markdown(f"**📅 Trả phòng:** {check_out}")
        
        with col3:
            st.markdown(f"**🛏️ Loại phòng:** {room_type}")
            st.markdown(f"**👥 Số khách:** {guests}")
            st.markdown(f"**📅 Đặt lúc:** {created_str}")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            if st.button("📋 Chi tiết", key=f"details_{booking_id}", use_container_width=True):
                show_hotel_booking_details(booking)
        
        with col2:
            if status == 'pending' and st.button("✅ Xác nhận", key=f"confirm_{booking_id}", use_container_width=True):
                update_hotel_booking_status(booking_id, 'confirmed')
                st.rerun()
        
        with col3:
            if status != 'cancelled' and st.button("❌ Hủy", key=f"cancel_{booking_id}", use_container_width=True):
                update_hotel_booking_status(booking_id, 'cancelled')
                st.rerun()
        
        with col4:
            if st.button("🗑️ Xóa", key=f"delete_{booking_id}", use_container_width=True, type="secondary"):
                if st.session_state.get(f"confirm_delete_hotel_{booking_id}"):
                    delete_hotel_booking(booking_id)
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_hotel_{booking_id}"] = True
                    st.warning("⚠️ Click lại để xác nhận xóa")


def show_hotel_booking_details(booking: Dict):
    """Show detailed information about a hotel booking"""
    
    booking_id = booking.get('id', 'N/A')
    
    with st.expander(f"📋 Chi tiết đặt phòng #{booking_id}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**👤 Thông tin khách hàng:**")
            st.markdown(f"- Tên: {clean_title(booking.get('customer_name', 'N/A'))}")
            st.markdown(f"- SĐT: {booking.get('customer_phone', 'N/A')}")
            st.markdown(f"- Email: {booking.get('customer_email', 'N/A')}")
            
            st.markdown("**🏨 Thông tin khách sạn:**")
            st.markdown(f"- Tên: {clean_html_for_display(booking.get('hotel_name', 'N/A'), 100)}")
            st.markdown(f"- Địa chỉ: {clean_html_for_display(booking.get('location', 'N/A'), 100)}")
        
        with col2:
            st.markdown("**🛏️ Thông tin phòng:**")
            st.markdown(f"- Loại phòng: {booking.get('room_type', 'N/A')}")
            st.markdown(f"- Số phòng: {booking.get('rooms', 'N/A')}")
            st.markdown(f"- Số khách: {booking.get('guests', 'N/A')}")
            
            st.markdown("**📅 Thời gian:**")
            st.markdown(f"- Nhận phòng: {booking.get('check_in_date', 'N/A')}")
            st.markdown(f"- Trả phòng: {booking.get('check_out_date', 'N/A')}")
            st.markdown(f"- Số đêm: {booking.get('nights', 'N/A')}")
        
        # Pricing info if available
        if booking.get('total_price'):
            st.markdown("**💰 Thông tin giá:**")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"- Tổng tiền: {booking.get('total_price', 'N/A')}")
            with col2:
                st.markdown(f"- Trạng thái: {booking.get('status', 'N/A')}")
        
        # Additional details
        if booking.get('special_requests'):
            st.markdown("**📝 Yêu cầu đặc biệt:**")
            st.markdown(clean_html_for_display(booking.get('special_requests', ''), 300))


def update_hotel_booking_status(booking_id: str, new_status: str):
    """Update hotel booking status"""
    try:
        from src.config_manager import ConfigManager
        config_manager = ConfigManager()
        
        if config_manager.db_manager.update_hotel_booking_status(booking_id, new_status):
            st.success(f"✅ Đã cập nhật trạng thái đặt phòng #{booking_id} thành {new_status}")
        else:
            st.error(f"❌ Không thể cập nhật trạng thái đặt phòng #{booking_id}")
    except Exception as e:
        st.error(f"❌ Lỗi khi cập nhật trạng thái: {str(e)}")


def delete_hotel_booking(booking_id: str):
    """Delete a hotel booking"""
    try:
        from src.config_manager import ConfigManager
        config_manager = ConfigManager()
        
        if config_manager.db_manager.delete_hotel_booking(booking_id):
            st.success(f"✅ Đã xóa đặt phòng #{booking_id}")
        else:
            st.error(f"❌ Không thể xóa đặt phòng #{booking_id}")
    except Exception as e:
        st.error(f"❌ Lỗi khi xóa đặt phòng: {str(e)}")