"""
Deterministic Rescue Evaluation Scenarios.

25+ scenarios covering various rescue allocation conditions.
All scenarios are deterministic and reproducible.
"""

from typing import List, Dict, Any
from ..baselines.rescue_baselines import RescueScenario


def get_rescue_scenarios() -> List[RescueScenario]:
    """Return all deterministic rescue evaluation scenarios."""
    return [
        # 1. Low-priority local incident
        RescueScenario(
            scenario_id="rescue_001",
            incident_id=1,
            incident_title="Minor Flooding",
            incident_type="Flood",
            latitude=10.9925,
            longitude=76.9600,
            priority_level="low",
            required_skills=[],
            required_equipment=[],
            affected_people=10,
            trapped_people=0,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 11.0, "longitude": 76.95, "availability_status": "available", "skills": ["flood_rescue"], "equipment": ["boat"], "capacity": 10, "current_workload": 0},
                {"id": 2, "name": "Team Beta", "latitude": 11.01, "longitude": 76.96, "availability_status": "available", "skills": [], "equipment": [], "capacity": 8, "current_workload": 2},
            ]
        ),
        
        # 2. High-priority incident
        RescueScenario(
            scenario_id="rescue_002",
            incident_id=2,
            incident_title="Building Collapse",
            incident_type="Earthquake",
            latitude=10.9950,
            longitude=76.9750,
            priority_level="high",
            required_skills=["search_and_rescue"],
            required_equipment=["heavy_lifting"],
            affected_people=50,
            trapped_people=15,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 11.0, "longitude": 76.95, "availability_status": "available", "skills": ["flood_rescue"], "equipment": ["boat"], "capacity": 10, "current_workload": 0},
                {"id": 3, "name": "Team Gamma", "latitude": 10.99, "longitude": 76.98, "availability_status": "available", "skills": ["search_and_rescue", "medical_support"], "equipment": ["heavy_lifting", "medical_kit"], "capacity": 20, "current_workload": 5},
            ]
        ),
        
        # 3. Critical incident
        RescueScenario(
            scenario_id="rescue_003",
            incident_id=3,
            incident_title="Major Building Collapse",
            incident_type="Earthquake",
            latitude=11.0180,
            longitude=76.9360,
            priority_level="critical",
            required_skills=["search_and_rescue", "medical_support"],
            required_equipment=["heavy_lifting", "medical_kit"],
            affected_people=100,
            trapped_people=30,
            available_teams=[
                {"id": 3, "name": "Team Gamma", "latitude": 10.99, "longitude": 76.98, "availability_status": "available", "skills": ["search_and_rescue", "medical_support"], "equipment": ["heavy_lifting", "medical_kit"], "capacity": 20, "current_workload": 0},
                {"id": 4, "name": "Team Delta", "latitude": 11.02, "longitude": 76.94, "availability_status": "available", "skills": ["debris_removal"], "equipment": ["crane"], "capacity": 15, "current_workload": 3},
            ]
        ),
        
        # 4. Multiple eligible teams
        RescueScenario(
            scenario_id="rescue_004",
            incident_id=4,
            incident_title="Multi-Vehicle Accident",
            incident_type="Accident",
            latitude=11.0168,
            longitude=76.9558,
            priority_level="high",
            required_skills=[],
            required_equipment=[],
            affected_people=20,
            trapped_people=5,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 11.0168, "longitude": 76.9558, "availability_status": "available", "skills": ["flood_rescue"], "equipment": ["boat"], "capacity": 10, "current_workload": 0},
                {"id": 2, "name": "Team Beta", "latitude": 11.0168, "longitude": 76.9558, "availability_status": "available", "skills": ["medical_support"], "equipment": ["medical_kit"], "capacity": 8, "current_workload": 0},
                {"id": 5, "name": "Team Epsilon", "latitude": 11.02, "longitude": 76.96, "availability_status": "available", "skills": [], "equipment": [], "capacity": 12, "current_workload": 0},
            ]
        ),
        
        # 5. Skill mismatch
        RescueScenario(
            scenario_id="rescue_005",
            incident_id=5,
            incident_title="Flood Rescue",
            incident_type="Flood",
            latitude=10.9925,
            longitude=76.9600,
            priority_level="high",
            required_skills=["flood_rescue", "swiftwater_rescue"],
            required_equipment=["boat", "life_jackets"],
            affected_people=30,
            trapped_people=10,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 11.0, "longitude": 76.95, "availability_status": "available", "skills": ["medical_support"], "equipment": ["medical_kit"], "capacity": 10, "current_workload": 0},
                {"id": 2, "name": "Team Beta", "latitude": 10.99, "longitude": 76.98, "availability_status": "available", "skills": ["debris_removal"], "equipment": ["crane"], "capacity": 15, "current_workload": 0},
            ]
        ),
        
        # 6. Equipment mismatch
        RescueScenario(
            scenario_id="rescue_006",
            incident_id=6,
            incident_title="Industrial Fire",
            incident_type="Fire",
            latitude=11.0270,
            longitude=77.0062,
            priority_level="critical",
            required_skills=["firefighting"],
            required_equipment=["fire_extinguisher", "respirator"],
            affected_people=25,
            trapped_people=8,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 11.03, "longitude": 77.01, "availability_status": "available", "skills": ["firefighting"], "equipment": ["boat"], "capacity": 10, "current_workload": 0},
                {"id": 2, "name": "Team Beta", "latitude": 11.02, "longitude": 77.00, "availability_status": "available", "skills": ["firefighting"], "equipment": ["medical_kit"], "capacity": 12, "current_workload": 0},
            ]
        ),
        
        # 7. High team workload
        RescueScenario(
            scenario_id="rescue_007",
            incident_id=7,
            incident_title="Road Accident",
            incident_type="Accident",
            latitude=11.0200,
            longitude=76.9600,
            priority_level="medium",
            required_skills=[],
            required_equipment=[],
            affected_people=15,
            trapped_people=3,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 11.02, "longitude": 76.96, "availability_status": "available", "skills": [], "equipment": [], "capacity": 10, "current_workload": 8},
                {"id": 2, "name": "Team Beta", "latitude": 11.03, "longitude": 76.97, "availability_status": "available", "skills": [], "equipment": [], "capacity": 10, "current_workload": 2},
            ]
        ),
        
        # 8. Team unavailable
        RescueScenario(
            scenario_id="rescue_008",
            incident_id=8,
            incident_title="Landslide",
            incident_type="Landslide",
            latitude=10.9378,
            longitude=76.7455,
            priority_level="critical",
            required_skills=["search_and_rescue"],
            required_equipment=["heavy_lifting"],
            affected_people=40,
            trapped_people=12,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 10.94, "longitude": 76.75, "availability_status": "unavailable", "skills": ["search_and_rescue"], "equipment": ["heavy_lifting"], "capacity": 20, "current_workload": 0},
            ]
        ),
        
        # 9. All teams available but no skills match
        RescueScenario(
            scenario_id="rescue_009",
            incident_id=9,
            incident_title="Water Rescue",
            incident_type="Flood",
            latitude=10.9925,
            longitude=76.9600,
            priority_level="high",
            required_skills=["swiftwater_rescue", "flood_rescue"],
            required_equipment=["boat", "life_jackets"],
            affected_people=35,
            trapped_people=15,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 11.0, "longitude": 76.97, "availability_status": "available", "skills": ["medical_support"], "equipment": ["medical_kit"], "capacity": 10, "current_workload": 0},
                {"id": 2, "name": "Team Beta", "latitude": 10.99, "longitude": 76.95, "availability_status": "available", "skills": ["debris_removal"], "equipment": ["crane"], "capacity": 15, "current_workload": 0},
            ]
        ),
        
        # 10. No eligible team - complete mismatch
        RescueScenario(
            scenario_id="rescue_010",
            incident_id=10,
            incident_title="Chemical Spill",
            incident_type="Hazardous Material",
            latitude=11.0016,
            longitude=76.9723,
            priority_level="critical",
            required_skills=["hazmat_response", "decontamination"],
            required_equipment=["hazmat_suit", "decontamination_unit"],
            affected_people=50,
            trapped_people=20,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 11.0, "longitude": 76.97, "availability_status": "available", "skills": ["medical_support"], "equipment": ["medical_kit"], "capacity": 10, "current_workload": 0},
            ]
        ),
        
        # 11. Perfect skill and equipment match
        RescueScenario(
            scenario_id="rescue_011",
            incident_id=11,
            incident_title="Flood Rescue",
            incident_type="Flood",
            latitude=10.9925,
            longitude=76.9600,
            priority_level="high",
            required_skills=["flood_rescue", "swiftwater_rescue"],
            required_equipment=["boat", "life_jackets"],
            affected_people=40,
            trapped_people=12,
            available_teams=[
                {"id": 1, "name": "CBE Disaster Response", "latitude": 10.99, "longitude": 76.96, "availability_status": "available", "skills": ["flood_rescue", "swiftwater_rescue", "first_aid", "medical_support"], "equipment": ["boat", "ropes", "life_jackets", "medical_kit"], "capacity": 15, "current_workload": 0},
            ]
        ),
        
        # 12. Medium priority with single team
        RescueScenario(
            scenario_id="rescue_012",
            incident_id=12,
            incident_title="Minor Landslide",
            incident_type="Landslide",
            latitude=10.9392,
            longitude=76.6800,
            priority_level="medium",
            required_skills=[],
            required_equipment=[],
            affected_people=15,
            trapped_people=2,
            available_teams=[
                {"id": 4, "name": "Siruvani Forest Rangers", "latitude": 10.94, "longitude": 76.68, "availability_status": "available", "skills": ["air_rescue", "medical_support"], "equipment": ["helicopter", "hoists", "medical_kit"], "capacity": 5, "current_workload": 0},
            ]
        ),
        
        # 13. Low priority distant incident
        RescueScenario(
            scenario_id="rescue_013",
            incident_id=13,
            incident_title="Small Fire",
            incident_type="Fire",
            latitude=11.0289,
            longitude=77.0270,
            priority_level="low",
            required_skills=[],
            required_equipment=[],
            affected_people=5,
            trapped_people=0,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 10.99, "longitude": 76.96, "availability_status": "available", "skills": [], "equipment": [], "capacity": 10, "current_workload": 0},
            ]
        ),
        
        # 14. High priority, all teams busy
        RescueScenario(
            scenario_id="rescue_014",
            incident_id=14,
            incident_title="Train Derailment",
            incident_type="Accident",
            latitude=11.0200,
            longitude=76.9600,
            priority_level="critical",
            required_skills=["search_and_rescue", "medical_support"],
            required_equipment=["heavy_lifting", "medical_kit"],
            affected_people=150,
            trapped_people=50,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 11.02, "longitude": 76.96, "availability_status": "assigned", "skills": ["search_and_rescue"], "equipment": ["heavy_lifting"], "capacity": 20, "current_workload": 10},
                {"id": 2, "name": "Team Beta", "latitude": 11.03, "longitude": 76.97, "availability_status": "assigned", "skills": ["medical_support"], "equipment": ["medical_kit"], "capacity": 15, "current_workload": 8},
            ]
        ),
        
        # 15. Multiple incidents competing for same team
        RescueScenario(
            scenario_id="rescue_015",
            incident_id=15,
            incident_title="Bridge Collapse",
            incident_type="Structural Failure",
            latitude=11.0200,
            longitude=76.9600,
            priority_level="critical",
            required_skills=["search_and_rescue"],
            required_equipment=["heavy_lifting"],
            affected_people=80,
            trapped_people=25,
            available_teams=[
                {"id": 3, "name": "Team Gamma", "latitude": 10.99, "longitude": 76.98, "availability_status": "available", "skills": ["search_and_rescue", "debris_removal"], "equipment": ["heavy_lifting", "cranes"], "capacity": 25, "current_workload": 0},
            ]
        ),
        
        # 16. Medical emergency
        RescueScenario(
            scenario_id="rescue_016",
            incident_id=16,
            incident_title="Hospital Emergency",
            incident_type="Medical",
            latitude=11.0016,
            longitude=76.9723,
            priority_level="critical",
            required_skills=["medical_support", "trauma_care"],
            required_equipment=["ambulance", "medical_kit", "stretchers"],
            affected_people=20,
            trapped_people=5,
            available_teams=[
                {"id": 2, "name": "GH Medical Unit", "latitude": 11.0016, "longitude": 76.9723, "availability_status": "available", "skills": ["medical_support", "trauma_care"], "equipment": ["ambulance", "medical_kit", "stretchers"], "capacity": 20, "current_workload": 5},
            ]
        ),
        
        # 17. Multiple requirements - complex scenario
        RescueScenario(
            scenario_id="rescue_017",
            incident_id=17,
            incident_title="School Bus Accident",
            incident_type="Accident",
            latitude=11.0312,
            longitude=77.0374,
            priority_level="high",
            required_skills=["medical_support", "child_safety"],
            required_equipment=["ambulance", "child_seat"],
            affected_people=45,
            trapped_people=10,
            available_teams=[
                {"id": 2, "name": "GH Medical Unit", "latitude": 11.03, "longitude": 77.04, "availability_status": "available", "skills": ["medical_support"], "equipment": ["ambulance", "medical_kit"], "capacity": 20, "current_workload": 3},
                {"id": 5, "name": "School Response Team", "latitude": 11.02, "longitude": 77.03, "availability_status": "available", "skills": ["child_safety"], "equipment": ["child_seat"], "capacity": 15, "current_workload": 0},
            ]
        ),
        
        # 18. Night-time incident with limited visibility
        RescueScenario(
            scenario_id="rescue_018",
            incident_id=18,
            incident_title="Night Flood",
            incident_type="Flood",
            latitude=10.9950,
            longitude=76.9750,
            priority_level="high",
            required_skills=["flood_rescue"],
            required_equipment=["boat", "flashlights"],
            affected_people=30,
            trapped_people=8,
            available_teams=[
                {"id": 1, "name": "CBE Disaster Response", "latitude": 10.99, "longitude": 76.98, "availability_status": "available", "skills": ["flood_rescue", "night_operations"], "equipment": ["boat", "flashlights", "life_jackets"], "capacity": 15, "current_workload": 0},
            ]
        ),
        
        # 19. Extreme weather condition
        RescueScenario(
            scenario_id="rescue_019",
            incident_id=19,
            incident_title="Cyclone Shelter Emergency",
            incident_type="Cyclone",
            latitude=10.9930,
            longitude=76.8290,
            priority_level="critical",
            required_skills=["disaster_response", "evacuation"],
            required_equipment=["transport_vehicles", "emergency_shelter"],
            affected_people=200,
            trapped_people=50,
            available_teams=[
                {"id": 5, "name": "TNFRS Station 1", "latitude": 11.02, "longitude": 76.96, "availability_status": "available", "skills": ["search_and_rescue", "evacuation_coordination"], "equipment": ["radio", "transport_vehicles"], "capacity": 30, "current_workload": 0},
            ]
        ),
        
        # 20. Remote area incident
        RescueScenario(
            scenario_id="rescue_020",
            incident_id=20,
            incident_title="Mountain Rescue",
            incident_type="Landslide",
            latitude=10.8500,
            longitude=76.7000,
            priority_level="high",
            required_skills=["mountain_rescue", "first_aid"],
            required_equipment=["climbing_gear", "stretcher"],
            affected_people=12,
            trapped_people=6,
            available_teams=[
                {"id": 4, "name": "Siruvani Forest Rangers", "latitude": 10.94, "longitude": 76.68, "availability_status": "available", "skills": ["air_rescue", "medical_support"], "equipment": ["helicopter", "hoists", "medical_kit"], "capacity": 5, "current_workload": 0},
            ]
        ),
        
        # 21. Easy local incident
        RescueScenario(
            scenario_id="rescue_021",
            incident_id=21,
            incident_title="Small Vehicle Accident",
            incident_type="Accident",
            latitude=11.0168,
            longitude=76.9558,
            priority_level="low",
            required_skills=[],
            required_equipment=[],
            affected_people=3,
            trapped_people=1,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 11.017, "longitude": 76.956, "availability_status": "available", "skills": [], "equipment": [], "capacity": 10, "current_workload": 0},
            ]
        ),
        
        # 22. Water flooding - multiple rescues needed
        RescueScenario(
            scenario_id="rescue_022",
            incident_id=22,
            incident_title="Flash Flood",
            incident_type="Flood",
            latitude=10.9925,
            longitude=76.9600,
            priority_level="critical",
            required_skills=["flood_rescue", "swiftwater_rescue"],
            required_equipment=["boat", "life_jackets", "rescue_boards"],
            affected_people=60,
            trapped_people=25,
            available_teams=[
                {"id": 1, "name": "CBE Disaster Response", "latitude": 10.99, "longitude": 76.96, "availability_status": "available", "skills": ["flood_rescue", "swiftwater_rescue", "first_aid"], "equipment": ["boat", "ropes", "life_jackets"], "capacity": 15, "current_workload": 0},
                {"id": 2, "name": "GH Medical Unit", "latitude": 11.00, "longitude": 76.97, "availability_status": "available", "skills": ["medical_support", "trauma_care"], "equipment": ["ambulance", "medical_kit"], "capacity": 20, "current_workload": 5},
            ]
        ),
        
        # 23. Industrial accident
        RescueScenario(
            scenario_id="rescue_023",
            incident_id=23,
            incident_title="Factory Accident",
            incident_type="Industrial Accident",
            latitude=11.0270,
            longitude=77.0062,
            priority_level="high",
            required_skills=["technical_rescue", "hazmat_response"],
            required_equipment=["cutting_equipment", "hazmat_suit"],
            affected_people=30,
            trapped_people=10,
            available_teams=[
                {"id": 3, "name": "Sulur Air Base Lift", "latitude": 11.01, "longitude": 77.16, "availability_status": "available", "skills": ["debris_removal", "heavy_lifting"], "equipment": ["crane", "bulldozers", "pumps"], "capacity": 10, "current_workload": 10},
            ]
        ),
        
        # 24. Multiple victims - capacity test
        RescueScenario(
            scenario_id="rescue_024",
            incident_id=24,
            incident_title="Mass Casualty Incident",
            incident_type="Accident",
            latitude=11.0200,
            longitude=76.9600,
            priority_level="critical",
            required_skills=["medical_support", "mass_casualty"],
            required_equipment=["multiple_ambulances", "medical_kits"],
            affected_people=100,
            trapped_people=0,
            available_teams=[
                {"id": 2, "name": "GH Medical Unit", "latitude": 11.00, "longitude": 76.97, "availability_status": "available", "skills": ["medical_support", "trauma_care"], "equipment": ["ambulance", "medical_kit", "stretchers"], "capacity": 20, "current_workload": 5},
            ]
        ),
        
        # 25. Reallocation scenario
        RescueScenario(
            scenario_id="rescue_025",
            incident_id=25,
            incident_title="Reallocation Test",
            incident_type="Flood",
            latitude=10.9378,
            longitude=76.7455,
            priority_level="high",
            required_skills=["flood_rescue"],
            required_equipment=["boat"],
            affected_people=20,
            trapped_people=5,
            available_teams=[
                {"id": 3, "name": "Team Gamma", "latitude": 10.94, "longitude": 76.75, "availability_status": "available", "skills": ["search_and_rescue", "flood_rescue"], "equipment": ["boat", "heavy_lifting"], "capacity": 20, "current_workload": 0},
                {"id": 4, "name": "Team Delta", "latitude": 10.94, "longitude": 76.75, "availability_status": "assigned", "skills": ["flood_rescue"], "equipment": ["boat"], "capacity": 15, "current_workload": 15},
            ]
        ),
    ]