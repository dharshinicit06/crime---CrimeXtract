# Deployment

## Docker
- docker-compose up --build
- Backend: port 8000, Frontend: port 5173, MySQL: 3306

## Production
- Backend: gunicorn with uvicorn workers
- Frontend: npm run build, deploy dist/ to static host
- Database: alembic upgrade head
