from typing import List, Optional, Dict, Any, Tuple
from app.models.request import TransactionHistoryEntry
from app.models.response import CaseType, EvidenceVerdict

class EvidenceService:
    @staticmethod
    def decide(
        facts: Dict[str, Any],
        match_result: Dict[str, Any],
        history: List[TransactionHistoryEntry]
    ) -> Tuple[EvidenceVerdict, CaseType, Optional[str]]:
        """
        Investigates the ledger evidence to decide:
        - evidence_verdict
        - final case_type
        - relevant_transaction_id
        """
        case_type = facts["case_type_hint"]
        matched_txn = match_result["matched_transaction"]
        relevant_id = match_result["relevant_transaction_id"]
        is_ambiguous = match_result.get("is_ambiguous", False)

        # 1. Phishing & Social Engineering (No transaction required)
        if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
            return EvidenceVerdict.INSUFFICIENT_DATA, CaseType.PHISHING_OR_SOCIAL_ENGINEERING, None

        # 2. Ambiguity or Vague complaints
        if is_ambiguous or case_type == CaseType.OTHER or not history:
            return EvidenceVerdict.INSUFFICIENT_DATA, case_type, None

        # 3. No match found in history
        if not matched_txn:
            return EvidenceVerdict.INSUFFICIENT_DATA, case_type, None

        # 4. Wrong Transfer Case Verification
        if case_type == CaseType.WRONG_TRANSFER:
            # Check for established recipient pattern in history
            # If there are 2 or more prior transfers to this counterparty, the claim is inconsistent
            counterparty = matched_txn.counterparty
            past_transfers = [t for t in history if t.counterparty == counterparty and t.type == "transfer" and t.status == "completed"]
            
            if len(past_transfers) >= 2:
                return EvidenceVerdict.INCONSISTENT, CaseType.WRONG_TRANSFER, relevant_id
            return EvidenceVerdict.CONSISTENT, CaseType.WRONG_TRANSFER, relevant_id

        # 5. Payment Failed Case Verification
        if case_type == CaseType.PAYMENT_FAILED:
            # Consistent if the matched transaction is failed or pending
            # Inconsistent if it is completed or reversed (conflicts with customer's claim of failure)
            if matched_txn.status in ["failed", "pending"]:
                return EvidenceVerdict.CONSISTENT, CaseType.PAYMENT_FAILED, relevant_id
            return EvidenceVerdict.INCONSISTENT, CaseType.PAYMENT_FAILED, relevant_id

        # 6. Duplicate Payment Case Verification
        if case_type == CaseType.DUPLICATE_PAYMENT:
            # Duplicate detection returned a match, so it's consistent
            return EvidenceVerdict.CONSISTENT, CaseType.DUPLICATE_PAYMENT, relevant_id

        # 7. Agent Cash-in Issue Verification
        if case_type == CaseType.AGENT_CASH_IN_ISSUE:
            if matched_txn.status in ["pending", "failed"]:
                return EvidenceVerdict.CONSISTENT, CaseType.AGENT_CASH_IN_ISSUE, relevant_id
            # If agent cash-in is already completed in ledger, but user complains they didn't get it:
            # We flag consistent for investigation of ledger delivery delay
            return EvidenceVerdict.CONSISTENT, CaseType.AGENT_CASH_IN_ISSUE, relevant_id

        # 8. Merchant Settlement Delay Verification
        if case_type == CaseType.MERCHANT_SETTLEMENT_DELAY:
            if matched_txn.status in ["pending", "failed"]:
                return EvidenceVerdict.CONSISTENT, CaseType.MERCHANT_SETTLEMENT_DELAY, relevant_id
            return EvidenceVerdict.CONSISTENT, CaseType.MERCHANT_SETTLEMENT_DELAY, relevant_id

        # Default fallback
        return EvidenceVerdict.CONSISTENT, case_type, relevant_id
