"""Explainable AI — Evidence-based explanation generator.

This module generates human-readable explanations for every AI response
using ONLY the structured data that was retrieved from MySQL. No
hallucination is possible because we never invent facts — only
summarise what the database returned.

Every explanation includes:
  - answer: Short summary of the finding
  - explanation: Narrative of why this conclusion was reached
  - evidence: List of bullet-point facts drawn directly from the data

Usage:
    ExplanationBuilder.build(intent_name, structured_data)
"""

from typing import Any


class ExplanationBuilder:
    """Generates evidence-based explanations from structured SQL data.

    Each ``build()`` call analyses the intent type and extracts
    relevant counts, patterns, and anomalies from the data dict.
    The result is always grounded in actual database fields.
    """

    @staticmethod
    def build(intent: str, data: dict[str, Any]) -> dict[str, Any]:
        """Build a data-grounded explanation for the given intent.

        Args:
            intent: Classified intent name (e.g. ``"FIR_SEARCH"``,
                    ``"HOTSPOT_ANALYSIS"``, ``"CRIME_PREDICTION"``).
            data: Structured data returned by the module service.

        Returns:
            dict with keys:
              - answer (str): One-line summary of what was found.
              - explanation (str): Narrative of the key drivers / reasons.
              - evidence (list[str]): Bullet-point facts from the data.
        """
        builder = _IntentExplanationBuilder()
        handler = builder._handlers.get(intent, builder._handle_default)
        return handler(data)


