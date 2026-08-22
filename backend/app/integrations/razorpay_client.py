"""Razorpay API Integration & Sandbox Client for Razorpay Revive."""
import os
import uuid
import time
from typing import Dict, Any, Optional
import requests
from requests.auth import HTTPBasicAuth


class RazorpayClientWrapper:
    """Wrapper supporting both live Razorpay Sandbox APIs and zero-config local simulation."""

    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None, mock_mode: bool = True):
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID", "rzp_test_mockKey123")
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET", "mockSecret456")
        # Automatically use mock mode if keys are placeholders or mock_mode is explicitly set
        self.mock_mode = mock_mode or "mock" in self.key_id.lower() or not self.key_secret
        self.base_url = "https://api.razorpay.com/v1"

    def create_payment_link(
        self,
        amount_inr: float,
        customer_name: str,
        customer_phone: str,
        customer_email: str,
        description: str,
        reference_id: Optional[str] = None,
        expire_by_minutes: int = 120,
    ) -> Dict[str, Any]:
        """Creates a dynamic Razorpay 1-click Payment Link (Supports Real Sandbox or Offline Simulation)."""
        ref_id = reference_id or f"plink_ref_{uuid.uuid4().hex[:8]}"
        amount_paise = int(amount_inr * 100)
        expire_by = int(time.time()) + (expire_by_minutes * 60)

        if not self.mock_mode:
            try:
                payload = {
                    "amount": amount_paise,
                    "currency": "INR",
                    "accept_partial": False,
                    "reference_id": ref_id,
                    "description": description,
                    "customer": {
                        "name": customer_name,
                        "contact": customer_phone,
                        "email": customer_email,
                    },
                    "notify": {"sms": True, "email": True, "whatsapp": True},
                    "reminder_enable": True,
                    "expire_by": expire_by,
                }
                res = requests.post(
                    f"{self.base_url}/payment_links",
                    json=payload,
                    auth=HTTPBasicAuth(self.key_id, self.key_secret),
                    timeout=10,
                )
                if res.status_code in [200, 201]:
                    data = res.json()
                    return {
                        "id": data.get("id"),
                        "short_url": data.get("short_url"),
                        "status": data.get("status", "created"),
                        "amount": amount_inr,
                        "reference_id": ref_id,
                        "is_mock": False,
                    }
            except Exception as e:
                # Graceful fallback to mock mode if live API times out
                pass

        # Offline Mock Simulator (Zero Cost & 100% Reliable)
        mock_id = f"plink_{uuid.uuid4().hex[:14]}"
        return {
            "id": mock_id,
            "short_url": f"https://rzp.io/i/{mock_id[:8]}",
            "status": "created",
            "amount": amount_inr,
            "reference_id": ref_id,
            "is_mock": True,
        }

    def trigger_gateway_retry(self, payment_id: str, scheduled_delay_minutes: int) -> Dict[str, Any]:
        """Simulates an intelligent scheduled retry via Razorpay Optimizer / Core Gateway."""
        retry_job_id = f"retry_job_{uuid.uuid4().hex[:8]}"
        return {
            "retry_job_id": retry_job_id,
            "payment_id": payment_id,
            "scheduled_delay_minutes": scheduled_delay_minutes,
            "status": "SCHEDULED",
            "rail": "RAZORPAY_SMART_ROUTER",
        }
