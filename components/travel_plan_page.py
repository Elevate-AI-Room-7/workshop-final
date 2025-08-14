"""
Travel Plan Management Page Component
Allows users to view, manage, and interact with saved travel plans
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Any

def render_travel_plan_page(config_manager):
    """Render the travel plan management page"""
    st.title("🧳 Quản lý kế hoạch du lịch")
    
    # Get all travel plans
    try:
        travel_plans = config_manager.db_manager.get_all_travel_plans()
    except Exception as e:
        st.error(f"❌ Không thể tải danh sách kế hoạch du lịch: {str(e)}")
        return
    
    if not travel_plans:
        st.info("📝 Chưa có kế hoạch du lịch nào. Hãy tạo kế hoạch mới thông qua chat!")
        st.markdown("""
        ### 💡 Hướng dẫn tạo kế hoạch du lịch:
        
        1. Chuyển về trang **💬 Chat**
        2. Nói với trợ lý: *"Tôi muốn lên kế hoạch du lịch"*
        3. Cung cấp thông tin khi được hỏi:
           - Điểm đến
           - Thời gian và thời lượng
           - Số người tham gia
           - Ngân sách
           - Yêu cầu về visa/sức khỏe
        4. Xác nhận thông tin để lưu kế hoạch
        """)
        return
    
    # Display summary statistics
    st.markdown("### 📊 Tổng quan")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tổng kế hoạch", len(travel_plans))
    
    with col2:
        planning_plans = len([p for p in travel_plans if get_plan_status(p) == "planning"])
        st.metric("Đang lên kế hoạch", planning_plans)
    
    with col3:
        active_plans = len([p for p in travel_plans if get_plan_status(p) == "active"])
        st.metric("Đang thực hiện", active_plans)
    
    with col4:
        completed_plans = len([p for p in travel_plans if get_plan_status(p) == "completed"])
        st.metric("Đã hoàn thành", completed_plans)
    
    st.markdown("---")
    
    # Search and filter section
    st.markdown("### 🔍 Tìm kiếm và lọc")
    
    col1, col2 = st.columns(2)
    
    with col1:
        search_query = st.text_input(
            "Tìm kiếm theo điểm đến hoặc tên kế hoạch",
            placeholder="Ví dụ: Đà Nẵng, Sapa, ..."
        )
    
    with col2:
        status_filter = st.selectbox(
            "Lọc theo trạng thái",
            ["Tất cả", "Đang lên kế hoạch", "Đang thực hiện", "Đã hoàn thành"]
        )
    
    # Filter plans
    filtered_plans = travel_plans
    
    if search_query:
        filtered_plans = [
            plan for plan in filtered_plans
            if search_query.lower() in plan.get('title', '').lower() or
               search_query.lower() in get_destination_name(plan).lower()
        ]
    
    if status_filter != "Tất cả":
        status_map = {
            "Đang lên kế hoạch": "planning",
            "Đang thực hiện": "active", 
            "Đã hoàn thành": "completed"
        }
        target_status = status_map.get(status_filter)
        if target_status:
            filtered_plans = [p for p in filtered_plans if get_plan_status(p) == target_status]
    
    st.markdown("---")
    
    # Display travel plans
    st.markdown(f"### 📋 Danh sách kế hoạch ({len(filtered_plans)})")
    
    if not filtered_plans:
        st.info("🔍 Không tìm thấy kế hoạch nào phù hợp với tiêu chí tìm kiếm.")
        return
    
    # Sort plans by created date (newest first)
    try:
        filtered_plans.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    except:
        pass
    
    for plan in filtered_plans:
        render_travel_plan_card(plan, config_manager)

def render_travel_plan_card(plan: Dict[str, Any], config_manager):
    """Render a single travel plan card"""
    
    # Parse plan data
    plan_id = plan.get('id', 'Unknown')
    title = plan.get('title', 'Kế hoạch du lịch')
    destination = get_destination_name(plan)
    status = get_plan_status(plan)
    created_at = plan.get('created_at', '')
    
    # Parse JSON fields
    destination_data = safe_json_parse(plan.get('destination_data', '{}'))
    dates_data = safe_json_parse(plan.get('dates_data', '{}'))
    duration_data = safe_json_parse(plan.get('duration_data', '{}'))
    participants_data = safe_json_parse(plan.get('participants_data', '{}'))
    budget_data = safe_json_parse(plan.get('budget_data', '{}'))
    
    # Status styling
    status_colors = {
        "planning": "🔵 Đang lên kế hoạch",
        "active": "🟢 Đang thực hiện", 
        "completed": "✅ Đã hoàn thành",
        "cancelled": "❌ Đã hủy"
    }
    
    status_display = status_colors.get(status, f"⚪ {status}")
    
    # Create expandable card
    with st.expander(f"🧳 {title} - {destination}", expanded=False):
        # Basic info
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **📍 Điểm đến:** {destination}  
            **📅 Thời gian:** {dates_data.get('start_date', 'Chưa xác định')}  
            **⏱️ Thời lượng:** {duration_data.get('total_days', 'N/A')} ngày  
            **👥 Số người:** {participants_data.get('total', 1)}  
            """)
        
        with col2:
            st.markdown(f"""
            **🏷️ Trạng thái:** {status_display}  
            **💰 Ngân sách:** {format_budget(budget_data)}  
            **📅 Tạo lúc:** {format_datetime(created_at)}  
            **🆔 ID:** `{plan_id[:8]}...`  
            """)
        
        # Detailed information in tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Chi tiết", "🎯 Hoạt động", "🏨 Sở thích", "⚙️ Hành động"])
        
        with tab1:
            render_plan_details(plan)
        
        with tab2:
            render_plan_activities(plan)
        
        with tab3:
            render_plan_preferences(plan)
            
        with tab4:
            render_plan_actions(plan, config_manager)

