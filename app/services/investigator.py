from datetime import datetime
from typing import Optional, List, Tuple
from app.models.request import TicketRequest, TransactionHistoryEntry
from app.models.response import EvidenceVerdict, CaseType, Severity, Department
from app.utils.helpers import extract_amounts

class InvestigatorService:
    @staticmethod
    def analyze_ticket_programmatically(request: TicketRequest) -> Tuple[Optional[str], EvidenceVerdict, CaseType, Severity, Department, bool, List[str]]:
        """
        Executes deterministic rule-based analysis to determine core fields:
        relevant_transaction_id, evidence_verdict, case_type, severity, department, human_review_required, reason_codes
        """
        complaint = request.complaint.lower()
        history = request.transaction_history or []
        reason_codes = []
        
        # 1. Phishing & Social Engineering Detection (Priority 1)
        phishing_keywords = ["otp", "pin", "password", "পাসওয়ার্ড", "পিন", "ওটিপি", "verify", "verification"]
        has_phishing_keywords = any(kw in complaint for kw in phishing_keywords)
        
        if has_phishing_keywords and ("ask" in complaint or "share" in complaint or "call" in complaint or "চাই" in complaint or "দিতে" in complaint or request.user_type == "customer"):
            # Check if this is a phishing report
            if any(term in complaint for term in ["scam", "phishing", "fake", "কল", "প্রতারণা"]):
                reason_codes.append("phishing_report")
                return (
                    None, 
                    EvidenceVerdict.INSUFFICIENT_DATA, 
                    CaseType.PHISHING_OR_SOCIAL_ENGINEERING, 
                    Severity.CRITICAL, 
                    Department.FRAUD_RISK, 
                    True, 
                    reason_codes
                )

        # Extract BDT amounts mentioned in complaint
        extracted_amounts_list = extract_amounts(request.complaint)
        
        # 2. Check for Duplicate Payment (if we have transactions)
        if len(history) >= 2:
            # Look for identical transactions (same amount, same counterparty, same type, completed status)
            # which occur within close timestamps (e.g. 5 minutes / 300 seconds)
            completed_txns = [t for t in history if t.status == "completed" and t.type == "payment"]
            for i in range(len(completed_txns)):
                for j in range(i + 1, len(completed_txns)):
                    t1 = completed_txns[i]
                    t2 = completed_txns[j]
                    if t1.amount == t2.amount and t1.counterparty == t2.counterparty:
                        # Parse timestamps
                        try:
                            time1 = datetime.fromisoformat(t1.timestamp.replace("Z", "+00:00"))
                            time2 = datetime.fromisoformat(t2.timestamp.replace("Z", "+00:00"))
                            diff = abs((time1 - time2).total_seconds())
                            # If within 10 minutes, treat as duplicate payment
                            if diff <= 600:
                                # Determine which is the duplicate (usually the later one)
                                duplicate_txn = t2 if time2 > time1 else t1
                                if duplicate_txn.amount in extracted_amounts_list or not extracted_amounts_list:
                                    reason_codes.extend(["duplicate_payment", "biller_verification_required"])
                                    return (
                                        duplicate_txn.transaction_id,
                                        EvidenceVerdict.CONSISTENT,
                                        CaseType.DUPLICATE_PAYMENT,
                                        Severity.HIGH,
                                        Department.PAYMENTS_OPS,
                                        True,
                                        reason_codes
                                    )
                        except Exception:
                            continue

        # If amounts are mentioned, attempt matching
        if extracted_amounts_list:
            target_amount = extracted_amounts_list[0]
            matching_txns = [t for t in history if abs(t.amount - target_amount) < 0.01]
            
            # If multiple matching transactions of same amount, it's ambiguous
            if len(matching_txns) > 1:
                # Except if they are duplicate payment (already handled)
                reason_codes.extend(["ambiguous_match", "needs_clarification"])
                
                # Check the transaction type of the matched entries
                txn_type = matching_txns[0].type
                if txn_type == "transfer":
                    case_type = CaseType.WRONG_TRANSFER
                    dept = Department.DISPUTE_RESOLUTION
                elif txn_type == "payment":
                    case_type = CaseType.PAYMENT_FAILED
                    dept = Department.PAYMENTS_OPS
                else:
                    case_type = CaseType.OTHER
                    dept = Department.CUSTOMER_SUPPORT
                
                # Override based on explicit keywords
                if any(kw in complaint for kw in ["wrong", "ভুল", "mistake", "send", "sent", "পাঠা", "পাঠিয়ে"]):
                    case_type = CaseType.WRONG_TRANSFER
                    dept = Department.DISPUTE_RESOLUTION
                return (
                    None,
                    EvidenceVerdict.INSUFFICIENT_DATA,
                    case_type,
                    Severity.MEDIUM,
                    dept,
                    False,
                    reason_codes
                )
            
            # If exactly one matching transaction
            elif len(matching_txns) == 1:
                txn = matching_txns[0]
                
                # Check for Cash-in issues
                if txn.type == "cash_in" and ("agent" in complaint or "এজেন্ট" in complaint or "ক্যাশ" in complaint or "cash" in complaint):
                    reason_codes.append("agent_cash_in")
                    if txn.status == "pending":
                        reason_codes.append("pending_transaction")
                    return (
                        txn.transaction_id,
                        EvidenceVerdict.CONSISTENT,
                        CaseType.AGENT_CASH_IN_ISSUE,
                        Severity.HIGH,
                        Department.AGENT_OPERATIONS,
                        True,
                        reason_codes
                    )
                
                # Check for Settlement delays (merchant)
                if txn.type == "settlement" or request.user_type == "merchant":
                    reason_codes.append("merchant_settlement")
                    if txn.status == "pending":
                        reason_codes.append("pending")
                    return (
                        txn.transaction_id,
                        EvidenceVerdict.CONSISTENT,
                        CaseType.MERCHANT_SETTLEMENT_DELAY,
                        Severity.MEDIUM,
                        Department.MERCHANT_OPERATIONS,
                        False,
                        reason_codes
                    )
                
                # Check for Wrong Transfer
                if "wrong" in complaint or "ভুল" in complaint or "mistake" in complaint or "recipient" in complaint:
                    # Verify recipient pattern in history to detect "inconsistent"
                    # If the user has transferred money to this counterparty 2 or more times,
                    # it indicates an established pattern, making "wrong transfer" inconsistent.
                    past_transfers = [t for t in history if t.counterparty == txn.counterparty and t.type == "transfer"]
                    if len(past_transfers) >= 2:
                        reason_codes.extend(["wrong_transfer_claim", "established_recipient_pattern", "evidence_inconsistent"])
                        return (
                            txn.transaction_id,
                            EvidenceVerdict.INCONSISTENT,
                            CaseType.WRONG_TRANSFER,
                            Severity.MEDIUM,
                            Department.DISPUTE_RESOLUTION,
                            True,
                            reason_codes
                        )
                    else:
                        reason_codes.extend(["wrong_transfer", "transaction_match", "dispute_initiated"])
                        return (
                            txn.transaction_id,
                            EvidenceVerdict.CONSISTENT,
                            CaseType.WRONG_TRANSFER,
                            Severity.HIGH,
                            Department.DISPUTE_RESOLUTION,
                            True,
                            reason_codes
                        )
                
                # Check for Failed Payment (balance deducted)
                if txn.status == "failed" and ("deduct" in complaint or "কেটে" in complaint or "balance" in complaint or "fail" in complaint):
                    reason_codes.extend(["payment_failed", "potential_balance_deduction"])
                    return (
                        txn.transaction_id,
                        EvidenceVerdict.CONSISTENT,
                        CaseType.PAYMENT_FAILED,
                        Severity.HIGH,
                        Department.PAYMENTS_OPS,
                        False,
                        reason_codes
                    )
                
                # Check for Refund Request
                if "refund" in complaint or "ফেরত" in complaint or "want money back" in complaint:
                    reason_codes.extend(["refund_request", "merchant_policy_dependent"])
                    return (
                        txn.transaction_id,
                        EvidenceVerdict.CONSISTENT,
                        CaseType.REFUND_REQUEST,
                        Severity.LOW,
                        Department.CUSTOMER_SUPPORT,
                        False,
                        reason_codes
                    )
                
                # Fallback for single match
                reason_codes.append("transaction_match")
                return (
                    txn.transaction_id,
                    EvidenceVerdict.CONSISTENT,
                    CaseType.OTHER,
                    Severity.LOW,
                    Department.CUSTOMER_SUPPORT,
                    False,
                    reason_codes
                )

        # 3. Phishing Check (Fallback if not caught in priority 1)
        if "otp" in complaint or "pin" in complaint or "password" in complaint or "পিন" in complaint or "ওটিপি" in complaint:
            reason_codes.extend(["phishing", "credential_protection", "critical_escalation"])
            return (
                None,
                EvidenceVerdict.INSUFFICIENT_DATA,
                CaseType.PHISHING_OR_SOCIAL_ENGINEERING,
                Severity.CRITICAL,
                Department.FRAUD_RISK,
                True,
                reason_codes
            )

        # 4. General Vague / Other Cases
        reason_codes.extend(["vague_complaint", "needs_clarification"])
        return (
            None,
            EvidenceVerdict.INSUFFICIENT_DATA,
            CaseType.OTHER,
            Severity.LOW,
            Department.CUSTOMER_SUPPORT,
            False,
            reason_codes
        )
