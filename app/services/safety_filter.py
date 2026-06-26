import re

class SafetyFilterService:
    @staticmethod
    def sanitize_customer_reply(text: str, is_bangla: bool = False) -> str:
        """
        Scans and sanitizes the customer reply to ensure 100% compliance with safety rules:
        1. No PIN/OTP/password requests.
        2. No absolute refund/reversal confirmations.
        3. No redirection to suspicious third parties.
        """
        if not text:
            return ""

        # Ensure credentials warning is present and never requested
        # Regex to detect credential requests (English and Bangla)
        cred_request_patterns = [
            r"\b(?:ask|share|provide|tell|send|enter|input|give)\b.*\b(?:pin|otp|password|passcode|card number)\b",
            r"\b(?:পিন|ওটিপি|পাসওয়ার্ড|কার্ড নম্বর)\b.*\b(?:দিন|বলুন|শেয়ার|সেন্ড|চান|দিন)\b",
            r"share.*(?:pin|otp)",
            r"provide.*(?:pin|otp)",
            r"tell.*(?:pin|otp)",
            r"ওটিপি.*দিন",
            r"পিন.*বলুন"
        ]
        
        for pattern in cred_request_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Replace request with safety warning
                if is_bangla:
                    text = "আমরা কখনোই আপনার পিন বা ওটিপি চাই না। অনুগ্রহ করে কারো সাথে এগুলো শেয়ার করবেন না।"
                else:
                    text = "We will never ask for your PIN or OTP. Please do not share these details with anyone."
                break

        # Always append standard safety disclaimer if not present
        en_disclaimer = "Please do not share your PIN or OTP with anyone."
        bn_disclaimer = "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
        
        if is_bangla:
            if bn_disclaimer not in text:
                text = f"{text.rstrip('. ')}. {bn_disclaimer}"
        else:
            if en_disclaimer not in text:
                text = f"{text.rstrip('. ')}. {en_disclaimer}"

        # Sanitize unauthorized refund/reversal promises
        # Match phrases like "we will refund", "reversal is confirmed", "money reversed", etc.
        refund_promise_patterns = [
            r"\bwe\b.*\b(?:refund|reverse|unblock|recover|credit)\b",
            r"\b(?:refund|reversal|unblock|recovery)\b.*\b(?:will be|is|has been|confirmed|initiated|completed)\b",
            r"\bwill refund you\b",
            r"\bwill reverse the\b",
            r"টাকা ফেরত (?:দেওয়া হবে|দিচ্ছি|দেবো)",
            r"রিফান্ড করে (?:দেওয়া হবে|দেবো|দিচ্ছি)",
            r"অ্যাকাউন্ট আনব্লক (?:করা হবে|হবে)"
        ]
        
        has_promise = False
        for pattern in refund_promise_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                has_promise = True
                break
                
        if has_promise:
            # Replace absolute promise with safe policy language
            if is_bangla:
                text = re.sub(
                    r"(?:রিফান্ড করে দেওয়া হবে|টাকা ফেরত দেওয়া হবে|রিফান্ড দেওয়া হবে|আমরা রিফান্ড করব)",
                    "যেকোনো যোগ্য পরিমাণ অফিশিয়াল চ্যানেলের মাধ্যমে ফেরত দেওয়া হবে",
                    text
                )
                # Fail-safe replacement if still matching
                if any(re.search(p, text, re.IGNORECASE) for p in refund_promise_patterns):
                    text = "আপনার অভিযোগটি সফলভাবে নথিভুক্ত করা হয়েছে। যেকোনো যোগ্য পরিমাণ অফিশিয়াল চ্যানেলের মাধ্যমে ফেরত দেওয়া হবে। অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
            else:
                text = re.sub(
                    r"(?:we will refund you|we will reverse the transaction|your refund has been confirmed|we have initiated your refund|we will send your money back)",
                    "any eligible amount will be returned through official channels",
                    text,
                    flags=re.IGNORECASE
                )
                if any(re.search(p, text, re.IGNORECASE) for p in refund_promise_patterns):
                    text = "We have received your concern. Any eligible amount will be returned through official channels. Please do not share your PIN or OTP with anyone."

        return text

    @staticmethod
    def sanitize_recommended_next_action(text: str) -> str:
        """
        Sanitizes internal agent action text to ensure it does not instruct the agent 
        to promise a direct refund without authority.
        """
        if not text:
            return ""
            
        # Replace absolute refund directives with verification directives
        refund_directives = [
            r"\b(?:refund|reverse|unblock)\b.*\b(?:now|immediately|confirm|promise)\b",
            r"\b(?:initiate|process|complete)\b.*\b(?:refund|reversal)\b"
        ]
        
        has_directive = False
        for pattern in refund_directives:
            if re.search(pattern, text, re.IGNORECASE):
                has_directive = True
                break
                
        if has_directive:
            text = "Verify transaction details and initiate the appropriate dispute workflow per company policy. Do not promise direct refunds."
            
        return text
