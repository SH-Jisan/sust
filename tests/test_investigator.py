import os
import json
import pytest
from app.models.request import TicketRequest
from app.services.investigator import InvestigatorService

def test_programmatic_investigator_on_samples():
    # Construct path to the sample cases pack
    sample_file_path = os.path.join("d:\\sust", "description & example", "SUST_Preli_Sample_Cases.json")
    
    with open(sample_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    cases = data["cases"]
    
    for case in cases:
        case_id = case["id"]
        label = case["label"]
        input_data = case["input"]
        expected = case["expected_output"]
        
        # Parse into request model
        req = TicketRequest(**input_data)
        
        # Analyze
        res_txn_id, res_verdict, res_case_type, res_severity, res_dept, res_hr, res_reasons = \
            InvestigatorService.analyze_ticket_programmatically(req)
            
        # Assertions
        assert res_txn_id == expected["relevant_transaction_id"], f"Case {case_id} ({label}) txn ID mismatch: got {res_txn_id}, expected {expected['relevant_transaction_id']}"
        assert res_verdict == expected["evidence_verdict"], f"Case {case_id} ({label}) verdict mismatch: got {res_verdict}, expected {expected['evidence_verdict']}"
        assert res_case_type == expected["case_type"], f"Case {case_id} ({label}) case type mismatch: got {res_case_type}, expected {expected['case_type']}"
        assert res_dept == expected["department"], f"Case {case_id} ({label}) department mismatch: got {res_dept}, expected {expected['department']}"
        assert res_severity == expected["severity"], f"Case {case_id} ({label}) severity mismatch: got {res_severity}, expected {expected['severity']}"
        assert res_hr == expected["human_review_required"], f"Case {case_id} ({label}) human review mismatch: got {res_hr}, expected {expected['human_review_required']}"
