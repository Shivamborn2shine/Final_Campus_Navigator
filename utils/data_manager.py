import pandas as pd
import io
import os
import networkx as nx
from typing import Dict, List, Optional, Tuple, Any
from utils.db_models import (
    Department, Building, Floor, Room, 
    get_database_connection, initialize_database
)
from sqlalchemy.exc import SQLAlchemyError

class DataManager:
    """
    Manages all data operations for the Smart Campus Navigator
    including importing, exporting, and querying hierarchical campus data.
    """
    
    def __init__(self):
        """Initialize the data manager with empty data structures."""
        # Core dataframe to store all campus data
        self.df = pd.DataFrame()
        
        # Hierarchical structure: department -> building -> floor -> room
        self.graph = nx.DiGraph()
        
        # Mappings for quick access
        self.departments = {}
        self.buildings = {}
        self.floors = {}
        self.rooms = {}
        
        # Required columns for the standard CSV format
        self.standard_columns = [
            'department_id', 'department_name', 
            'building_id', 'building_name',
            'floor_id', 'floor_name',
            'room_id', 'room_name', 'room_type',
            'capacity', 'x_coordinate', 'y_coordinate'
        ]
        
        # Optional columns for the standard format
        self.optional_columns = [
            'department_description', 'building_description',
            'floor_description', 'room_description',
            'room_facilities', 'accessibility'
        ]
        



        # Simple format columns
        self.simple_format_columns = [
            'type', 'id', 'name', 'building_id', 'description','x', 'y'
        ]




        
        # Required columns (either standard or simple format)
        self.required_columns = []
        
        # Database connection
        try:
            self._initialize_database()
            self._load_from_database()
        except Exception as e:
            print(f"Database initialization error: {str(e)}")
            # Continue with empty data structures if database fails
    
    def _initialize_database(self):
        """Initialize the database connection and create tables if they don't exist"""
        try:
            # Create database tables
            initialize_database()
            
            # Get database connection
            _, self.Session = get_database_connection()
        except Exception as e:
            raise ValueError(f"Failed to initialize database: {str(e)}")
    




    def _load_from_database(self):
        """Load data from database into memory structures"""
        try:
            session = self.Session()
            
            # Reset the graph and add root node
            self.graph = nx.DiGraph()
            self.graph.add_node("root", type="root", name="Campus")
            
            # Reset mappings
            self.departments = {}
            self.buildings = {}
            self.floors = {}
            self.rooms = {}
            
            # Load departments
            db_departments = session.query(Department).all()
            for dept in db_departments:
                dept_dict = dept.to_dict()
                self.departments[dept.id] = dept_dict
                
                # Add to graph
                self.graph.add_node(f"dept_{dept.id}", 
                                   type="department", 
                                   name=dept.name,
                                   description=dept.description or '')
                self.graph.add_edge("root", f"dept_{dept.id}")
            
            # Load buildings
            db_buildings = session.query(Building).all()
            for building in db_buildings:
                building_dict = building.to_dict()
                self.buildings[building.id] = building_dict
                
                # Add to graph
                self.graph.add_node(f"building_{building.id}", 
                                   type="building", 
                                   name=building.name,
                                   description=building.description or '')
                self.graph.add_edge(f"dept_{building.department_id}", f"building_{building.id}")
            
            # Load floors
            db_floors = session.query(Floor).all()
            for floor in db_floors:
                floor_dict = floor.to_dict()
                self.floors[floor.id] = floor_dict
                
                # Add to graph
                self.graph.add_node(f"floor_{floor.id}", 
                                   type="floor", 
                                   name=floor.name,
                                   description=floor.description or '')
                self.graph.add_edge(f"building_{floor.building_id}", f"floor_{floor.id}")
            
            # Load rooms
            db_rooms = session.query(Room).all()
            for room in db_rooms:
                room_dict = room.to_dict()
                self.rooms[room.id] = room_dict
                






                # Add to graph
                self.graph.add_node(f"room_{room.id}", 
                                   type="room", 
                                   name=room.name,
                                   room_type=room.type,
                                   description=room.description or '',
                                   capacity=room.capacity,
                                   x=room.x,
                                   y=room.y,
                                   facilities=room.facilities or '',
                                   accessibility=room.accessibility or '')
                self.graph.add_edge(f"floor_{room.floor_id}", f"room_{room.id}")
                
            session.close()
            





            # Convert data to dataframe format if needed
            self._build_dataframe()
        except Exception as e:
            session.close()
            raise ValueError(f"Failed to load data from database: {str(e)}")
    
    def _save_to_database(self):
        """Save current data to the database"""
        try:
            session = self.Session()
            
            # First, clear existing data
            try:
                session.query(Room).delete()
                session.query(Floor).delete()
                session.query(Building).delete()
                session.query(Department).delete()
                session.commit()
            except Exception as e:
                session.rollback()
                raise ValueError(f"Failed to clear existing data: {str(e)}")
            
            # Add departments
            for dept_id, dept in self.departments.items():
                db_dept = Department(
                    id=dept_id,
                    name=dept['name'],
                    description=dept.get('description', '')
                )
                session.add(db_dept)
            
            # Commit departments first
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                raise ValueError(f"Failed to add departments: {str(e)}")
            
            # Add buildings
            for building_id, building in self.buildings.items():
                db_building = Building(
                    id=building_id,
                    name=building['name'],
                    description=building.get('description', ''),
                    department_id=building['department_id'],
                    x=building.get('x', 50),  # <- ADD THIS
                    y=building.get('y', 50)   # <- AND THIS
                )
                session.add(db_building)
            
            # Commit buildings
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                raise ValueError(f"Failed to add buildings: {str(e)}")
            
            # Add floors
            # for floor_id, floor in self.floors.items():
            #     db_floor = Floor(
            #         id=floor_id,
            #         name=floor['name'],
            #         description=floor.get('description', ''),
            #         building_id=floor['building_id']
            #     )
            #     session.add(db_floor)
            # Add floors
            for floor_id, floor in self.floors.items():
                db_floor = Floor(
                    id=floor_id,
                    name=floor['name'],
                    description=floor.get('description', ''),
                    building_id=floor['building_id'],
                    x=floor.get('x', 50),  # <-- Add x position
                    y=floor.get('y', 50)   # <-- Add y position
                )
                session.add(db_floor)

            
            # Commit floors
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                raise ValueError(f"Failed to add floors: {str(e)}")
            
            # Add rooms
            for room_id, room in self.rooms.items():
                db_room = Room(
                    id=room_id,
                    name=room['name'],
                    description=room.get('description', ''),
                    type=room.get('type', 'generic'),
                    capacity=room.get('capacity', 0),
                    x=room.get('x', 50),
                    y=room.get('y', 50),
                    facilities=room.get('facilities', ''),
                    accessibility=room.get('accessibility', ''),
                    floor_id=room['floor_id']
                )
                session.add(db_room)
            
            # Commit rooms
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                raise ValueError(f"Failed to add rooms: {str(e)}")
                
            session.close()
        except Exception as e:
            if 'session' in locals() and session:
                session.close()
            raise ValueError(f"Failed to save data to database: {str(e)}")
    
    def _build_dataframe(self):
        """Build a dataframe from the current data for CSV export"""
        # If no data, create empty dataframe
        if not self.departments:
            self.df = pd.DataFrame(columns=self.standard_columns + self.optional_columns)
            return
        
        # Create a list of rows for the dataframe
        rows = []
        
        for room_id, room in self.rooms.items():
            floor_id = room['floor_id']
            floor = self.floors.get(floor_id, {})
            
            building_id = floor.get('building_id', '')
            building = self.buildings.get(building_id, {})
            
            dept_id = building.get('department_id', '')
            dept = self.departments.get(dept_id, {})
            
            row = {
                'department_id': dept_id,
                'department_name': dept.get('name', ''),
                'department_description': dept.get('description', ''),
                'building_id': building_id,
                'building_name': building.get('name', ''),
                'building_description': building.get('description', ''),
                'floor_id': floor_id,
                'floor_name': floor.get('name', ''),
                'floor_description': floor.get('description', ''),
                'room_id': room_id,
                'room_name': room.get('name', ''),
                'room_type': room.get('type', 'generic'),
                'room_description': room.get('description', ''),
                'capacity': room.get('capacity', 0),
                'x_coordinate': room.get('x', 50),
                'y_coordinate': room.get('y', 50),
                'room_facilities': room.get('facilities', ''),
                'accessibility': room.get('accessibility', '')
            }
            
            rows.append(row)
        
        self.df = pd.DataFrame(rows)
    
    def has_data(self) -> bool:
        """Check if data has been loaded."""
        return not self.df.empty
    
    def validate_csv(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate that the CSV has the required columns and format.
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Determine which format we're dealing with (standard or simple)
        is_simple_format = all(col in df.columns for col in self.simple_format_columns)
        is_standard_format = all(col in df.columns for col in self.standard_columns)
        
        if not is_simple_format and not is_standard_format:
            return False, f"CSV format not recognized. Must include either standard columns or simplified columns."
        
        # Set required columns based on the format detected
        if is_simple_format:
            self.required_columns = self.simple_format_columns
        else:
            self.required_columns = self.standard_columns
        
        # Check for required columns
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        
        # Check for duplicate IDs if using standard format
        if is_standard_format:
            for id_col in ['department_id', 'building_id', 'floor_id', 'room_id']:
                if df[id_col].duplicated().any():
                    dupes = df[df[id_col].duplicated(keep=False)][id_col].unique()
                    return False, f"Duplicate {id_col} values found: {', '.join(map(str, dupes))}"
        # Check for duplicate IDs if using simple format
        elif is_simple_format and df['id'].duplicated().any():
            dupes = df[df['id'].duplicated(keep=False)]['id'].unique()
            return False, f"Duplicate id values found: {', '.join(map(str, dupes))}"
        
        return True, ""
    
    def import_from_csv(self, file_obj: Any) -> None:
        """
        Import campus data from an uploaded CSV file.
        
        Args:
            file_obj: File-like object containing CSV data
        """
        try:
            df = pd.read_csv(file_obj)
            valid, error_msg = self.validate_csv(df)
            
            if not valid:
                raise ValueError(error_msg)
            
            # Process the data
            self._process_data(df)
        except Exception as e:
            raise ValueError(f"Error importing CSV data: {str(e)}")
    
    def import_from_file(self, file_path: str) -> None:
        """
        Import campus data from a CSV file path.
        
        Args:
            file_path: Path to the CSV file
        """
        try:
            df = pd.read_csv(file_path)
            valid, error_msg = self.validate_csv(df)
            
            if not valid:
                raise ValueError(error_msg)
            
            # Process the data
            self._process_data(df)
        except Exception as e:
            raise ValueError(f"Error importing CSV data: {str(e)}")
    
    def _process_data(self, df: pd.DataFrame) -> None:
        """
        Process imported data to build the hierarchical data structures.
        
        Args:
            df: DataFrame containing campus data
        """
        # Store the dataframe
        self.df = df
        
        # Reset the graph and mappings
        self.graph = nx.DiGraph()
        self.departments = {}
        self.buildings = {}
        self.floors = {}
        self.rooms = {}
        
        # Add a special root node
        self.graph.add_node("root", type="root", name="Campus")
        
        # Check if we're using the simple format
        is_simple_format = 'type' in df.columns
        
        if is_simple_format:
            self._process_simple_format(df)
        else:
            self._process_standard_format(df)
            
        # Save the processed data to the database
        try:
            self._save_to_database()
        except Exception as e:
            print(f"Warning: Failed to save data to database: {str(e)}")
            # Continue with in-memory data even if database save fails
    
    def _process_simple_format(self, df: pd.DataFrame) -> None:
        """
        Process data from the simple CSV format.
        
        Args:
            df: DataFrame with simplified structure
        """
        # First collect all entities by type
        departments_df = df[df['type'].str.lower() == 'department']
        buildings_df = df[df['type'].str.lower() == 'building']
        floors_df = df[df['type'].str.lower() == 'floor']
        rooms_df = df[df['type'].str.lower() == 'room']
        
        # Process departments
        for _, row in departments_df.iterrows():
            dept_id = row['id']
            dept_name = row['name']
            dept_desc = row.get('description', '')
            
            # Add to graph
            self.graph.add_node(f"dept_{dept_id}", 
                               type="department", 
                               name=dept_name,
                               description=dept_desc)
            self.graph.add_edge("root", f"dept_{dept_id}")
            
            # Add to mapping
            self.departments[dept_id] = {
                'id': dept_id,
                'name': dept_name,
                'description': dept_desc
            }
        #=-------------------------------------------------------------------------------------------------
        # Process buildings
        for _, row in buildings_df.iterrows():
            building_id = row['id']
            building_name = row['name']
            building_desc = row.get('description', '')
            dept_id = row.get('building_id', '')  # In simple format, building_id column holds department_id for buildings
            

             # Try to read x and y from the CSV. If not present or invalid, fallback to default.
            x_raw = row.get('x')
            if pd.notna(x_raw) and str(x_raw).strip() != '':
                try:
                    x_coord = float(x_raw)
                except ValueError:
                    x_coord = 50 + (hash(building_id) % 40)
            else:
                x_coord = 50 + (hash(building_id) % 40)

            # Same logic for y
            y_raw = row.get('y')
            if pd.notna(y_raw) and str(y_raw).strip() != '':
                try:
                    y_coord = float(y_raw)
                except ValueError:
                    y_coord = 50 + (hash(building_name) % 40)
            else:
                y_coord = 50 + (hash(building_name) % 40)

    
            # Add to graph
            self.graph.add_node(f"building_{building_id}", 
                               type="building", 
                               name=building_name,
                               description=building_desc,
                               x=x_coord,
                               y=y_coord)
            
            # Connect to parent department if specified
            if dept_id and f"dept_{dept_id}" in self.graph:
                self.graph.add_edge(f"dept_{dept_id}", f"building_{building_id}")
            else:
                # If no parent specified or parent not found, connect to root
                self.graph.add_edge("root", f"building_{building_id}")
            
            # Add to mapping
            self.buildings[building_id] = {
                'id': building_id,
                'department_id': dept_id if dept_id else 'unknown',
                'name': building_name,
                'x': x_coord,#added
                'y': y_coord,#added
                'description': building_desc
            }
            #-----------------------------------------------------------------------
        
        # Process floors
        for _, row in floors_df.iterrows():
            floor_id = row['id']
            floor_name = row['name']
            floor_desc = row.get('description', '')
            building_id = row.get('building_id', '')
            
            # Try to read x and y from the CSV. If not present or invalid, fallback to default.
            x_raw = row.get('x')
            if pd.notna(x_raw) and str(x_raw).strip() != '':
                try:
                    x_coord = float(x_raw)
                except ValueError:
                    x_coord = 50 + (hash(floor_id) % 40)
            else:
                x_coord = 50 + (hash(floor_id) % 40)

            y_raw = row.get('y')
            if pd.notna(y_raw) and str(y_raw).strip() != '':
                try:
                    y_coord = float(y_raw)
                except ValueError:
                    y_coord = 50 + (hash(floor_name) % 40)
            else:
                y_coord = 50 + (hash(floor_name) % 40)
                
            # Add to graph
            # self.graph.add_node(f"floor_{floor_id}", 
            #                    type="floor", 
            #                    name=floor_name,
            #                    description=floor_desc)
            
            self.graph.add_node(f"floor_{floor_id}",
                        type="floor",
                        name=floor_name,
                        description=floor_desc,
                        x=x_coord,
                        y=y_coord)
            
            # Connect to parent building if specified
            if building_id and f"building_{building_id}" in self.graph:
                self.graph.add_edge(f"building_{building_id}", f"floor_{floor_id}")
            else:
                # If no parent specified or parent not found, connect to a building or root
                if self.buildings:
                    # Connect to first building
                    first_building = list(self.buildings.keys())[0]
                    self.graph.add_edge(f"building_{first_building}", f"floor_{floor_id}")
                else:
                    self.graph.add_edge("root", f"floor_{floor_id}")
            
            # Add to mapping
            # self.floors[floor_id] = {
            #     'id': floor_id,
            #     'building_id': building_id if building_id else 'unknown',
            #     'name': floor_name,
            #     'description': floor_desc
            # }
            self.floors[floor_id] = {
            'id': floor_id,
            'building_id': building_id if building_id else 'unknown',
            'name': floor_name,
            'description': floor_desc,
            'x': x_coord,
            'y': y_coord
            }
        
        # Process rooms--------------------------------------------------------------------------------------------------------
        for _, row in rooms_df.iterrows():
            room_id = row['id']
            room_name = row['name']
            room_desc = row.get('description', '')
            floor_id = row.get('building_id', '')  # In simple format, building_id column holds floor_id for rooms
            
            # Default values for required fields
            room_type = 'generic'
            capacity = 40
            # Try to read x and y from the CSV. If not present or invalid, fallback to default.
            x_raw = row.get('x')
            if pd.notna(x_raw) and str(x_raw).strip() != '':
                try:
                    x_coord = float(x_raw)
                except ValueError:
                    x_coord = 50 + (hash(room_id) % 40)
            else:
                x_coord = 50 + (hash(room_id) % 40)

            # Same logic for y
            y_raw = row.get('y')
            if pd.notna(y_raw) and str(y_raw).strip() != '':
                try:
                    y_coord = float(y_raw)
                except ValueError:
                    y_coord = 50 + (hash(room_name) % 40)
            else:
                y_coord = 50 + (hash(room_name) % 40)
            
            
            
            # Add to graph
            self.graph.add_node(f"room_{room_id}", 
                               type="room", 
                               name=room_name,
                               room_type=room_type,
                               description=room_desc,
                               capacity=capacity,
                               x=x_coord,
                               y=y_coord,
                               facilities='',
                               accessibility='')
            
            # Connect to parent floor if specified
            if floor_id and f"floor_{floor_id}" in self.graph:
                self.graph.add_edge(f"floor_{floor_id}", f"room_{room_id}")
            else:
                # If no parent specified or parent not found, connect to a floor
                if self.floors:
                    # Connect to first floor
                    first_floor = list(self.floors.keys())[0]
                    self.graph.add_edge(f"floor_{first_floor}", f"room_{room_id}")
                else:
                    # If no floors, connect to a building or root
                    if self.buildings:
                        first_building = list(self.buildings.keys())[0]
                        self.graph.add_edge(f"building_{first_building}", f"room_{room_id}")
                    else:
                        self.graph.add_edge("root", f"room_{room_id}")
            
            # Add to mapping
            self.rooms[room_id] = {
                'id': room_id,
                'floor_id': floor_id if floor_id else 'unknown',
                'name': room_name,
                'type': room_type,
                'description': room_desc,
                'capacity': capacity,
                'x': x_coord,
                'y': y_coord,
                'facilities': '',
                'accessibility': ''
            }
    
    def _process_standard_format(self, df: pd.DataFrame) -> None:
        """
        Process data from the standard CSV format.
        
        Args:
            df: DataFrame with standard structure
        """
        # Process departments
        for _, row in df.drop_duplicates('department_id').iterrows():
            dept_id = row['department_id']
            dept_name = row['department_name']
            dept_desc = row.get('department_description', '')
            
            # Add to graph
            self.graph.add_node(f"dept_{dept_id}", 
                               type="department", 
                               name=dept_name,
                               description=dept_desc)
            self.graph.add_edge("root", f"dept_{dept_id}")
            
            # Add to mapping
            self.departments[dept_id] = {
                'id': dept_id,
                'name': dept_name,
                'description': dept_desc
            }
        
        # Process buildings
        for _, row in df.drop_duplicates('building_id').iterrows():
            dept_id = row['department_id']
            building_id = row['building_id']
            building_name = row['building_name']
            building_desc = row.get('building_description', '')
            
            # Add to graph
            self.graph.add_node(f"building_{building_id}", 
                               type="building", 
                               name=building_name,
                               description=building_desc)
            self.graph.add_edge(f"dept_{dept_id}", f"building_{building_id}")
            
            # Add to mapping
            self.buildings[building_id] = {
                'id': building_id,
                'department_id': dept_id,
                'name': building_name,
                'description': building_desc
            }
        
        # Process floors
        for _, row in df.drop_duplicates('floor_id').iterrows():
            building_id = row['building_id']
            floor_id = row['floor_id']
            floor_name = row['floor_name']
            floor_desc = row.get('floor_description', '')
            
            # Add to graph
            self.graph.add_node(f"floor_{floor_id}", 
                               type="floor", 
                               name=floor_name,
                               description=floor_desc)
            self.graph.add_edge(f"building_{building_id}", f"floor_{floor_id}")
            
            # Add to mapping
            self.floors[floor_id] = {
                'id': floor_id,
                'building_id': building_id,
                'name': floor_name,
                'description': floor_desc
            }
        
        # Process rooms
        for _, row in df.iterrows():
            floor_id = row['floor_id']
            room_id = row['room_id']
            room_name = row['room_name']
            room_type = row['room_type']
            room_desc = row.get('room_description', '')
            capacity = row['capacity']
            x_coord = row['x_coordinate']
            y_coord = row['y_coordinate']
            
            facilities = row.get('room_facilities', '')
            accessibility = row.get('accessibility', '')
            
            # Add to graph
            self.graph.add_node(f"room_{room_id}", 
                               type="room", 
                               name=room_name,
                               room_type=room_type,
                               description=room_desc,
                               capacity=capacity,
                               x=x_coord,
                               y=y_coord,
                               facilities=facilities,
                               accessibility=accessibility)
            self.graph.add_edge(f"floor_{floor_id}", f"room_{room_id}")
            
            # Add to mapping
            self.rooms[room_id] = {
                'id': room_id,
                'floor_id': floor_id,
                'name': room_name,
                'type': room_type,
                'description': room_desc,
                'capacity': capacity,
                'x': x_coord,
                'y': y_coord,
                'facilities': facilities,
                'accessibility': accessibility
            }
    
    def export_to_csv(self, format_type="auto") -> str:
        """
        Export current data to CSV.
        
        Args:
            format_type: Type of CSV format to export ('standard', 'simple', or 'auto')
        
        Returns:
            str: CSV content as a string
        """
        buffer = io.StringIO()
        
        # Detect if we have a simple format already loaded or use specified format
        is_simple_format = format_type == "simple" or (format_type == "auto" and 'type' in self.df.columns)
        
        if self.df.empty:
            if is_simple_format:
                # Return an empty CSV with simple format headers
                pd.DataFrame(columns=self.simple_format_columns).to_csv(buffer, index=False)
            else:
                # Return an empty CSV with standard format headers
                pd.DataFrame(columns=self.standard_columns + self.optional_columns).to_csv(buffer, index=False)
            return buffer.getvalue()
        
        if is_simple_format:
            # If current data is already in simple format or export to simple is requested
            if 'type' in self.df.columns:
                # Export the current dataframe as is
                self.df.to_csv(buffer, index=False)
            else:
                # Convert from standard to simple format
                simple_data = []
                
                # Add departments
                for dept_id, dept in self.departments.items():
                    simple_data.append({
                        'type': 'department',
                        'id': dept_id,
                        'name': dept['name'],
                        'building_id': '',  # No parent for departments
                        'description': dept.get('description', '')
                    })
                
                # Add buildings
                for building_id, building in self.buildings.items():
                    simple_data.append({
                        'type': 'building',
                        'id': building_id,
                        'name': building['name'],
                        'building_id': building.get('department_id', ''),  # Parent department
                        'description': building.get('description', '')
                    })
                
                # Add floors
                for floor_id, floor in self.floors.items():
                    simple_data.append({
                        'type': 'floor',
                        'id': floor_id,
                        'name': floor['name'],
                        'building_id': floor.get('building_id', ''),  # Parent building
                        'description': floor.get('description', '')
                    })
                
                # Add rooms
                for room_id, room in self.rooms.items():
                    simple_data.append({
                        'type': 'room',
                        'id': room_id,
                        'name': room['name'],
                        'building_id': room.get('floor_id', ''),  # Parent floor
                        'description': room.get('description', '')
                    })
                
                # Create and export the simple format dataframe
                simple_df = pd.DataFrame(simple_data)
                simple_df.to_csv(buffer, index=False)
        else:
            # Export in standard format
            if 'type' in self.df.columns:
                # Convert from simple format to standard format
                # This is a complex task requiring synthesizing missing data
                # For now, just export the original data
                self.df.to_csv(buffer, index=False)
            else:
                # Export the current standard format dataframe
                self.df.to_csv(buffer, index=False)
        
        return buffer.getvalue()
    
    def get_departments(self) -> List[Dict]:
        """Get all departments."""
        return list(self.departments.values())
    
    def get_buildings(self, department_id: Optional[str] = None) -> List[Dict]:
        """Get all buildings or buildings for a specific department."""
        if department_id is not None:
            return [b for b in self.buildings.values() if b['department_id'] == department_id]
        return list(self.buildings.values())
    
    def get_floors(self, building_id: Optional[str] = None) -> List[Dict]:
        """Get all floors or floors for a specific building."""
        if building_id is not None:
            return [f for f in self.floors.values() if f['building_id'] == building_id]
        return list(self.floors.values())
    
    def get_rooms(self, floor_id: Optional[str] = None) -> List[Dict]:
        """Get all rooms or rooms for a specific floor."""
        if floor_id is not None:
            return [r for r in self.rooms.values() if r['floor_id'] == floor_id]
        return list(self.rooms.values())
    
    def get_item_details(self, item_type: str, item_id: str) -> Optional[Dict]:
        """
        Get details for a specific item by type and ID.
        
        Args:
            item_type: Type of item ('department', 'building', 'floor', 'room')
            item_id: ID of the item
        
        Returns:
            Dict or None: Item details or None if not found
        """
        if item_type == 'department':
            return self.departments.get(item_id)
        elif item_type == 'building':
            return self.buildings.get(item_id)
        elif item_type == 'floor':
            return self.floors.get(item_id)
        elif item_type == 'room':
            return self.rooms.get(item_id)
        return None
    
    def get_parent(self, item_type: str, item_id: str) -> Optional[Dict]:
        """
        Get the parent item of a specific item.
        
        Args:
            item_type: Type of item ('building', 'floor', 'room')
            item_id: ID of the item
        
        Returns:
            Dict or None: Parent item details or None if not found
        """
        if item_type == 'building':
            building = self.buildings.get(item_id)
            if building:
                return self.departments.get(building['department_id'])
        elif item_type == 'floor':
            floor = self.floors.get(item_id)
            if floor:
                return self.buildings.get(floor['building_id'])
        elif item_type == 'room':
            room = self.rooms.get(item_id)
            if room:
                return self.floors.get(room['floor_id'])
        return None

    def search(self, query: str) -> Dict[str, List[Dict]]:
        """
        Search for items matching the query across all categories.

        Args:
            query: Search string

        Returns:
            Dict: Dictionary with results by category
        """
        if not query:
            return {
                'departments': [],
                'buildings': [],
                'floors': [],
                'rooms': []
            }

        query = query.lower()
        results = {
            'departments': [],
            'buildings': [],
            'floors': [],
            'rooms': []
        }

        # Helper function to safely check if a key exists and contains the query
        def matches_query(item: Dict, key: str) -> bool:
            return key in item and item[key] and query in str(item[key]).lower()

        # Search departments
        for dept in self.departments.values():
            if matches_query(dept, 'name') or matches_query(dept, 'description'):
                results['departments'].append(dept)

        # Search buildings
        for building in self.buildings.values():
            if matches_query(building, 'name') or matches_query(building, 'description'):
                results['buildings'].append(building)

        # Search floors
        for floor in self.floors.values():
            if matches_query(floor, 'name') or matches_query(floor, 'description'):
                results['floors'].append(floor)

        # Search rooms
        for room in self.rooms.values():
            if (matches_query(room, 'name') or 
                matches_query(room, 'type') or 
                matches_query(room, 'description') or
                matches_query(room, 'facilities')):
                results['rooms'].append(room)

        return results
