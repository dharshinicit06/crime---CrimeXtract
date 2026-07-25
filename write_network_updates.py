"""Updates to network_analysis/services.py to add Vehicle extraction and broader phone scanning."""

import os

svc_path = "app/network_analysis/services.py"

# Read the current file
with open(svc_path, "r") as f:
    content = f.read()

# Add Evidence import after the existing imports
old_imports = "from app.financial_transaction.models import FinancialTransaction\nfrom app.location.models import Location"
new_imports = "from app.evidence.models import Evidence\nfrom app.financial_transaction.models import FinancialTransaction\nfrom app.location.models import Location"
content = content.replace(old_imports, new_imports)

# Add a _extract_vehicles method after _extract_phones
old_phone_method = """    def _extract_phones(self, text_val: str | None) -> list[str]:
        \"\"\"Extract Indian phone numbers from text.\"\"\"
        if not text_val:
            return []
        pattern = r'\\b[6789]\\d{9}\\b'
        return list(set(re.findall(pattern, text_val)))
"""

new_phone_method = """    def _extract_phones(self, text_val: str | None) -> list[str]:
        \"\"\"Extract Indian phone numbers from text.\"\"\"
        if not text_val:
            return []
        pattern = r'\\b[6789]\\d{9}\\b'
        return list(set(re.findall(pattern, text_val)))

    _VEHICLE_PATTERNS = [
        r'\\b[A-Z]{2}[ -]?[0-9]{1,2}[ -]?[A-Z]{1,2}[ -]?[0-9]{1,4}\\b',  # Indian plates: MH-12-AB-1234
        r'\\bvehicle[ :#]?([A-Z0-9 -]+)\\b',
        r'\\breg[ :]?(?:no|number)[ :]?([A-Z0-9 -]+)\\b',
        r'\\b(?:car|bike|motorcycle|scooter|van|truck|auto)\\b',
    ]

    def _extract_vehicles(self, text_val: str | None) -> list[str]:
        \"\"\"Extract vehicle references from text (license plates, vehicle types).\"\"\"
        if not text_val:
            return []
        found = []
        for pattern in self._VEHICLE_PATTERNS:
            matches = re.findall(pattern, text_val, re.IGNORECASE)
            found.extend([m.strip().upper() for m in matches if m.strip()])
        return list(set(found))
"""

content = content.replace(old_phone_method, new_phone_method)

# Add phone extraction from accused fields after the accused edge creation
old_accused_loop_close = """                self._add_edge(
                    f\"fir:{link.fir_id}\", nid, \"has_accused\",
                    metadata={\"role\": link.role},
                )
"""

new_accused_loop_close = """                self._add_edge(
                    f\"fir:{link.fir_id}\", nid, \"has_accused\",
                    metadata={\"role\": link.role},
                )

            # Extract phones from accused fields
            for accused in accused_map.values():
                anid = f\"accused:{accused.id}\"
                # Only add phone edges if the node was actually created (it was linked)
                if anid not in self.nodes:
                    continue
                phones = self._extract_phones(accused.address) + self._extract_phones(accused.alias)
                for phone in phones:
                    pid = f\"phone:{phone}\"
                    self._add_node(pid, phone, \"phone\", \"contact\", {\"source\": f\"accused:{accused.id}\"})
                    self._add_edge(anid, pid, \"has_phone\")
"""

content = content.replace(old_accused_loop_close, new_accused_loop_close)

# Add Vehicle extraction from evidence after the Crime section and before Financial Transactions
old_crime_section_end = """        # --- 6. Load Financial Transactions (Bank Accounts) ---"""
new_crime_section_end = """        # --- 6. Extract Vehicle references from Evidence ---
        r = await self.session.execute(
            select(Evidence).where(Evidence.fir_id.in_(fir_ids))
        )
        evidence_items = list(r.scalars().all())
        for ev in evidence_items:
            vehicles = self._extract_vehicles(ev.name) + self._extract_vehicles(ev.description) + self._extract_vehicles(ev.notes)
            for v in vehicles:
                vid = f"vehicle:{v}"
                self._add_node(vid, v, "vehicle", "asset", {"source": f"evidence:{ev.id}"})
                self._add_edge(f"fir:{ev.fir_id}", vid, "has_vehicle_evidence")

        # --- 7. Load Financial Transactions (Bank Accounts) ---"""

content = content.replace(old_crime_section_end, new_crime_section_end)

with open(svc_path, "w") as f:
    f.write(content)

print("services.py updated successfully")
