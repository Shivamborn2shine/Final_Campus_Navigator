import streamlit as st
import pandas as pd
from utils.visualization import create_detail_map

def details_view():
    """
    Render the details view for the selected campus item.
    """
    if not st.session_state.data_manager.has_data():
        st.info("No data available. Please import campus data using the sidebar.")
        _display_placeholder_images()
        return
    
    if not st.session_state.selected_item:
        st.info("Select a location from the navigation panel to view details.")
        _display_placeholder_images()
        return
    
    item_id, item_type = st.session_state.selected_item
    
    # Get details based on item type
    if item_type == 'department':
        _display_department_details(item_id)
    elif item_type == 'building':
        _display_building_details(item_id)
    elif item_type == 'floor':
        _display_floor_details(item_id)
    elif item_type == 'room':
        _display_room_details(item_id)
    else:
        st.error("Unknown item type.")

def _display_department_details(dept_id):
    """Display detailed information about a department."""
    department = st.session_state.data_manager.departments.get(dept_id)
    
    if not department:
        st.error("Department not found.")
        return
    
    st.header(department['name'])
    
    if department.get('description'):
        st.subheader("Description")
        st.write(department['description'])
    
    # Get buildings in this department
    buildings = st.session_state.data_manager.get_buildings(dept_id)
    
    # Display stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Buildings", len(buildings))
        
        # Count total rooms
        total_rooms = 0
        for building in buildings:
            floors = st.session_state.data_manager.get_floors(building['id'])
            for floor in floors:
                rooms = st.session_state.data_manager.get_rooms(floor['id'])
                total_rooms += len(rooms)
        
        st.metric("Total Rooms", total_rooms)
    
    with col2:
        # Count floors
        total_floors = 0
        for building in buildings:
            floors = st.session_state.data_manager.get_floors(building['id'])
            total_floors += len(floors)
        
        st.metric("Total Floors", total_floors)
        
        # Calculate total capacity
        total_capacity = 0
        for room in st.session_state.data_manager.rooms.values():
            # Check if room belongs to this department
            floor = st.session_state.data_manager.floors.get(room['floor_id'])
            if floor:
                building = st.session_state.data_manager.buildings.get(floor['building_id'])
                if building and building['department_id'] == dept_id:
                    total_capacity += room['capacity']
        
        st.metric("Total Capacity", total_capacity)
    
    # Display visualization
    st.subheader("Department Overview")
    fig = create_detail_map(st.session_state.data_manager, 'department', dept_id)
    st.plotly_chart(fig, use_container_width=True)
    
    # Display sample image
    st.image("https://pixabay.com/get/g1f1182d6afcd3f9bb48eac0b1a46e0f57f479068b2d7a7248461914d01aa17f475cda410763fca85fa207112536852f3fb036e3ecbdbf600b6292a837610300e_1280.jpg", 
             caption=f"{department['name']} Building Example", 
             use_column_width=True)

