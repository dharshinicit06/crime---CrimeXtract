# Project Structure

backend/
  app/
    api/v1/router.py
    chat/ (services, routers, classifiers, translators, etc.)
    fir/, victim/, accused/, evidence/
    financial_transaction/, crime/, crime_analytics/
    crime_history/, crime_prediction/, hotspots/
    network/, network_analysis/, prediction/
    offender_profiling/, ml/, demo/
    auth/, users/, settings/, audit_log/
    location/, core/
  ml/ (training, models)
  alembic/ (migrations)
  tests/

frontend/
  src/
    pages/ (18+ pages)
    components/chat/ (message, input, timeline, recommendations)
    context/ (AuthContext, DemoModeContext)
    services/ (API clients)
    styles/ (theme, shared)
    routes/ (ProtectedRoute)

docs/ (documentation)
Database/ (schema, data)
scripts/ (utilities)
