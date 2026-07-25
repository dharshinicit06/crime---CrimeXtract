# API Reference

## Auth
- POST /auth/register, /auth/login, /auth/refresh
- GET /auth/me

## FIR
- GET/POST /fir, GET/PUT/DELETE /fir/{id}
- GET /fir/statistics, /fir/{id}/summary, /fir/{id}/timeline

## Victims
- GET/POST /victims, GET/PUT/DELETE /victims/{id}

## Accused
- GET/POST /accused, GET/PUT/DELETE /accused/{id}

## Evidence
- GET/POST /evidence, GET/PUT/DELETE /evidence/{id}

## Hotspots
- GET /hotspots, /hotspots/map, /hotspots/{district}

## Network
- GET /network, /network/{fir_number}

## Prediction
- GET /prediction/forecast?months_ahead=N&district=X

## Chat
- POST /chat/message {message, conversation_id, language, demo_mode}
- GET /chat/conversations
- POST /chat/upload, /chat/feedback
- POST /chat/speech-to-text, /chat/text-to-speech
- GET /chat/{id}/export-pdf

## Demo (all mirror production)
- GET /demo/firs, /demo/victims, /demo/hotspots, etc.

## Health
- GET /health, /version
