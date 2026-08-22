"""Synthetic Dataset Generator for Razorpay Revive 100+ Benchmark Evaluation."""
import json
import random
from typing import List, Dict, Any
from app.models.schemas import FailureEvent, PaymentMethod, CustomerProfile, CustomerSegment


INDIAN_NAMES = [
    "Aarav Sharma", "Priya Patel", "Rohan Mehta", "Ananya Iyer", "Vikram Singh",
    "Sneha Reddy", "Aditya Verma", "Pooja Nair", "Rahul Joshi", "Divya Deshmukh",
    "Kunal Gupta", "Neha Kulkarni", "Siddharth Rao", "Kavya Bhat", "Amitav Sen",
    "Tanvi Choudhury", "Manish Bansal", "Ritu Agrawal", "Nikhil Pillai", "Simran Kaur"
]

FAILURE_PROFILES = [
    {
        "category": "TRANSIENT_BANK_DOWNTIME",
        "weight": 30,
        "codes": ["GATEWAY_TIMEOUT_HDFC", "NPCI_SWITCH_BUSY", "SBI_NETBANKING_503", "ICICI_UPI_DOWN"],
        "descriptions": ["Issuing bank gateway failed to acknowledge payment packet within 15s", "NPCI switch under high congestion", "Bank server returned HTTP 503 Service Unavailable"],
        "methods": [PaymentMethod.UPI, PaymentMethod.NETBANKING, PaymentMethod.DEBIT_CARD],
        "amount_range": (350, 4500),
    },
    {
        "category": "INSUFFICIENT_FUNDS",
        "weight": 25,
        "codes": ["INSUFFICIENT_FUNDS_SBI", "ACCOUNT_BALANCE_LOW", "DAILY_LIMIT_EXCEEDED"],
        "descriptions": ["Payer account has insufficient balance to complete debit", "Bank declined authorization due to daily UPI debit limit"],
        "methods": [PaymentMethod.UPI, PaymentMethod.DEBIT_CARD],
        "amount_range": (499, 8500),
    },
    {
        "category": "AUTH_OR_OTP_TIMEOUT",
        "weight": 15,
        "codes": ["OTP_EXPIRED_2FA", "AUTH_SESSION_TIMEOUT", "BAD_REQUEST_PAYMENT_TIMED_OUT"],
        "descriptions": ["Customer did not enter 2FA SMS OTP within 180 seconds", "3DS verification window timed out before customer entered password"],
        "methods": [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD, PaymentMethod.NETBANKING],
        "amount_range": (999, 12000),
    },
    {
        "category": "CHECKOUT_ABANDONMENT",
        "weight": 15,
        "codes": ["CART_DROP_OFF_HIGH_INTENT", "EXIT_CHECKOUT_STEP_2", "ABANDONED_CHECKOUT"],
        "descriptions": ["User exited Razorpay Standard Checkout after selecting payment method", "User closed browser tab during order review step"],
        "methods": [PaymentMethod.UPI, PaymentMethod.CREDIT_CARD],
        "amount_range": (1299, 18500),
    },
    {
        "category": "MANDATE_EXPIRED_OR_REVOKED",
        "weight": 10,
        "codes": ["MANDATE_EXPIRED_SUB", "AUTOPAY_REVOKED_USER", "MANDATE_LIMIT_BREACHED"],
        "descriptions": ["UPI Autopay recurring mandate expired on billing anniversary", "Customer revoked automated mandate on PSP app"],
        "methods": [PaymentMethod.UPI_AUTOPAY],
        "amount_range": (299, 2999),
    },
    {
        "category": "B2B_OVERDUE_INVOICE",
        "weight": 3,
        "codes": ["INVOICE_NET30_OVERDUE", "ENTERPRISE_TERMS_EXCEEDED", "DUE_DATE_PASSED_B2B"],
        "descriptions": ["Net-30 B2B vendor invoice passed due date by 7 days", "Accounts payable invoice awaiting corporate card / wire settlement"],
        "methods": [PaymentMethod.B2B_INVOICE],
        "amount_range": (25000, 150000),
    },
    {
        "category": "FRAUD_OR_CARD_BLOCKED",
        "weight": 2,
        "codes": ["FRAUD_HOTLISTED_CARD", "RISK_SENTINEL_BLOCKED", "STOLEN_CARD_DECLINE"],
        "descriptions": ["Card identified on national hotlist or high-velocity risk trigger", "Card issuing bank returned strict risk restriction"],
        "methods": [PaymentMethod.CREDIT_CARD],
        "amount_range": (5000, 65000),
    },
]


def generate_benchmark_dataset(count: int = 100, seed: int = 42) -> List[Dict[str, Any]]:
    """Generates a reproducible, high-fidelity synthetic benchmark dataset of failed transactions."""
    random.seed(seed)
    dataset = []

    # Flatten weighted profile pool
    pool = []
    for p in FAILURE_PROFILES:
        pool.extend([p] * p["weight"])

    for i in range(1, count + 1):
        prof = random.choice(pool)
        name = random.choice(INDIAN_NAMES)
        first_name = name.split()[0].lower()
        
        event_id = f"evt_bench_{i:04d}"
        order_id = f"order_rzp_{random.randint(100000, 999999)}"
        amount = round(random.uniform(*prof["amount_range"]), 2)
        code = random.choice(prof["codes"])
        desc = random.choice(prof["descriptions"])
        method = random.choice(prof["methods"])
        segment = random.choices(
            [CustomerSegment.STANDARD, CustomerSegment.MEDIUM_LTV, CustomerSegment.HIGH_LTV],
            weights=[60, 25, 15],
            k=1,
        )[0]
        
        # Occasional retry count variations (some fresh, some on 1st/2nd/3rd retry)
        retry_count = random.choices([0, 1, 2, 3], weights=[75, 15, 7, 3], k=1)[0]

        event = FailureEvent(
            event_id=event_id,
            order_id=order_id,
            payment_id=f"pay_{random.randint(1000000, 9999999)}",
            merchant_id="rzp_merch_acme",
            merchant_name="Acme Fashion & Tech India",
            amount=amount,
            currency="INR",
            payment_method=method,
            error_code=code,
            error_description=desc,
            retry_count=retry_count,
            customer=CustomerProfile(
                customer_id=f"cust_{i:04d}",
                name=name,
                phone=f"+91{random.randint(7000000000, 9999999999)}",
                email=f"{first_name}.{random.randint(10, 99)}@example.com",
                preferred_language=random.choice(["hinglish", "en", "hi"]),
                segment=segment,
                historical_payment_success_rate=round(random.uniform(0.70, 0.95), 2),
            ),
            metadata={
                "expected_category": prof["category"],
                "last_contact_hours_ago": random.choice([6, 12, 24, 48, 1]),
            },
        )
        dataset.append(event.model_dump(mode="json"))

    return dataset


if __name__ == "__main__":
    data = generate_benchmark_dataset(100)
    with open("benchmarks/dataset_100.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Generated {len(data)} benchmark records in benchmarks/dataset_100.json")
