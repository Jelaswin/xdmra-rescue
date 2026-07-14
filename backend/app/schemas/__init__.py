from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.models import IncidentSeverity, IncidentStatus, TeamAvailability, AllocationStatus, RouteRisk

class IncidentBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    incident_type: str = Field(..., min_length=1)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    severity: IncidentSeverity
    affected_people: int = Field(0, ge=0)
    injured_people: int = Field(0, ge=0)
    vulnerable_people: int = Field(0, ge=0)

class IncidentCreate(IncidentBase):
    pass

class Incident(IncidentBase):
    id: int
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RescueTeam(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    skills: List[str]
    equipment: List[str]
    capacity: int
    current_workload: int
    availability_status: TeamAvailability
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DashboardSummary(BaseModel):
    total_incidents: int
    critical_incidents: int
    available_teams: int
    active_allocations: int
