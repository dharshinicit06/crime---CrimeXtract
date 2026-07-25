"""Realistic Karnataka Police sample data for Demo Mode.

All data is hard-coded and never touches the database.
Covers: FIRs, Victims, Accused, Evidence, Financial Transactions,
Crime History, Locations, Hotspots, Network nodes, Predictions.
"""

from datetime import datetime, timedelta
from random import Random

_rng = Random(42)  # Seeded for reproducible demo data


# ── Districts ──────────────────────────────────────────────────
DISTRICTS = [
    "Bengaluru North", "Bengaluru South", "Mysuru",
    "Hubballi-Dharwad", "Mangaluru", "Belagavi",
    "Kalaburagi", "Shivamogga",
]

CITIES = {
    "Bengaluru North": "Bengaluru",
    "Bengaluru South": "Bengaluru",
    "Mysuru": "Mysuru",
    "Hubballi-Dharwad": "Hubballi",
    "Mangaluru": "Mangaluru",
    "Belagavi": "Belagavi",
    "Kalaburagi": "Kalaburagi",
    "Shivamogga": "Shivamogga",
}

CRIME_TYPES = [
    "Theft", "Burglary", "Assault", "Robbery", "Cyber Crime",
    "Fraud", "Kidnapping", "Riot", "Murder", "Hit and Run",
]

FIR_STATUSES = ["Pending", "Under Investigation", "Solved", "Closed"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]

ACCUSED_NAMES = [
    "Arjun Kumar", "Ravi Shastri", "Satish Reddy", "Vinay Patil",
    "Manoj Hegde", "Kiran Shetty", "Prakash Rao", "Suresh Gowda",
]

VICTIM_NAMES = [
    "Priya Sharma", "Anita Desai", "Ramesh Iyer", "Sneha Kapoor",
    "Vikram Joshi", "Lakshmi Narayan", "Deepa Murthy", "Ganesh Pai",
]

BANK_NAMES = [
    "State Bank of India", "Canara Bank", "Karnataka Bank",
    "HDFC Bank", "ICICI Bank", "Axis Bank",
]

EVIDENCE_TYPES = ["Physical", "Digital", "Document", "Forensic", "Weapon"]


# ── FIR Data ────────────────────────────────────────────────────
def generate_firs():
    """Generate 20 realistic Karnataka-style FIRs."""
    firs = []
    for i in range(1, 21):
        district = _rng.choice(DISTRICTS)
        crime_type = _rng.choice(CRIME_TYPES)
        incident_date = datetime.now() - timedelta(days=_rng.randint(1, 365))
        complaint_date = incident_date + timedelta(days=_rng.randint(0, 3))

        firs.append({
            "fir_id": i,
            "fir_number": f"FIR-{incident_date.year}-{i:05d}",
            "title": f"{crime_type} at {CITIES[district]} — Case #{i}",
            "description": (
                f"A case of {crime_type.lower()} was reported at "
                f"{CITIES[district]} on {incident_date.strftime('%d %b %Y')}. "
                f"The incident occurred near {district} and is under investigation."
            ),
            "status": _rng.choice(FIR_STATUSES),
            "priority": _rng.choice(PRIORITIES),
            "incident_date": incident_date.strftime("%Y-%m-%d"),
            "complaint_date": complaint_date.strftime("%Y-%m-%d"),
            "crime_type_id": crime_type,
            "location_id": district,
            "officer_id": _rng.randint(1, 10),
            "created_at": complaint_date.isoformat(),
        })
    return firs


FIR_DATA = generate_firs()


# ── Victim Data ────────────────────────────────────────────────
def generate_victims():
    """Generate 15 victims linked to FIRs."""
    victims = []
    for i in range(1, 16):
        name = _rng.choice(VICTIM_NAMES)
        victims.append({
            "victim_id": i,
            "full_name": name,
            "age": _rng.randint(18, 65),
            "gender": _rng.choice(["Male", "Female"]),
            "phone": f"9{_rng.randint(7000000000, 9999999999)}",
            "email": f"{name.lower().replace(' ', '.')}@email.com",
            "address": f"{_rng.randint(1, 999)}, {_rng.choice(DISTRICTS)}, Karnataka",
            "fir_id": _rng.randint(1, 20),
        })
    return victims


