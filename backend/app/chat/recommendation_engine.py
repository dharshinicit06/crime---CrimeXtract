"""Recommendation Engine — generates intelligent investigation recommendations.

Produces crime-type-specific recommendations based on available case data.
Never fabricates facts — only uses data already retrieved from the database.
Recommendations are appended below AI summaries, never replacing them.
"""

from typing import Any


class RecommendationEngine:
    """Generates smart investigation recommendations per crime type.

    Recommendations are derived from:
      - Crime type (theft, fraud, murder, etc.)
      - Available evidence records
      - Victim information
      - Accused criminal history
      - Financial transaction patterns
      - Network connections
      - Crime predictions
    """

    # ── Crime-type recommendation templates ─────────────────────

    _RECOMMENDATIONS: dict[str, list[dict]] = {
        "Theft": [
            {"icon": "📹", "action": "Check nearby CCTV footage", "reason": "Identify suspect movement and vehicle details"},
            {"icon": "📋", "action": "Review previous theft FIRs in same area", "reason": "Identify pattern and potential repeat offenders"},
            {"icon": "🔍", "action": "Verify suspect alibi and movement", "reason": "Corroborate or refute suspect statements"},
            {"icon": "💰", "action": "Examine financial transactions for stolen assets", "reason": "Track stolen property through financial trail"},
            {"icon": "👤", "action": "Interview witnesses in vicinity", "reason": "Gather additional eyewitness accounts"},
            {"icon": "🔗", "action": "Check criminal network connections", "reason": "Identify organized theft rings"},
            {"icon": "📊", "action": "Analyze theft patterns and hotspots", "reason": "Deploy preventive patrols in high-risk areas"},
        ],
        "Burglary": [
            {"icon": "🔬", "action": "Process crime scene for forensic evidence", "reason": "Collect fingerprints, DNA, and trace evidence"},
            {"icon": "📹", "action": "Review neighbourhood surveillance footage", "reason": "Identify suspect vehicle and entry method"},
            {"icon": "👥", "action": "Interview neighbours for suspicious activity", "reason": "Establish timeline and suspect description"},
            {"icon": "📋", "action": "Cross-reference with nearby burglary cases", "reason": "Identify serial burglary patterns"},
            {"icon": "🔗", "action": "Check local pawn shops and online marketplaces", "reason": "Recover stolen goods and identify sellers"},
            {"icon": "📊", "action": "Analyze burglary time patterns", "reason": "Deploy targeted patrols during peak hours"},
        ],
        "Assault": [
            {"icon": "🏥", "action": "Obtain medical reports and injury documentation", "reason": "Document severity for legal proceedings"},
            {"icon": "👤", "action": "Record detailed victim statement", "reason": "Preserve witness testimony while memory is fresh"},
            {"icon": "📹", "action": "Review area surveillance for altercation", "reason": "Establish sequence of events"},
            {"icon": "👥", "action": "Identify and interview witnesses", "reason": "Corroborate victim account"},
            {"icon": "📋", "action": "Check accused criminal history", "reason": "Identify history of violence or repeat offences"},
            {"icon": "🔗", "action": "Investigate relationship between parties", "reason": "Determine if assault was targeted or random"},
        ],
        "Robbery": [
            {"icon": "📹", "action": "Review CCTV footage from robbery location", "reason": "Identify suspect appearance and getaway route"},
            {"icon": "👤", "action": "Take detailed victim statement", "reason": "Document suspect description and stolen items"},
            {"icon": "💰", "action": "Monitor financial accounts for unusual activity", "reason": "Track stolen cards or funds"},
            {"icon": "🔍", "action": "Search area for discarded items or weapons", "reason": "Recover evidence discarded during escape"},
            {"icon": "📋", "action": "Check for similar recent robberies", "reason": "Identify potential serial offender"},
            {"icon": "👥", "action": "Canvass area for additional witnesses", "reason": "Strengthen case with multiple accounts"},
        ],
        "Cyber Crime": [
            {"icon": "💻", "action": "Preserve digital evidence immediately", "reason": "Prevent data loss or tampering"},
            {"icon": "🔐", "action": "Freeze compromised accounts", "reason": "Prevent further unauthorised transactions"},
            {"icon": "📧", "action": "Analyze email headers and IP logs", "reason": "Trace source of phishing or hacking attempts"},
            {"icon": "💰", "action": "Trace cryptocurrency or digital payment trail", "reason": "Follow money trail in cyber fraud cases"},
            {"icon": "🔗", "action": "Check for linked cyber crime complaints", "reason": "Identify larger coordinated cyber attack"},
            {"icon": "📱", "action": "Recover deleted digital communications", "reason": "Extract evidence from messaging apps"},
            {"icon": "📊", "action": "Engage cyber forensics team", "reason": "Specialised analysis of compromised systems"},
        ],
        "Fraud": [
            {"icon": "💰", "action": "Freeze suspicious bank accounts", "reason": "Prevent further fund diversion"},
            {"icon": "🔗", "action": "Verify entire transaction chain", "reason": "Identify all parties involved in fraud"},
            {"icon": "👥", "action": "Compare beneficiary account details", "reason": "Identify mule accounts and common beneficiaries"},
            {"icon": "📋", "action": "Review historical transaction patterns", "reason": "Detect unusual activity preceding the fraud"},
            {"icon": "💻", "action": "Preserve digital evidence and logs", "reason": "Document IP addresses and device information"},
            {"icon": "🔍", "action": "Cross-reference with similar fraud cases", "reason": "Identify organised fraud networks"},
            {"icon": "📊", "action": "Alert other departments about fraud pattern", "reason": "Prevent similar frauds across jurisdictions"},
        ],
        "Kidnapping": [
            {"icon": "📱", "action": "Analyze call records and last known location", "reason": "Establish victim's movements before disappearance"},
            {"icon": "📹", "action": "Review CCTV near last known location", "reason": "Identify vehicle and suspects involved"},
            {"icon": "👥", "action": "Interview family and close associates", "reason": "Gather information about possible motives"},
            {"icon": "💰", "action": "Monitor for ransom demands and financial activity", "reason": "Prepare for negotiation and tracking"},
            {"icon": "🔗", "action": "Check criminal network connections", "reason": "Identify known kidnapping syndicates"},
            {"icon": "🚨", "action": "Issue alerts at transit points", "reason": "Prevent suspect from moving victim across borders"},
            {"icon": "📊", "action": "Deploy specialized kidnapping investigation team", "reason": "Experienced negotiators and trackers"},
        ],
        "Murder": [
            {"icon": "🔬", "action": "Comprehensive forensic examination of scene", "reason": "Collect DNA, fingerprints, and ballistic evidence"},
            {"icon": "📱", "action": "Analyze victim and suspect call records", "reason": "Establish communication patterns and last contacts"},
            {"icon": "👥", "action": "Interview all known associates", "reason": "Establish motive and suspect alibis"},
            {"icon": "📋", "action": "Check accused criminal history thoroughly", "reason": "Identify history of violence or threats"},
            {"icon": "💰", "action": "Examine financial records for disputes", "reason": "Identify financial motives and beneficiaries"},
            {"icon": "📹", "action": "Review all available surveillance near scene", "reason": "Track suspect movement before and after incident"},
            {"icon": "🔗", "action": "Build complete network of relationships", "reason": "Identify all persons connected to victim and suspect"},
            {"icon": "📊", "action": "Coordinate with forensics and prosecution team", "reason": "Build comprehensive case for trial"},
        ],
        "Hit and Run": [
            {"icon": "📹", "action": "Review traffic and area surveillance cameras", "reason": "Identify vehicle make, model, and license plate"},
            {"icon": "🔍", "action": "Search for vehicle debris and paint samples", "reason": "Forensic matching to suspect vehicle"},
            {"icon": "👥", "action": "Interview witnesses at scene", "reason": "Gather vehicle description and direction of travel"},
            {"icon": "🔧", "action": "Check nearby auto repair shops", "reason": "Look for vehicles with recent accident damage"},
            {"icon": "📋", "action": "Check traffic challan database for vehicle", "reason": "Identify registered owner of suspect vehicle"},
            {"icon": "🔗", "action": "Issue lookout notice at state borders", "reason": "Prevent suspect vehicle from leaving jurisdiction"},
        ],
        "Riot": [
            {"icon": "📹", "action": "Review all available video evidence", "reason": "Identify instigators and participants"},
            {"icon": "📱", "action": "Analyze social media and messaging groups", "reason": "Identify coordination and planning"},
            {"icon": "👥", "action": "Record witness and victim statements", "reason": "Document sequence of events and damages"},
            {"icon": "🏥", "action": "Document injuries and medical reports", "reason": "Support prosecution with medical evidence"},
            {"icon": "💰", "action": "Assess property damage and financial loss", "reason": "Support victim compensation claims"},
            {"icon": "🔗", "action": "Verify identities of arrested individuals", "reason": "Check criminal records and prior riot involvement"},
            {"icon": "📊", "action": "File detailed incident report", "reason": "Document complete chain of events for legal proceedings"},
        ],
    }

    _DEFAULT = [
        {"icon": "🔍", "action": "Document all available evidence thoroughly", "reason": "Preserve chain of custody for legal proceedings"},
        {"icon": "👤", "action": "Record witness and victim statements", "reason": "Preserve testimony for investigation"},
        {"icon": "📋", "action": "Cross-reference with similar cases", "reason": "Identify patterns and potential serial offences"},
        {"icon": "🔗", "action": "Check relationships between involved parties", "reason": "Establish connections and possible motives"},
        {"icon": "📊", "action": "Generate comprehensive case report", "reason": "Document complete investigation for prosecution"},
    ]

    @classmethod
    def generate(cls, data: dict) -> list[dict]:
        """Generate recommendations based on case data.

        Args:
            data: Structured case data (FIR, victims, accused, evidence, etc.)

        Returns:
            List of recommendation dicts:
            [{"icon": str, "action": str, "reason": str, "priority": str}, ...]
        """
        crime_type = cls._detect_crime_type(data)
        recommendations = list(cls._RECOMMENDATIONS.get(crime_type, cls._DEFAULT))

        # Enrich with data-driven context
        cls._enrich_from_evidence(recommendations, data)
        cls._enrich_from_accused(recommendations, data)
        cls._enrich_from_transactions(recommendations, data)
        cls._enrich_from_history(recommendations, data)

        # Add priority tags
        for rec in recommendations:
            rec["priority"] = cls._assign_priority(rec)

        return recommendations[:10]  # Limit to 10 max

    @classmethod
    def _detect_crime_type(cls, data: dict) -> str:
        """Detect the primary crime type from available data."""
        # Check FIR data
        if "crime_type_id" in data:
            return data["crime_type_id"]
        firs = data.get("firs", [])
        if firs and isinstance(firs, list):
            ct = firs[0].get("crime_type_id", "")
            if ct:
                return ct
        # Check if crime_type is in data
        ct = data.get("crime_type", "")
        if ct:
            return ct
        return "General"

    @classmethod
    def _enrich_from_evidence(cls, recommendations: list, data: dict) -> None:
        """Add evidence-specific recommendations."""
        evidence = data.get("evidence", [])
        if not evidence:
            recommendations.insert(0, {
                "icon": "🔬",
                "action": "Collect and document physical evidence from scene",
                "reason": "No evidence records found — evidence collection should be prioritised",
            })
            return
        # Count evidence types
        types = {}
        for e in evidence:
            t = e.get("evidence_type", "Unknown")
            types[t] = types.get(t, 0) + 1
        if "Digital" in types:
            recommendations.append({
                "icon": "💻",
                "action": "Analyze digital evidence thoroughly",
                "reason": f"{types['Digital']} digital evidence item(s) found — requires cyber forensics",
            })

    @classmethod
    def _enrich_from_accused(cls, recommendations: list, data: dict) -> None:
        """Add accused-specific recommendations."""
        accused = data.get("accused", [])
        repeat = [a for a in accused if a.get("is_repeat_offender")]
        if repeat:
            recommendations.insert(0, {
                "icon": "⚠️",
                "action": f"Prioritize investigation of repeat offender(s): {', '.join(a.get('full_name', 'Unknown') for a in repeat[:3])}",
                "reason": "Repeat offenders present elevated risk and may be linked to unsolved cases",
            })
        high_risk = [a for a in accused if (a.get("risk_score") or 0) >= 7]
        if high_risk:
            recommendations.append({
                "icon": "🚨",
                "action": "Apply enhanced surveillance for high-risk accused",
                "reason": f"{len(high_risk)} accused flagged with risk score ≥ 7",
            })

    @classmethod
    def _enrich_from_transactions(cls, recommendations: list, data: dict) -> None:
        """Add financial investigation recommendations."""
        transactions = data.get("transactions", data.get("transaction_data", []))
        if transactions:
            total = sum(t.get("amount", 0) for t in transactions)
            if total > 100000:
                recommendations.insert(0, {
                    "icon": "💰",
                    "action": "Deep financial investigation required",
                    "reason": f"Total transaction amount ₹{total:,.2f} exceeds threshold — possible financial crime",
                })

    @classmethod
    def _enrich_from_history(cls, recommendations: list, data: dict) -> None:
        """Add criminal history recommendations."""
        history = data.get("history", [])
        if history:
            convicted = sum(1 for h in history if h.get("conviction_status") == "Convicted")
            if convicted > 0:
                recommendations.append({
                    "icon": "📋",
                    "action": f"Review {convicted} previous conviction(s) for pattern analysis",
                    "reason": "Previous convictions provide modus operandi insights",
                })

    @classmethod
    def _assign_priority(cls, rec: dict) -> str:
        """Assign priority based on action content."""
        high_keywords = ["freeze", "forensic", "immediately", "priority", "surveillance", "alert", "preserve"]
        medium_keywords = ["analyze", "review", "examine", "interview", "monitor", "investigate", "trace"]
        action_lower = rec.get("action", "").lower()
        for kw in high_keywords:
            if kw in action_lower:
                return "high"
        for kw in medium_keywords:
            if kw in action_lower:
                return "medium"
        return "standard"
