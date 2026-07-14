# Implementation Plan: X-DMRA Rescue Foundation

## Phase 1: Environment Setup & Project Structure
- Initialize Git repository.
- Create `backend/` and `frontend/` folders in the root.
- Create `.gitignore` to exclude node_modules, Python cache, SQLite db, .env files, etc.
- Write `README.md` with project details and setup instructions.

## Phase 2: Backend Development (FastAPI)
- Set up a Python virtual environment and `requirements.txt`.
- Create SQLAlchemy models for `Incident`, `RescueTeam`, `Allocation`, and `RouteCondition`.
- Implement API endpoints:
  - `GET /api/health`
  - `GET /api/incidents`
  - `POST /api/incidents`
  - `GET /api/incidents/{incident_id}`
  - `GET /api/teams`
  - `GET /api/teams/{team_id}`
  - `GET /api/dashboard/summary`
- Add idempotent seed script `seed.py` for realistic sample data.
- Configure CORS.
- Write backend tests with Pytest.

## Phase 3: Frontend Development (React + Vite + TypeScript)
- Initialize React app using Vite (`npm create vite@latest frontend -- --template react-ts`).
- Setup Tailwind CSS.
- Create API service layer to interface with the FastAPI backend.
- Build components:
  - Header with connection status.
  - Dashboard Summary Cards.
  - Responsive Incident Table/Cards.
  - Rescue Team Cards.
  - Incident Creation Form with validation.
- Implement responsive layout.
- Configure `.env.example` and load `VITE_API_BASE_URL`.

## Phase 4: Integration & Verification
- Run backend tests and verify health.
- Build frontend (`npm run build`) and check for TypeScript errors.
- Start both services and verify the end-to-end flow manually (dashboard data, form submission).

## Intended Folder Structure
```
c:/KRATOS/Git Project/Nxtwve_hackathon/
  frontend/
    src/
      components/
      pages/
      services/
      types/
      utils/
    .env.example
    package.json
  backend/
    app/
      __init__.py
      main.py
      database.py
      models.py
      schemas.py
      api/
      services.py
      seed.py
    tests/
    requirements.txt
    .env.example
  README.md
  PLAN.md
  .gitignore
```
