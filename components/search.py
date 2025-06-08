import streamlit as st
from typing import Dict, List, Optional, Any

def search_interface():
    """
    Render the search interface for finding campus locations.
    """
    search_query = st.text_input(
        "Search campus locations",
        placeholder="Enter department, building, floor, or room name",
        key="search_box"
    )
    
    if st.button("Search", key="search_button") or search_query:
        if search_query and len(search_query) >= 2:
            # Execute search if query is at least 2 characters
            results = st.session_state.data_manager.search(search_query)
            st.session_state.search_results = results
            
            # Display search results
            _display_search_results(results)
        elif search_query:
            st.warning("Please enter at least 2 characters to search.")
        else:
            st.info("Enter a search term to find campus locations.")

def _display_search_results(results: Dict[str, List[Dict]]):
    """
    Display the search results in an organized manner.
    
    Args:
        results: Dictionary with results by category
    """
    # Count total results
    total_results = sum(len(items) for items in results.values())
    
    if total_results == 0:
        st.warning("No results found. Try a different search term.")
        return
    
    st.success(f"Found {total_results} results")
    
    # Create tabs for different result categories
    if len(results['departments']) > 0:
        with st.expander(f"Departments ({len(results['departments'])})", expanded=True):
            _display_result_items(results['departments'], 'department')
    
    if len(results['buildings']) > 0:
        with st.expander(f"Buildings ({len(results['buildings'])})", expanded=True):
            _display_result_items(results['buildings'], 'building')
    
    if len(results['floors']) > 0:
        with st.expander(f"Floors ({len(results['floors'])})", expanded=True):
            _display_result_items(results['floors'], 'floor')
    
    if len(results['rooms']) > 0:
        with st.expander(f"Rooms ({len(results['rooms'])})", expanded=True):
            _display_result_items(results['rooms'], 'room')

def _display_result_items(items: List[Dict], item_type: str):
    """
    Display a list of result items with navigation buttons.
    
    Args:
        items: List of items to display
        item_type: Type of items being displayed
    """
    for item in items:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if item_type == 'department':
                st.markdown(f"**{item['name']}**")
                if item.get('description'):
                    st.caption(item['description'])
            elif item_type == 'building':
                # Get parent department
                dept = st.session_state.data_manager.get_parent(item_type, item['id'])
                dept_name = dept['name'] if dept else "Unknown Department"
                
                st.markdown(f"**{item['name']}** ({dept_name})")
                if item.get('description'):
                    st.caption(item['description'])
            elif item_type == 'floor':
                # Get parent building
                building = st.session_state.data_manager.get_parent(item_type, item['id'])
                building_name = building['name'] if building else "Unknown Building"
                
                st.markdown(f"**{item['name']}** ({building_name})")
                if item.get('description'):
                    st.caption(item['description'])
            elif item_type == 'room':
                # Get parent floor
                floor = st.session_state.data_manager.get_parent(item_type, item['id'])
                floor_name = "Unknown Floor"
                building_name = "Unknown Building"
                
                if floor:
                    floor_name = floor['name']
                    building = st.session_state.data_manager.get_parent('floor', floor['id'])
                    if building:
                        building_name = building['name']
                
                st.markdown(f"**{item['name']}** - {item['type']}")
                st.caption(f"{building_name}, {floor_name}")
                if item.get('description'):
                    st.caption(item['description'])
                st.caption(f"Capacity: {item['capacity']}")
        
        with col2:
            if st.button("View", key=f"view_{item_type}_{item['id']}"):
                # Set selected item and update view
                parent_type = None
                parent_id = None
                
                if item_type == 'department':
                    st.session_state.current_view = 'buildings'
                    st.session_state.nav_history = ['departments']
                elif item_type == 'building':
                    st.session_state.current_view = 'floors'
                    st.session_state.nav_history = ['departments', 'buildings']
                    parent_type = 'department'
                    parent_id = item['department_id']
                elif item_type == 'floor':
                    st.session_state.current_view = 'rooms'
                    st.session_state.nav_history = ['departments', 'buildings', 'floors']
                    parent_type = 'building'
                    parent_id = item['building_id']
                elif item_type == 'room':
                    st.session_state.current_view = 'rooms'
                    st.session_state.nav_history = ['departments', 'buildings', 'floors']
                    parent_type = 'floor'
                    parent_id = item['floor_id']
                
                st.session_state.selected_item = (item['id'], item_type)
                
                if parent_type and parent_id:
                    st.session_state.parent_item = (parent_id, parent_type)
                
                st.rerun()
        
        st.divider()
