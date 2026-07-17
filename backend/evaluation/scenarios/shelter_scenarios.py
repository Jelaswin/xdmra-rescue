"""
Deterministic Shelter Evaluation Scenarios.

20+ scenarios covering various shelter allocation conditions.
All scenarios are deterministic and reproducible.
"""

from typing import List, Dict, Any
from ..baselines.shelter_baselines import ShelterScenario


def get_shelter_scenarios() -> List[ShelterScenario]:
    """Return all deterministic shelter evaluation scenarios."""
    return [
        # 1. Single shelter has enough capacity
        ShelterScenario(
            scenario_id="shelter_001",
            incident_id=1,
            displaced_people=100,
            medical_required=False,
            accessibility_required=False,
            latitude=11.0289,
            longitude=77.0270,
            shelters=[
                {"id": 1, "name": "Codissia Trade Fair Complex", "latitude": 11.0289, "longitude": 77.0270, "operating_status": "open", "total_capacity": 5000, "occupied_capacity": 1000, "reserved_capacity": 500, "has_medical_support": 1, "has_accessibility_support": 1},
            ]
        ),
        
        # 2. Split shelter allocation required
        ShelterScenario(
            scenario_id="shelter_002",
            incident_id=2,
            displaced_people=2500,
            medical_required=False,
            accessibility_required=False,
            latitude=10.9950,
            longitude=76.9750,
            shelters=[
                {"id": 1, "name": "Codissia Trade Fair Complex", "latitude": 11.0289, "longitude": 77.0270, "operating_status": "open", "total_capacity": 5000, "occupied_capacity": 3000, "reserved_capacity": 1000, "has_medical_support": 1, "has_accessibility_support": 1},
                {"id": 2, "name": "GCT Shelter", "latitude": 11.0180, "longitude": 76.9360, "operating_status": "open", "total_capacity": 1500, "occupied_capacity": 500, "reserved_capacity": 200, "has_medical_support": 1, "has_accessibility_support": 1},
            ]
        ),
        
        # 3. Medical support required
        ShelterScenario(
            scenario_id="shelter_003",
            incident_id=3,
            displaced_people=50,
            medical_required=True,
            accessibility_required=False,
            latitude=11.0016,
            longitude=76.9723,
            shelters=[
                {"id": 1, "name": "Codissia Trade Fair Complex", "latitude": 11.0289, "longitude": 77.0270, "operating_status": "open", "total_capacity": 5000, "occupied_capacity": 1000, "reserved_capacity": 500, "has_medical_support": 1, "has_accessibility_support": 1},
                {"id": 3, "name": "PSG College", "latitude": 11.0312, "longitude": 77.0374, "operating_status": "open", "total_capacity": 2000, "occupied_capacity": 500, "reserved_capacity": 300, "has_medical_support": 1, "has_accessibility_support": 1},
            ]
        ),
        
        # 4. Accessibility required
        ShelterScenario(
            scenario_id="shelter_004",
            incident_id=4,
            displaced_people=30,
            medical_required=False,
            accessibility_required=True,
            latitude=11.0094,
            longitude=76.9472,
            shelters=[
                {"id": 1, "name": "Codissia Trade Fair Complex", "latitude": 11.0289, "longitude": 77.0270, "operating_status": "open", "total_capacity": 5000, "occupied_capacity": 1000, "reserved_capacity": 500, "has_medical_support": 1, "has_accessibility_support": 1},
                {"id": 4, "name": "RS Puram Community Hall", "latitude": 11.0094, "longitude": 76.9472, "operating_status": "open", "total_capacity": 300, "occupied_capacity": 100, "reserved_capacity": 50, "has_medical_support": 0, "has_accessibility_support": 1},
            ]
        ),
        
        # 5. Nearly full shelter
        ShelterScenario(
            scenario_id="shelter_005",
            incident_id=5,
            displaced_people=100,
            medical_required=False,
            accessibility_required=False,
            latitude=11.0289,
            longitude=77.0270,
            shelters=[
                {"id": 1, "name": "Codissia Trade Fair Complex", "latitude": 11.0289, "longitude": 77.0270, "operating_status": "open", "total_capacity": 5000, "occupied_capacity": 4800, "reserved_capacity": 100, "has_medical_support": 1, "has_accessibility_support": 1},
            ]
        ),
        
        # 6. Critical overcrowding risk
        ShelterScenario(
            scenario_id="shelter_006",
            incident_id=6,
            displaced_people=500,
            medical_required=False,
            accessibility_required=False,
            latitude=11.0180,
            longitude=76.9360,
            shelters=[
                {"id": 2, "name": "GCT Shelter", "latitude": 11.0180, "longitude": 76.9360, "operating_status": "open", "total_capacity": 1500, "occupied_capacity": 1400, "reserved_capacity": 50, "has_medical_support": 1, "has_accessibility_support": 1},
            ]
        ),
        
        # 7. Blocked shelter route
        ShelterScenario(
            scenario_id="shelter_007",
            incident_id=7,
            displaced_people=200,
            medical_required=False,
            accessibility_required=False,
            latitude=11.0289,
            longitude=77.0270,
            shelters=[
                {"id": 1, "name": "Codissia Trade Fair Complex", "latitude": 11.0289, "longitude": 77.0270, "operating_status": "open", "total_capacity": 5000, "occupied_capacity": 1000, "reserved_capacity": 500, "has_medical_support": 1, "has_accessibility_support": 1},
            ]
        ),
        
        # 8. Shelter unavailable
        ShelterScenario(
            scenario_id="shelter_008",
            incident_id=8,
            displaced_people=300,
            medical_required=False,
            accessibility_required=False,
            latitude=11.0200,
            longitude=76.9600,
            shelters=[
                {"id": 2, "name": "GCT Shelter", "latitude": 11.0180, "longitude": 76.9360, "operating_status": "closed", "total_capacity": 1500, "occupied_capacity": 0, "reserved_capacity": 0, "has_medical_support": 1, "has_accessibility_support": 1},
            ]
        ),
        
        # 9. Insufficient total capacity
        ShelterScenario(
            scenario_id="shelter_009",
            incident_id=9,
            displaced_people=5000,
            medical_required=False,
            accessibility_required=False,
            latitude=10.9925,
            longitude=76.9600,
            shelters=[
                {"id": 1, "name": "Codissia Trade Fair Complex", "latitude": 11.0289, "longitude": 77.0270, "operating_status": "open", "total_capacity": 5000, "occupied_capacity": 3000, "reserved_capacity": 1000, "has_medical_support": 1, "has_accessibility_support": 1},
                {"id": 2, "name": "GCT Shelter", "latitude": 11.0180, "longitude": 76.9360, "operating_status": "open", "total_capacity": 1500, "occupied_capacity": 1000, "reserved_capacity": 200, "has_medical_support": 1, "has_accessibility_support": 1},
            ]
        ),
        
        # 10. Reallocation required - shelter full
        ShelterScenario(
            scenario_id="shelter_010",
            incident_id=10,
            displaced_people=100,
            medical_required=False,
            accessibility_required=False,
            latitude=11.0180,
            longitude=76.9360,
            shelters=[
                {"id": 2, "name": "GCT Shelter", "latitude": 11.0180, "longitude": 76.9360, "operating_status": "open", "total_capacity": 1500, "occupied_capacity": 1450, "reserved_capacity": 50, "has_medical_support": 1, "has_accessibility_support": 1},
                {"id": 3, "name": "PSG College", "latitude": 11.0312, "longitude": 77.0374, "operating_status": "open", "total_capacity": 2000, "occupied_capacity": 500, "reserved_capacity": 300, "has_medical_support": 1, "has_accessibility_support": 1},
            ]
        ),
        
        # 11. Vulnerable population - medical and accessibility
        ShelterScenario(
            scenario_id="shelter_011",
            incident_id=11,
            displaced_people=40,
            medical_required=True,
            accessibility_required=True,
            latitude=11.0094,
            longitude=76.9472,
            shelters=[
                {"id": 1, "name": "Codissia Trade Fair Complex", "latitude": 11.0289, "longitude": 77.0270, "operating_status": "open", "total_capacity": 5000, "occupied_capacity": 1000, "reserved_capacity": 500, "has_medical_support": 1, "has_accessibility_support": 1},
            ]
        ),
        
        # 12. Small displaced group
        ShelterScenario(
            scenario_id="shelter_012",
            incident_id=12,
            displaced_people=15,
            medical_required=False,
            accessibility_required=False,
            latitude=11.0094,
            longitude=76.9472,
            shelters=[
                {"id": 4, "name": "RS Puram Community Hall", "latitude": 11.0094, "longitude": 76.9472, "operating_status": "open", "total_capacity": 300, "occupied_capacity": 100, "reserved_capacity": 50, "has_medical_support": 0, "has_accessibility_support": 0},
            ]
        ),
        
        # 13. Large family group
        ShelterScenario(
            scenario_id="shelter_013",
            incident_id=13,
            displaced_people=25,
            medical_required=False,
            accessibility_required=True,
            latitude=11.0312,
            longitude=77.0374,
            shelters=[
                {"id": 3, "name": "PSG College", "latitude": 11.0312, "longitude": 77.0374, "operating_status": "open", "total_capacity": 2000, "occupied_capacity": 500, "reserved_capacity": 300, "has_medical_support": 1, "has_accessibility_support": 1},
            ]
        ),
        
        # 14. Children and elderly focus
        ShelterScenario(
            scenario_id="shelter_014",
            incident_id=14,
            displaced_people=80,
            medical_required=True,
            accessibility_required=True,
            latitude=11.0289,
            longitude=77.0270,
            shelters=[
                {"id": 1, "name": "Codissia Trade Fair Complex", "latitude": 11.0289, "longitude": 77.0270, "operating_status": "open", "total_capacity": 5000, "occupied_capacity": 1000, "reserved_capacity": 500, "has_medical_support": 1, "has_accessibility_support": 1, "has_women_child_safe_area": 1},
            ]
        ),
        
        # 15. Perfect match - large shelter available
        ShelterScenario(
            scenario_id="shelter_015",
            incident_id=15,
            displaced_people=500,
            medical_required=False,
            accessibility_required=False,
            latitude=11.0289,
            longitude=77.0270,
            shelters=[
                {"id": 1, "name": "Codissia Trade Fair Complex", "latitude": 11.0289, "longitude": 77.0270, "operating_status": "open", "total_capacity": 5000, "occupied_capacity": 500, "reserved_capacity": 200, "has_medical_support": 1, "has_accessibility_support": 1},
            ]
        ),
        
        # 16. Limited shelter
        ShelterScenario(
            scenario_id="shelter_016",
            incident_id=16,
            displaced_people=200,
            medical_required=False,
            accessibility_required=False,
            latitude=11.0094,
            longitude=76.9472,
            shelters=[
                {"id": 4, "name": "RS Puram Community Hall", "latitude": 11.0094, "longitude": 76.9472, "operating_status": "limited", "total_capacity": 300, "occupied_capacity": 200, "reserved_capacity": 50, "has_medical_support": 0, "has_accessibility_support": 0},
            ]
        ),
        
        # 17. Women and child safe area required
        ShelterScenario(
            scenario_id="shelter_017",
            incident_id=17,
            displaced_people=60,
            medical_required=False,
            accessibility_required=False,
            latitude=11.0312,
            longitude=77.0374,
            shelters=[
                {"id": 1, "name": "Codissia Trade Fair Complex", "latitude": 11.0289, "longitude": 77.0270, "operating_status": "open", "total_capacity": 5000, "occupied_capacity": 1000, "reserved_capacity": 500, "has_medical_support": 1, "has_accessibility_support": 1, "has_women_child_safe_area": 1},
                {"id": 3, "name": "PSG College", "latitude": 11.0312, "longitude": 77.0374, "operating_status": "open", "total_capacity": 2000, "occupied_capacity": 500, "reserved_capacity": 300, "has_medical_support": 1, "has_accessibility_support": 1, "has_women_child_safe_area": 1},
            ]
        ),
        
        # 18. Exact capacity match
        ShelterScenario(
            scenario_id="shelter_018",
            incident_id=18,
            displaced_people=200,
            medical_required=False,
            accessibility_required=False,
            latitude=11.0180,
            longitude=76.9360,
            shelters=[
                {"id": 2, "name": "GCT Shelter", "latitude": 11.0180, "longitude": 76.9360, "operating_status": "open", "total_capacity": 1500, "occupied_capacity": 1300, "reserved_capacity": 0, "has_medical_support": 1, "has_accessibility_support": 1},
            ]
        ),
        
        # 19. Multiple requirements - all features needed
        ShelterScenario(
            scenario_id="shelter_019",
            incident_id=19,
            displaced_people=50,
            medical_required=True,
            accessibility_required=True,
            latitude=11.0094,
            longitude=76.9472,
            shelters=[
                {"id": 1, "name": "Codissia Trade Fair Complex", "latitude": 11.0289, "longitude": 77.0270, "operating_status": "open", "total_capacity": 5000, "occupied_capacity": 1000, "reserved_capacity": 500, "has_medical_support": 1, "has_accessibility_support": 1, "has_women_child_safe_area": 1},
            ]
        ),
        
        # 20. No shelter available
        ShelterScenario(
            scenario_id="shelter_020",
            incident_id=20,
            displaced_people=100,
            medical_required=False,
            accessibility_required=False,
            latitude=11.0200,
            longitude=76.9600,
            shelters=[
                {"id": 1, "name": "Codissia Trade Fair Complex", "latitude": 11.0289, "longitude": 77.0270, "operating_status": "full", "total_capacity": 5000, "occupied_capacity": 5000, "reserved_capacity": 0, "has_medical_support": 1, "has_accessibility_support": 1},
                {"id": 2, "name": "GCT Shelter", "latitude": 11.0180, "longitude": 76.9360, "operating_status": "closed", "total_capacity": 1500, "occupied_capacity": 1500, "reserved_capacity": 0, "has_medical_support": 1, "has_accessibility_support": 1},
            ]
        ),
    ]