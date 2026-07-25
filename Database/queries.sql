USE crime_intelligence;

-- =====================================================
-- ALL USERS
-- =====================================================

SELECT * FROM users;

-- =====================================================
-- ALL OFFICERS
-- =====================================================

SELECT * FROM officers;

-- =====================================================
-- ALL FIRS
-- =====================================================

SELECT * FROM firs;

-- =====================================================
-- FIR DETAILS
-- =====================================================

SELECT
f.fir_id,
f.fir_number,
ct.crime_name,
l.city,
l.area,
o.full_name AS investigating_officer,
f.incident_date,
f.investigation_status
FROM firs f
JOIN crime_types ct
ON f.crime_type_id = ct.crime_type_id
JOIN locations l
ON f.location_id = l.location_id
LEFT JOIN officers o
ON f.officer_id = o.officer_id;

-- =====================================================
-- SEARCH FIR BY NUMBER
-- =====================================================

SELECT *
FROM firs
WHERE fir_number = 'FIR2025001';

-- =====================================================
-- SEARCH FIR BY STATUS
-- =====================================================

SELECT *
FROM firs
WHERE investigation_status = 'Open';

-- =====================================================
-- ALL ACCUSED
-- =====================================================

SELECT * FROM accused;

-- =====================================================
-- REPEAT OFFENDERS
-- =====================================================

SELECT *
FROM accused
WHERE is_repeat_offender = TRUE;

-- =====================================================
-- HIGH RISK ACCUSED
-- =====================================================

SELECT *
FROM accused
ORDER BY risk_score DESC;

-- =====================================================
-- ALL VICTIMS
-- =====================================================

SELECT * FROM victims;

-- =====================================================
-- EVIDENCE FOR EACH FIR
-- =====================================================

SELECT
e.evidence_name,
e.evidence_type,
f.fir_number
FROM evidence e
JOIN firs f
ON e.fir_id = f.fir_id;

-- =====================================================
-- ACCUSED LINKED TO FIR
-- =====================================================

SELECT
f.fir_number,
a.full_name
FROM fir_accused fa
JOIN firs f
ON fa.fir_id = f.fir_id
JOIN accused a
ON fa.accused_id = a.accused_id;

-- =====================================================
-- VICTIMS LINKED TO FIR
-- =====================================================

SELECT
f.fir_number,
v.full_name
FROM fir_victims fv
JOIN firs f
ON fv.fir_id = f.fir_id
JOIN victims v
ON fv.victim_id = v.victim_id;

-- =====================================================
-- CRIME COUNT BY CITY
-- =====================================================

SELECT
l.city,
COUNT(*) AS total_cases
FROM firs f
JOIN locations l
ON f.location_id = l.location_id
GROUP BY l.city;

-- =====================================================
-- CRIME COUNT BY TYPE
-- =====================================================

SELECT
ct.crime_name,
COUNT(*) AS total_cases
FROM firs f
JOIN crime_types ct
ON f.crime_type_id = ct.crime_type_id
GROUP BY ct.crime_name;

-- =====================================================
-- CRIME HOTSPOTS
-- =====================================================

SELECT
l.city,
l.area,
COUNT(*) AS total_crimes
FROM firs f
JOIN locations l
ON f.location_id = l.location_id
GROUP BY l.city,l.area
ORDER BY total_crimes DESC;

-- =====================================================
-- MONTHLY CRIME TREND
-- =====================================================

SELECT
MONTH(incident_date) AS month,
COUNT(*) AS total_cases
FROM firs
GROUP BY MONTH(incident_date)
ORDER BY month;

-- =====================================================
-- CRIME HISTORY
-- =====================================================

SELECT
a.full_name,
c.crime_type,
c.conviction_status
FROM crime_history c
JOIN accused a
ON c.accused_id = a.accused_id;

-- =====================================================
-- FINANCIAL TRANSACTIONS
-- =====================================================

SELECT
a.full_name,
t.bank_name,
t.amount,
t.transaction_type
FROM financial_transactions t
JOIN accused a
ON t.accused_id = a.accused_id;

-- =====================================================
-- PREDICTION RESULTS
-- =====================================================

SELECT
l.city,
ct.crime_name,
p.predicted_cases,
p.confidence_score,
p.risk_level
FROM predictions p
JOIN locations l
ON p.location_id = l.location_id
JOIN crime_types ct
ON p.crime_type_id = ct.crime_type_id;

-- =====================================================
-- CONVERSATION HISTORY
-- =====================================================

SELECT
u.full_name,
c.question,
c.ai_response,
c.created_at
FROM conversation_history c
JOIN users u
ON c.user_id = u.user_id;

-- =====================================================
-- AUDIT LOGS
-- =====================================================

SELECT
u.full_name,
a.action,
a.table_name,
a.log_time
FROM audit_logs a
JOIN users u
ON a.user_id = u.user_id;

-- =====================================================
-- DASHBOARD TOTALS
-- =====================================================

SELECT COUNT(*) AS total_firs FROM firs;

SELECT COUNT(*) AS total_accused FROM accused;

SELECT COUNT(*) AS total_victims FROM victims;

SELECT COUNT(*) AS total_officers FROM officers;

SELECT COUNT(*) AS total_predictions FROM predictions;

-- =====================================================
-- OPEN CASES
-- =====================================================

SELECT *
FROM firs
WHERE investigation_status='Open';

-- =====================================================
-- CLOSED CASES
-- =====================================================

SELECT *
FROM firs
WHERE investigation_status='Closed';