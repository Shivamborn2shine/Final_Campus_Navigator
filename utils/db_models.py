"""
Database models for the Smart Campus Navigator
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

# Create base class for declarative models
Base = declarative_base()

class Department(Base):
    """Department model"""
    __tablename__ = 'departments'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Relationships
    buildings = relationship("Building", back_populates="department", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or ''
        }

class Building(Base):
    """Building model"""
    __tablename__ = 'buildings'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    department_id = Column(String, ForeignKey('departments.id'), nullable=False)
    
    # Relationships
    department = relationship("Department", back_populates="buildings")
    floors = relationship("Floor", back_populates="building", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or '',
            'department_id': self.department_id
        }

class Floor(Base):
    """Floor model"""
    __tablename__ = 'floors'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    building_id = Column(String, ForeignKey('buildings.id'), nullable=False)
    
    # Relationships
    building = relationship("Building", back_populates="floors")
    rooms = relationship("Room", back_populates="floor", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or '',
            'building_id': self.building_id
        }

class Room(Base):
    """Room model"""
    __tablename__ = 'rooms'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    type = Column(String, nullable=False, default='generic')
    capacity = Column(Integer, nullable=False, default=0)
    x = Column(Float, nullable=False, default=50.0)
    y = Column(Float, nullable=False, default=50.0)
    facilities = Column(String, nullable=True)
    accessibility = Column(String, nullable=True)
    floor_id = Column(String, ForeignKey('floors.id'), nullable=False)
    
    # Relationships
    floor = relationship("Floor", back_populates="rooms")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or '',
            'type': self.type,
            'capacity': self.capacity,
            'x': self.x,
            'y': self.y,
            'facilities': self.facilities or '',
            'accessibility': self.accessibility or '',
            'floor_id': self.floor_id
        }

def get_database_connection():
    """
    Create database engine and session factory
    
    Returns:
        tuple: (engine, session_factory)
    """
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///campus_navigator.db')
    
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    
    return engine, Session

def initialize_database():
    """Initialize the database by creating all tables"""
    engine, _ = get_database_connection()
    Base.metadata.create_all(engine)