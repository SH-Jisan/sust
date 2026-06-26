import re

class SafetyService:
    @staticmethod
    def sanitize_customer_reply(text: str, is_bangla: bool = False) -> str:
        """
        Scans and sanitizes the customer reply to guarantee compliance with all safety rules.
        """
        if not text:
            return ""

        # 1. Credentials Requests Checks (PIN/OTP/passwords/cards)
        unsafe_creds = [
            r"share your otp", r"provide otp", r"send otp", r"share pin", r"provide pin",
            r"password", r"full card number", r"verification code", r"secret credential",
            r"ওটিপি দিন", r"পিন দিন", r"পাসওয়ার্ড দিন", r"ওটিপি চান", r"পিন বলুন"
        ]
        
        has_cred_violation = False
        text_lower = text.lower()
        for pattern in unsafe_creds:
            if re.search(pattern, text_lower):
                has_cred_violation = True
                break
                
        if has_cred_violation:
            # Overwrite with strict safety warning
            if is_bangla:
                return "আমরা কখনোই আপনার পিন বা ওটিপি চাই না। অনুগ্রহ করে কারো সাথে এগুলো শেয়ার করবেন না।"
            else:
                return "We will never ask for your PIN, OTP, or password. Please do not share these details with anyone."

        # 2. Refund / Reversal Confirmation Checks
        unsafe_promises = [
            r"we will refund", r"refund confirmed", r"reversal confirmed", r"we will reverse",
            r"account unblocked", r"money recovered", r"টাকা ফেরত দেওয়া হবে নিশ্চিত", r"রিফান্ড নিশ্চিত"
        ]
        
        has_promise_violation = False
        for pattern in unsafe_promises:
            if re.search(pattern, text_lower):
                has_promise_violation = True
                break
                
        if has_promise_violation:
            # Override with safe policies
            if is_bangla:
                return "আপনার অভিযোগটি সফলভাবে নথিভুক্ত করা হয়েছে। যেকোনো যোগ্য পরিমাণ অফিশিয়াল চ্যানেলের মাধ্যমে ফেরত দেওয়া হবে। অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
            else:
                return "We have received your concern. Any eligible amount will be returned through official channels. Please do not share your PIN or OTP with anyone."

        # 3. Add missing safety disclaimers
        en_disclaimer = "Please do not share your PIN or OTP with anyone."
        bn_disclaimer = "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
        
        if is_bangla:
            if "পিন" not in text or "ওটিপি" not in text:
                text = f"{text.rstrip('. ')}. {bn_disclaimer}"
        else:
            if "PIN" not in text or "OTP" not in text:
                text = f"{text.rstrip('. ')}. {en_disclaimer}"

        return text

    @staticmethod
    def sanitize_recommended_next_action(text: str) -> str:
        """
        Sanitizes internal next actions to prevent agents from promising unauthorized refunds.
        """
        if not text:
            return ""
            
        unsafe_directives = [
            r"\b(?:refund|reverse|unblock)\b.*\b(?:now|immediately|confirm|promise)\b",
            r"\b(?:initiate|process|complete)\b.*\b(?:refund|reversal)\b",
            r"refund confirmed", r"reversal confirmed"
        ]
        
        has_violation = False
        text_lower = text.lower()
        for pattern in unsafe_directives:
            if re.search(pattern, text_lower):
                has_violation = True
                break
                
        if has_violation:
            return "Verify transaction details and initiate the appropriate dispute workflow per company policy. Do not promise direct refunds."
            
        return text
