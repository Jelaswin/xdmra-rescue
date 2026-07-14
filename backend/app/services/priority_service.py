from datetime import datetime, timezone
from app.models import Incident, IncidentSeverity
from app.schemas import PriorityResult

# Configuration weights
WEIGHTS = {
    "severity_critical": 25,
    "severity_high": 15,
    "severity_medium": 5,
    "severity_low": 0,
    "injury_multiplier": 2.0,
    "injury_max": 20,
    "trapped_multiplier": 3.0,
    "trapped_max": 25,
    "vulnerable_multiplier": 1.5,
    "vulnerable_max": 15,
    "affected_multiplier": 0.1,
    "affected_max": 10,
    "waiting_hour_multiplier": 0.5,
    "waiting_max": 5
}

def calculate_incident_priority(incident: Incident) -> PriorityResult:
    reasons = []
    factor_breakdown = {}
    
    # 1. Severity Contribution
    severity_val = 0
    if incident.severity == IncidentSeverity.critical:
        severity_val = WEIGHTS["severity_critical"]
    elif incident.severity == IncidentSeverity.high:
        severity_val = WEIGHTS["severity_high"]
    elif incident.severity == IncidentSeverity.medium:
        severity_val = WEIGHTS["severity_medium"]
    
    factor_breakdown["severity"] = severity_val
    if severity_val > 0:
        reasons.append(f"Base severity is {incident.severity.value}.")
        
    # 2. Injuries
    injury_score = min(WEIGHTS["injury_max"], incident.injured_people * WEIGHTS["injury_multiplier"])
    factor_breakdown["injuries"] = injury_score
    if injury_score > 0:
        reasons.append(f"{incident.injured_people} injured victim(s) require medical support.")

    # 3. Trapped People
    trapped_score = min(WEIGHTS["trapped_max"], incident.trapped_people * WEIGHTS["trapped_multiplier"])
    factor_breakdown["trapped_people"] = trapped_score
    if trapped_score > 0:
        reasons.append(f"{incident.trapped_people} trapped people require immediate rescue.")

    # 4. Vulnerability (children + elderly + general vulnerable)
    total_vuln = incident.vulnerable_people + incident.children_count + incident.elderly_count
    vuln_score = min(WEIGHTS["vulnerable_max"], total_vuln * WEIGHTS["vulnerable_multiplier"])
    factor_breakdown["vulnerability"] = vuln_score
    if vuln_score > 0:
        reasons.append(f"Vulnerable populations (children/elderly/others) are present.")

    # 5. Affected Population
    affected_score = min(WEIGHTS["affected_max"], incident.affected_people * WEIGHTS["affected_multiplier"])
    factor_breakdown["affected_population"] = affected_score
    
    # 6. Waiting Time
    if incident.created_at:
        now = datetime.now(timezone.utc)
        created_utc = incident.created_at.replace(tzinfo=timezone.utc) if incident.created_at.tzinfo is None else incident.created_at
        delta_hours = (now - created_utc).total_seconds() / 3600.0
        waiting_score = min(WEIGHTS["waiting_max"], delta_hours * WEIGHTS["waiting_hour_multiplier"])
    else:
        waiting_score = 0
    factor_breakdown["waiting_time"] = round(waiting_score, 1)

    total_score = min(100.0, sum(factor_breakdown.values()))
    
    # Thresholds
    if total_score >= 75:
        priority_level = "critical"
    elif total_score >= 50:
        priority_level = "high"
    elif total_score >= 25:
        priority_level = "medium"
    else:
        priority_level = "low"
        
    if not reasons:
        reasons.append("Standard incident processing.")

    return PriorityResult(
        priority_score=round(total_score, 1),
        priority_level=priority_level,
        reasons=reasons,
        factor_breakdown=factor_breakdown
    )
