"""
End-to-End Chat Tests — Verifies the Hybrid SQL + LLM architecture.

Tests both SQL-only queries (no AI) and SQL+AI queries (with Gemini summarization).

Prerequisites:
    1. Backend server running on localhost:8000
    2. Test data seeded (run seed_test_data.py first)
    3. JWT token obtained from login

Usage:
    cd scripts && python test_chat_e2e.py
"""

import asyncio
import json
import sys

import httpx

API_BASE = "http://localhost:8000/api/v1"
TEST_USER = {"email": "arjun.kumar@ksp.gov.in", "password": "Police@123"}

PASS = "✅"
FAIL = "❌"


class ChatTester:
    """Tests the chat endpoint with various query types."""

    def __init__(self):
        self.token: Optional[str] = None
        self.conversation_id: Optional[str] = None
        self.results = {"passed": 0, "failed": 0, "skipped": 0, "tests": []}

    async def login(self) -> bool:
        """Login and obtain JWT token."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{API_BASE}/auth/login",
                    json=TEST_USER,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.token = data.get("access_token", "")
                    print(f"{PASS} Login successful — got JWT token")
                    return True
                else:
                    print(f"{FAIL} Login failed: {resp.status_code} - {resp.text}")
                    return False
        except httpx.ConnectError:
            print(f"{FAIL} Cannot connect to backend at {API_BASE}")
            print(f"   Make sure the backend server is running!")
            return False
        except Exception as e:
            print(f"{FAIL} Login error: {e}")
            return False

    async def send_chat(self, message: str, expect_sql_only: bool = False) -> dict:
        """Send a chat message and return the response."""
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"message": message}
        if self.conversation_id:
            payload["conversation_id"] = self.conversation_id

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{API_BASE}/chat/message",
                json=payload,
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                # Save conversation_id for follow-ups
                if not self.conversation_id:
                    self.conversation_id = data.get("conversation_id", "")
                return data
            else:
                return {"error": f"HTTP {resp.status_code}: {resp.text}", "status": "error"}

    def check_response(self, data: dict, test_name: str, expected_fields: list[str] = None) -> bool:
        """Validate response structure."""
        if "response" not in data or "conversation_id" not in data:
            error_msg = data.get("error", data.get("detail", "Unknown error format"))
            print(f"  {FAIL} {test_name}: {error_msg}")
            return False

        if expected_fields:
            missing = [f for f in expected_fields if f not in data]
            if missing:
                print(f"  {FAIL} {test_name}: Missing fields: {missing}")
                print(f"    Response keys: {list(data.keys())}")
                return False

        # Check for the new structured response fields
        if "success" in data and "intent" in data and "data" in data:
            intent = data.get("intent", "unknown")
            summary = data.get("summary")
            suggestions = data.get("suggestions", [])
            print(f"  {PASS} Intent: {intent} | Summary: {'Yes' if summary else 'No'} | Suggestions: {len(suggestions)}")
        elif "response" in data:
            resp_preview = data["response"][:80] + "..." if len(data.get("response", "")) > 80 else data.get("response", "")
            print(f"  {PASS} Response: {resp_preview}")
        else:
            print(f"  {FAIL} {test_name}: Unknown response format")
            return False

        return True

    async def run_test(self, name: str, message: str, expected_fields: list[str] = None, is_ai: bool = False):
        """Run a single test and record results."""
        print(f"\n  📤 Query: \"{message}\"")
        data = await self.send_chat(message)
        success = self.check_response(data, name, expected_fields)
        if success:
            self.results["passed"] += 1
            self.results["tests"].append({"name": name, "passed": True, "ai": is_ai})
        else:
            self.results["failed"] += 1
            self.results["tests"].append({"name": name, "passed": False, "ai": is_ai})

    async def run_all(self):
        """Run all test queries."""
        print("=" * 70)
        print("🧪 Crime Intelligence Platform — Chat E2E Tests")
        print("=" * 70)

        # ── Login ───────────────────────────────────────────────
        print("\n" + "-" * 70)
        print("🔑 Authentication")
        print("-" * 70)
        if not await self.login():
            print(f"\n{FAIL} Cannot proceed without authentication. Start the backend first.")
            return

        # ── SQL-only Queries (No AI) ────────────────────────────
        print("\n" + "-" * 70)
        print("📊 SQL-only Queries (No AI — data from MySQL only)")
        print("-" * 70)

        # 1. Show FIR
        await self.run_test(
            "FIR Search",
            "Show FIR FIR2026001",
            expected_fields=["response", "conversation_id"],
        )

        # 2. Search victims
        await self.run_test(
            "Victim Search",
            "Show victims for FIR2026001",
            expected_fields=["response", "conversation_id"],
        )

        # 3. Search accused
        await self.run_test(
            "Accused Search",
            "Show accused in FIR2026001",
            expected_fields=["response", "conversation_id"],
        )

        # 4. Search evidence
        await self.run_test(
            "Evidence Search",
            "Show evidence for FIR2026001",
            expected_fields=["response", "conversation_id"],
        )

        # 5. Financial transactions
        await self.run_test(
            "Financial Search",
            "Show financial transactions for FIR2026001",
            expected_fields=["response", "conversation_id"],
        )

        # 6. Crime history
        await self.run_test(
            "Crime History Search",
            "Show crime history of Suresh Kumar",
            expected_fields=["response", "conversation_id"],
        )

        # 7. Hotspot search
        await self.run_test(
            "Hotspot Search",
            "Show hotspot near MG Road",
            expected_fields=["response", "conversation_id"],
        )

        # 8. Audit logs
        await self.run_test(
            "Audit Log Search",
            "Show audit logs for today",
            expected_fields=["response", "conversation_id"],
        )

        # 9. Criminal network
        await self.run_test(
            "Network Search",
            "Show criminal network connections",
            expected_fields=["response", "conversation_id"],
        )

        # 10. Help
        await self.run_test(
            "Help",
            "What can you do?",
            expected_fields=["response", "conversation_id"],
        )

        # ── SQL + AI Queries (With Gemini Summarization) ───────
        print("\n" + "-" * 70)
        print("🧠 SQL + AI Queries (Data from MySQL → Gemini summary)")
        print("-" * 70)

        # 11. Summarize FIR
        await self.run_test(
            "FIR Summary",
            "Summarize FIR2026001",
            expected_fields=["response", "conversation_id"],
            is_ai=True,
        )

        # 12. Explain evidence
        await self.run_test(
            "Evidence Explanation",
            "Explain the evidence collected for FIR2026001",
            expected_fields=["response", "conversation_id"],
            is_ai=True,
        )

        # 13. Analyze transaction
        await self.run_test(
            "Financial Analysis",
            "Analyze the suspicious transactions in FIR2026001",
            expected_fields=["response", "conversation_id"],
            is_ai=True,
        )

        # 14. Explain network
        await self.run_test(
            "Network Analysis",
            "Explain the criminal network connections",
            expected_fields=["response", "conversation_id"],
            is_ai=True,
        )

        # 15. Summarize accused
        await self.run_test(
            "Accused Summary",
            "Summarize the accused profile of Suresh Kumar",
            expected_fields=["response", "conversation_id"],
            is_ai=True,
        )

        # 16. Hotspot analysis
        await self.run_test(
            "Hotspot Analysis",
            "Why is MG Road a hotspot?",
            expected_fields=["response", "conversation_id"],
            is_ai=True,
        )

        # 17. Case summary
        await self.run_test(
            "Case Summary",
            "Generate a case summary for FIR2026001",
            expected_fields=["response", "conversation_id"],
            is_ai=True,
        )

        # 18. Report generation
        await self.run_test(
            "Report Generation",
            "Generate a crime report for Bengaluru",
            expected_fields=["response", "conversation_id"],
            is_ai=True,
        )

        # 19. Crime prediction
        await self.run_test(
            "Crime Prediction",
            "Predict crime trends for next month",
            expected_fields=["response", "conversation_id"],
            is_ai=True,
        )

        # 20. Investigation assistance
        await self.run_test(
            "Investigation Assistance",
            "What are the key findings in this investigation?",
            expected_fields=["response", "conversation_id"],
            is_ai=True,
        )

        # ── Error Handling Tests ────────────────────────────────
        print("\n" + "-" * 70)
        print("⚠️  Error Handling Tests")
        print("-" * 70)

        # 21. Empty message (should return 422)
        print(f"\n  📤 Query: \"\" (empty message)")
        headers = {"Authorization": f"Bearer {self.token}"}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{API_BASE}/chat/message",
                json={"message": ""},
                headers=headers,
            )
            if resp.status_code == 422:
                print(f"  {PASS} Empty message correctly rejected with 422")
                self.results["passed"] += 1
            else:
                print(f"  {FAIL} Expected 422, got {resp.status_code}")
                self.results["failed"] += 1

        # 22. Very long message (should return 422)
        print(f"\n  📤 Query: (2001 chars — exceeds max length)")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{API_BASE}/chat/message",
                json={"message": "x" * 2001},
                headers=headers,
            )
            if resp.status_code == 422:
                print(f"  {PASS} Long message correctly rejected with 422")
                self.results["passed"] += 1
            else:
                print(f"  {FAIL} Expected 422, got {resp.status_code}")
                self.results["failed"] += 1

        # 23. No JWT (should return 401)
        print(f"\n  📤 Query: (no auth token)")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{API_BASE}/chat/message",
                json={"message": "Hello"},
            )
            if resp.status_code == 401:
                print(f"  {PASS} No-auth request correctly rejected with 401")
                self.results["passed"] += 1
            else:
                print(f"  {FAIL} Expected 401, got {resp.status_code}")
                self.results["failed"] += 1

        # ── Summary ─────────────────────────────────────────────
        print("\n" + "=" * 70)
        passed = self.results["passed"]
        failed = self.results["failed"]
        total = passed + failed
        print(f"📊 Test Results: {PASS} {passed}/{total} passed | {FAIL} {failed}/{total} failed")
        print("=" * 70)

        if failed > 0:
            print("\n❌ Some tests failed. Check the output above for details.")
            sys.exit(1)
        else:
            print("\n🎉 All tests passed! The Hybrid SQL + LLM architecture is working correctly.")
            print("   Data flows: MySQL → Service → (optional Gemini) → Response Builder → User")


if __name__ == "__main__":
    tester = ChatTester()
    asyncio.run(tester.run_all())
