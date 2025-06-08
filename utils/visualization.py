import networkx as nx
import plotly.graph_objects as go
import streamlit as st
from typing import Dict, Optional, Any, Tuple, List

def create_campus_map(data_manager, current_view, selected_item=None, parent_item=None):
    """
    Create a hierarchical visualization of the campus map based on the current view.
    
    Args:
        data_manager: The DataManager instance
        current_view: Current view level ('departments', 'buildings', 'floors', 'rooms')
        selected_item: Currently selected item (id, type)
        parent_item: Parent item for context (id, type)
    
    Returns:
        Plotly figure object
    """
    if not data_manager.has_data():
        # Return empty figure if no data
        return go.Figure()
    
    # Create a subgraph based on the current view
    if current_view == 'departments':
        nodes_to_include = ['root'] + [f"dept_{d['id']}" for d in data_manager.get_departments()]
        title = "Campus Departments"
        
    elif current_view == 'buildings':
        # Get buildings for the selected department
        dept_id = selected_item[0] if selected_item else None
        if not dept_id:
            return go.Figure()
        
        nodes_to_include = [f"dept_{dept_id}"] + [f"building_{b['id']}" for b in data_manager.get_buildings(dept_id)]
        title = f"Buildings - {data_manager.departments[dept_id]['name']}"
        
    elif current_view == 'floors':
        # Get floors for the selected building
        building_id = selected_item[0] if selected_item else None
        if not building_id:
            return go.Figure()
        
        nodes_to_include = [f"building_{building_id}"] + [f"floor_{f['id']}" for f in data_manager.get_floors(building_id)]
        title = f"Floors - {data_manager.buildings[building_id]['name']}"
        
    elif current_view == 'rooms':
        # Get rooms for the selected floor
        floor_id = selected_item[0] if selected_item else None
        if not floor_id:
            return go.Figure()
        
        # Check if floor_id is actually a room_id (happens with simple format data)
        if floor_id in data_manager.rooms:
            # This is a room ID, not a floor ID
            room = data_manager.rooms[floor_id]
            floor_id = room.get('floor_id', 'unknown')
            
        if floor_id not in data_manager.floors:
            # If we still don't have a valid floor, return an empty figure
            empty_fig = go.Figure()
            empty_fig.add_annotation(
                text="Unable to display rooms - floor data not found",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return empty_fig
        
        nodes_to_include = [f"floor_{floor_id}"] + [f"room_{r['id']}" for r in data_manager.get_rooms(floor_id)]
        title = f"Rooms - {data_manager.floors[floor_id]['name']}"
    
    else:
        # Default case
        return go.Figure()
    
    # Create a subgraph
    subgraph = data_manager.graph.subgraph(nodes_to_include)
    
    # Get positions using a layout algorithm
    if current_view == 'rooms':
        # For rooms, use the x/y coordinates from the data
        pos = {}
        for node in subgraph.nodes():
            if node.startswith('room_'):
                room_id = node.split('_')[1]
                x = data_manager.rooms[room_id]['x']
                y = data_manager.rooms[room_id]['y']
                pos[node] = (x, y)

            else:
                # Position the floor node in the center
                pos[node] = (50, 50)  # Assuming 0-100 range for coordinates
    elif current_view == 'floors':
        pos = {}
        
        # Step 1: Place floor nodes based on saved x/y coordinates
        for node in subgraph.nodes():
            if node.startswith('floor_'):
                floor_id = node.split('_')[1]
                floor_data = data_manager.floors.get(floor_id, {})
                x = floor_data.get('x', 50)
                y = floor_data.get('y', 50)
                pos[node] = (x, y)

        # Step 2: Position the building node (parent of floors) as average of its children
        for node in subgraph.nodes():
            if not node.startswith('floor_'):
                # Get average of floor positions
                floor_coords = list(pos.values())
                if floor_coords:
                    avg_x = sum(x for x, y in floor_coords) / len(floor_coords)
                    avg_y = sum(y for x, y in floor_coords) / len(floor_coords)
                    pos[node] = (avg_x, avg_y + 10)  # Slightly above the center
                else:
                    pos[node] = (50, 60)

    # elif current_view == 'buildings':
    #     pos = {}
    #     for node in subgraph.nodes():
    #         if node.startswith('building_'):
    #             building_id = node.split('_')[1]
    #             building_data = data_manager.buildings.get(building_id, {})

    #             # Use x and y if available, otherwise default to (50, 50)
    #             x = building_data.get('x', 50)
    #             y = building_data.get('y', 50)
    #             pos[node] = (x, y)
    #         else:
    #             # Place non-building nodes (like departments) at the center or use a fixed layout
    #             pos[node] = nx.spring_layout(subgraph, seed=42)





    else:
        # For other levels, use a radial layout with the parent in the center
        pos = nx.spring_layout(subgraph, seed=42)
    
    # Create the figure
    fig = go.Figure()
    
    # Collect edge trace data
    edge_x = []
    edge_y = []
    for edge in subgraph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    # Add edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    ))
    
    # Collect node data
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    node_info = []
    
    for node in subgraph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        # Get node attributes
        attrs = subgraph.nodes[node]
        node_type = attrs.get('type', '')
        node_name = attrs.get('name', '')
        
        # Set node properties based on type
        if node_type == 'root':
            color = '#1E88E5'  # blue
            size = 20
            text = 'Campus'
        elif node_type == 'department':
            color = '#43A047'  # green
            size = 15
            text = node_name
        elif node_type == 'building':
            color = '#FB8C00'  # orange
            size = 15
            text = node_name
        elif node_type == 'floor':
            color = '#8E24AA'  # purple
            size = 15
            text = node_name
        elif node_type == 'room':
            room_id = node.split('_')[1]
            room_type = data_manager.rooms[room_id]['type']
            
            # Different colors for room types
            if room_type.lower() == 'lecture':
                color = '#E53935'  # red
            elif room_type.lower() == 'lab':
                color = '#00ACC1'  # cyan
            elif room_type.lower() == 'office':
                color = '#7CB342'  # light green
            elif room_type.lower() == 'hall':
                color = '#FFB300'  # amber
            else:
                color = '#78909C'  # blue grey
            
            size = 10
            text = node_name
        else:
            color = '#78909C'  # blue grey
            size = 10
            text = node_name
        
        # Highlight selected node
        if selected_item and node.endswith(f"_{selected_item[0]}"):
            size *= 1.5
            color = '#D81B60'  # pink
        
        node_color.append(color)
        node_size.append(size)
        node_text.append(text)
        
        # Create hover text
        if node_type == 'room':
            room_id = node.split('_')[1]
            room = data_manager.rooms[room_id]
            hover_text = f"Room: {room['name']}<br>Type: {room['type']}<br>Capacity: {room['capacity']}"
            if room['facilities']:
                hover_text += f"<br>Facilities: {room['facilities']}"
        else:
            hover_text = f"{node_type.capitalize()}: {node_name}"
        
        node_info.append(hover_text)
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        marker=dict(
            color=node_color,
            size=node_size,
            line=dict(width=1, color='#333')
        ),
        text=node_text,
        textposition="top center",
        hoverinfo='text',
        hovertext=node_info,
        textfont=dict(size=10)
    ))
    
    # Layout customization
    fig.update_layout(
        title=title,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        height=600
    )
    
    return fig

