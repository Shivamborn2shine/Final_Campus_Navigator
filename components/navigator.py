import streamlit as st
from typing import List, Dict, Tuple, Optional

def navigator_interface():
    """
    Render the hierarchical navigation interface for the campus map.
    """
    # Display current navigation path
    _display_breadcrumbs()
    
    # Display the items for the current view
    if st.session_state.current_view == 'departments':
        _display_departments()
    elif st.session_state.current_view == 'buildings':
        _display_buildings()
    elif st.session_state.current_view == 'floors':
        _display_floors()
    elif st.session_state.current_view == 'rooms':
        _display_rooms()

def _display_breadcrumbs():
    """Display navigation breadcrumbs."""
    if not st.session_state.data_manager.has_data():
        return
    
    # Create breadcrumb navigation
    cols = st.columns(4)
    
    # Department level
    with cols[0]:
        if "departments" in st.session_state.nav_history or st.session_state.current_view == "departments":
            btn_style = "primary" if st.session_state.current_view == "departments" else "secondary"
            if st.button("Departments", key="nav_dept", type=btn_style):
                st.session_state.current_view = "departments"
                st.session_state.nav_history = []
                st.session_state.selected_item = None
                st.session_state.parent_item = None
                st.rerun()
    
    # Building level
    with cols[1]:
        if "buildings" in st.session_state.nav_history or st.session_state.current_view == "buildings":
            btn_style = "primary" if st.session_state.current_view == "buildings" else "secondary"
            
            # Display selected department name if available
            label = "Buildings"
            if st.session_state.selected_item and st.session_state.current_view != "buildings":
                selected_dept = None
                # For rooms or floors view, we need to find the parent department
                if st.session_state.parent_item and st.session_state.parent_item[1] == 'department':
                    dept_id = st.session_state.parent_item[0]
                    selected_dept = st.session_state.data_manager.departments.get(dept_id)
                # For buildings view, we can get the department directly
                elif st.session_state.selected_item[1] == 'department':
                    dept_id = st.session_state.selected_item[0]
                    selected_dept = st.session_state.data_manager.departments.get(dept_id)
                
                if selected_dept:
                    label = f"{selected_dept['name']} Buildings"
                    
            if st.button(label, key="nav_building", type=btn_style):
                if st.session_state.selected_item and st.session_state.selected_item[1] == 'department':
                    # If we have a selected department, use it
                    st.session_state.current_view = "buildings"
                    st.session_state.nav_history = ['departments']
                elif st.session_state.parent_item and st.session_state.parent_item[1] == 'department':
                    # Use the parent department
                    st.session_state.current_view = "buildings"
                    st.session_state.nav_history = ['departments']
                    st.session_state.selected_item = st.session_state.parent_item
                st.rerun()
    
    # Floor level
    with cols[2]:
        if "floors" in st.session_state.nav_history or st.session_state.current_view == "floors":
            btn_style = "primary" if st.session_state.current_view == "floors" else "secondary"
            
            # Display selected building name if available
            label = "Floors"
            if st.session_state.selected_item and st.session_state.current_view != "floors":
                selected_building = None
                # For rooms view, we need to find the parent building
                if st.session_state.parent_item and st.session_state.parent_item[1] == 'building':
                    building_id = st.session_state.parent_item[0]
                    selected_building = st.session_state.data_manager.buildings.get(building_id)
                # For floors view, we can get the building directly
                elif st.session_state.selected_item[1] == 'building':
                    building_id = st.session_state.selected_item[0]
                    selected_building = st.session_state.data_manager.buildings.get(building_id)
                
                if selected_building:
                    label = f"{selected_building['name']} Floors"
            
            if st.button(label, key="nav_floor", type=btn_style):
                if st.session_state.selected_item and st.session_state.selected_item[1] == 'building':
                    # If we have a selected building, use it
                    st.session_state.current_view = "floors"
                    st.session_state.nav_history = ['departments', 'buildings']
                elif st.session_state.parent_item and st.session_state.parent_item[1] == 'building':
                    # Use the parent building
                    st.session_state.current_view = "floors"
                    st.session_state.nav_history = ['departments', 'buildings']
                    st.session_state.selected_item = st.session_state.parent_item
                st.rerun()
    
    # Room level
    with cols[3]:
        if "rooms" in st.session_state.nav_history or st.session_state.current_view == "rooms":
            btn_style = "primary" if st.session_state.current_view == "rooms" else "secondary"
            
            # Display selected floor name if available
            label = "Rooms"
            if st.session_state.selected_item and st.session_state.selected_item[1] == 'floor':
                floor_id = st.session_state.selected_item[0]
                selected_floor = st.session_state.data_manager.floors.get(floor_id)
                if selected_floor:
                    label = f"{selected_floor['name']} Rooms"
            
            if st.button(label, key="nav_room", type=btn_style):
                if st.session_state.selected_item and st.session_state.selected_item[1] == 'floor':
                    # If we have a selected floor, use it
                    st.session_state.current_view = "rooms"
                    st.session_state.nav_history = ['departments', 'buildings', 'floors']
                elif st.session_state.parent_item and st.session_state.parent_item[1] == 'floor':
                    # Use the parent floor
                    st.session_state.current_view = "rooms"
                    st.session_state.nav_history = ['departments', 'buildings', 'floors']
                    st.session_state.selected_item = st.session_state.parent_item
                st.rerun()

