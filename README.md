# X-DMRA Rescue

An Explainable Dynamic Multi-Resource Allocation System for Disaster Response.

## Overview
X-DMRA Rescue is a full-stack emergency response coordination system supporting:
- Incident creation and management
- Rule-based and ML-powered priority prediction
- Explainable rescue-team allocation and reallocation
- Relief-supply demand calculation and dispatch
- Shelter allocation with overcrowding prevention
- **Unified Emergency Command Dashboard (Phase 8)**

**Note:** All data is demonstration data for development purposes. No live emergency systems are integrated.

## Features Implemented
- RESTful API with FastAPI and SQLite (PostgreSQL compatible schema).
- Incident creation, management, and status tracking.
- Rule-based Incident Priority Engine with explainable factors.
- Custom Machine Learning Priority Predictor (Random Forest Classifier) using synthetic dataset.
- Explainable Rescue Team Allocation (skill matching, capacity, workload, distance).
- Dynamic Rescue Team Reallocation with route-risk handling.
- Relief-demand calculation, warehouse ranking, and split allocation.
- Shelter Evaluation with overcrowding prevention.
- Unified Emergency Command Dashboard with alerts and pending decisions.
- Map and Location Management via OpenStreetMap Nominatim Geocoding.
- Officer-controlled allocation, dispatch, and reservation approval.
- **188 passing backend tests**.

## Tech Stack
- **Frontend**: React, Vite, TypeScript, Tailwind CSS
- **Backend**: Python 3, FastAPI, SQLAlchemy, SQLite (PostgreSQL compatible schema), Pytest, Scikit-Learn, Pandas, Joblib

## Folder Structure
```text
x-dmra-rescue/
  frontend/     # React frontend
  backend/      # FastAPI backend
  PLAN.md       # Implementation plan
  README.md     # This file
```

## Prerequisites
- Node.js (v20+ recommended)
- Python (v3.10+ recommended)
- Git

## Windows Setup Instructions

