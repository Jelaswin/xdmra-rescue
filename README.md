# X-DMRA Rescue

An Explainable Dynamic Rescue-Team Allocation System for Disaster Response.

## Overview
This is the X-DMRA Rescue project up to **Phase 4**. It includes a FastAPI backend and a React/Vite frontend for emergency incident reporting, rule-based priority engine, explainable rescue team allocation, custom Machine Learning incident priority predictor, and Map/Location Management.

**Note:** Relief-supply allocation, shelter allocation, maps, and real-time external APIs are not yet implemented.

## Features Implemented
- RESTful API with FastAPI and SQLite.
- Incident creation and severity scaling.
- Rule-based Incident Priority Engine.
- Explainable Rescue Team Allocation Engine (Skill matching, capacity, workload, distance).
- Custom Machine Learning Priority Predictor (Random Forest Classifier) using synthetic dataset.
- Map and Location Management via OpenStreetMap Nominatim Geocoding.
- Operations Dashboard Map with active incidents and rescue teams.
- Interactive Side-by-side Decision Support Panel for Dispatch Officers.
- 62 passing end-to-end backend tests.

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

See `backend/app/services/RELIEF_ALGORITHM.md` for algorithm details.
