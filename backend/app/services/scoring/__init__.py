"""
Shared X-DMRA scoring functions for research evaluation.

This package provides pure scoring functions with no database access,
no writes, and no allocation logic. Both production services and
evaluation adapters use these functions as the single source of truth
for scoring behavior.
"""
from app.services.scoring.common import (
    haversine_distance,
    normalize_string,
    normalize_string_set,
    distance_score_km,
    distance_score_tiered,
    RouteRiskLevel,
)
from app.services.scoring.rescue_scoring import (
    RescueScoringInput,
    RescueScoringOutput,
    score_rescue_team,
    rank_rescue_teams,
)
from app.services.scoring.relief_scoring import (
    ReliefVehicleInput,
    ReliefScoringInput,
    ReliefScoringOutput,
    ReliefItemSupply,
    score_relief_warehouse,
    rank_relief_warehouses,
    WEIGHT_STOCK_COVERAGE,
    WEIGHT_ITEM_COVERAGE,
    WEIGHT_DISTANCE,
    WEIGHT_VEHICLE_CAPACITY,
    WEIGHT_ROUTE_SAFETY,
    WEIGHT_WORKLOAD,
)
from app.services.scoring.shelter_scoring import (
    ShelterScoringInput,
    ShelterScoringOutput,
    score_shelter,
    rank_shelters,
    calculate_overcrowding_risk,
    WEIGHT_CAPACITY,
    WEIGHT_VULNERABILITY,
    WEIGHT_UTILITIES,
    WEIGHT_OVERCROWDING,
    WEIGHT_ROUTE_SAFETY as SHELTER_ROUTE_WEIGHT,
    WEIGHT_WORKLOAD as SHELTER_WORKLOAD_WEIGHT,
)

__all__ = [
    "haversine_distance",
    "normalize_string",
    "normalize_string_set",
    "distance_score_km",
    "distance_score_tiered",
    "RouteRiskLevel",
    "RescueScoringInput",
    "RescueScoringOutput",
    "score_rescue_team",
    "rank_rescue_teams",
    "ReliefVehicleInput",
    "ReliefScoringInput",
    "ReliefScoringOutput",
    "ReliefItemSupply",
    "score_relief_warehouse",
    "rank_relief_warehouses",
    "WEIGHT_STOCK_COVERAGE",
    "WEIGHT_ITEM_COVERAGE",
    "WEIGHT_DISTANCE",
    "WEIGHT_VEHICLE_CAPACITY",
    "WEIGHT_ROUTE_SAFETY",
    "WEIGHT_WORKLOAD",
    "ShelterScoringInput",
    "ShelterScoringOutput",
    "score_shelter",
    "rank_shelters",
    "calculate_overcrowding_risk",
    "WEIGHT_CAPACITY",
    "WEIGHT_VULNERABILITY",
    "WEIGHT_UTILITIES",
    "WEIGHT_OVERCROWDING",
    "SHELTER_ROUTE_WEIGHT",
    "SHELTER_WORKLOAD_WEIGHT",
]