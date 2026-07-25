USE crime_intelligence;

-- ===========================
-- ROLES
-- ===========================

INSERT INTO roles (role_name)
VALUES
('Admin'),
('Investigator'),
('Analyst');

-- ===========================
-- USERS
-- ===========================

INSERT INTO users
(full_name,email,password_hash,phone,role_id)
VALUES
('Admin User','admin@crime.com','$2b$12$zAbWcyKPqboQVkVmZSt0c.iEg.38/49eePNibBxPtgS.rr5glFTUW','9876543210',1),
('Inspector Ravi','ravi@crime.com','$2b$12$8jBW5.eneVhM/5/6UILSMOzokhZGo2RD3zyHnGH3AEUArrxJNXofC','9876543211',2),
('Analyst Priya','priya@crime.com','$2b$12$g9bEjNwfk9.t6QwSc/DIFufSkbZty2UjyF4Xh.b/3fgpRiQT/yyRC','9876543212',3);

-- ===========================
-- OFFICERS
-- ===========================

INSERT INTO officers
(full_name,designation,station_name,phone,email)
VALUES
('Ravi Kumar','Inspector','Central Police Station','9876543211','ravi@police.com'),
('Suresh Babu','Sub Inspector','North Police Station','9876543213','suresh@police.com');

-- ===========================
-- LOCATIONS
-- ===========================

INSERT INTO locations
(city,district,state,pincode,area)
VALUES
('Chennai','Chennai','Tamil Nadu','600001','T Nagar'),
('Coimbatore','Coimbatore','Tamil Nadu','641001','Gandhipuram'),
('Madurai','Madurai','Tamil Nadu','625001','Anna Nagar');

-- ===========================
-- CRIME TYPES
-- ===========================

INSERT INTO crime_types
(crime_name,category,severity)
VALUES
('Theft','Property Crime','Medium'),
('Murder','Violent Crime','High'),
('Cyber Fraud','Cyber Crime','High'),
('Drug Trafficking','Narcotics','Critical');

-- ===========================
-- FIRS
-- ===========================

INSERT INTO firs
(
fir_number,
crime_type_id,
location_id,
officer_id,
incident_date,
incident_time,
description,
investigation_status
)
VALUES
(
'FIR2025001',
1,
1,
1,
'2025-01-10',
'10:30:00',
'Mobile phone theft',
'Open'
),
(
'FIR2025002',
2,
2,
2,
'2025-02-15',
'18:15:00',
'Murder investigation',
'In Progress'
);

-- ===========================
-- ACCUSED
-- ===========================

INSERT INTO accused
(
full_name,
age,
gender,
phone,
occupation,
risk_score,
is_repeat_offender
)
VALUES
(
'Arun Kumar',
30,
'Male',
'9000000001',
'Driver',
82.50,
TRUE
),
(
'Rahul',
27,
'Male',
'9000000002',
'Business',
45.00,
FALSE
);

-- ===========================
-- VICTIMS
-- ===========================

INSERT INTO victims
(
full_name,
age,
gender,
phone,
occupation
)
VALUES
(
'Karthik',
26,
'Male',
'9111111111',
'Engineer'
),
(
'Sneha',
24,
'Female',
'9222222222',
'Student'
);

-- ===========================
-- FIR ACCUSED
-- ===========================

INSERT INTO fir_accused
(fir_id,accused_id)
VALUES
(1,1),
(2,2);

-- ===========================
-- FIR VICTIMS
-- ===========================

INSERT INTO fir_victims
(fir_id,victim_id)
VALUES
(1,1),
(2,2);

-- ===========================
-- EVIDENCE
-- ===========================

INSERT INTO evidence
(
fir_id,
evidence_type,
evidence_name,
description,
file_path,
collected_by,
collected_date
)
VALUES
(
1,
'Photo',
'CCTV Image',
'CCTV image near crime scene',
'/uploads/cctv1.jpg',
1,
NOW()
),
(
2,
'Weapon',
'Knife',
'Recovered knife',
'/uploads/knife.jpg',
2,
NOW()
);

-- ===========================
-- CRIME HISTORY
-- ===========================

INSERT INTO crime_history
(
accused_id,
fir_id,
crime_type,
arrest_date,
conviction_status,
sentence,
remarks
)
VALUES
(
1,
1,
'Theft',
'2025-01-12',
'Pending',
NULL,
'Under Investigation'
);

-- ===========================
-- FINANCIAL TRANSACTIONS
-- ===========================

INSERT INTO financial_transactions
(
accused_id,
fir_id,
bank_name,
account_number,
transaction_reference,
amount,
transaction_type,
transaction_date,
remarks
)
VALUES
(
1,
1,
'SBI',
'1234567890',
'TXN10001',
50000.00,
'Credit',
NOW(),
'Suspicious transaction'
);

-- ===========================
-- CONVERSATION HISTORY
-- ===========================

INSERT INTO conversation_history
(
user_id,
question,
ai_response,
language
)
VALUES
(
1,
'Show all theft cases',
'Found 1 theft case.',
'English'
);

-- ===========================
-- AUDIT LOGS
-- ===========================

INSERT INTO audit_logs
(
user_id,
action,
table_name,
record_id,
ip_address
)
VALUES
(
1,
'INSERT',
'firs',
1,
'127.0.0.1'
);

-- ===========================
-- PREDICTIONS
-- ===========================

INSERT INTO predictions
(
location_id,
crime_type_id,
prediction_date,
predicted_cases,
confidence_score,
risk_level,
generated_by
)
VALUES
(
1,
1,
'2025-12-01',
15,
91.25,
'High',
'AI Model v1'
),
(
2,
2,
'2025-12-01',
6,
84.50,
'Medium',
'AI Model v1'
);