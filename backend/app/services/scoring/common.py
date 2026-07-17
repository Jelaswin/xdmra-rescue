"""
Shared scoring utilities for X-DMRA research evaluation.

Contains no database queries, no writes, no allocation logic.
Pure functions only.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class RouteRiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def normalize_string(s: str) -> str:
    """Normalize skill/equipment string to lowercase set key."""
    return s.lower().replace("-", "_").replace(" ", "_")


def normalize_string_set(str_list: list[str]) -> set[str]:
    """Normalize a list of strings to a lowercase set."""
    if not str_list:
        return set()
    return {normalize_string(s) for s in str_list}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate straight-line distance in km using Haversine formula."""
    R = 6371.0
    lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def distance_score_km(dist_km: float) -> float:
    """
    Rescue-style continuous distance score.
    Max 30 points at 0 km, 0 points at >= 50 km.
    """
    return max(0.0, 30.0 - (dist_km / 50.0) * 30.0)


def distance_score_tiered(dist_km: float) -> float:
    """
    Relief/shelter 3-tier distance score.
    15 pts if <= 10 km, 10.5 pts if 10-50 km, 4.5 pts if > 50 km.
    """
    if dist_km <= 10.0:
        return 15.0
    elif dist_km <= 50.0:
        return 10.5
    else:
        return 4.5