from app.models.response import CaseType, EvidenceVerdict, Severity, Department

class RoutingService:
    @staticmethod
    def route(case_type: CaseType, verdict: EvidenceVerdict, match_result: dict) -> tuple[Department, Severity, bool]:
        """
        Calculates:
        - department
        - severity
        - human_review_required
        """
        # 1. Department Routing
        dept_map = {
            CaseType.WRONG_TRANSFER: Department.DISPUTE_RESOLUTION,
            CaseType.PAYMENT_FAILED: Department.PAYMENTS_OPS,
            CaseType.REFUND_REQUEST: Department.CUSTOMER_SUPPORT,
            CaseType.DUPLICATE_PAYMENT: Department.PAYMENTS_OPS,
            CaseType.MERCHANT_SETTLEMENT_DELAY: Department.MERCHANT_OPERATIONS,
            CaseType.AGENT_CASH_IN_ISSUE: Department.AGENT_OPERATIONS,
            CaseType.PHISHING_OR_SOCIAL_ENGINEERING: Department.FRAUD_RISK,
            CaseType.OTHER: Department.CUSTOMER_SUPPORT
        }
        dept = dept_map.get(case_type, Department.CUSTOMER_SUPPORT)

        # 2. Severity Classification
        if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
            severity = Severity.CRITICAL
        elif verdict == EvidenceVerdict.INCONSISTENT:
            severity = Severity.MEDIUM
        elif case_type in [CaseType.WRONG_TRANSFER, CaseType.PAYMENT_FAILED, CaseType.DUPLICATE_PAYMENT, CaseType.AGENT_CASH_IN_ISSUE]:
            severity = Severity.HIGH
        elif case_type == CaseType.MERCHANT_SETTLEMENT_DELAY:
            severity = Severity.MEDIUM
        elif match_result.get("is_ambiguous", False):
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        # 3. Human Review Required Flag
        if case_type in [CaseType.WRONG_TRANSFER, CaseType.PHISHING_OR_SOCIAL_ENGINEERING, CaseType.DUPLICATE_PAYMENT, CaseType.AGENT_CASH_IN_ISSUE]:
            human_review = True
        elif verdict == EvidenceVerdict.INCONSISTENT:
            human_review = True
        elif match_result.get("is_ambiguous", False):
            # Ambiguous matches should be resolved by a human agent
            human_review = True
        else:
            human_review = False

        return dept, severity, human_review
