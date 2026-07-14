# X-DMRA Rescue

An Explainable Dynamic Rescue-Team Allocation System for Disaster Response.

## Overview
This is the foundation phase of the X-DMRA Rescue project. It includes a FastAPI backend and a React/Vite frontend for emergency incident reporting and team monitoring. 

**Note:** Allocation AI, intelligent routing, and map views are planned for later phases and are not included in this foundation release.

## Features Implemented
- RESTful API with FastAPI and SQLite.
- Realistic sample data seeding.
- React-based dashboard for incidents and rescue teams.
- Incident creation form with validation.
- Responsive, clean interface.

## Tech Stack
- **Frontend**: React, Vite, TypeScript, Tailwind CSS
- **Backend**: Python 3, FastAPI, SQLAlchemy, SQLite (PostgreSQL compatible schema), Pytest

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
- `GET /api/teams` - List rescue teams
- `GET /api/teams/{team_id}` - Get rescue team details
- `GET /api/dashboard/summary` - Get summary statistics

## Tests
To run backend tests:
```cmd
cd backend
venv\Scripts\activate
pytest
```

## Known Limitations
- Real-time updates via WebSockets are not implemented yet.
- Map view is absent.
- Advanced AI allocation is not part of this release.
