from fastapi import APIRouter, HTTPException, status
from app.models.request import TicketRequest
from app.models.response import TicketResponse
from app.utils.language import detect_is_bangla
from app.services.investigator import InvestigatorService
from app.services.llm_client import LLMClientService
from app.services.safety_filter import SafetyFilterService

router = APIRouter()

@router.post("/analyze-ticket", response_model=TicketResponse)
async def analyze_ticket(request: TicketRequest):
    # 1. Semantic Validation
    complaint_stripped = request.complaint.strip() if request.complaint else ""
    if not complaint_stripped:
        raise ValueError("Complaint text cannot be empty.")

    # 2. Language Detection
    is_bangla = detect_is_bangla(request.complaint)

    # 3. Core Programmatic Investigation (Verdicts, IDs, Enums)
    relevant_txn_id, verdict, case_type, severity, department, human_review, reason_codes = \
        InvestigatorService.analyze_ticket_programmatically(request)

    # 4. Generate Support Text (LLM with Fallback)
    summary, recommended_action, customer_reply = await LLMClientService.generate_support_text(
        complaint=request.complaint,
        case_type=case_type,
        verdict=verdict,
        relevant_txn_id=relevant_txn_id,
        user_type=request.user_type,
        is_bangla=is_bangla
    )

    # 5. Apply Post-processing Safety Guardrails
    safe_reply = SafetyFilterService.sanitize_customer_reply(customer_reply, is_bangla=is_bangla)
    safe_action = SafetyFilterService.sanitize_recommended_next_action(recommended_action)

    # 6. Formulate response
    return TicketResponse(
        ticket_id=request.ticket_id,
        relevant_transaction_id=relevant_txn_id,
        evidence_verdict=verdict,
        case_type=case_type,
        severity=severity,
        department=department,
        agent_summary=summary,
        recommended_next_action=safe_action,
        customer_reply=safe_reply,
        human_review_required=human_review,
        confidence=0.9,  # baseline high programmatic match confidence
        reason_codes=reason_codes
    )
