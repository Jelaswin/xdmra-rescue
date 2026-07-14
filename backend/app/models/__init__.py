from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database import Base

class IncidentSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class IncidentStatus(str, enum.Enum):
    reported = "reported"
    verified = "verified"
    assigned = "assigned"
    in_progress = "in_progress"
    resolved = "resolved"

class TeamAvailability(str, enum.Enum):
    available = "available"
    assigned = "assigned"
    unavailable = "unavailable"

class AllocationStatus(str, enum.Enum):
    recommended = "recommended"
    approved = "approved"
    dispatched = "dispatched"
    completed = "completed"
    cancelled = "cancelled"

class RouteRisk(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    blocked = "blocked"

def utcnow():
    return datetime.now(timezone.utc)

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    incident_type = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    severity = Column(Enum(IncidentSeverity), nullable=False)
    affected_people = Column(Integer, default=0)
    injured_people = Column(Integer, default=0)
    vulnerable_people = Column(Integer, default=0)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.reported)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    allocations = relationship("Allocation", back_populates="incident")

class RescueTeam(Base):
    __tablename__ = "rescue_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    skills = Column(JSON, nullable=False)
    equipment = Column(JSON, nullable=False)
    capacity = Column(Integer, nullable=False)
    current_workload = Column(Integer, default=0)
    availability_status = Column(Enum(TeamAvailability), default=TeamAvailability.available)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    allocations = relationship("Allocation", back_populates="rescue_team")

class Allocation(Base):
    __tablename__ = "allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    rescue_team_id = Column(Integer, ForeignKey("rescue_teams.id"), nullable=False)
    status = Column(Enum(AllocationStatus), default=AllocationStatus.recommended)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    incident = relationship("Incident", back_populates="allocations")
    rescue_team = relationship("RescueTeam", back_populates="allocations")

class RouteCondition(Base):
    __tablename__ = "route_conditions"
    
    id = Column(Integer, primary_key=True, index=True)
    route_name = Column(String, nullable=False)
    origin_label = Column(String, nullable=False)
    destination_label = Column(String, nullable=False)
    risk_level = Column(Enum(RouteRisk), nullable=False)
    is_blocked = Column(Integer, default=0) # boolean stored as integer for sqlite compat 
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
