from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TransactionHistoryEntry(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction identifier")
    timestamp: str = Field(..., description="ISO 8601 timestamp when transaction occurred")
    type: str = Field(..., description="Type of transaction: transfer, payment, cash_in, cash_out, settlement, refund")
    amount: float = Field(..., description="Transaction amount in BDT")
    counterparty: str = Field(..., description="Recipient phone number, merchant ID, or agent ID")
    status: str = Field(..., description="Status: completed, failed, pending, reversed")

class TicketRequest(BaseModel):
    ticket_id: str = Field(..., description="Unique ticket identifier")
    complaint: str = Field(..., description="Customer complaint text in English, Bangla, or mixed Banglish")
    language: Optional[str] = Field(None, description="One of: en, bn, mixed")
    channel: Optional[str] = Field(None, description="One of: in_app_chat, call_center, email, merchant_portal, field_agent")
    user_type: Optional[str] = Field(None, description="One of: customer, merchant, agent, unknown")
    campaign_context: Optional[str] = None
    transaction_history: Optional[List[TransactionHistoryEntry]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
