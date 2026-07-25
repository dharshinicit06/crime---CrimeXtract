# Installation

## Prerequisites
- Python 3.10+, Node 18+, MySQL 8.0+, Gemini API key

## Backend
1. python -m venv venv
2. pip install -r requirements.txt
3. Configure .env (DATABASE_URL, SECRET_KEY, GEMINI_API_KEY)
4. alembic upgrade head
5. uvicorn app.main:app --reload --port 8000

## Frontend
1. cd frontend && npm install
2. Configure .env (VITE_API_URL)
3. npm run dev
