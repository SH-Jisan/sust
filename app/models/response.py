from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class EvidenceVerdict(str, Enum):
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    INSUFFICIENT_DATA = "insufficient_data"

class CaseType(str, Enum):
    WRONG_TRANSFER = "wrong_transfer"
    PAYMENT_FAILED = "payment_failed"
    REFUND_REQUEST = "refund_request"
    DUPLICATE_PAYMENT = "duplicate_payment"
    MERCHANT_SETTLEMENT_DELAY = "merchant_settlement_delay"
    AGENT_CASH_IN_ISSUE = "agent_cash_in_issue"
    PHISHING_OR_SOCIAL_ENGINEERING = "phishing_or_social_engineering"
    OTHER = "other"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Department(str, Enum):
    CUSTOMER_SUPPORT = "customer_support"
    DISPUTE_RESOLUTION = "dispute_resolution"
    PAYMENTS_OPS = "payments_ops"
    MERCHANT_OPERATIONS = "merchant_operations"
    AGENT_OPERATIONS = "agent_operations"
    FRAUD_RISK = "fraud_risk"

class TicketResponse(BaseModel):
    ticket_id: str = Field(..., description="Must match the value sent in the request")
    relevant_transaction_id: Optional[str] = Field(..., description="Transaction ID from history or null")
    evidence_verdict: EvidenceVerdict = Field(..., description="Verdict based on transaction data comparison")
    case_type: CaseType = Field(..., description="Case category classification")
    severity: Severity = Field(..., description="Urgency / risk priority level")
    department: Department = Field(..., description="Department designated to handle this case")
    agent_summary: str = Field(..., description="Concise 1-2 sentence case summary")
    recommended_next_action: str = Field(..., description="Actionable next step recommendation for agents")
    customer_reply: str = Field(..., description="Safe official reply text drafted for the client")
    human_review_required: bool = Field(..., description="Toggled true for disputes, suspicious or high-risk cases")
    confidence: Optional[float] = Field(None, description="Float between 0 and 1 representing confidence level")
    reason_codes: Optional[List[str]] = Field(None, description="Short labels supporting decision justifications")
