"""
Seed Test Data — Populates the Crime Intelligence Platform with realistic test data.

Usage:
    cd backend && python ../scripts/seed_test_data.py

This script uses the ORM models directly so it works with both MySQL and PostgreSQL.
All records are linked through FIR FIR2026001 for end-to-end testing.
"""

import asyncio
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

# Ensure backend is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory, initialize_database
from app.core.security import hash_password

from app.auth.models import User
from app.auth.role_models import Role
from app.officer.models import Officer
from app.location.models import Location
from app.crime.models import CrimeType, CrimeSeverity
from app.fir.models import FIR, InvestigationStatus, Priority
from app.victim.models import Victim, Gender as VGender, FIRVictimLink
from app.accused.models import Accused, Gender as AGender, FIRAccusedLink, Accused as _A
from app.evidence.models import Evidence, EvidenceType
from app.financial_transaction.models import FinancialTransaction, TransactionType
from app.crime_history.models import CrimeHistory, ConvictionStatus
from app.audit_log.models import AuditLog, AuditAction




async def seed_database():
    """Seed the database with realistic test data."""
    async with async_session_factory() as session:
        # ── Check if data already exists ────────────────────────
        result = await session.execute(select(func.count(Role.role_id)))
        if result.scalar_one() > 0:
            print("⚠️  Database already contains data. Skipping seed.")
            print("   To re-seed, truncate all tables and re-run.")
            return

        print("=" * 60)
        print("🌱 Seeding Crime Intelligence Database...")
        print("=" * 60)

        # ── 1. ROLES ────────────────────────────────────────────
        roles_data = [
            {"role_name": "Admin", "description": "System administrator"},
            {"role_name": "Investigator", "description": "Crime investigator"},
            {"role_name": "Analyst", "description": "Data analyst"},
        ]
        roles = []
        for r in roles_data:
            role = Role(**r)
            session.add(role)
            roles.append(role)
        await session.flush()
        print(f"✅ Created {len(roles)} roles")

        # ── 2. USERS ────────────────────────────────────────────
        users_data = [
            {
                "full_name": "Arjun Kumar",
                "email": "arjun.kumar@ksp.gov.in",
                "password": "Police@123",
                "phone": "9876543210",
                "role_id": roles[1].role_id,  # Investigator
            },
            {
                "full_name": "Admin User",
                "email": "admin@crime.com",
                "password": "Admin@123",
                "phone": "9876543211",
                "role_id": roles[0].role_id,  # Admin
            },
            {
                "full_name": "Analyst Priya",
                "email": "priya@crime.com",
                "password": "Analyst@123",
                "phone": "9876543212",
                "role_id": roles[2].role_id,  # Analyst
            },
        ]
        users = []
        for u in users_data:
            user = User(
                full_name=u["full_name"],
                email=u["email"],
                password_hash=hash_password(u["password"]),
                phone=u["phone"],
                role_id=u["role_id"],
            )
            session.add(user)
            users.append(user)
        await session.flush()
        print(f"✅ Created {len(users)} users")
        print(f"   Login: arjun.kumar@ksp.gov.in / Police@123")

        # ── 3. OFFICERS ─────────────────────────────────────────
        officers_data = [
            {
                "badge_number": "INSP001",
                "designation": "Inspector",
                "department": "Criminal Investigation",
                "police_station": "Central Police Station, Bengaluru",
            },
            {
                "badge_number": "SI001",
                "designation": "Sub Inspector",
                "department": "Law and Order",
                "police_station": "Central Police Station, Bengaluru",
            },
        ]
        officers = []
        for o in officers_data:
            officer = Officer(**o)
            session.add(officer)
            officers.append(officer)
        await session.flush()
        print(f"✅ Created {len(officers)} officers")

        # ── 4. LOCATIONS ────────────────────────────────────────
        locations_data = [
            {
                "district": "Bengaluru Urban",
                "city": "Bengaluru",
                "area": "MG Road",
                "pincode": "560001",
                "latitude": Decimal("12.97560000"),
                "longitude": Decimal("77.60500000"),
            },
            {
                "district": "Bengaluru Urban",
                "city": "Bengaluru",
                "area": "Shivajinagar",
                "pincode": "560001",
                "latitude": Decimal("12.98560000"),
                "longitude": Decimal("77.59000000"),
            },
            {
                "district": "Bengaluru Urban",
                "city": "Bengaluru",
                "area": "Indiranagar",
                "pincode": "560038",
                "latitude": Decimal("12.97800000"),
                "longitude": Decimal("77.64000000"),
            },
            {
                "district": "Bengaluru Urban",
                "city": "Bengaluru",
                "area": "Majestic",
                "pincode": "560002",
                "latitude": Decimal("12.97700000"),
                "longitude": Decimal("77.57100000"),
            },
        ]
        locations = []
        for loc in locations_data:
            location = Location(**loc)
            session.add(location)
            locations.append(location)
        await session.flush()
        print(f"✅ Created {len(locations)} locations")

        # ── 5. CRIME TYPES ──────────────────────────────────────
        crime_types_data = [
            {"crime_name": "Robbery", "category": "Property Crime", "severity": CrimeSeverity.HIGH},
            {"crime_name": "Theft", "category": "Property Crime", "severity": CrimeSeverity.MEDIUM},
            {"crime_name": "Chain Snatching", "category": "Property Crime", "severity": CrimeSeverity.MEDIUM},
            {"crime_name": "Pickpocket", "category": "Property Crime", "severity": CrimeSeverity.LOW},
            {"crime_name": "Cyber Fraud", "category": "Cyber Crime", "severity": CrimeSeverity.HIGH},
            {"crime_name": "Drug Trafficking", "category": "Narcotics", "severity": CrimeSeverity.CRITICAL},
        ]
        crime_types = []
        for ct in crime_types_data:
            crime_type = CrimeType(**ct)
            session.add(crime_type)
            crime_types.append(crime_type)
        await session.flush()
        print(f"✅ Created {len(crime_types)} crime types")

        # ── 6. FIR ──────────────────────────────────────────────
        now = datetime(2026, 7, 20, 21, 30)
        firs_data = [
            {
                "fir_number": "FIR2026001",
                "crime_type_id": crime_types[0].crime_type_id,  # Robbery
                "location_id": locations[0].location_id,  # MG Road
                "officer_id": officers[0].officer_id,  # Inspector
                "title": "Jewellery Store Robbery on MG Road",
                "description": "Two unidentified suspects robbed a jewellery store and fled on a motorcycle. "
                               "The suspects were armed and threatened the store staff before escaping with "
                               "valuable jewellery worth approximately ₹8,50,000.",
                "incident_date": datetime(2026, 7, 20, 21, 30),
                "complaint_date": datetime(2026, 7, 20, 22, 15),
                "investigation_status": InvestigationStatus.UNDER_INVESTIGATION,
                "priority": Priority.HIGH,
            },
            {
                "fir_number": "FIR2026002",
                "crime_type_id": crime_types[1].crime_type_id,  # Theft
                "location_id": locations[1].location_id,  # Shivajinagar
                "officer_id": officers[1].officer_id,  # Sub Inspector
                "title": "Vehicle Theft in Shivajinagar",
                "description": "A two-wheeler was stolen from a parking area. CCTV footage shows an unknown "
                               "individual breaking the lock and riding away.",
                "incident_date": datetime(2026, 7, 18, 14, 00),
                "complaint_date": datetime(2026, 7, 18, 16, 30),
                "investigation_status": InvestigationStatus.PENDING,
                "priority": Priority.MEDIUM,
            },
        ]
        created_firs = []
        for f in firs_data:
            fir = FIR(**f)
            session.add(fir)
            created_firs.append(fir)
        await session.flush()
        for f in created_firs:
            await session.refresh(f)
        print(f"✅ Created {len(created_firs)} FIRs")
        print(f"   Primary FIR: FIR2026001 (fir_id={created_firs[0].fir_id})")

        # ── 7. VICTIMS ──────────────────────────────────────────
        victims_data = [
            {
                "full_name": "Ramesh Gowda",
                "age": 45,
                "gender": VGender.MALE,
                "phone": "9123456789",
                "email": "ramesh.gowda@gmail.com",
                "address": "24 Brigade Road, Bengaluru",
                "occupation": "Business Owner",
            },
            {
                "full_name": "Sneha Patel",
                "age": 29,
                "gender": VGender.FEMALE,
                "phone": "9234567890",
                "email": "sneha.patel@gmail.com",
                "address": "56 Koramangala, Bengaluru",
                "occupation": "Software Engineer",
            },
        ]
        created_victims = []
        for v in victims_data:
            victim = Victim(**v)
            session.add(victim)
            created_victims.append(victim)
        await session.flush()
        print(f"✅ Created {len(created_victims)} victims")

        # ── 8. FIR-VICTIM LINKS ─────────────────────────────────
        fir_victim_links_data = [
            {"fir_id": created_firs[0].fir_id, "victim_id": created_victims[0].victim_id},
            {"fir_id": created_firs[1].fir_id, "victim_id": created_victims[1].victim_id},
        ]
        for link in fir_victim_links_data:
            fvl = FIRVictimLink(**link)
            session.add(fvl)
        await session.flush()

        # ── 9. ACCUSED ──────────────────────────────────────────
        accused_data = [
            {
                "full_name": "Suresh Kumar",
                "age": 32,
                "gender": AGender.MALE,
                "phone": "9988776655",
                "email": "suresh.kumar@gmail.com",
                "address": "18 Shivajinagar, Bengaluru",
                "occupation": "Driver",
                "aadhaar_number": "567812349876",
                "risk_score": Decimal("82.50"),
                "is_repeat_offender": True,
            },
            {
                "full_name": "Ravi Shetty",
                "age": 28,
                "gender": AGender.MALE,
                "phone": "8877665544",
                "email": "ravi.shetty@gmail.com",
                "address": "45 Jayanagar, Bengaluru",
                "occupation": "Auto Driver",
                "aadhaar_number": "432198765432",
                "risk_score": Decimal("45.00"),
                "is_repeat_offender": False,
            },
            {
                "full_name": "Manoj Das",
                "age": 35,
                "gender": AGender.MALE,
                "phone": "7766554433",
                "email": "manoj.das@gmail.com",
                "address": "12 Whitefield, Bengaluru",
                "occupation": "Contractor",
                "risk_score": Decimal("30.00"),
                "is_repeat_offender": False,
            },
        ]
        created_accused = []
        for a in accused_data:
            accused = Accused(**a)
            session.add(accused)
            created_accused.append(accused)
        await session.flush()
        print(f"✅ Created {len(created_accused)} accused persons")

        # ── 10. FIR-ACCUSED LINKS ───────────────────────────────
        fir_accused_links_data = [
            {"fir_id": created_firs[0].fir_id, "accused_id": created_accused[0].accused_id},
            {"fir_id": created_firs[0].fir_id, "accused_id": created_accused[1].accused_id},
            {"fir_id": created_firs[1].fir_id, "accused_id": created_accused[2].accused_id},
        ]
        for link in fir_accused_links_data:
            fal = FIRAccusedLink(**link)
            session.add(fal)
        await session.flush()

        # ── 11. EVIDENCE ────────────────────────────────────────
        evidence_data = [
            {
                "fir_id": created_firs[0].fir_id,
                "evidence_type": EvidenceType.VIDEO,
                "evidence_name": "CCTV Footage",
                "description": "CCTV footage from jewellery shop entrance showing the robbery in progress. "
                               "Two suspects wearing helmets can be seen entering and fleeing.",
                "file_path": "/uploads/cctv_footage_20260720.mp4",
                "collected_by": officers[0].officer_id,
                "collected_date": datetime(2026, 7, 20, 22, 15),
            },
            {
                "fir_id": created_firs[0].fir_id,
                "evidence_type": EvidenceType.FINGERPRINT,
                "evidence_name": "Fingerprint Sample",
                "description": "Fingerprint samples collected from the broken jewellery display counter.",
                "file_path": "/uploads/fingerprint_001.jpg",
                "collected_by": officers[0].officer_id,
                "collected_date": datetime(2026, 7, 20, 23, 00),
            },
            {
                "fir_id": created_firs[1].fir_id,
                "evidence_type": EvidenceType.PHOTO,
                "evidence_name": "Crime Scene Photos",
                "description": "Photographs of the vehicle theft crime scene including broken lock.",
                "file_path": "/uploads/theft_scene_001.jpg",
                "collected_by": officers[1].officer_id,
                "collected_date": datetime(2026, 7, 18, 17, 00),
            },
        ]
        for e in evidence_data:
            evidence = Evidence(**e)
            session.add(evidence)
        await session.flush()
        print(f"✅ Created {len(evidence_data)} evidence records")

        # ── 12. FINANCIAL TRANSACTIONS ──────────────────────────
        transactions_data = [
            {
                "fir_id": created_firs[0].fir_id,
                "accused_id": created_accused[0].accused_id,
                "bank_name": "State Bank of India",
                "account_number": "123456789012",
                "transaction_reference": "UPI202607200001",
                "amount": Decimal("85000.00"),
                "transaction_type": TransactionType.DEBIT,
                "transaction_date": datetime(2026, 7, 20, 20, 45),
                "remarks": "Large cash withdrawal one hour before the robbery",
            },
            {
                "fir_id": created_firs[0].fir_id,
                "accused_id": created_accused[1].accused_id,
                "bank_name": "HDFC Bank",
                "account_number": "987654321098",
                "transaction_reference": "NEFT202607210001",
                "amount": Decimal("50000.00"),
                "transaction_type": TransactionType.CREDIT,
                "transaction_date": datetime(2026, 7, 21, 10, 30),
                "remarks": "Suspicious deposit after robbery",
            },
        ]
        for t in transactions_data:
            tx = FinancialTransaction(**t)
            session.add(tx)
        await session.flush()
        print(f"✅ Created {len(transactions_data)} financial transactions")

        # ── 13. CRIME HISTORY ───────────────────────────────────
        crime_history_data = [
            {
                "accused_id": created_accused[0].accused_id,
                "fir_id": created_firs[0].fir_id,
                "crime_type": "Chain Snatching",
                "arrest_date": date(2025, 6, 15),
                "conviction_status": ConvictionStatus.CONVICTED,
                "sentence": "2 years imprisonment",
                "remarks": "Previous conviction for chain snatching in 2025",
            },
            {
                "accused_id": created_accused[0].accused_id,
                "fir_id": None,
                "crime_type": "Theft",
                "arrest_date": date(2024, 3, 10),
                "conviction_status": ConvictionStatus.CONVICTED,
                "sentence": "1 year probation",
                "remarks": "Petty theft case",
            },
            {
                "accused_id": created_accused[2].accused_id,
                "fir_id": created_firs[1].fir_id,
                "crime_type": "Receiving Stolen Property",
                "arrest_date": date(2025, 11, 20),
                "conviction_status": ConvictionStatus.PENDING,
                "sentence": None,
                "remarks": "Under investigation for receiving stolen vehicles",
            },
        ]
        for ch in crime_history_data:
            history = CrimeHistory(**ch)
            session.add(history)
        await session.flush()
        print(f"✅ Created {len(crime_history_data)} crime history records")

        # ── 14. AUDIT LOGS ──────────────────────────────────────
        audit_logs_data = [
            {
                "user_id": users[0].id,
                "action": AuditAction.CREATE.value,
                "table_name": "firs",
                "record_id": created_firs[0].fir_id,
                "ip_address": "192.168.1.10",
            },
            {
                "user_id": users[0].id,
                "action": AuditAction.CREATE.value,
                "table_name": "victims",
                "record_id": created_victims[0].victim_id,
                "ip_address": "192.168.1.10",
            },
            {
                "user_id": users[0].id,
                "action": AuditAction.CREATE.value,
                "table_name": "evidence",
                "record_id": 1,
                "ip_address": "192.168.1.10",
            },
            {
                "user_id": users[0].id,
                "action": "LOGIN",
                "table_name": "users",
                "record_id": users[0].id,
                "ip_address": "192.168.1.10",
            },
        ]
        for al in audit_logs_data:
            log = AuditLog(**al)
            session.add(log)
        await session.flush()
        print(f"✅ Created {len(audit_logs_data)} audit logs")

        # ── 15. HOTSPOT DATA (existing locations have FIRs) ─────
        # Hotspots are computed dynamically from FIR + Location tables
        # Adding a third FIR at Majestic for hotspot variety
        majestic_fir = FIR(
            fir_number="FIR2026003",
            crime_type_id=crime_types[3].crime_type_id,  # Pickpocket
            location_id=locations[3].location_id,  # Majestic
            officer_id=officers[1].officer_id,
            title="Pickpocket Incidents at Majestic Bus Stand",
            description="Multiple pickpocket incidents reported at the Majestic bus stand. "
                       "Victims reported losing wallets and phones in crowded buses.",
            incident_date=datetime(2026, 7, 15, 18, 00),
            complaint_date=datetime(2026, 7, 15, 18, 30),
            investigation_status=InvestigationStatus.PENDING,
            priority=Priority.MEDIUM,
        )
        session.add(majestic_fir)
        await session.flush()
        print(f"✅ Created additional FIR for hotspot data")

        # ── 16. CRIMINAL NETWORK DATA (additional connections) ──
        # Network is computed dynamically by the NetworkAnalysisService
        # Adding an FIR at Indiranagar for more network variety
        indiranagar_fir = FIR(
            fir_number="FIR2026004",
            crime_type_id=crime_types[4].crime_type_id,  # Cyber Fraud
            location_id=locations[2].location_id,  # Indiranagar
            officer_id=officers[0].officer_id,
            title="Cyber Fraud Complaint",
            description="Online banking fraud where victim lost ₹2,50,000 to phishing attack.",
            incident_date=datetime(2026, 7, 10, 11, 00),
            complaint_date=datetime(2026, 7, 10, 14, 00),
            investigation_status=InvestigationStatus.UNDER_INVESTIGATION,
            priority=Priority.HIGH,
        )
        session.add(indiranagar_fir)
        await session.flush()

        # Additional criminal network links
        # Imran Khan — associated with Suresh Kumar (accused 1) via new FIR
        imran = Accused(
            full_name="Imran Khan",
            age=30,
            gender=AGender.MALE,
            phone="6655443322",
            email="imran.khan@gmail.com",
            address="78 Banashankari, Bengaluru",
            occupation="Electronics Repair",
            risk_score=Decimal("65.00"),
            is_repeat_offender=False,
        )
        session.add(imran)
        await session.flush()

        # Link Imran to cyber fraud FIR
        fal = FIRAccusedLink(fir_id=indiranagar_fir.fir_id, accused_id=imran.accused_id)
        session.add(fal)
        await session.flush()

        # Link Suresh Kumar to cyber fraud FIR (network connection)
        fal2 = FIRAccusedLink(fir_id=indiranagar_fir.fir_id, accused_id=created_accused[0].accused_id)
        session.add(fal2)
        await session.flush()

        print(f"✅ Created criminal network data (4 persons linked across FIRs)")
        print(f"   Suresh Kumar ↔ Ravi Shetty (robbery)")
        print(f"   Suresh Kumar ↔ Imran Khan (cyber fraud)")
        print(f"   Manoj Das ↔ vehicle theft")

        # ── Commit ──────────────────────────────────────────────
        await session.commit()
        print("\n" + "=" * 60)
        print("🎉 Database seeding complete! ✅")
        print("=" * 60)
        print(f"\n📋 Test Login:")
        print(f"   Email:    arjun.kumar@ksp.gov.in")
        print(f"   Password: Police@123")
        print(f"\n📋 Test Queries:")
        print(f"   SQL-only:  Show FIR FIR2026001")
        print(f"   SQL-only:  Show accused in FIR2026001")
        print(f"   SQL+AI:    Summarize FIR2026001")
        print(f"   SQL+AI:    Analyze hotspots in Bengaluru")
        print(f"   SQL+AI:    Generate a case summary")


if __name__ == "__main__":
    asyncio.run(seed_database())