def render_plan_details(plan: Dict[str, Any]):
    """Render detailed plan information"""
    
    # Parse JSON data
    destination_data = safe_json_parse(plan.get('destination_data', '{}'))
    dates_data = safe_json_parse(plan.get('dates_data', '{}'))
    duration_data = safe_json_parse(plan.get('duration_data', '{}'))
    participants_data = safe_json_parse(plan.get('participants_data', '{}'))
    budget_data = safe_json_parse(plan.get('budget_data', '{}'))
    requirements_data = safe_json_parse(plan.get('requirements_data', '{}'))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Địa điểm")
        st.markdown(f"""
        - **Điểm đến chính:** {destination_data.get('primary', 'N/A')}
        - **Quốc gia:** {destination_data.get('country', 'N/A')}
        - **Vùng miền:** {destination_data.get('region', 'N/A')}
        """)
        
        st.markdown("#### 👥 Thông tin người tham gia")
        st.markdown(f"""
        - **Tổng số người:** {participants_data.get('total', 1)}
        - **Người lớn:** {participants_data.get('adults', 1)}
        - **Trẻ em:** {participants_data.get('children', 0)}
        """)
    
    with col2:
        st.markdown("#### 📅 Thời gian")
        st.markdown(f"""
        - **Ngày bắt đầu:** {dates_data.get('start_date', 'Chưa xác định')}
        - **Thời lượng:** {duration_data.get('total_days', 'N/A')} ngày
        - **Đơn vị:** {duration_data.get('unit', 'days')}
        - **Linh hoạt:** {'Có' if dates_data.get('flexible') else 'Không'}
        """)
        
        st.markdown("#### 💰 Ngân sách")
        budget_amount = budget_data.get('total_amount', 'N/A')
        budget_currency = budget_data.get('currency', 'VND')
        per_person = budget_data.get('per_person', 'N/A')
        
        if budget_amount != 'N/A':
            st.markdown(f"""
            - **Tổng ngân sách:** {budget_amount:,} {budget_currency}
            - **Mỗi người:** {per_person:,} {budget_currency}
            - **Mức độ:** {budget_data.get('level', 'N/A')}
            """)
        else:
            st.markdown(f"- **Mức độ:** {budget_data.get('level', 'Chưa xác định')}")
    
    # Requirements
    if requirements_data:
        st.markdown("#### 📋 Yêu cầu")
        visa_req = requirements_data.get('visa', {})
        health_req = requirements_data.get('health', {})
        
        if visa_req:
            st.markdown(f"**Visa:** {visa_req.get('status', 'N/A')}")
        if health_req:
            st.markdown(f"**Y tế:** {health_req.get('vaccination_status', 'N/A')}")

def render_plan_activities(plan: Dict[str, Any]):
    """Render plan activities and itinerary"""
    
    activities_data = safe_json_parse(plan.get('activities_data', '[]'))
    itinerary_data = safe_json_parse(plan.get('itinerary_data', '[]'))
    
    if activities_data:
        st.markdown("#### 🎯 Hoạt động yêu thích")
        for activity in activities_data:
            st.markdown(f"- {activity}")
    else:
        st.info("Chưa có hoạt động nào được xác định.")
    
    if itinerary_data:
        st.markdown("#### 📅 Lịch trình chi tiết") 
        for day_plan in itinerary_data:
            st.markdown(f"**{day_plan.get('day', 'N/A')}:** {day_plan.get('activities', 'N/A')}")
    else:
        st.info("Chưa có lịch trình chi tiết.")

