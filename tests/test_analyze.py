import os
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_analyze_ticket_validation_error_400():
    # missing required complaint
    response = client.post("/analyze-ticket", json={"ticket_id": "TKT-TEST"})
    assert response.status_code == 400
    assert "Malformed input" in response.json()["error"]

def test_analyze_ticket_semantic_error_422():
    # empty complaint
    response = client.post("/analyze-ticket", json={"ticket_id": "TKT-TEST", "complaint": "   "})
    assert response.status_code == 422
    assert "Unprocessable Entity" in response.json()["error"]

def test_analyze_ticket_sample_cases():
    sample_file_path = os.path.join("d:\\sust", "description & example", "SUST_Preli_Sample_Cases.json")
    
    with open(sample_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    cases = data["cases"]
    
    for case in cases:
        case_id = case["id"]
        label = case["label"]
        input_data = case["input"]
        expected = case["expected_output"]
        
        response = client.post("/analyze-ticket", json=input_data)
        assert response.status_code == 200, f"Case {case_id} failed with status {response.status_code}"
        
        res_body = response.json()
        
        # Verify schema correctness (no missing fields, correct keys)
        required_fields = [
            "ticket_id", "relevant_transaction_id", "evidence_verdict", 
            "case_type", "severity", "department", "agent_summary", 
            "recommended_next_action", "customer_reply", "human_review_required"
        ]
        for field in required_fields:
            assert field in res_body, f"Case {case_id} response missing required field: {field}"
            
        # Verify matching logic values
        assert res_body["ticket_id"] == expected["ticket_id"]
        assert res_body["relevant_transaction_id"] == expected["relevant_transaction_id"], \
            f"Case {case_id} ({label}) txn ID mismatch: got {res_body['relevant_transaction_id']}, expected {expected['relevant_transaction_id']}"
        assert res_body["evidence_verdict"] == expected["evidence_verdict"], \
            f"Case {case_id} ({label}) verdict mismatch: got {res_body['evidence_verdict']}, expected {expected['evidence_verdict']}"
        assert res_body["case_type"] == expected["case_type"], \
            f"Case {case_id} ({label}) case type mismatch: got {res_body['case_type']}, expected {expected['case_type']}"
        assert res_body["department"] == expected["department"], \
            f"Case {case_id} ({label}) department mismatch: got {res_body['department']}, expected {expected['department']}"
        assert res_body["severity"] == expected["severity"], \
            f"Case {case_id} ({label}) severity mismatch: got {res_body['severity']}, expected {expected['severity']}"
        assert res_body["human_review_required"] == expected["human_review_required"], \
            f"Case {case_id} ({label}) human review mismatch: got {res_body['human_review_required']}, expected {expected['human_review_required']}"
            
        # Safety rules verification
        reply = res_body["customer_reply"]
        action = res_body["recommended_next_action"]
        
        # 1. No PIN/OTP requests
        assert not any(w in reply.lower() for w in ["please share your pin", "please provide your otp", "give your password"]), \
            f"Case {case_id} reply contains credential requests: {reply}"
        # 2. No direct refund promises
        assert not any(w in reply.lower() for w in ["we will refund you", "refund confirmed"]), \
            f"Case {case_id} reply promises direct refund: {reply}"
        # 3. Next action safety check
        assert not any(w in action.lower() for w in ["refund immediately", "confirm refund"]), \
            f"Case {case_id} action directs immediate refund: {action}"