def _display_building_details(building_id):
    """Display detailed information about a building."""
    building = st.session_state.data_manager.buildings.get(building_id)
    
    if not building:
        st.error("Building not found.")
        return
    
    # Get parent department
    department = st.session_state.data_manager.departments.get(building['department_id'])
    dept_name = department['name'] if department else "Unknown Department"
    
    st.header(f"{building['name']}")
    st.subheader(f"Department: {dept_name}")
    
    if building.get('description'):
        st.write(building['description'])
    
    # Get floors in this building
    floors = st.session_state.data_manager.get_floors(building_id)
    
    # Display stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Floors", len(floors))
        
        # Count rooms by type
        room_types = {}
        total_rooms = 0
        
        for floor in floors:
            rooms = st.session_state.data_manager.get_rooms(floor['id'])
            total_rooms += len(rooms)
            
            for room in rooms:
                room_type = room['type']
                if room_type not in room_types:
                    room_types[room_type] = 0
                room_types[room_type] += 1
        
        st.metric("Total Rooms", total_rooms)
    
    with col2:
        # Calculate total capacity
        total_capacity = 0
        for floor in floors:
            for room in st.session_state.data_manager.get_rooms(floor['id']):
                total_capacity += room['capacity']
        
        st.metric("Total Capacity", total_capacity)
        
        # Display most common room type
        if room_types:
            most_common_type = max(room_types.items(), key=lambda x: x[1])
            st.metric("Most Common Room Type", f"{most_common_type[0]} ({most_common_type[1]})")
    
    # Display room types breakdown
    if room_types:
        st.subheader("Room Types")
        room_type_data = pd.DataFrame({
            'Type': list(room_types.keys()),
            'Count': list(room_types.values())
        })
        st.bar_chart(room_type_data.set_index('Type'))
    
    # Display visualization
    st.subheader("Building Overview")
    fig = create_detail_map(st.session_state.data_manager, 'building', building_id)
    st.plotly_chart(fig, use_container_width=True)
    
    # Display sample image
    st.image("https://pixabay.com/get/gf4528f2f5fccecbdf0deb7f3e8300bfb5a31b899670a2d6c817aa2765cd110df13ab29ae646d8525e138d46d3b159d15db029619e13c31f40e951f642e63af57_1280.jpg", 
             caption=f"{building['name']} Example", 
             use_column_width=True)

def _display_floor_details(floor_id):
    """Display detailed information about a floor."""
    floor = st.session_state.data_manager.floors.get(floor_id)
    
    if not floor:
        st.error("Floor not found.")
        return
    
    # Get parent building and department
    building = st.session_state.data_manager.buildings.get(floor['building_id'])
    building_name = building['name'] if building else "Unknown Building"
    
    department = None
    if building:
        department = st.session_state.data_manager.departments.get(building['department_id'])
    dept_name = department['name'] if department else "Unknown Department"
    
    st.header(f"{floor['name']}")
    st.subheader(f"{building_name}, {dept_name}")
    
    if floor.get('description'):
        st.write(floor['description'])
    
    # Get rooms on this floor
    rooms = st.session_state.data_manager.get_rooms(floor_id)
    
    # Display stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Rooms", len(rooms))
        
        # Count rooms by type
        room_types = {}
        for room in rooms:
            room_type = room['type']
            if room_type not in room_types:
                room_types[room_type] = 0
            room_types[room_type] += 1
        
        # Display most common room type
        if room_types:
            most_common_type = max(room_types.items(), key=lambda x: x[1])
            st.metric("Most Common Room Type", f"{most_common_type[0]} ({most_common_type[1]})")
    
    with col2:
        # Calculate total capacity
        total_capacity = sum(room['capacity'] for room in rooms)
        st.metric("Total Capacity", total_capacity)
        
        # Calculate average room capacity
        if rooms:
            avg_capacity = total_capacity / len(rooms)
            st.metric("Average Room Capacity", f"{avg_capacity:.1f}")
    
    # Display visualization
    st.subheader("Floor Plan")
    fig = create_detail_map(st.session_state.data_manager, 'floor', floor_id)
    st.plotly_chart(fig, use_container_width=True)
    
    # Display sample image
    st.image("https://pixabay.com/get/g176511e077f9a1c1235efd0117d0c0da8cb1ecdc5c8065ad7bc090ec621f24574ad6b3527e52e4c904a07fd340345c73a60e6059a0cbedfb688912a6ec8e900b_1280.jpg", 
             caption="University Hallway Example", 
             use_column_width=True)

