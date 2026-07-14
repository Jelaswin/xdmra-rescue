from app.models import Incident
from app.schemas import ReliefDemandSuggestion, ReliefDemandSuggestionItem

# Configurable planning rules
MEALS_PER_PERSON_PER_DAY = 3
LITRES_PER_PERSON_PER_DAY = 3
PEOPLE_PER_MEDICAL_KIT = 10  # 1 kit for every 10 injured/vulnerable
PEOPLE_PER_TENT = 5
HYGIENE_KITS_PER_HOUSEHOLD = 1  # assuming 4 people per household
PEOPLE_PER_HOUSEHOLD = 4
BABY_KITS_PER_CHILD = 1
BLANKETS_PER_PERSON = 1
EMERGENCY_LIGHT_PER_HOUSEHOLD = 1

def generate_relief_demand(incident: Incident, support_duration_days: int) -> ReliefDemandSuggestion:
    items = []
    
    # Base calculation fields
    affected = incident.affected_people
    injured = incident.injured_people
    vulnerable = incident.vulnerable_people
    children = incident.children_count
    
    # 1. Food Packets
    if affected > 0:
        food_qty = affected * MEALS_PER_PERSON_PER_DAY * support_duration_days
        items.append(ReliefDemandSuggestionItem(
            item_type="food_packet",
            quantity=food_qty,
            unit="packets",
            reason=f"{affected} affected people × {MEALS_PER_PERSON_PER_DAY} meals × {support_duration_days} days"
        ))
        
    # 2. Drinking Water
    if affected > 0:
        water_qty = affected * LITRES_PER_PERSON_PER_DAY * support_duration_days
        items.append(ReliefDemandSuggestionItem(
            item_type="drinking_water_litre",
            quantity=water_qty,
            unit="litres",
            reason=f"{affected} affected people × {LITRES_PER_PERSON_PER_DAY} litres × {support_duration_days} days"
        ))
        
    # 3. Medical Kits
    if injured > 0 or vulnerable > 0:
        # e.g., 1 kit per 10 injured/vulnerable, minimum 1
        med_qty = max(1, (injured + vulnerable) // PEOPLE_PER_MEDICAL_KIT)
        items.append(ReliefDemandSuggestionItem(
            item_type="medical_kit",
            quantity=med_qty,
            unit="kits",
            reason=f"{injured} injured + {vulnerable} vulnerable people (1 kit per {PEOPLE_PER_MEDICAL_KIT} people)"
        ))
        
    # 4. Blankets
    if affected > 0:
        items.append(ReliefDemandSuggestionItem(
            item_type="blanket",
            quantity=affected * BLANKETS_PER_PERSON,
            unit="items",
            reason=f"{affected} affected people × {BLANKETS_PER_PERSON} blanket"
        ))
        
    # 5. Hygiene Kits
    if affected > 0:
        households = max(1, affected // PEOPLE_PER_HOUSEHOLD)
        items.append(ReliefDemandSuggestionItem(
            item_type="hygiene_kit",
            quantity=households * HYGIENE_KITS_PER_HOUSEHOLD,
            unit="kits",
            reason=f"Estimated {households} households ({PEOPLE_PER_HOUSEHOLD} people/household) × {HYGIENE_KITS_PER_HOUSEHOLD} kit"
        ))
        
    # 6. Baby Supply Kits
    if children > 0:
        items.append(ReliefDemandSuggestionItem(
            item_type="baby_supply_kit",
            quantity=children * BABY_KITS_PER_CHILD,
            unit="kits",
            reason=f"{children} children × {BABY_KITS_PER_CHILD} kit"
        ))
        
    # 7. Emergency Lights
    if affected > 0:
        households = max(1, affected // PEOPLE_PER_HOUSEHOLD)
        items.append(ReliefDemandSuggestionItem(
            item_type="emergency_light",
            quantity=households * EMERGENCY_LIGHT_PER_HOUSEHOLD,
            unit="items",
            reason=f"Estimated {households} households × {EMERGENCY_LIGHT_PER_HOUSEHOLD} light"
        ))
        
    # 8. Temporary Tents (for displaced/trapped or severe incidents)
    # Using affected people for rough estimation of displaced
    if incident.severity in ['high', 'critical'] and affected > 0:
        tents_qty = max(1, affected // PEOPLE_PER_TENT)
        items.append(ReliefDemandSuggestionItem(
            item_type="temporary_tent",
            quantity=tents_qty,
            unit="tents",
            reason=f"High/Critical severity: {affected} affected people (1 tent per {PEOPLE_PER_TENT} people)"
        ))
        
    return ReliefDemandSuggestion(
        support_duration_days=support_duration_days,
        suggested_items=items
    )