VICTIM_DATA = generate_victims()


# ── Accused Data ───────────────────────────────────────────────
def generate_accused():
    """Generate 12 accused persons with risk scores."""
    accused = []
    for i in range(1, 13):
        name = _rng.choice(ACCUSED_NAMES)
        is_repeat = _rng.random() < 0.3
        accused.append({
            "accused_id": i,
            "full_name": name,
            "age": _rng.randint(18, 60),
            "gender": "Male",
            "phone": f"9{_rng.randint(7000000000, 9999999999)}",
            "email": f"{name.lower().replace(' ', '.')}@email.com",
            "address": f"{_rng.randint(1, 999)}, {_rng.choice(DISTRICTS)}, Karnataka",
            "risk_score": round(_rng.uniform(0, 10), 1),
            "is_repeat_offender": is_repeat,
            "fir_ids": [_rng.randint(1, 20) for _ in range(_rng.randint(1, 3))],
        })
    return accused


ACCUSED_DATA = generate_accused()


# ── Evidence Data ──────────────────────────────────────────────
def generate_evidence():
    """Generate 18 evidence records linked to FIRs."""
    evidence = []
    for i in range(1, 19):
        evidence.append({
            "evidence_id": i,
            "evidence_name": f"{_rng.choice(EVIDENCE_TYPES)} Evidence #{i}",
            "description": f"Collected from crime scene. Refer to FIR for details.",
            "evidence_type": _rng.choice(EVIDENCE_TYPES),
            "collected_date": (datetime.now() - timedelta(days=_rng.randint(1, 180))).strftime("%Y-%m-%d"),
            "fir_id": _rng.randint(1, 20),
        })
    return evidence


EVIDENCE_DATA = generate_evidence()


# ── Financial Transaction Data ─────────────────────────────────
def generate_transactions():
    """Generate 15 financial transactions."""
    txns = []
    for i in range(1, 16):
        txns.append({
            "transaction_id": i,
            "bank_name": _rng.choice(BANK_NAMES),
            "account_number": f"XXXXXX{_rng.randint(1000, 9999)}",
            "transaction_reference": f"TXN{i:08d}",
            "amount": round(_rng.uniform(1000, 2500000), 2),
            "transaction_type": _rng.choice(["NEFT", "RTGS", "IMPS", "UPI", "Cheque"]),
            "transaction_date": (datetime.now() - timedelta(days=_rng.randint(1, 365))).strftime("%Y-%m-%d"),
            "accused_id": _rng.randint(1, 12),
        })
    return txns


TRANSACTION_DATA = generate_transactions()


# ── Crime History Data ─────────────────────────────────────────
def generate_history():
    """Generate 20 criminal history records."""
    history = []
    for i in range(1, 21):
        history.append({
            "history_id": i,
            "accused_id": _rng.randint(1, 12),
            "crime_type": _rng.choice(CRIME_TYPES),
            "arrest_date": (datetime.now() - timedelta(days=_rng.randint(30, 1095))).strftime("%Y-%m-%d"),
            "conviction_status": _rng.choice(["Convicted", "Acquitted", "Pending"]),
        })
    return history


HISTORY_DATA = generate_history()


# ── Hotspot Data ───────────────────────────────────────────────
def generate_hotspots():
    """Generate hotspot data for all districts."""
    hotspots = []
    for i, district in enumerate(DISTRICTS):
        crime_count = _rng.randint(15, 150)
        hotspots.append({
            "district": district,
            "city": CITIES[district],
            "area": f"{district} Area",
            "crime_count": crime_count,
            "risk_score": round(_rng.uniform(10, 95), 1),
            "risk_level": "High" if crime_count > 80 else "Medium" if crime_count > 40 else "Low",
            "priority_count": _rng.randint(1, 20),
            "pending_count": _rng.randint(5, 30),
            "recent_count": _rng.randint(3, 25),
            "last_incident": (datetime.now() - timedelta(days=_rng.randint(1, 14))).strftime("%Y-%m-%d"),
            "latitude": 12.97 + _rng.uniform(-0.5, 0.5),
            "longitude": 77.59 + _rng.uniform(-0.5, 0.5),
        })
    return hotspots


