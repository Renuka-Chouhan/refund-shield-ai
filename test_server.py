"""
RefundShield AI - Automated Integration Test Suite
Validates all asynchronous endpoints, Pydantic schemas, and error responses.
"""

import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi.testclient import TestClient
from main import app

def run_suite():
    print("\n=======================================================")
    print("[TEST] RUNNING REFUNDSHIELD AI INTEGRATION TEST SUITE")
    print("=======================================================\n")

    with TestClient(app) as client:
        # 1. Health Endpoint
        r = client.get("/api/health")
        assert r.status_code == 200, f"Health check failed: {r.text}"
        data = r.json()
        print(f"[PASS] 1. Health Status: {data['status']} | Model: {data['model_type']} | Graph Nodes: {data['graph_nodes']}")

        # 2. Benchmark Customer C0022 (High Risk)
        r = client.get("/api/customers/C0022")
        assert r.status_code == 200, f"C0022 lookup failed: {r.text}"
        d = r.json()
        print(f"[PASS] 2. Customer C0022 (High Risk): Score {d['risk_evaluation']['hybrid_risk_score']}/100 -> {d['risk_evaluation']['risk_level']} | Orders: {len(d['orders'])}")
        assert d['risk_evaluation']['risk_level'] == "High Risk"
        assert d['metrics']['total_orders'] >= 10

        # 3. Customer C0051 (From User Screenshot)
        r = client.get("/api/customers/C0051")
        assert r.status_code == 200, f"C0051 lookup failed: {r.text}"
        d51 = r.json()
        print(f"[PASS] 3. Customer C0051: Score {d51['risk_evaluation']['hybrid_risk_score']}/100 -> {d51['risk_evaluation']['risk_level']} | Returns: {d51['metrics']['total_returns']}")

        # 4. Clean Customer C0001 (Low Risk)
        r = client.get("/api/customers/C0001")
        assert r.status_code == 200, f"C0001 lookup failed: {r.text}"
        d_clean = r.json()
        print(f"[PASS] 4. Customer C0001: Score {d_clean['risk_evaluation']['hybrid_risk_score']}/100 -> {d_clean['risk_evaluation']['risk_level']} (Auto-Approve)")
        assert d_clean['risk_evaluation']['risk_level'] == "Low Risk"

        # 5. Invalid / Non-Existent Customer (Verify 404 graceful handling)
        r = client.get("/api/customers/INVALID_CUSTOMER_9999")
        assert r.status_code == 404, f"Expected 404, got {r.status_code}"
        err_res = r.json()
        print(f"[PASS] 5. Graceful 404 on Invalid ID: {err_res['error']} - {err_res['message']}")
        assert err_res['error'] == "CUSTOMER_NOT_FOUND"

        # 6. Order Lookup (O00231)
        r = client.get("/api/orders/O00231")
        assert r.status_code == 200, f"Order lookup failed: {r.text}"
        ord_data = r.json()
        print(f"[PASS] 6. Order O00231 Telemetry: Category: {ord_data['category']} | Amount: Rs. {ord_data['order_amount']}")

        # 7. Real-Time Transaction Evaluation Sandbox (POST /api/evaluate)
        eval_payload = {
            "customer_id": "C0022",
            "order_amount": 42000,
            "category": "Electronics",
            "original_weight_kg": 3.4,
            "returned_weight_kg": 0.2,
            "item_match_flag": 0.0,
            "product_condition": "Missing",
            "return_reason": "Wrong Item"
        }
        r = client.post("/api/evaluate", json=eval_payload)
        assert r.status_code == 200, f"Evaluate failed: {r.text}"
        eval_res = r.json()
        print(f"[PASS] 7. Real-Time Scoring: Score {eval_res['hybrid_risk_score']}/100 -> Action: {eval_res['recommended_action']} | Typology: {eval_res['probable_fraud_type']}")
        assert eval_res['hybrid_risk_score'] >= 75

        # 8. Boundary Validation Handling (POST with invalid order_amount <= 0)
        invalid_payload = { "order_amount": -500 }
        r = client.post("/api/evaluate", json=invalid_payload)
        assert r.status_code == 422, f"Expected 422, got {r.status_code}"
        print(f"[PASS] 8. Boundary Validation Error Handled (422): {r.json()['error']}")

        # 9. Autocomplete Search
        r = client.get("/api/search?q=C0022")
        assert r.status_code == 200
        search_items = r.json()
        assert len(search_items) > 0
        print(f"[PASS] 9. Search Autocomplete: Found {len(search_items)} matches for 'C0022' (Top: {search_items[0]['label']})")

        # 10. Dashboard HTML Web Console
        r = client.get("/")
        assert r.status_code == 200
        assert "RefundShield AI" in r.text
        assert "metricChargebacks" in r.text
        print(f"[PASS] 10. Web Console Render: {len(r.text)} bytes served cleanly.")

    print("\n=======================================================")
    print("[SUCCESS] ALL 10 INTEGRATION TESTS PASSED WITH 100% SUCCESS!")
    print("=======================================================\n")

if __name__ == "__main__":
    run_suite()
