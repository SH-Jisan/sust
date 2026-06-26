import re
from typing import Optional, Dict, Any, List
from app.config import settings
from app.utils.language import detect_is_bangla
from app.utils.helpers import extract_amounts
from app.models.response import CaseType

class UnderstandingService:
    @staticmethod
    def understand_complaint(complaint_text: str, user_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Parses untrusted raw complaint text into structured semantic facts.
        Supports English, Bangla, and Banglish.
        """
        complaint = complaint_text.strip()
        complaint_lower = complaint.lower()
        
        # 1. Detect language
        is_bangla = detect_is_bangla(complaint)
        lang = "bn" if is_bangla else "en"
        # Simple Banglish detector (checks for English alphabet with common Bangla sounds)
        banglish_keywords = ["taka", "pathaisi", "kete", "nise", "bhul", "kore", "dhaka", "chengel", "bikas"]
        if not is_bangla and any(kw in complaint_lower for kw in banglish_keywords):
            lang = "mixed"
            
        # 2. Extract amount(s)
        amounts = extract_amounts(complaint)
        mentioned_amount = amounts[0] if amounts else None
        
        # 3. Extract transaction ID mentioned in text
        txn_matches = re.findall(r"\bTXN-\w+\b", complaint, re.IGNORECASE)
        mentioned_transaction_id = txn_matches[0].upper() if txn_matches else None
        
        # 4. Extract counterparty / phone number
        # Matches standard Bangladeshi numbers like 01712345678, +8801812345678, etc.
        phone_matches = re.findall(r"\b(?:\+?88)?01[3-9]\d{8}\b", complaint)
        # Also matches AGENT-123 or MERCHANT-123
        party_matches = re.findall(r"\b(?:AGENT|MERCHANT|BILLER)-\w+\b", complaint, re.IGNORECASE)
        
        mentioned_counterparty = None
        if phone_matches:
            # Standardize by adding +88 prefix if missing to match ledger records
            phone = phone_matches[0]
            if not phone.startswith("+88"):
                if phone.startswith("88"):
                    phone = "+" + phone
                else:
                    phone = "+88" + phone
            mentioned_counterparty = phone
        elif party_matches:
            mentioned_counterparty = party_matches[0].upper()
            
        # 5. Extract Time Clues
        time_clues = []
        time_keywords = ["today", "yesterday", "morning", "afternoon", "evening", "now", "আজ", "গতকাল", "সকালে", "বিকালে", "দুপুরে", "shokale", "bikal", "aj", "gothokal"]
        for kw in time_keywords:
            if kw in complaint_lower:
                time_clues.append(kw)
        time_clue = ", ".join(time_clues) if time_clues else None
        
        # 6. Case Type Intent Classification
        case_type_hint = CaseType.OTHER
        
        # Check for Prompt Injection / Adversarial inputs first
        injection_indicators = ["ignore previous", "ignore rules", "ignore instruction", "override", "system prompt", "translate this"]
        is_injection = any(indicator in complaint_lower for indicator in injection_indicators)
        
        if is_injection:
            case_type_hint = CaseType.OTHER
        else:
            # Wrong Transfer keywords
            wrong_transfer_kws = ["wrong number", "wrong transfer", "wrong recipient", "wrong person", "wrong account", "wrong mobile", "mistake", "recipient", "brother", "friend", "sister", "ভুল", "ভুল নম্বরে", "ভুল নাম্বারে", "অন্য নাম্বারে", "ভুল করে", "bhul", "bhul number", "taka pathaisi", "sent to wrong", "sent", "send", "transfer", "transferred", "পাঠা", "পাঠিয়ে"]
            # Payment Failed keywords
            payment_failed_kws = ["failed", "cut", "deducted", "recharge failed", "recharge fail", "payment fail", "ব্যর্থ", "কেটে নিয়েছে", "কেটে গেছে", "ব্যালেন্স কেটেছে", "taka kete", "kete nise", "payment fail", "recharge fail"]
            # Refund Request keywords
            refund_request_kws = ["refund", "change my mind", "do not want", "return my money", "রিফান্ড", "টাকা ফেরত", "want money back"]
            # Duplicate Payment keywords
            duplicate_payment_kws = ["twice", "double", "duplicate", "two times", "double charged", "double payment", "দুইবার", "২ বার", "ক্যাপ ডবল", "keteche", "charge double"]
            # Merchant Settlement keywords
            settlement_kws = ["settlement", "settle", "sales", "merchant sales", "সেটেলমেন্ট", "সেটেল"]
            # Agent Cash-in keywords
            agent_kws = ["agent", "cash in", "cash-in", "এজেন্ট", "এজেন্টের", "ক্যাশ ইন", "ক্যাশ-ইন"]
            # Phishing keywords
            phishing_kws = ["otp", "pin", "password", "blocked", "called me", "asked for", "fake call", "ওটিপি", "পিন", "পাসওয়ার্ড", "কল করেছে", "পিন চেয়েছে", "ব্লক"]

            if any(kw in complaint_lower for kw in phishing_kws):
                case_type_hint = CaseType.PHISHING_OR_SOCIAL_ENGINEERING
            elif any(kw in complaint_lower for kw in duplicate_payment_kws):
                case_type_hint = CaseType.DUPLICATE_PAYMENT
            elif any(kw in complaint_lower for kw in wrong_transfer_kws):
                case_type_hint = CaseType.WRONG_TRANSFER
            elif any(kw in complaint_lower for kw in payment_failed_kws):
                case_type_hint = CaseType.PAYMENT_FAILED
            elif any(kw in complaint_lower for kw in refund_request_kws):
                case_type_hint = CaseType.REFUND_REQUEST
            elif any(kw in complaint_lower for kw in settlement_kws) or user_type == "merchant":
                case_type_hint = CaseType.MERCHANT_SETTLEMENT_DELAY
            elif any(kw in complaint_lower for kw in agent_kws):
                case_type_hint = CaseType.AGENT_CASH_IN_ISSUE
            else:
                case_type_hint = CaseType.OTHER
            
        return {
            "detected_language": lang,
            "case_type_hint": case_type_hint,
            "mentioned_amount": mentioned_amount,
            "mentioned_transaction_id": mentioned_transaction_id,
            "mentioned_counterparty": mentioned_counterparty,
            "time_clue": time_clue,
            "issue_summary": f"User reports potential {case_type_hint.value} issue.",
            "confidence": 0.85 if mentioned_amount or mentioned_transaction_id else 0.60,
            "reason_codes": [case_type_hint.value]
        }