### Backend
1. Open a terminal in the `backend` directory.
2. Create a virtual environment:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env`.
5. Run the server:
   ```cmd
   uvicorn app.main:app --reload
   ```

### Frontend
1. Open a new terminal in the `frontend` directory.
2. Install dependencies:
   ```cmd
   npm install
   ```
3. Copy `.env.example` to `.env`.
4. Run the development server:
   ```cmd
   npm run dev
   ```

## API Endpoints
- `GET /api/health` - Health check
- `GET /api/incidents` - List incidents
- `POST /api/incidents` - Create a new incident
- `GET /api/incidents/{incident_id}` - Get incident details
- `POST /api/incidents/{incident_id}/calculate-priority` - Rule-based priority
- `POST /api/incidents/{incident_id}/predict-priority-ml` - ML priority prediction
- `GET /api/incidents/{incident_id}/team-recommendations` - Explainable allocation ranking
- `POST /api/incidents/{incident_id}/allocations` - Approve allocation
- `GET /api/incidents/{incident_id}/allocations` - Allocation history
- `GET /api/teams` - List rescue teams
- `GET /api/teams/{team_id}` - Get rescue team details
- `GET /api/dashboard/summary` - Get summary statistics
- `GET /api/ml/model-info` - ML model metadata
- `GET /api/locations/search?q={query}` - Geocoding location search
- `PATCH /api/incidents/{incident_id}/location` - Update incident location
- `PATCH /api/teams/{team_id}/location` - Update team location
- `GET /api/map/overview` - Map overview for incidents and teams

## Tests
To run backend tests:
```cmd
cd backend
venv\Scripts\activate
pytest
```

## Known Limitations
- Real-time updates via WebSockets are not implemented yet.
- Dynamic en-route reallocation is planned for future phases.
- Rescue team location editing UI in the frontend is not implemented yet.

## Phase 6: Relief-Supply Allocation
Added robust supply-chain logistics to X-DMRA.

- **Relief-Demand Workflow**: Automatically calculates required items (food, water, medical) based on incident metrics. Officers can override these suggestions.
- **Demand Calculation Rules**: E.g., 3 meals per affected person per day.
- **Warehouse Ranking Factors**:
  - Stock Coverage (35%)
  - Item Coverage (15%)
  - Distance (15%)
  - Vehicle Capacity (15%)
  - Route Risk (10%)
  - Warehouse Workload (10%)
- **Single & Split Allocation**: Suggests a single warehouse if fully stocked, or splits the requirement across multiple warehouses.
- **Inventory Reservation Lifecycle**: Available -> Reserved (on dispatch approval) -> Dispatched -> Delivered (final deduction).
- **Officer Approval Requirement**: No dispatch is executed without officer verification.
- **New API Endpoints**: `/api/warehouses`, `/api/inventory`, `/api/delivery-vehicles`, `/api/relief-requests`, etc.
- **Demonstration Data Disclaimer**: The Coimbatore seed data is for demonstration only and does not represent real government stock.
- **Database Recreation Limitation**: The `migrate.py` script destructively drops and recreates SQLite tables, which is intended for development environments only and will cause data loss in production.

See `backend/app/services/RELIEF_ALGORITHM.md` for algorithm details.

## Phase 7: Explainable Shelter Allocation and Overcrowding Prevention
Added comprehensive emergency shelter management and allocation to X-DMRA.

- **Shelter Evaluation Engine**: Dynamically evaluates available shelters based on proximity, specialized facilities (medical, accessibility, women/child safe areas), and capacity.
- **Overcrowding Prevention Rules**: Strict scoring penalties for shelters nearing capacity, with hard limits to prevent critical overcrowding.
- **Single & Split Allocation**: Suggests a single shelter if capable of housing the entire group, or splits the allocation across multiple shelters to balance the load.
- **Capacity Movement Lifecycle**: Tracks detailed capacity changes: Reserved -> Admitted -> Discharged/Cancelled.
- **Officer Approval**: Dispatch officers review clear explanations and metrics (e.g., overcrowding risk level) before approving reservations.
- **New API Endpoints**: `/api/shelters`, `/api/shelter-requests`, `/api/shelter-reservations`, `/api/shelter/dashboard-summary`.

See `SHELTER_ALGORITHM.md` for algorithm details.

## Phase 8: Unified Emergency Command Dashboard

Added a unified command center interface for monitoring and coordinating disaster response operations.

- **Command Center Dashboard**: Single interface displaying active incidents, critical incidents, unassigned incidents, rescue deployments, relief requests, shelter requests, and operational alerts.
- **Priority Incident List**: Displayed with title, location, rule priority, ML priority, current status, rescue/relief/shelter status, active alert count, and waiting duration.
- **Pending Decision Queue**: Unified queue sorted by severity, priority, and waiting duration. Officers review and act on recommendations.
- **Operational Alerts**: Generated from stored conditions only. Categories include: critical_incident, incident_unassigned, rescue_route_blocked, shelter_overcrowding, warehouse_low_stock, relief_shortage, officer_approval_pending.
- **Alert Acknowledgement and Resolution**: Acknowledging an alert indicates officer awareness but does NOT alter the underlying condition. Resolution requires actually fixing the condition.
- **Alert Deduplication**: Duplicate active alerts are prevented - existing alerts are updated rather than creating new ones.
- **Incident Command View**: Provides unified view of incident details, priority analysis, rescue/relief/shelter operations, alerts, and unified timeline.
- **Unified Timeline**: Aggregates events from incident creation, priority calculations, ML predictions, rescue recommendations and allocations, relief dispatches, shelter reservations, route updates, and alert actions.
- **Command Map**: Displays incidents, rescue teams, warehouses, and shelters with blocked/high-risk route indicators.
- **Manual and Auto-Refresh**: Dashboard supports manual refresh and optional 30-60 second auto-refresh (clearly labeled).
- **Officer Approval Requirement**: No automatic allocation approval - all decisions require explicit officer action.

See `backend/app/services/COMMAND_DASHBOARD.md` for detailed documentation.

## Phase 8 Command API Endpoints

- `GET /api/command/dashboard-summary` - Dashboard summary metrics
- `GET /api/command/pending-decisions` - Pending officer decisions (sorted by severity/priority/waiting)
- `GET /api/command/alerts` - List alerts (supports ?severity= and ?status= filters)
- `POST /api/command/alerts/generate` - Manually trigger alert generation
- `PATCH /api/command/alerts/{alert_id}/acknowledge` - Acknowledge alert
- `PATCH /api/command/alerts/{alert_id}/resolve` - Resolve alert
- `GET /api/command/incidents/{incident_id}/operational-summary` - Incident operational summary
- `GET /api/command/incidents/{incident_id}/timeline` - Unified incident timeline
- `GET /api/command/map-overview` - Command center map data

## Phase 9: Research Evaluation and Explainable Baseline Comparison

Added a comprehensive Research Evaluation framework for reproducible X-DMRA versus baseline comparison.

- **Research Evaluation Dashboard**: Frontend tab with module selection, seed/scenario controls, rescue/relief/shelter comparison tables, priority model evaluation with confusion matrix, performance benchmarks, and explainability coverage.
- **Shared Scoring Architecture**: Production services and evaluation adapters use identical shared scoring functions from `backend/app/services/scoring/`. No duplicated formulas. No evaluation-time database mutations.
- **Six Rescue Algorithms**: `random_available`, `first_available`, `nearest_available`, `skill_match_only`, `priority_distance_only`, and `xdmra_explainable`.
- **Five Relief Algorithms**: `first_stocked_warehouse`, `nearest_stocked_warehouse`, `highest_stock_coverage`, `single_warehouse_only`, and `xdmra_relief_allocation`.
- **Five Shelter Algorithms**: `nearest_available_shelter`, `largest_capacity_shelter`, `first_available_shelter`, `capacity_only`, and `xdmra_shelter_allocation`.
- **Deterministic Scenarios**: 25 rescue, 20 relief, 20 shelter scenarios with fixed seed 42 for reproducibility.
- **Priority Model Evaluation**: Accuracy, macro precision/recall/F1, weighted F1, confusion matrix, rule-versus-ML agreement rate, prediction latency, training vs evaluation accuracy comparison.
- **Explainability Coverage**: Structural checks for resource-name, distance, factor, limitation, route-risk, and alternative-comparison coverage.
- **Performance Benchmarking**: Latency benchmarks (mean, median, P95, min, max) for key X-DMRA operations.
- **Experiment Runner**: `python -m evaluation.experiment_runner --module <rescue|relief|shelter|priority|explainability|performance|all> --seed 42`
- **Evaluation API Endpoints**: `/api/evaluation/algorithms`, `/api/evaluation/scenarios`, `/api/evaluation/experiments`, `/api/evaluation/comparisons`, `/api/evaluation/priority-model`, `/api/evaluation/performance`, `/api/evaluation/explainability`
- **Export Formats**: CSV, JSON, Markdown, and LaTeX via `/api/evaluation/export/{experiment_id}?format=csv|json|markdown|lattex`
- **Runtime Outputs Ignored**: Experiment results written to `backend/evaluation_results/`, `backend/ml/evaluation_output/`, and root `evaluation_results/` — all git-ignored.
- **Synthetic-Data Limitation**: All training, scenarios, and evaluations use synthetic/generated data. **Results do not reflect real-world disaster response performance. No statistical significance claim is made.**
- **Distance Limitation**: Straight-line Haversine distance only — not road-network distance.

See `backend/evaluation/README.md` and `backend/evaluation/EVALUATION_METHODOLOGY.md` for detailed documentation.

## Running Tests

To run all backend tests:
```cmd
cd backend
venv\Scripts\activate
pytest
```

Expected: 188 tests collected and passing.

## Current Limitations

- No WebSocket real-time updates (polling-based refresh only)
- Straight-line (Haversine) distances only - not road distances
- No live GPS tracking of vehicles or teams
- No integration with external government systems
- Timeline aggregation limited to database-stored events