HOTSPOT_DATA = generate_hotspots()


# ── Network Graph Data ─────────────────────────────────────────
def generate_network():
    """Generate a criminal network graph with nodes and edges."""
    nodes = []
    edges = []
    node_id = 0

    # FIR nodes
    for fir in FIR_DATA[:5]:
        node_id += 1
        nodes.append({"id": f"fir:{fir['fir_id']}", "label": fir["fir_number"], "type": "FIR"})

    # Accused nodes
    for a in ACCUSED_DATA[:8]:
        node_id += 1
        nodes.append({"id": f"accused:{a['accused_id']}", "label": a["full_name"], "type": "Accused"})

    # Victim nodes
    for v in VICTIM_DATA[:8]:
        node_id += 1
        nodes.append({"id": f"victim:{v['victim_id']}", "label": v["full_name"], "type": "Victim"})

    # Evidence nodes
    for e in EVIDENCE_DATA[:10]:
        node_id += 1
        nodes.append({"id": f"evidence:{e['evidence_id']}", "label": e["evidence_name"], "type": "Evidence"})

    # Transaction nodes
    for t in TRANSACTION_DATA[:8]:
        node_id += 1
        nodes.append({"id": f"transaction:{t['transaction_id']}", "label": f"₹{t['amount']:,.0f}", "type": "Financial"})

    # Location nodes
    for d in DISTRICTS[:5]:
        node_id += 1
        nodes.append({"id": f"location:{d}", "label": d, "type": "Location"})

    # Edges
    for i in range(1, 6):
        edges.append({"from": f"fir:{i}", "to": f"accused:{_rng.randint(1, min(i, 8))}", "label": "INVOLVED_IN"})
        edges.append({"from": f"victim:{_rng.randint(1, 8)}", "to": f"fir:{i}", "label": "VICTIM_OF"})
        edges.append({"from": f"evidence:{_rng.randint(1, 10)}", "to": f"fir:{i}", "label": "EVIDENCE_FOR"})

    for i in range(1, 9):
        edges.append({"from": f"accused:{i}", "to": f"transaction:{_rng.randint(1, 8)}", "label": "MONEY_TRANSFER"})

    return {"nodes": nodes, "edges": edges, "statistics": {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "node_types": {"FIR": 5, "Accused": 8, "Victim": 8, "Evidence": 10, "Financial": 8, "Location": 5},
    }}


NETWORK_DATA = generate_network()


# ── Dashboard Summary ──────────────────────────────────────────
def generate_dashboard():
    return {
        "summary": {
            "total_firs": len(FIR_DATA),
            "solved_count": sum(1 for f in FIR_DATA if f["status"] in ("Solved", "Closed")),
            "pending_count": sum(1 for f in FIR_DATA if f["status"] == "Pending"),
            "conviction_rate": round(_rng.uniform(60, 85), 1),
            "unique_districts": len(DISTRICTS),
            "time_period": f"Jan 2025 - {datetime.now().strftime('%b %Y')}",
        },
        "crime_by_type": {
            "labels": CRIME_TYPES[:8],
            "datasets": [{"data": [_rng.randint(5, 50) for _ in range(8)]}],
        },
        "crime_by_month": {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][-6:],
            "datasets": [{"data": [_rng.randint(10, 60) for _ in range(6)]}],
        },
        "top_hotspots": {
            "labels": [h["district"] for h in HOTSPOT_DATA[:5]],
            "datasets": [{"data": [h["crime_count"] for h in HOTSPOT_DATA[:5]]}],
        },
        "recent_firs": [
            {
                "fir_id": f["fir_id"],
                "fir_number": f["fir_number"],
                "title": f["title"],
                "investigation_status": f["status"],
                "priority": f["priority"],
                "incident_date": f["incident_date"],
                "created_at": f["created_at"],
            }
            for f in FIR_DATA[:6]
        ],
        "total_users": 24,
    }


DASHBOARD_DATA = generate_dashboard()


