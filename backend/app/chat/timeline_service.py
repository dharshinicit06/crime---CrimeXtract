"""Investigation Timeline -- generates a chronological investigation flow for a case.

Builds a complete timeline from FIR data plus related victims, accused,
evidence, financial records, network connections, and predictions.
Uses existing service methods -- never queries the database directly.
"""

from typing import Any, Optional


class InvestigationTimeline:
    """Generates a chronological investigation timeline for a given case.

    The timeline covers:
      - Complaint Registration
      - FIR Created
      - Victim Statement Recorded
      - Evidence Collected
      - Accused Identified
      - Financial Investigation
      - Network Analysis
      - Current Status

    Uses timestamps where available; falls back to logical order.
    """

    # Icon map for timeline events
    ICONS = {
        "Complaint Registered": "clipboard",
        "FIR Registered": "document",
        "FIR Created": "document",
        "Investigation Started": "search",
        "Victim Statement Recorded": "person",
        "Victim Identified": "person",
        "Evidence Collected": "microscope",
        "Evidence Documented": "microscope",
        "Accused Identified": "warning",
        "Accused Arrested": "warning",
        "Financial Investigation": "money",
        "Transaction Analyzed": "money",
        "Network Analysis": "link",
        "Connection Found": "link",
        "Officer Assigned": "shield",
        "Case Solved": "check",
        "Case Closed": "locked",
        "Prediction Generated": "chart",
        "Report Generated": "file",
        "Status Update": "refresh",
    }

    DEFAULT_ICON = "circle"

    @classmethod
    def build(cls, data: dict, intent: str = "CASE_SUMMARY") -> list[dict]:
        """Build a chronological timeline from case data.

        Args:
            data: Structured case data (FIR, victims, accused, etc.)
            intent: The intent that generated the data

        Returns:
            List of timeline events sorted chronologically:
            [{"date": str, "event": str, "description": str, "icon": str, "status": str}, ...]
        """
        events = []

        # Extract FIR data
        fir = data if "fir_id" in data else (data.get("firs", [None])[0] if data.get("firs") else None)
        if fir:
            events.extend(cls._build_fir_events(fir))

        # Extract victims
        victims = data.get("victims", [])
        for v in victims:
            events.append({
                "date": None,
                "event": "Victim Identified",
                "description": "Victim %s identified (Age: %s)" % (v.get('full_name', 'N/A'), v.get('age', 'N/A')),
                "icon": cls.ICONS.get("Victim Identified", cls.DEFAULT_ICON),
                "status": "completed",
            })

        # Extract accused
        accused_list = data.get("accused", [])
        for a in accused_list:
            repeat_text = " (Repeat offender)" if a.get("is_repeat_offender") else ""
            events.append({
                "date": None,
                "event": "Accused Identified",
                "description": "Accused %s identified%s" % (a.get('full_name', 'N/A'), repeat_text),
                "icon": cls.ICONS.get("Accused Identified", cls.DEFAULT_ICON),
                "status": "completed",
            })

        # Extract evidence
        evidence = data.get("evidence", [])
        for e in evidence:
            events.append({
                "date": e.get("collected_date"),
                "event": "Evidence Collected",
                "description": "%s evidence: %s" % (e.get('evidence_type', 'Unknown'), e.get('evidence_name', 'N/A')),
                "icon": cls.ICONS.get("Evidence Collected", cls.DEFAULT_ICON),
                "status": "completed",
            })

        # Extract transactions
        transactions = data.get("transactions", data.get("transaction_data", []))
        for t in transactions:
            amount = t.get("amount", 0)
            events.append({
                "date": t.get("transaction_date"),
                "event": "Transaction Analyzed",
                "description": "Rs.%.2f via %s (%s)" % (amount, t.get('bank_name', 'Unknown'), t.get('transaction_type', 'N/A')),
                "icon": cls.ICONS.get("Transaction Analyzed", cls.DEFAULT_ICON),
                "status": "completed",
            })

        # Extract network data
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        if nodes:
            events.append({
                "date": None,
                "event": "Network Analysis",
                "description": "Network analysis complete: %d entities, %d connections found" % (len(nodes), len(edges)),
                "icon": cls.ICONS.get("Network Analysis", cls.DEFAULT_ICON),
                "status": "completed",
            })

        # Extract hotspot data
        hotspots = data.get("hotspots", [])
        if hotspots:
            events.append({
                "date": None,
                "event": "Hotspot Analysis",
                "description": "Crime hotspot analysis identified %d high-risk areas" % len(hotspots),
                "icon": "flame",
                "status": "completed",
            })

        # Extract prediction data
        predictions = data.get("predictions", [])
        if predictions:
            confidence = data.get("confidence", 0)
            events.append({
                "date": data.get("generated_at"),
                "event": "Prediction Generated",
                "description": "Crime forecast generated: %d month prediction with %.1f%% confidence" % (len(predictions), confidence * 100),
                "icon": cls.ICONS.get("Prediction Generated", cls.DEFAULT_ICON),
                "status": "completed",
            })

        # Extract statistics / status
        stats = data.get("statistics", {})
        if stats and isinstance(stats, dict):
            total = stats.get("total_firs", stats.get("total", 0))
            solved = stats.get("solved_count", 0)
            pending = stats.get("pending_count", 0)
            events.append({
                "date": None,
                "event": "Status Update",
                "description": "%d total case(s): %d solved, %d pending investigation" % (total, solved, pending),
                "icon": cls.ICONS.get("Status Update", cls.DEFAULT_ICON),
                "status": "completed",
            })

        # Check if there's a timeline already in the data (from FIRService.get_fir_timeline)
        existing_timeline = data.get("timeline", [])
        if existing_timeline:
            for te in existing_timeline:
                events.append({
                    "date": te.get("date"),
                    "event": te.get("event", "Timeline Event"),
                    "description": te.get("description", ""),
                    "icon": cls.ICONS.get(te.get("event", ""), cls.DEFAULT_ICON),
                    "status": "completed",
                })

        # Sort chronologically -- events with dates first, then logical order
        dated = [e for e in events if e.get("date")]
        undated = [e for e in events if not e.get("date")]

        dated.sort(key=lambda x: str(x["date"] or ""), reverse=False)

        # For undated events, use a logical order
        order_map = {
            "Complaint Registered": 1,
            "FIR Created": 2,
            "FIR Registered": 2,
            "Victim Identified": 3,
            "Victim Statement Recorded": 3,
            "Officer Assigned": 4,
            "Investigation Started": 5,
            "Evidence Collected": 6,
            "Evidence Documented": 6,
            "Accused Identified": 7,
            "Accused Arrested": 7,
            "Transaction Analyzed": 8,
            "Financial Investigation": 8,
            "Network Analysis": 9,
            "Connection Found": 9,
            "Hotspot Analysis": 10,
            "Prediction Generated": 11,
            "Report Generated": 12,
            "Case Solved": 13,
            "Case Closed": 14,
            "Status Update": 15,
        }
        undated.sort(key=lambda x: order_map.get(x["event"], 99))

        return dated + undated

    @classmethod
    def _build_fir_events(cls, fir: dict) -> list[dict]:
        """Build timeline events from a single FIR record."""
        events = []
        events.append({
            "date": fir.get("complaint_date") or fir.get("created_at"),
            "event": "Complaint Registered",
            "description": "Complaint received for %s" % fir.get('title', 'Unknown case'),
            "icon": cls.ICONS.get("Complaint Registered", cls.DEFAULT_ICON),
            "status": "completed",
        })
        events.append({
            "date": fir.get("created_at") or fir.get("incident_date"),
            "event": "FIR Created",
            "description": "FIR %s was registered" % fir.get('fir_number', 'N/A'),
            "icon": cls.ICONS.get("FIR Created", cls.DEFAULT_ICON),
            "status": "completed",
        })

        status = fir.get("status", "")
        if status and status.lower() in ("under investigation", "solved", "closed"):
            events.append({
                "date": fir.get("created_at"),
                "event": "Investigation Started",
                "description": "Investigation began for %s" % fir.get('fir_number', 'N/A'),
                "icon": cls.ICONS.get("Investigation Started", cls.DEFAULT_ICON),
                "status": "completed",
            })
        if status and status.lower() in ("solved", "closed"):
            events.append({
                "date": fir.get("incident_date"),
                "event": "Case Solved",
                "description": "%s marked as solved" % fir.get('fir_number', 'N/A'),
                "icon": cls.ICONS.get("Case Solved", cls.DEFAULT_ICON),
                "status": "completed",
            })
        if status and status.lower() == "closed":
            events.append({
                "date": fir.get("incident_date"),
                "event": "Case Closed",
                "description": "%s closed" % fir.get('fir_number', 'N/A'),
                "icon": cls.ICONS.get("Case Closed", cls.DEFAULT_ICON),
                "status": "completed",
            })
        return events
