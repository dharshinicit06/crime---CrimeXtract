"""Demo Mode API — returns hard-coded sample data for all entity types.

All endpoints return data from demo_data.py, never from the database.
Useful for demonstrations, testing, and onboarding new users.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.auth.models import User
from app.dependencies import get_current_user
from app.demo.demo_service import DemoService

router = APIRouter(prefix="/demo", tags=["Demo Mode"])
_demo = DemoService()


@router.get("/info", summary="Demo mode info and data counts")
async def get_demo_info(current_user: User = Depends(get_current_user)):
    return _demo.get_demo_info()


@router.get("/firs", summary="List demo FIRs")
async def list_demo_firs(
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    return _demo.list_firs(search or "")


@router.get("/firs/{fir_id}", summary="Get a single demo FIR")
async def get_demo_fir(fir_id: int, current_user: User = Depends(get_current_user)):
    return _demo.get_fir(fir_id)


@router.get("/firs/statistics", summary="Demo FIR statistics")
async def get_demo_fir_stats(current_user: User = Depends(get_current_user)):
    return _demo.get_statistics()


@router.get("/victims", summary="List demo victims")
async def list_demo_victims(
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    return _demo.list_victims(search or "")


@router.get("/accused", summary="List demo accused")
async def list_demo_accused(
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    return _demo.list_accused(search or "")


@router.get("/evidence", summary="List demo evidence")
async def list_demo_evidence(
    fir_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
):
    return _demo.list_evidence(fir_id or 0)


@router.get("/transactions", summary="List demo financial transactions")
async def list_demo_transactions(
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    return _demo.list_transactions(search or "")


@router.get("/history", summary="List demo crime history")
async def list_demo_history(current_user: User = Depends(get_current_user)):
    return _demo.list_history()


@router.get("/hotspots", summary="List demo crime hotspots")
async def list_demo_hotspots(
    time_range: str = Query("30d"),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    return _demo.get_hotspots(time_range, search or "")


@router.get("/hotspots/map", summary="Demo hotspot map data (GIS)")
async def demo_hotspot_map(current_user: User = Depends(get_current_user)):
    return _demo.get_hotspot_map()


@router.get("/hotspots/{district}", summary="Demo hotspot detail")
async def demo_hotspot_detail(district: str, current_user: User = Depends(get_current_user)):
    return _demo.get_hotspot_detail(district)


@router.get("/network", summary="Demo criminal network graph")
async def demo_network_graph(
    fir_number: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    return _demo.build_graph(fir_number or "")


@router.get("/dashboard", summary="Demo dashboard data")
async def demo_dashboard(current_user: User = Depends(get_current_user)):
    return _demo.get_dashboard()


@router.get("/predictions", summary="Demo crime predictions")
async def demo_predictions(current_user: User = Depends(get_current_user)):
    return _demo.get_prediction()


@router.get("/users", summary="List demo users")
async def list_demo_users(current_user: User = Depends(get_current_user)):
    return _demo.list_users()


@router.get("/audit-logs", summary="List demo audit logs")
async def list_demo_audit_logs(current_user: User = Depends(get_current_user)):
    return _demo.list_audit_logs()


@router.get("/settings", summary="Demo settings")
async def demo_settings(current_user: User = Depends(get_current_user)):
    return _demo.get_settings()
