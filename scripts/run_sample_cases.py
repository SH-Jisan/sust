import os
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_all_cases():
    sample_file_path = os.path.join("description & example", "SUST_Preli_Sample_Cases.json")
    if not os.path.exists(sample_file_path):
        sample_file_path = os.path.join("d:\\sust", sample_file_path)

    print("=" * 80)
    print("QUEUESTORM INVESTIGATOR — SAMPLE PACK RUNNER")
    print("=" * 80)
    
    with open(sample_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    cases = data["cases"]
    
    for case in cases:
        case_id = case["id"]
        label = case["label"]
        input_data = case["input"]
        
        response = client.post("/analyze-ticket", json=input_data)
        if response.status_code != 200:
            print(f"[-] Case {case_id} failed with code {response.status_code}")
            continue
            
        res = response.json()
        print(f"\n[+] CASE: {case_id} — {label}")
        print(f"    - Complaint Summary: {res['agent_summary']}")
        print(f"    - Case Type: {res['case_type']}")
        print(f"    - Verdict: {res['evidence_verdict']} (Txn ID: {res['relevant_transaction_id']})")
        print(f"    - Department: {res['department']} (Severity: {res['severity']})")
        print(f"    - Human Review Required: {res['human_review_required']}")
        print(f"    - Safe Reply: {res['customer_reply']}")
        print("-" * 50)
        
    print("\nAll cases processed successfully.")

if __name__ == "__main__":
    run_all_cases()
