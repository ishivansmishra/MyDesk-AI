# MyDesk AI — Documentation

Welcome to the MyDesk AI documentation. This folder contains high-level docs, architecture notes, and contributor guidance.

## Contents

- `architecture.md` — high-level architecture and sequence diagrams
- `developer.md` — developer onboarding and local setup
- `api.md` — backend API reference and examples

### Quickstart

1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --reload
```

2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit the README in the repository root for more information.