def _display_departments():
    """Display list of departments for navigation."""
    if not st.session_state.data_manager.has_data():
        st.info("No data available. Please import campus data using the sidebar.")
        return
    
    departments = st.session_state.data_manager.get_departments()
    
    if not departments:
        st.info("No departments found in the data.")
        return
    
    st.subheader("Departments")
    
    for dept in departments:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{dept['name']}**")
            if dept.get('description'):
                st.caption(dept['description'])
        
        with col2:
            if st.button("View", key=f"view_dept_{dept['id']}"):
                st.session_state.selected_item = (dept['id'], 'department')
                st.session_state.current_view = "buildings"
                st.session_state.nav_history = ['departments']
                st.session_state.parent_item = None
                st.rerun()
        
        st.divider()

def _display_buildings():
    """Display list of buildings for the selected department."""
    if not st.session_state.data_manager.has_data():
        st.info("No data available. Please import campus data using the sidebar.")
        return
    
    if not st.session_state.selected_item or st.session_state.selected_item[1] != 'department':
        st.info("Please select a department first.")
        return
    
    dept_id = st.session_state.selected_item[0]
    department = st.session_state.data_manager.departments.get(dept_id)
    
    if not department:
        st.error("Selected department not found.")
        return
    
    buildings = st.session_state.data_manager.get_buildings(dept_id)
    
    if not buildings:
        st.info(f"No buildings found for {department['name']}.")
        return
    
    st.subheader(f"Buildings in {department['name']}")
    
    for building in buildings:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{building['name']}**")
            if building.get('description'):
                st.caption(building['description'])
        
        with col2:
            if st.button("View", key=f"view_building_{building['id']}"):
                st.session_state.selected_item = (building['id'], 'building')
                st.session_state.current_view = "floors"
                st.session_state.nav_history = ['departments', 'buildings']
                st.session_state.parent_item = (dept_id, 'department')
                st.rerun()
        
        st.divider()

def _display_floors():
    """Display list of floors for the selected building."""
    if not st.session_state.data_manager.has_data():
        st.info("No data available. Please import campus data using the sidebar.")
        return
    
    if not st.session_state.selected_item or st.session_state.selected_item[1] != 'building':
        st.info("Please select a building first.")
        return
    
    building_id = st.session_state.selected_item[0]
    building = st.session_state.data_manager.buildings.get(building_id)
    
    if not building:
        st.error("Selected building not found.")
        return
    
    floors = st.session_state.data_manager.get_floors(building_id)
    
    if not floors:
        st.info(f"No floors found for {building['name']}.")
        return
    
    st.subheader(f"Floors in {building['name']}")
    
    for floor in floors:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{floor['name']}**")
            if floor.get('description'):
                st.caption(floor['description'])
        
        with col2:
            if st.button("View", key=f"view_floor_{floor['id']}"):
                st.session_state.selected_item = (floor['id'], 'floor')
                st.session_state.current_view = "rooms"
                st.session_state.nav_history = ['departments', 'buildings', 'floors']
                st.session_state.parent_item = (building_id, 'building')
                st.rerun()
        
        st.divider()

def _display_rooms():
    """Display list of rooms for the selected floor."""
    if not st.session_state.data_manager.has_data():
        st.info("No data available. Please import campus data using the sidebar.")
        return
    
    if not st.session_state.selected_item or st.session_state.selected_item[1] != 'floor':
        st.info("Please select a floor first.")
        return
    
    floor_id = st.session_state.selected_item[0]
    floor = st.session_state.data_manager.floors.get(floor_id)
    
    if not floor:
        st.error("Selected floor not found.")
        return
    
    rooms = st.session_state.data_manager.get_rooms(floor_id)
    
    if not rooms:
        st.info(f"No rooms found for {floor['name']}.")
        return
    
    st.subheader(f"Rooms on {floor['name']}")
    
    # Group rooms by type
    room_types = {}
    for room in rooms:
        room_type = room['type']
        if room_type not in room_types:
            room_types[room_type] = []
        room_types[room_type].append(room)
    
    # Display rooms grouped by type
    for room_type, type_rooms in room_types.items():
        with st.expander(f"{room_type} ({len(type_rooms)})", expanded=True):
            for room in type_rooms:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{room['name']}**")
                    details = []
                    if room.get('description'):
                        details.append(room['description'])
                    details.append(f"Capacity: {room['capacity']}")
                    if room.get('facilities'):
                        details.append(f"Facilities: {room['facilities']}")
                    if room.get('accessibility'):
                        details.append(f"Accessibility: {room['accessibility']}")
                    
                    st.caption(" | ".join(details))
                
                with col2:
                    if st.button("Details", key=f"view_room_{room['id']}"):
                        st.session_state.selected_item = (room['id'], 'room')
                        # Stay in rooms view but update selected item
                        st.session_state.parent_item = (floor_id, 'floor')
                        st.rerun()
                
                st.divider()
