"""
Car Booking Management Page
Displays and manages car booking records
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


def render_car_booking_page(config_manager):
    """Render the car booking management page"""
    
    st.title("🚗 Quản lý đặt xe")
    
    # Get all car bookings
    try:
        car_bookings = config_manager.db_manager.get_all_car_bookings()
    except Exception as e:
        st.error(f"❌ Không thể tải danh sách đặt xe: {str(e)}")
        return
    
    # Header with stats
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"**Tổng cộng:** {len(car_bookings)} lượt đặt xe")
    
    with col2:
        if st.button("🔄 Làm mới", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("🆕 Đặt xe mới", use_container_width=True, type="primary"):
            # Add a new booking message to chat
            st.session_state.messages = st.session_state.get("messages", [])
            st.session_state.messages.append({
                "role": "user",
                "content": "Tôi muốn đặt xe"
            })
            st.session_state.selected_page = "💬 Chat"
            st.rerun()
    
    if not car_bookings:
        # Empty state
        st.markdown("""
        <div style="text-align: center; padding: 3rem 0; color: #666;">
            <h3>🚗 Chưa có đặt xe nào</h3>
            <p>Khi bạn đặt xe qua chat, thông tin sẽ hiển thị tại đây</p>
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
    filtered_bookings = filter_car_bookings(car_bookings, search_query, status_filter)
    
    if search_query and not filtered_bookings:
        st.warning(f"🔍 Không tìm thấy đặt xe nào với từ khóa: **{search_query}**")
        return
    
    # Sort bookings by created date (newest first)
    sorted_bookings = sorted(filtered_bookings, 
                           key=lambda x: x.get('created_at', ''), 
                           reverse=True)
    
    # Display bookings
    st.markdown("---")
    
    for booking in sorted_bookings:
        display_car_booking_card(booking)
        st.markdown("---")


def filter_car_bookings(bookings: List[Dict], search_query: str, status_filter: str) -> List[Dict]:
    """Filter car bookings based on search and status"""
    
    filtered = bookings.copy()
    
    # Search filter
    if search_query:
        search_lower = search_query.lower()
        filtered = [
            booking for booking in filtered 
            if search_lower in booking.get('customer_name', '').lower()
            or search_lower in booking.get('pickup_location', '').lower()
            or search_lower in booking.get('destination', '').lower()
        ]
    
    # Status filter
    if status_filter != "Tất cả":
        filtered = [
            booking for booking in filtered
            if booking.get('status', '') == status_filter
        ]
    
    return filtered


def display_car_booking_card(booking: Dict):
    """Display a single car booking card"""
    
    # Clean data for display
    booking_id = booking.get('id', 'N/A')
    customer_name = clean_title(booking.get('customer_name', 'N/A'))
    pickup_location = clean_html_for_display(booking.get('pickup_location', 'N/A'), 50)
    destination = clean_html_for_display(booking.get('destination', 'N/A'), 50)
    pickup_time = booking.get('pickup_time', 'N/A')
    car_type = booking.get('car_type', 'N/A')
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
            st.markdown(f"### 🚗 Đặt xe #{booking_id}")
            st.markdown(f"**👤 Khách hàng:** {customer_name}")
        
        with col2:
            st.markdown(f"<div style='text-align: right; color: {status_color}; font-weight: 500;'>{status_text}</div>", 
                       unsafe_allow_html=True)
        
        # Booking details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**📍 Điểm đón:** {pickup_location}")
            st.markdown(f"**🎯 Điểm đến:** {destination}")
        
        with col2:
            st.markdown(f"**🕐 Thời gian đón:** {pickup_time}")
            st.markdown(f"**🚙 Loại xe:** {car_type}")
        
        with col3:
            st.markdown(f"**📅 Đặt lúc:** {created_str}")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            if st.button("📋 Chi tiết", key=f"details_{booking_id}", use_container_width=True):
                show_car_booking_details(booking)
        
        with col2:
            if status == 'pending' and st.button("✅ Xác nhận", key=f"confirm_{booking_id}", use_container_width=True):
                update_car_booking_status(booking_id, 'confirmed')
                st.rerun()
        
        with col3:
            if status != 'cancelled' and st.button("❌ Hủy", key=f"cancel_{booking_id}", use_container_width=True):
                update_car_booking_status(booking_id, 'cancelled')
                st.rerun()
        
        with col4:
            if st.button("🗑️ Xóa", key=f"delete_{booking_id}", use_container_width=True, type="secondary"):
                if st.session_state.get(f"confirm_delete_car_{booking_id}"):
                    delete_car_booking(booking_id)
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_car_{booking_id}"] = True
                    st.warning("⚠️ Click lại để xác nhận xóa")


def show_car_booking_details(booking: Dict):
    """Show detailed information about a car booking"""
    
    booking_id = booking.get('id', 'N/A')
    
    with st.expander(f"📋 Chi tiết đặt xe #{booking_id}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**👤 Thông tin khách hàng:**")
            st.markdown(f"- Tên: {clean_title(booking.get('customer_name', 'N/A'))}")
            st.markdown(f"- SĐT: {booking.get('customer_phone', 'N/A')}")
            
            st.markdown("**📍 Thông tin chuyến đi:**")
            st.markdown(f"- Điểm đón: {clean_html_for_display(booking.get('pickup_location', 'N/A'), 100)}")
            st.markdown(f"- Điểm đến: {clean_html_for_display(booking.get('destination', 'N/A'), 100)}")
            st.markdown(f"- Thời gian đón: {booking.get('pickup_time', 'N/A')}")
        
        with col2:
            st.markdown("**🚙 Thông tin xe:**")
            st.markdown(f"- Loại xe: {booking.get('car_type', 'N/A')}")
            st.markdown(f"- Số ghế: {booking.get('seats', 'N/A')}")
            
            st.markdown("**📊 Trạng thái:**")
            st.markdown(f"- Trạng thái: {booking.get('status', 'N/A')}")
            st.markdown(f"- Đặt lúc: {booking.get('created_at', 'N/A')}")
        
        # Additional details
        if booking.get('notes'):
            st.markdown("**📝 Ghi chú:**")
            st.markdown(clean_html_for_display(booking.get('notes', ''), 300))


def update_car_booking_status(booking_id: str, new_status: str):
    """Update car booking status"""
    try:
        from src.config_manager import ConfigManager
        config_manager = ConfigManager()
        
        if config_manager.db_manager.update_car_booking_status(booking_id, new_status):
            st.success(f"✅ Đã cập nhật trạng thái đặt xe #{booking_id} thành {new_status}")
        else:
            st.error(f"❌ Không thể cập nhật trạng thái đặt xe #{booking_id}")
    except Exception as e:
        st.error(f"❌ Lỗi khi cập nhật trạng thái: {str(e)}")


def delete_car_booking(booking_id: str):
    """Delete a car booking"""
    try:
        from src.config_manager import ConfigManager
        config_manager = ConfigManager()
        
        if config_manager.db_manager.delete_car_booking(booking_id):
            st.success(f"✅ Đã xóa đặt xe #{booking_id}")
        else:
            st.error(f"❌ Không thể xóa đặt xe #{booking_id}")
    except Exception as e:
        st.error(f"❌ Lỗi khi xóa đặt xe: {str(e)}")