def create_detail_map(data_manager, item_type, item_id):
    """
    Create a detailed visualization for a specific item.
    
    Args:
        data_manager: The DataManager instance
        item_type: Type of item ('department', 'building', 'floor', 'room')
        item_id: ID of the item
    
    Returns:
        Plotly figure object
    """
    if not data_manager.has_data():
        return go.Figure()
    
    # Create a figure based on the item type
    fig = go.Figure()
    
    if item_type == 'department':
        # Show buildings in this department
        buildings = data_manager.get_buildings(item_id)
        
        if not buildings:
            return go.Figure()
        
        # Create a bar chart of buildings by number of rooms
        building_names = []
        room_counts = []
        
        for building in buildings:
            building_id = building['id']
            floors = data_manager.get_floors(building_id)
            room_count = 0
            
            for floor in floors:
                floor_id = floor['id']
                rooms = data_manager.get_rooms(floor_id)
                room_count += len(rooms)
            
            building_names.append(building['name'])
            room_counts.append(room_count)
        
        fig.add_trace(go.Bar(
            x=building_names,
            y=room_counts,
            text=room_counts,
            textposition='auto',
            marker_color='#1E88E5'
        ))
        
        fig.update_layout(
            title=f"Room Count by Building in {data_manager.departments[item_id]['name']}",
            xaxis_title="Building",
            yaxis_title="Number of Rooms"
        )
    
    elif item_type == 'building':
        # Show floors in this building with room distribution
        floors = data_manager.get_floors(item_id)
        
        if not floors:
            return go.Figure()
        
        floor_names = []
        lecture_rooms = []
        labs = []
        offices = []
        other_rooms = []
        
        for floor in floors:
            floor_id = floor['id']
            rooms = data_manager.get_rooms(floor_id)
            
            lecture_count = len([r for r in rooms if r['type'].lower() == 'lecture'])
            lab_count = len([r for r in rooms if r['type'].lower() == 'lab'])
            office_count = len([r for r in rooms if r['type'].lower() == 'office'])
            other_count = len([r for r in rooms if r['type'].lower() not in ['lecture', 'lab', 'office']])
            
            floor_names.append(floor['name'])
            lecture_rooms.append(lecture_count)
            labs.append(lab_count)
            offices.append(office_count)
            other_rooms.append(other_count)
        
        fig.add_trace(go.Bar(
            x=floor_names,
            y=lecture_rooms,
            name='Lecture Rooms',
            marker_color='#E53935'
        ))
        
        fig.add_trace(go.Bar(
            x=floor_names,
            y=labs,
            name='Labs',
            marker_color='#00ACC1'
        ))
        
        fig.add_trace(go.Bar(
            x=floor_names,
            y=offices,
            name='Offices',
            marker_color='#7CB342'
        ))
        
        fig.add_trace(go.Bar(
            x=floor_names,
            y=other_rooms,
            name='Other',
            marker_color='#78909C'
        ))
        
        fig.update_layout(
            title=f"Room Types by Floor in {data_manager.buildings[item_id]['name']}",
            xaxis_title="Floor",
            yaxis_title="Number of Rooms",
            barmode='stack'
        )
    
    # elif item_type == 'floor':
    #     # Show room layout on this floor
    #     rooms = data_manager.get_rooms(item_id)
        
    #     if not rooms:
    #         return go.Figure()
        
    #     # Use the x/y coordinates to create a floor plan
    #     room_x = [r['x'] for r in rooms]
    #     room_y = [r['y'] for r in rooms]
    #     room_text = [r['name'] for r in rooms]
    #     room_colors = []
    #     room_sizes = []
    #     hover_texts = []
        
    #     for room in rooms:
    #         room_type = room['type'].lower()
    #         capacity = room['capacity']
            
    #         # Different colors for room types
    #         if room_type == 'lecture':
    #             color = '#E53935'  # red
    #         elif room_type == 'lab':
    #             color = '#00ACC1'  # cyan
    #         elif room_type == 'office':
    #             color = '#7CB342'  # light green
    #         elif room_type == 'hall':
    #             color = '#FFB300'  # amber
    #         else:
    #             color = '#78909C'  # blue grey
            
    #         # Size based on capacity
    #         size = min(20 + (capacity / 5), 50)
            
    #         room_colors.append(color)
    #         room_sizes.append(size)
            
    #         # Create hover text
    #         hover_text = f"Room: {room['name']}<br>Type: {room['type']}<br>Capacity: {room['capacity']}"
    #         if room['facilities']:
    #             hover_text += f"<br>Facilities: {room['facilities']}"
            
    #         hover_texts.append(hover_text)
        
    #     fig.add_trace(go.Scatter(
    #         x=room_x,
    #         y=room_y,
    #         mode='markers+text',
    #         marker=dict(
    #             color=room_colors,
    #             size=room_sizes,
    #             line=dict(width=1, color='#333')
    #         ),
    #         text=room_text,
    #         textposition="top center",
    #         hoverinfo='text',
    #         hovertext=hover_texts
    #     ))
        
    #     # Add a legend for room types
    #     for room_type, color in [
    #         ('Lecture Room', '#E53935'),
    #         ('Lab', '#00ACC1'),
    #         ('Office', '#7CB342'),
    #         ('Hall', '#FFB300'),
    #         ('Other', '#78909C')
    #     ]:
    #         fig.add_trace(go.Scatter(
    #             x=[None],
    #             y=[None],
    #             mode='markers',
    #             marker=dict(size=10, color=color),
    #             name=room_type,
    #             showlegend=True
    #         ))
        
    #     fig.update_layout(
    #         title=f"Room Layout for {data_manager.floors[item_id]['name']}",
    #         showlegend=True,
    #         legend=dict(
    #             orientation="h",
    #             yanchor="bottom",
    #             y=1.02,
    #             xanchor="right",
    #             x=1
    #         ),
    #         xaxis=dict(
    #             range=[0, 100],
    #             showgrid=True,
    #             zeroline=True,
    #             showticklabels=False
    #         ),
    #         yaxis=dict(
    #             range=[0, 100],
    #             showgrid=True,
    #             zeroline=True,
    #             showticklabels=False
    #         ),
    #         plot_bgcolor='rgba(240,240,240,0.3)'
    #     )
    elif item_type == 'floor':
        rooms = data_manager.get_rooms(item_id)
        if not rooms:
            return go.Figure()
        
        # Create a more sophisticated floor plan
        fig = go.Figure()
        
        # Add room shapes instead of just points
        for room in rooms:
            # Calculate room dimensions (assuming x,y are center points)
            width = room.get('width', 10)  # default width if not provided
            height = room.get('height', 8)  # default height if not provided
            
            # Determine color based on room type
            color_map = {
                'lecture': '#E53935',
                'lab': '#00ACC1',
                'office': '#7CB342',
                'hall': '#FFB300'
            }
            color = color_map.get(room['type'].lower(), '#78909C')
            
            # Add rectangle shape for the room
            fig.add_shape(
                type="rect",
                x0=room['x'] - width/2,
                y0=room['y'] - height/2,
                x1=room['x'] + width/2,
                y1=room['y'] + height/2,
                line=dict(color="#333", width=1),
                fillcolor=color,
                opacity=0.7
            )
            
            # Add room label
            fig.add_annotation(
                x=room['x'],
                y=room['y'],
                text=room['name'],
                showarrow=False,
                font=dict(size=10)
            )
        
        # Add legend
        for room_type, color in color_map.items():
            fig.add_trace(go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                marker=dict(size=15, color=color),
                name=room_type.capitalize(),
                showlegend=True
            ))
        
        fig.update_layout(
            title=f"Floor Plan: {data_manager.floors[item_id]['name']}",
            showlegend=True,
            xaxis=dict(scaleanchor="y", showgrid=False),
            yaxis=dict(showgrid=False),
            plot_bgcolor='white',
            height=600
        )
    
    elif item_type == 'room':
        # Show detailed room information
        room = data_manager.rooms.get(item_id)
        
        if not room:
            return go.Figure()
        
        # Create a simple pie chart of room capacity
        fig.add_trace(go.Pie(
            labels=['Capacity', 'Available'],
            values=[room['capacity'], max(10, room['capacity'] * 0.2)],  # Add some buffer
            hole=0.6,
            marker=dict(colors=['#1E88E5', '#E0E0E0'])
        ))
        
        fig.update_layout(
            title=f"Room Capacity: {room['name']}",
            annotations=[dict(
                text=f"{room['capacity']}",
                x=0.5, y=0.5,
                font_size=20,
                showarrow=False
            )]
        )
    
    else:
        # Default case
        return go.Figure()
    
    return fig
