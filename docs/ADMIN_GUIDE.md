# Admin Guide

## User Management

### Roles
- **Investigator** -- Standard officer role. Can create and manage FIRs, victims, accused, evidence.
- **Supervisor** -- Can oversee cases, assign officers, view all records.
- **Crime Analyst** -- Access to analytics, predictions, hotspots, network analysis. Read-only on case data.
- **Policymaker** -- Aggregate data access for strategic decisions. Cannot modify individual cases.

### Creating Users
Admin users can create new accounts via the Users page. New users receive email verification.

## System Configuration

### Environment Variables (backend/.env)
| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | MySQL connection string | mysql://root:pass@localhost/crimeai |
| SECRET_KEY | JWT signing key | (required) |
| GEMINI_API_KEY | Google Gemini API key | (required for AI features) |
| ACCESS_TOKEN_EXPIRE_MINUTES | JWT token lifetime | 30 |
| CORS_ORIGINS | Allowed frontend origins | http://localhost:5173 |

### Frontend Configuration (frontend/.env)
| Variable | Description | Default |
|----------|-------------|---------|
| VITE_API_URL | Backend API URL | http://localhost:8000/api/v1 |

## Database Maintenance

### Backups
Schedule regular MySQL dumps:
mysqldump -u root crimeai > backup_$(date +%Y%m%d).sql

### Migrations
cd backend
alembic upgrade head    # Apply pending migrations
alembic downgrade -1   # Rollback one migration
alembic history        # View migration history

## Monitoring
Health check: GET /api/v1/health
Logs: Application logs are written to stdout.

## Troubleshooting

### Database connection failed
- Verify MySQL is running
- Check DATABASE_URL in .env
- Ensure host is accessible

### Gemini API error
- Verify GEMINI_API_KEY is set and valid
- Check API quota limits
- Chat falls back gracefully without AI summaries

### Frontend shows blank page
- Check browser console for errors
- Verify VITE_API_URL matches backend
- Run npm run build

## Security
- All demo endpoints require JWT authentication
- Passwords hashed with bcrypt
- File uploads validated by type and size
- CORS restricted to configured origins
- Rate limiting on auth and upload endpoints