def render_plan_preferences(plan: Dict[str, Any]):
    """Render plan preferences"""
    
    preferences_data = safe_json_parse(plan.get('preferences_data', '{}'))
    logistics_data = safe_json_parse(plan.get('logistics_data', '{}'))
    
    if preferences_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎨 Phong cách du lịch")
            st.markdown(f"- {preferences_data.get('travel_style', 'Chưa xác định')}")
            
            accommodations = preferences_data.get('accommodations', {})
            if accommodations:
                st.markdown("#### 🏨 Lưu trú")
                st.markdown(f"- **Loại:** {accommodations.get('type', 'N/A')}")
                st.markdown(f"- **Mức giá:** {accommodations.get('budget_level', 'N/A')}")
        
        with col2:
            transportation = preferences_data.get('transportation', {})
            if transportation:
                st.markdown("#### 🚗 Di chuyển")
                st.markdown(f"- **Chính:** {transportation.get('primary', 'N/A')}")
            
            meals = preferences_data.get('meals', {})
            if meals:
                st.markdown("#### 🍽️ Ăn uống")
                if meals.get('vegetarian'):
                    st.markdown("- Ăn chay")
                if meals.get('halal'):
                    st.markdown("- Halal")
                fav_cuisines = meals.get('favorite_cuisines', [])
                if fav_cuisines:
                    st.markdown(f"- **Yêu thích:** {', '.join(fav_cuisines)}")
    else:
        st.info("Chưa có thông tin sở thích.")

def render_plan_actions(plan: Dict[str, Any], config_manager):
    """Render plan action buttons"""
    
    plan_id = plan.get('id')
    current_status = get_plan_status(plan)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Cập nhật trạng thái", key=f"status_{plan_id}"):
            render_status_update_dialog(plan_id, current_status, config_manager)
    
    with col2:
        if st.button("📝 Chỉnh sửa", key=f"edit_{plan_id}"):
            st.info("Tính năng chỉnh sửa sẽ được phát triển trong tương lai.")
    
    with col3:
        if st.button("📄 Xuất PDF", key=f"export_{plan_id}"):
            st.info("Tính năng xuất PDF sẽ được phát triển trong tương lai.")
    
    with col4:
        if st.button("🗑️ Xóa", key=f"delete_{plan_id}", type="secondary"):
            if st.button(f"⚠️ Xác nhận xóa", key=f"confirm_delete_{plan_id}"):
                try:
                    success = config_manager.db_manager.delete_travel_plan(plan_id)
                    if success:
                        st.success("✅ Đã xóa kế hoạch du lịch!")
                        st.rerun()
                    else:
                        st.error("❌ Không thể xóa kế hoạch.")
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")

def render_status_update_dialog(plan_id: str, current_status: str, config_manager):
    """Render status update dialog"""
    
    status_options = ["planning", "active", "completed", "cancelled"]
    status_labels = {
        "planning": "🔵 Đang lên kế hoạch",
        "active": "🟢 Đang thực hiện",
        "completed": "✅ Đã hoàn thành", 
        "cancelled": "❌ Đã hủy"
    }
    
    new_status = st.selectbox(
        "Chọn trạng thái mới:",
        status_options,
        index=status_options.index(current_status) if current_status in status_options else 0,
        format_func=lambda x: status_labels.get(x, x),
        key=f"new_status_{plan_id}"
    )
    
    if st.button(f"Cập nhật trạng thái", key=f"update_status_{plan_id}"):
        try:
            success = config_manager.db_manager.update_travel_plan_status(plan_id, new_status)
            if success:
                st.success(f"✅ Đã cập nhật trạng thái thành: {status_labels.get(new_status, new_status)}")
                st.rerun()
            else:
                st.error("❌ Không thể cập nhật trạng thái.")
        except Exception as e:
            st.error(f"❌ Lỗi: {str(e)}")

# Helper functions
def safe_json_parse(json_str: str) -> Dict[str, Any]:
    """Safely parse JSON string, return empty dict on error"""
    try:
        if not json_str or json_str == 'NULL':
            return {}
        return json.loads(json_str)
    except:
        return {}

def get_destination_name(plan: Dict[str, Any]) -> str:
    """Get destination name from plan"""
    destination_data = safe_json_parse(plan.get('destination_data', '{}'))
    return destination_data.get('primary', 'Không xác định')

def get_plan_status(plan: Dict[str, Any]) -> str:
    """Get plan status"""
    status_data = safe_json_parse(plan.get('status_data', '{}'))
    return status_data.get('current', 'planning')

def format_budget(budget_data: Dict[str, Any]) -> str:
    """Format budget display"""
    amount = budget_data.get('total_amount')
    currency = budget_data.get('currency', 'VND')
    level = budget_data.get('level', '')
    
    if amount:
        return f"{amount:,} {currency}"
    elif level:
        level_map = {
            'budget': 'Tiết kiệm',
            'medium': 'Trung bình', 
            'luxury': 'Cao cấp',
            'flexible': 'Linh hoạt'
        }
        return level_map.get(level, level)
    else:
        return 'Chưa xác định'

def format_datetime(datetime_str: str) -> str:
    """Format datetime string for display"""
    try:
        if not datetime_str:
            return 'N/A'
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%Y %H:%M')
    except:
        return datetime_str if datetime_str else 'N/A'