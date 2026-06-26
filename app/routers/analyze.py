from fastapi import APIRouter
from app.models.request import TicketRequest
from app.models.response import TicketResponse
from app.services.understanding_service import UnderstandingService
from app.services.transaction_matcher import TransactionMatcher
from app.services.evidence_service import EvidenceService
from app.services.routing_service import RoutingService
from app.services.safety_service import SafetyService
from app.services.llm_client import LLMClientService
from app.utils.language import detect_is_bangla

router = APIRouter()

@router.post("/analyze-ticket", response_model=TicketResponse)
async def analyze_ticket(request: TicketRequest):
    # 1. Semantic Validation
    complaint_text = request.complaint.strip() if request.complaint else ""
    if not complaint_text:
        raise ValueError("Complaint text cannot be empty.")

    # 2. Extract facts from raw complaint text dynamically at runtime
    facts = UnderstandingService.understand_complaint(complaint_text, request.user_type)
    is_bangla = (facts["detected_language"] in ["bn", "mixed"]) or detect_is_bangla(complaint_text)

    # 3. Match facts against the transaction history
    match_result = TransactionMatcher.match(facts, request.transaction_history or [])

    # 4. Determine evidence consistency and case types
    verdict, final_case_type, relevant_txn_id = EvidenceService.decide(
        facts, match_result, request.transaction_history or []
    )

    # 5. Route to designated department, severity, and human review flag
    department, severity, human_review = RoutingService.route(
        final_case_type, verdict, match_result
    )

    # 6. Generate agent summary and customer responses (LLM or Falling back)
    summary, recommended_action, customer_reply = await LLMClientService.generate_support_text(
        complaint=complaint_text,
        case_type=final_case_type,
        verdict=verdict,
        relevant_txn_id=relevant_txn_id,
        user_type=request.user_type,
        is_bangla=is_bangla,
        matched_transaction=match_result["matched_transaction"],
        extracted_facts=facts,
        ambiguity_reason=match_result.get("ambiguity_reason")
    )

    # 7. Final Security Sanitizer Layer
    safe_reply = SafetyService.sanitize_customer_reply(customer_reply, is_bangla=is_bangla)
    safe_action = SafetyService.sanitize_recommended_next_action(recommended_action)

    # 8. Output Response conformant to the strict contract
    return TicketResponse(
        ticket_id=request.ticket_id,
        relevant_transaction_id=relevant_txn_id,
        evidence_verdict=verdict,
        case_type=final_case_type,
        severity=severity,
        department=department,
        agent_summary=summary,
        recommended_next_action=safe_action,
        customer_reply=safe_reply,
        human_review_required=human_review,
        confidence=facts.get("confidence", 0.9),
        reason_codes=match_result.get("reason_codes", [final_case_type.value])
    )
