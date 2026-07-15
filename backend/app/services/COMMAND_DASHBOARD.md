# Unified Emergency Command Dashboard

This document describes the Command Dashboard system implemented in Phase 8.

## 1. Overview

The Unified Emergency Command Dashboard provides a single command-center interface for monitoring and coordinating disaster response operations across rescue, relief, and shelter domains.

## 2. Dashboard Metric Definitions

| Metric | Description |
|--------|-------------|
| `total_active_incidents` | Count of incidents with status in: reported, verified, assigned, in_progress |
| `critical_incidents` | Active incidents with priority_level = critical |
| `high_priority_incidents` | Active incidents with priority_level = high |
| `unassigned_incidents` | Active incidents without an approved allocation |
| `incidents_awaiting_rescue` | Incidents with officer_approval_pending alerts |
| `active_rescue_allocations` | Allocations with status = approved |
| `rescue_reallocations_pending` | Alerts with category = rescue_route_blocked |
| `active_relief_requests` | Relief requests with status in: pending, partially_allocated |
| `relief_shortages` | Alerts with category = relief_shortage |
| `dispatches_preparing` | Dispatches with status = preparing |
| `dispatches_in_transit` | Dispatches with status = dispatched |
| `low_stock_alerts` | Alerts with category = warehouse_low_stock |
| `active_shelter_requests` | Shelter requests with status in: pending, partially_allocated |
| `uncovered_displaced_people` | Total displaced people in non-allocated shelter requests |
| `shelter_reservations_in_transit` | People in shelter reservations with status = in_transit |
| `high_overcrowding_risk_shelters` | Shelters where (occupied + reserved) / total >= 85% |
| `blocked_routes` | Shelter route conditions with is_blocked = true |
| `high_risk_routes` | Shelter route conditions with risk_level = high |
| `pending_officer_decisions` | Alerts with category = officer_approval_pending |

## 3. Alert Generation Rules

Alerts are generated from stored conditions in the database:

| Category | Trigger Condition | Severity |
|----------|-------------------|----------|
| `critical_incident` | Critical incident with no approved allocation | critical |
| `incident_unassigned` | High priority incident with no approved allocation | high |
| `rescue_route_blocked` | Route condition with is_blocked = true for an allocated team | critical |
| `shelter_overcrowding_high` | Shelter at >= 95% capacity | critical |
| `shelter_overcrowding_high` | Shelter at >= 85% capacity | high |
| `shelter_route_blocked` | Shelter route with is_blocked = true | critical |
| `warehouse_low_stock` | Inventory below reorder level | configurable |
| `relief_shortage` | Relief request items with approved_quantity < requested_quantity | high |
| `officer_approval_pending` | Incident awaiting allocation approval | high |
| `stale_operational_update` | Incident not updated in 4+ hours | warning |

## 4. Alert Severity Levels

| Level | Description |
|-------|-------------|
| `critical` | Immediate action required - life safety at risk |
| `high` | Urgent attention needed - significant impact |
| `warning` | Attention recommended - potential escalation risk |
| `info` | Informational - no immediate action |

## 5. Alert Deduplication

The system prevents duplicate active alerts:
- Before creating a new alert, the system checks for existing active or acknowledged alerts with the same category, incident_id, resource_type, and resource_id.
- If an alert exists with status = active or acknowledged, the existing alert is updated (severity/description) rather than creating a duplicate.
- Alert acknowledgement does NOT resolve the underlying operational condition.

## 6. Alert Acknowledgement vs Resolution

| Action | Effect |
|--------|--------|
| **Acknowledge** | Indicates officer is aware; alert remains active; does NOT modify resource state |
| **Resolve** | Indicates condition has been addressed; alert marked resolved; underlying condition must actually be fixed separately |

## 7. Pending Decision Ordering

Pending decisions are sorted by:
1. Severity (critical > high > medium > low)
2. Priority level (critical > high > medium > low)
3. Waiting duration (longest first)

## 8. Operational Summary Structure

The incident operational summary provides a unified view:

```
- Incident Overview: id, title, type, location, priority, status
- Priority Analysis: rule_priority, ml_priority, agreement status
- Rescue Operations: assigned_team, allocation_status, rescue_score
- Relief Operations: relief_request_status, items, shortages, dispatches
- Shelter Operations: shelter_request_status, displaced, reserved, admitted
- Alerts: active_alerts count, highest severity, pending_decisions
- Routes: blocked_routes count
```

## 9. Unified Timeline Sources

Timeline events are aggregated from:
- Incident creation (incident_creation)
- Priority calculation (priority_calculation)
- ML predictions (ml_prediction)
- Rescue recommendations and approvals (rescue_recommendation, rescue_allocation)
- Rescue reallocations (rescue_reallocation)
- Relief-demand generation (relief_demand_generation)
- Relief recommendations (relief_recommendation)
- Relief dispatches (relief_dispatch)
- Inventory movements (inventory_movement)
- Shelter requests (shelter_request)
- Shelter reservations (shelter_reservation)
- Shelter admissions (shelter_admission)
- Shelter reallocations (shelter_reallocation)
- Route updates (route_update)
- Alert actions (alert_acknowledged, alert_resolved)

## 10. Command Map Limitations

- Map displays straight-line positions only
- Distances shown are Haversine (straight-line), not road distances
- No live GPS tracking
- No real-time traffic data
- Route risk is evaluated from stored conditions, not real-time navigation

## 11. Dashboard Refresh

- Manual refresh available via button
- Optional 30-60 second auto-refresh (clearly labeled as dashboard refresh)
- All data sourced from stored records (no random generation)

## 12. Simulation Disclaimer

All data in this system is **demonstration data** for development and testing purposes. It does not represent real emergency situations, actual resource availability, or live government systems.

## 13. Officer Approval Requirement

The Command Dashboard provides recommendations and alerts, but all allocation decisions require explicit officer approval. The system does not automatically approve or execute allocations.

## 14. API Endpoints

### Command Dashboard
- `GET /api/command/dashboard-summary` - Summary metrics
- `GET /api/command/pending-decisions` - Pending officer decisions
- `GET /api/command/alerts` - List alerts (supports ?severity= and ?status= filters)
- `POST /api/command/alerts/generate` - Trigger alert generation
- `PATCH /api/command/alerts/{alert_id}/acknowledge` - Acknowledge alert
- `PATCH /api/command/alerts/{alert_id}/resolve` - Resolve alert

### Incident Operations
- `GET /api/command/incidents/{incident_id}/operational-summary` - Operational summary for an incident
- `GET /api/command/incidents/{incident_id}/timeline` - Unified timeline for an incident

### Map
- `GET /api/command/map-overview` - Map data for command center

## 15. Known Limitations

1. No WebSocket real-time updates (polling-based refresh only)
2. No road-distance routing (straight-line distances only)
3. No live GPS tracking of vehicles or teams
4. No integration with external government systems
5. Timeline aggregation limited to database-stored events
6. Shelter overcrowding calculations do not account for transient admissions
7. Relief shortage detection based on approved vs. requested quantities, not predictive
8. Pending decision queue aggregation limited to alert-generated decisions

## 16. Database Schema Changes

Phase 8 introduced the following new tables:
- `operational_alerts` - Stores generated alerts with status tracking

## 17. Test Coverage

Phase 8 includes 40 tests covering:
- Dashboard summary metrics
- Alert generation and deduplication
- Alert acknowledgement and resolution
- Pending decision ordering
- Incident operational summary
- Unified timeline
- Filtering functionality
- Existing API regression tests