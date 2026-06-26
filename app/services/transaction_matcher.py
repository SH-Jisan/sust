from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from app.models.request import TransactionHistoryEntry
from app.models.response import CaseType, EvidenceVerdict

class TransactionMatcher:
    @staticmethod
    def match(facts: Dict[str, Any], history: List[TransactionHistoryEntry]) -> Dict[str, Any]:
        """
        Scores and matches transaction history against semantic facts.
        Returns a dictionary containing the best matched transaction, relevant transaction ID,
        ambiguity flag, match confidence, and reasons.
        """
        if not history:
            return {
                "matched_transaction": None,
                "relevant_transaction_id": None,
                "is_ambiguous": False,
                "ambiguity_reason": "empty_history",
                "match_confidence": 0.0,
                "reason_codes": ["no_transactions"]
            }

        case_type = facts["case_type_hint"]
        mentioned_id = facts["mentioned_transaction_id"]
        mentioned_amount = facts["mentioned_amount"]
        mentioned_party = facts["mentioned_counterparty"]

        # Special Case: Duplicate Payment Detection (Priority 1)
        if case_type == CaseType.DUPLICATE_PAYMENT:
            # Find identical transactions (same amount, same counterparty, type='payment', status='completed')
            completed_payments = [t for t in history if t.type == "payment" and t.status == "completed"]
            duplicate_pairs = []
            
            for i in range(len(completed_payments)):
                for j in range(i + 1, len(completed_payments)):
                    t1 = completed_payments[i]
                    t2 = completed_payments[j]
                    if t1.amount == t2.amount and t1.counterparty == t2.counterparty:
                        try:
                            time1 = datetime.fromisoformat(t1.timestamp.replace("Z", "+00:00"))
                            time2 = datetime.fromisoformat(t2.timestamp.replace("Z", "+00:00"))
                            diff = abs((time1 - time2).total_seconds())
                            # Within 10 minutes
                            if diff <= 600:
                                # Pick the second (later) transaction as the duplicate
                                duplicate_txn = t2 if time2 > time1 else t1
                                duplicate_pairs.append((duplicate_txn, diff))
                        except Exception:
                            continue
            if duplicate_pairs:
                # Sort by smallest time difference or latest timestamp
                duplicate_txn = duplicate_pairs[0][0]
                return {
                    "matched_transaction": duplicate_txn,
                    "relevant_transaction_id": duplicate_txn.transaction_id,
                    "is_ambiguous": False,
                    "match_confidence": 0.95,
                    "reason_codes": ["duplicate_payment_matched"]
                }

        # General scoring algorithm
        scored_txns: List[Tuple[TransactionHistoryEntry, float]] = []
        
        for txn in history:
            score = 0.0
            
            # 1. Exact transaction ID match (Highest weight)
            if mentioned_id and txn.transaction_id.lower() == mentioned_id.lower():
                score += 100.0
                
            # 2. Amount match
            if mentioned_amount and abs(txn.amount - mentioned_amount) < 0.01:
                score += 40.0
                
            # 3. Type mapping match
            if case_type == CaseType.WRONG_TRANSFER and txn.type == "transfer":
                score += 30.0
            elif case_type == CaseType.PAYMENT_FAILED and txn.type in ["payment", "transfer"]:
                score += 30.0
            elif case_type == CaseType.REFUND_REQUEST and txn.type == "payment":
                score += 30.0
            elif case_type == CaseType.AGENT_CASH_IN_ISSUE and txn.type == "cash_in":
                score += 30.0
            elif case_type == CaseType.MERCHANT_SETTLEMENT_DELAY and txn.type == "settlement":
                score += 30.0
                
            # 4. Status match based on issue type
            if case_type == CaseType.PAYMENT_FAILED and txn.status == "failed":
                score += 20.0
            elif case_type == CaseType.AGENT_CASH_IN_ISSUE and txn.status == "pending":
                score += 20.0
            elif case_type == CaseType.MERCHANT_SETTLEMENT_DELAY and txn.status == "pending":
                score += 20.0
                
            # 5. Counterparty match
            if mentioned_party and (mentioned_party.lower() in txn.counterparty.lower() or txn.counterparty.lower() in mentioned_party.lower()):
                score += 30.0
                
            if score > 0:
                scored_txns.append((txn, score))

        if not scored_txns:
            return {
                "matched_transaction": None,
                "relevant_transaction_id": None,
                "is_ambiguous": False,
                "match_confidence": 0.0,
                "reason_codes": ["no_matching_transaction"]
            }

        # Sort scored transactions by score descending
        scored_txns.sort(key=lambda x: x[1], reverse=True)
        max_score = scored_txns[0][1]
        
        # Check for ambiguity: are there multiple transactions with the same maximum score?
        highest_matches = [item for item in scored_txns if abs(item[1] - max_score) < 0.01]
        
        if len(highest_matches) > 1:
            # Ambiguity detected
            return {
                "matched_transaction": None,
                "relevant_transaction_id": None,
                "is_ambiguous": True,
                "ambiguity_reason": "multiple_plausible_matches",
                "match_confidence": 0.5,
                "reason_codes": ["ambiguous_match", "multiple_transactions_found"]
            }
            
        best_match, score = highest_matches[0]
        
        # We require a minimum confidence score threshold (e.g., must match at least amount or ID)
        if score < 40.0:
            return {
                "matched_transaction": None,
                "relevant_transaction_id": None,
                "is_ambiguous": False,
                "match_confidence": 0.2,
                "reason_codes": ["low_confidence_match"]
            }
            
        return {
            "matched_transaction": best_match,
            "relevant_transaction_id": best_match.transaction_id,
            "is_ambiguous": False,
            "match_confidence": min(score / 140.0, 1.0),
            "reason_codes": ["transaction_matched"]
        }
