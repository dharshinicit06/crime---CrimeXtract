# Crime Intelligence Platform

A production-ready police intelligence system that combines structured crime data with AI-powered analysis. Built for Karnataka Police to modernize crime investigation, analysis, and reporting.

## Key Features

- **AI Chat (CrimeAI)** — Natural language queries powered by Hybrid SQL + LLM architecture
- **FIR Management** — End-to-end case management with status tracking
- **Crime Hotspots** — Geographic crime clustering with risk analysis
- **Criminal Network Visualization** — Interactive relationship graphs
- **Crime Prediction** — ML-based forecasting with confidence intervals
- **Kannada Language Support** — Full bilingual capability via AI translation
- **Explainable AI** — Every answer includes "Why?" with evidence
- **Demo Mode** — Explore with realistic Karnataka Police sample data
- **Voice Support** — Speech-to-text and text-to-speech in English & Kannada

## Tech Stack

**Backend:** FastAPI, SQLAlchemy, MySQL, Gemini AI, ReportLab, gTTS
**Frontend:** React 18, Vite, Recharts, React Flow, Leaflet
**ML:** Scikit-learn (Linear Regression), NumPy

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure DATABASE_URL, GEMINI_API_KEY
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Demo Mode

Toggle Demo Mode in the top bar to explore the platform with 20+ realistic Karnataka Police sample records across all modules — no database setup needed.

## Documentation

See the `docs/` directory for:
- `ARCHITECTURE.md` — System architecture
- `API_REFERENCE.md` — Complete API documentation
- `DATABASE.md` — Schema and relationships
- `FEATURES.md` — All feature details
- `USER_GUIDE.md` — How to use the platform
- `HACKATHON_DEMO.md` — 5-minute demo guide

## License

Internal use — Karnataka Police Department