# ── Prediction Data ────────────────────────────────────────────
def generate_predictions():
    now = datetime.now()
    predictions = []
    for i in range(1, 7):
        month = now.month + i
        year = now.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        pred = round(_rng.uniform(20, 80), 1)
        predictions.append({
            "month": f"{year:04d}-{month:02d}",
            "predicted_count": pred,
            "lower_bound": round(pred - _rng.uniform(5, 15), 1),
            "upper_bound": round(pred + _rng.uniform(5, 15), 1),
            "historical_count": round(_rng.uniform(15, 70), 1) if i < 4 else None,
        })

    return {
        "predictions": predictions,
        "hotspot_trends": [
            {
                "district": d,
                "current_count": _rng.randint(20, 100),
                "predicted_next_month": round(_rng.uniform(20, 100), 1),
                "trend": _rng.choice(["rising", "stable", "declining"]),
                "risk_score": round(_rng.uniform(10, 95), 1),
            }
            for d in DISTRICTS[:5]
        ],
        "seasonal_patterns": [
            {"season": s, "average_crimes": round(_rng.uniform(80, 200), 1),
             "change_percent": round(_rng.uniform(-15, 25), 1) if s != "Winter" else None}
            for s in ["Winter", "Summer", "Monsoon", "Autumn"]
        ],
        "confidence": round(_rng.uniform(0.75, 0.95), 2),
        "total_predicted": round(_rng.uniform(100, 500), 1),
        "total_historical": _rng.randint(800, 2000),
        "generated_at": datetime.now().isoformat(),
    }


PREDICTION_DATA = generate_predictions()


# ── Hotspot Map Data (GIS) ─────────────────────────────────────
def generate_hotspot_map():
    return [
        {
            "district": h["district"],
            "latitude": h["latitude"],
            "longitude": h["longitude"],
            "crime_count": h["crime_count"],
            "risk_level": h["risk_level"],
        }
        for h in HOTSPOT_DATA
    ]


HOTSPOT_MAP_DATA = generate_hotspot_map()


# ── Users ──────────────────────────────────────────────────────
USERS_DATA = [
    {"id": 1, "full_name": "Inspector Vikram Rathore", "email": "vikram@ksp.gov.in", "role": "Investigator", "is_active": True},
    {"id": 2, "full_name": "ACP Meera Nair", "email": "meera@ksp.gov.in", "role": "Supervisor", "is_active": True},
    {"id": 3, "full_name": "SI Ramesh Gowda", "email": "ramesh@ksp.gov.in", "role": "Investigator", "is_active": True},
    {"id": 4, "full_name": "Analyst Priya Kulkarni", "email": "priya@ksp.gov.in", "role": "Crime Analyst", "is_active": True},
    {"id": 5, "full_name": "Commissioner Sanjay Mirji", "email": "sanjay@ksp.gov.in", "role": "Policymaker", "is_active": True},
]


# ── Audit Logs ────────────────────────────────────────────────
AUDIT_LOGS_DATA = [
    {"id": i, "action": _rng.choice(["FIR_CREATED", "FIR_UPDATED", "USER_LOGIN", "EVIDENCE_ADDED", "REPORT_GENERATED"]),
     "user_name": _rng.choice([u["full_name"] for u in USERS_DATA]),
     "details": f"Action performed on record #{_rng.randint(1, 100)}",
     "timestamp": (datetime.now() - timedelta(hours=_rng.randint(1, 720))).isoformat(),
     "ip_address": f"192.168.{_rng.randint(1, 255)}.{_rng.randint(1, 255)}"}
    for i in range(1, 21)
]


# ── Settings ───────────────────────────────────────────────────
SETTINGS_DATA = {
    "theme": "dark",
    "language": "en",
    "notifications_enabled": True,
    "auto_save": True,
    "page_size": 15,
    "timezone": "Asia/Kolkata",
}


# ── Demo Mode Info ─────────────────────────────────────────────
DEMO_INFO = {
    "demo_mode": True,
    "message": "You are viewing demo data. Toggle Demo Mode off in settings to use production data.",
    "data_counts": {
        "firs": len(FIR_DATA),
        "victims": len(VICTIM_DATA),
        "accused": len(ACCUSED_DATA),
        "evidence": len(EVIDENCE_DATA),
        "transactions": len(TRANSACTION_DATA),
        "history": len(HISTORY_DATA),
        "hotspots": len(HOTSPOT_DATA),
        "users": len(USERS_DATA),
        "audit_logs": len(AUDIT_LOGS_DATA),
    },
}