def _display_room_details(room_id):
    """Display detailed information about a room."""
    room = st.session_state.data_manager.rooms.get(room_id)
    
    if not room:
        st.error("Room not found.")
        return
    
    # Get parent floor, building, and department
    floor = st.session_state.data_manager.floors.get(room['floor_id'])
    floor_name = floor['name'] if floor else "Unknown Floor"
    
    building = None
    if floor:
        building = st.session_state.data_manager.buildings.get(floor['building_id'])
    building_name = building['name'] if building else "Unknown Building"
    
    department = None
    if building:
        department = st.session_state.data_manager.departments.get(building['department_id'])
    dept_name = department['name'] if department else "Unknown Department"
    
    st.header(f"{room['name']}")
    st.subheader(f"{room['type']} | {building_name}, {floor_name}")
    
    if room.get('description'):
        st.write(room['description'])
    
    # Display details
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Capacity", room['capacity'])
        
        if room.get('facilities'):
            st.subheader("Facilities")
            facilities = room['facilities'].split(';')
            for facility in facilities:
                st.markdown(f"- {facility.strip()}")
    
    with col2:
        if room.get('accessibility'):
            st.metric("Accessibility", room['accessibility'])
        
        st.metric("Coordinates", f"X: {room['x']}, Y: {room['y']}")
    
    # Display visualization
    st.subheader("Room Details")
    fig = create_detail_map(st.session_state.data_manager, 'room', room_id)
    st.plotly_chart(fig, use_container_width=True)
    
    # Display appropriate sample image based on room type
    image_url = ""
    if room['type'].lower() == 'lecture':
        image_url = "https://pixabay.com/get/g812b797073a417c099430b1488d3c211ab3622af66ae5f6ca9e10b35769574c2b80d2b94b2349bf918bcb8c3c13cc93e0859cf619e4d6e311f32179c45a84593_1280.jpg"
    elif room['type'].lower() == 'lab':
        image_url = "https://pixabay.com/get/g8a114c87a84f08d0f7a9662692cde2757c5d43c122e0bb7ce201e26ff4775e3cdd6e9a699ee65983e362ea5595dc8c999a5d70b84748352613e1fa127b8d8b7f_1280.jpg"
    elif room['type'].lower() == 'hall':
        image_url = "https://pixabay.com/get/g2a49c9f697aceeca4f30b7c13dd8f5a3b8e1d7faf96bdaef8c1d6fe91bb105bdfb0fe30e6e7ea4408ada554b98a02042087537fd0014aac91743f88aa5acc9fa_1280.jpg"
    else:
        image_url = "https://pixabay.com/get/gd0c15c15436e3421f05495d1b93cc5c54979a3d4f1c150f243323ebeaa822cf76dd015fa0f74bc12cb366396c124e08480216df75c0698c3e057c4260dfac739_1280.jpg"
    
    st.image(image_url, caption=f"{room['type']} Example", use_column_width=True)

def _display_placeholder_images():
    """Display placeholder images when no data is selected."""
    # Display a grid of sample images
    col1, col2 = st.columns(2)
    
    with col1:
        st.image("assets/csit_sideview.jpg", 
        caption="CSIT", 
        use_column_width=True)

        
        st.image("https://pixabay.com/get/g176511e077f9a1c1235efd0117d0c0da8cb1ecdc5c8065ad7bc090ec621f24574ad6b3527e52e4c904a07fd340345c73a60e6059a0cbedfb688912a6ec8e900b_1280.jpg", 
                caption="University Hallway", 
                use_column_width=True)
    
    with col2:
        st.image("https://pixabay.com/get/g0e9f5d48186fe1575504b95f71a3729d0769511506e4003588b8ada51c4955b597a10f87f0663dda3749cfe7cbc74c0db86b8b1119bb3a63c6d53ce33b4c8890_1280.jpg", 
                caption="Campus Map", 
                use_column_width=True)
        
        st.image("https://pixabay.com/get/g812b797073a417c099430b1488d3c211ab3622af66ae5f6ca9e10b35769574c2b80d2b94b2349bf918bcb8c3c13cc93e0859cf619e4d6e311f32179c45a84593_1280.jpg", 
                caption="Lecture Room", 
                use_column_width=True)
