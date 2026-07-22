# MyDesk AI Backend

## Overview

This backend provides the API foundation for a production-ready AI personal assistant with Google Workspace integration.

## Development

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Testing

```bash
pytest -q
```
