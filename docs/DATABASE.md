# Database Schema

## Core Tables
- FIR (fir_id, fir_number, title, status, priority, dates, foreign keys)
- Victim (victim_id, name, contact, fir_id FK)
- Accused (accused_id, name, risk_score, is_repeat_offender)
- FIR-Accused (join table)
- Evidence (evidence_id, type, fir_id FK)
- FinancialTransaction (transaction_id, amount, type, accused_id FK)
- Location (location_id, district, city, lat, lng)
- CrimeType (crime_type_id, crime_name)
- Officer (officer_id, badge_number, designation)
- CrimeHistory (history_id, accused FK, crime_type, conviction)
- User (id, email, password_hash, role)

## Key Relationships
- FIR -> Victim: One-to-Many
- FIR -> Accused: Many-to-Many
- FIR -> Evidence: One-to-Many
- Accused -> Financial: One-to-Many
- Accused -> History: One-to-Many