class _IntentExplanationBuilder:
    """Internal handler registry — maps intents to explanation logic."""

    def __init__(self) -> None:
        self._handlers: dict[str, callable] = {
            "FIR_SEARCH": self._explain_fir_search,
            "FIR_SUMMARY": self._explain_fir_summary,
            "VICTIM_SEARCH": self._explain_victim_search,
            "VICTIM_SUMMARY": self._explain_victim_summary,
            "ACCUSED_SEARCH": self._explain_accused_search,
            "ACCUSED_SUMMARY": self._explain_accused_summary,
            "EVIDENCE_SEARCH": self._explain_evidence_search,
            "EVIDENCE_SUMMARY": self._explain_evidence_summary,
            "FINANCIAL_SEARCH": self._explain_financial_search,
            "FINANCIAL_SUMMARY": self._explain_financial_summary,
            "CRIME_HISTORY_SEARCH": self._explain_history_search,
            "CRIME_HISTORY_SUMMARY": self._explain_history_summary,
            "HOTSPOT_SEARCH": self._explain_hotspot_search,
            "HOTSPOT_ANALYSIS": self._explain_hotspot_analysis,
            "NETWORK_SEARCH": self._explain_network_search,
            "NETWORK_ANALYSIS": self._explain_network_analysis,
            "NETWORK_GRAPH": self._explain_network_graph,
            "CRIME_PREDICTION": self._explain_prediction,
            "LOCATION_SEARCH": self._explain_location_search,
            "REPORT_GENERATION": self._explain_report,
            "CASE_SUMMARY": self._explain_case_summary,
        }

    @staticmethod
    def _build_result(answer: str, explanation: str, evidence: list[str]) -> dict[str, Any]:
        return {"answer": answer, "explanation": explanation, "evidence": evidence}

    @staticmethod
    def _count(items: list | None) -> int:
        return len(items) if items else 0

    @staticmethod
    def _format_list(items: list[Any], key: str = "name", max_items: int = 5) -> str:
        names = []
        for item in items[:max_items]:
            val = item.get(key) or item.get("fir_number") or item.get("full_name") or str(item.get("id", ""))
            if val:
                names.append(str(val))
        if not names:
            return "None"
        text = ", ".join(names)
        remaining = len(items) - max_items
        if remaining > 0:
            text += f" and {remaining} more"
        return text

    def _explain_fir_search(self, data: dict) -> dict:
        firs = data.get("firs", [])
        total = data.get("total", len(firs))
        closed = sum(1 for f in firs if f.get("status", "").lower() == "closed")
        high_priority = sum(1 for f in firs if f.get("priority", "").lower() == "high")
        evidence = [f"\u2022 {total} FIR(s) found matching your search criteria"]
        if closed:
            evidence.append(f"\u2022 {closed} FIR(s) marked as closed")
        if high_priority:
            evidence.append(f"\u2022 {high_priority} FIR(s) flagged as high priority")
        if firs:
            evidence.append(f"\u2022 Recent: {self._format_list(firs, 'fir_number')}")
        explanation = f"Query returned {total} records from the FIR database."
        if closed or high_priority:
            explanation += f" Of these, {closed} are closed and {high_priority} are high priority."
        return self._build_result(f"Found {total} FIR(s)", explanation, evidence)

    def _explain_fir_summary(self, data: dict) -> dict:
        return self._explain_fir_search(data)

    def _explain_victim_search(self, data: dict) -> dict:
        victims = data.get("victims", [])
        total = data.get("total", len(victims))
        evidence = [f"\u2022 {total} victim(s) matching the search"]
        if victims:
            evidence.append(f"\u2022 Names: {self._format_list(victims, 'full_name')}")
        return self._build_result(f"Found {total} victim(s)",
            f"Database returned {total} victim records based on the provided search terms.", evidence)

    def _explain_victim_summary(self, data: dict) -> dict:
        return self._explain_victim_search(data)

    def _explain_accused_search(self, data: dict) -> dict:
        accused = data.get("accused", [])
        total = data.get("total", len(accused))
        repeat = sum(1 for a in accused if a.get("is_repeat_offender"))
        high_risk = sum(1 for a in accused if (a.get("risk_score") or 0) >= 7)
        evidence = [f"\u2022 {total} accused person(s) found"]
        if repeat:
            evidence.append(f"\u2022 {repeat} identified as repeat offenders")
        if high_risk:
            evidence.append(f"\u2022 {high_risk} flagged as high-risk (score \u2265 7)")
        if accused:
            evidence.append(f"\u2022 Names: {self._format_list(accused, 'full_name')}")
        parts = [f"Search identified {total} accused records."]
        if repeat:
            parts.append(f"Repeat offenders: {repeat}.")
        if high_risk:
            parts.append(f"High-risk individuals: {high_risk}.")
        return self._build_result(f"Found {total} accused person(s)", " ".join(parts), evidence)

    def _explain_accused_summary(self, data: dict) -> dict:
        return self._explain_accused_search(data)

    def _explain_evidence_search(self, data: dict) -> dict:
        evs = data.get("evidence", [])
        total = data.get("total", len(evs))
        types: dict[str, int] = {}
        for e in evs:
            t = e.get("evidence_type", "Unknown")
            types[t] = types.get(t, 0) + 1
        evidence = [f"\u2022 {total} evidence record(s) found"]
        for etype, count in sorted(types.items(), key=lambda x: -x[1]):
            evidence.append(f"\u2022 {etype}: {count} record(s)")
        type_str = ", ".join(f"{t} ({c})" for t, c in sorted(types.items(), key=lambda x: -x[1]))
        return self._build_result(f"Found {total} evidence record(s)",
            f"Retrieved {total} evidence records. Types include: {type_str}.", evidence)

    def _explain_evidence_summary(self, data: dict) -> dict:
        return self._explain_evidence_search(data)

    def _explain_financial_search(self, data: dict) -> dict:
        txs = data.get("transactions", [])
        total = data.get("total", len(txs))
        total_amount = sum(t.get("amount", 0) for t in txs)
        tx_types: dict[str, int] = {}
        for t in txs:
            tt = t.get("transaction_type", "Unknown")
            tx_types[tt] = tx_types.get(tt, 0) + 1
        evidence = [f"\u2022 {total} transaction(s) found", f"\u2022 Total amount: \u20b9{total_amount:,.2f}"]
        for tt, count in sorted(tx_types.items(), key=lambda x: -x[1]):
            evidence.append(f"\u2022 {tt}: {count} transaction(s)")
        type_str = ", ".join(f"{t} ({c})" for t, c in sorted(tx_types.items(), key=lambda x: -x[1]))
        return self._build_result(f"Found {total} transaction(s) totalling \u20b9{total_amount:,.2f}",
            f"Financial records show {total} transactions (\u20b9{total_amount:,.2f}). Types: {type_str}.", evidence)

    def _explain_financial_summary(self, data: dict) -> dict:
        return self._explain_financial_search(data)

    def _explain_history_search(self, data: dict) -> dict:
        items = data.get("history", [])
        total = data.get("total", len(items))
        convicted = sum(1 for h in items if h.get("conviction_status", "").lower() == "convicted")
        evidence = [f"\u2022 {total} criminal history record(s) found"]
        if convicted:
            evidence.append(f"\u2022 {convicted} resulted in conviction")
        return self._build_result(f"Found {total} criminal history record(s)",
            f"Historical records show {total} entries, of which {convicted} resulted in convictions.", evidence)

    def _explain_history_summary(self, data: dict) -> dict:
        return self._explain_history_search(data)

    def _explain_hotspot_search(self, data: dict) -> dict:
        hotspots = data.get("hotspots", [])
        total = data.get("total_hotspots", len(hotspots))
        high_risk = sum(1 for h in hotspots if str(h.get("risk_level", "")).lower() == "high")
        evidence = [f"\u2022 {total} crime hotspot(s) identified"]
        if high_risk:
            evidence.append(f"\u2022 {high_risk} classified as high risk")
        if hotspots:
            for h in hotspots[:3]:
                evidence.append(f"\u2022 {h.get('district', 'Unknown')}: {h.get('crime_count', 0)} crimes")
        return self._build_result(f"Identified {total} crime hotspot(s)",
            f"Analysis reveals {total} hotspot areas. {f'Of these, {high_risk} are high risk.' if high_risk else ''}", evidence)

    def _explain_hotspot_analysis(self, data: dict) -> dict:
        hotspots = data.get("hotspots", [])
        high_risk = data.get("high_risk_count", 0)
        total_crimes = data.get("total_crimes", 0)
        evidence = [f"\u2022 {len(hotspots)} hotspot area(s) analysed"]
        if total_crimes:
            evidence.append(f"\u2022 {total_crimes} total crimes in analysed areas")
        if high_risk:
            evidence.append(f"\u2022 {high_risk} area(s) flagged as high risk")
        if hotspots:
            for h in hotspots[:3]:
                evidence.append(f"\u2022 {h.get('district', 'Unknown')}: {h.get('crime_count', 0)} crimes (risk: {h.get('risk_level', 'N/A')})")
        return self._build_result(f"Analysed {len(hotspots)} hotspot(s) with {total_crimes} total crimes",
            f"Hotspot analysis covered {len(hotspots)} areas totalling {total_crimes} crimes.", evidence)

    def _explain_network_search(self, data: dict) -> dict:
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        node_types: dict[str, int] = {}
        for n in nodes:
            nt = n.get("type", "Unknown")
            node_types[nt] = node_types.get(nt, 0) + 1
        evidence = [f"\u2022 Network has {len(nodes)} node(s) and {len(edges)} connection(s)"]
        for nt, count in sorted(node_types.items(), key=lambda x: -x[1]):
            evidence.append(f"\u2022 {nt}: {count} node(s)")
        type_str = ", ".join(f"{t} ({c})" for t, c in sorted(node_types.items(), key=lambda x: -x[1]))
        return self._build_result(f"Network has {len(nodes)} entities with {len(edges)} connections",
            f"The network consists of {len(nodes)} entities connected by {len(edges)} relationships. Types: {type_str}.", evidence)

    def _explain_network_analysis(self, data: dict) -> dict:
        return self._explain_network_search(data)

    def _explain_network_graph(self, data: dict) -> dict:
        return self._explain_network_search(data)

    def _explain_prediction(self, data: dict) -> dict:
        predictions = data.get("predictions", [])
        hotspot_trends = data.get("hotspot_trends", [])
        seasonal = data.get("seasonal_patterns", [])
        confidence = data.get("confidence", 0)
        total_historical = data.get("total_historical", 0)
        evidence = [
            f"\u2022 Model confidence: {confidence * 100:.1f}%",
            f"\u2022 Historical records analysed: {total_historical}",
        ]
        if predictions:
            nm = predictions[0]
            evidence.append(f"\u2022 Predicted crimes next month: {nm.get('predicted_count', 'N/A')} "
                          f"({nm.get('lower_bound', 'N/A')} \u2013 {nm.get('upper_bound', 'N/A')})")
        rising = [h for h in hotspot_trends if h.get("trend") == "rising"]
        if rising:
            evidence.append(f"\u2022 {len(rising)} district(s) showing rising crime trends")
        if seasonal:
            trends = [f"{s.get('season', '')} ({s.get('average_crimes', 0):.0f} avg)" for s in seasonal[:4]]
            evidence.append(f"\u2022 Seasonal: {', '.join(trends)}")
        parts = [f"The Linear Regression model analysed {total_historical} historical FIR records "
                 f"and achieved {confidence * 100:.1f}% confidence."]
        if predictions:
            parts.append(f"Next month's forecast is {predictions[0].get('predicted_count', 'N/A')} crimes.")
        if rising:
            parts.append(f"{len(rising)} districts show rising trends requiring attention.")
        return self._build_result(f"Predicted with {confidence * 100:.1f}% confidence",
            " ".join(parts), evidence)

    def _explain_location_search(self, data: dict) -> dict:
        locations = data.get("locations", [])
        total = data.get("total", len(locations))
        evidence = [f"\u2022 {total} location(s) found"]
        if locations:
            evidence.append(f"\u2022 Areas: {self._format_list(locations, 'district')}")
        return self._build_result(f"Found {total} location(s)",
            f"Location database returned {total} records matching your search.", evidence)

    def _explain_report(self, data: dict) -> dict:
        firs = data.get("firs", [])
        stats = data.get("statistics", {})
        evidence = [f"\u2022 Report includes {len(firs)} FIR(s)"]
        if stats and isinstance(stats, dict):
            for key, val in list(stats.items())[:5]:
                if isinstance(val, (int, float, str)):
                    evidence.append(f"\u2022 {key}: {val}")
        return self._build_result(f"Generated report with {len(firs)} FIR(s)",
            f"Report compiled from {len(firs)} FIR records and associated statistics.", evidence)

    def _explain_case_summary(self, data: dict) -> dict:
        firs = data.get("firs", [])
        note = data.get("note", "")
        evidence = [f"\u2022 {len(firs)} FIR(s) in case summary"]
        if note:
            evidence.append(f"\u2022 Note: {note}")
        explanation = f"Summary generated from {len(firs)} FIR records. {note}" if note else f"Summary generated from {len(firs)} FIR records."
        return self._build_result(f"Case summary covering {len(firs)} FIR(s)", explanation, evidence)

    def _handle_default(self, data: dict) -> dict:
        keys = list(data.keys())
        evidence = []
        for key in keys[:8]:
            val = data[key]
            if isinstance(val, list):
                evidence.append(f"\u2022 {key}: {len(val)} record(s)")
            elif isinstance(val, dict):
                evidence.append(f"\u2022 {key}: {len(val)} field(s)")
            elif isinstance(val, (int, float, str)):
                evidence.append(f"\u2022 {key}: {val}")
        if not evidence:
            evidence = ["\u2022 No structured data available for explanation."]
        return self._build_result(f"Data retrieved with {len(keys)} field(s)",
            f"The response is based on {len(keys)} data fields retrieved from the database.", evidence)
