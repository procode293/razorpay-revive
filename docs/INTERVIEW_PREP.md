# Razorpay AI Buildathon: Technical Panel Interview Defense Guide
**Track 03: AI Revenue Recovery — Razorpay Revive**

This guide prepares you for deep technical questions from Razorpay engineers and engineering managers during the panel interview.

---

### Q1: Why did you use a deterministic state machine + guardrails instead of letting an autonomous LLM agent make the decisions end-to-end?

**Answer:**
> *"In consumer fintech and payments, predictability, compliance, and sub-100ms latency are non-negotiable. An unconstrained LLM agent introduces non-deterministic latency (500ms–2s), risk of prompt injection, and catastrophic failure modes like hallucinating discounted transaction amounts or double-charging users.*
> 
> *We designed Razorpay Revive with a **hybrid architecture**: the AI/classifier provides rich taxonomy parsing, sentiment context, and personalized localized copy, while execution is governed by a **deterministic, rule-gated finite state machine (FSM)**. This guarantees zero financial hallucinations and 100% compliance with TRAI and RBI regulations."*

---

### Q2: How do you handle race conditions and duplicate webhook events in high-concurrency payment streams?

**Answer:**
> *"We enforce strict idempotency at the ingestion boundary:*
> 1. *Every event uses a composite idempotency key: `idempotency_key = hash(order_id + payment_id + failure_event_type)`.*
> 2. *Before processing, the worker executes an atomic Redis `SET key value NX EX 86400` (24h TTL).*
> 3. *If the key exists or an in-flight transaction lock is held, subsequent webhook payloads are acknowledged with HTTP 200 and deduplicated without re-triggering interventions.*
> 4. *In our SQLite/PostgreSQL audit store, the `event_id` column has a unique constraint to ensure write-level idempotency."*

---

### Q3: How do you calculate the optimal retry window for transient bank downtime?

**Answer:**
> *"Instead of naive fixed intervals, we use an adaptive exponential backoff schedule ($15 \times 2^{\text{retry\_count}}$ minutes) bounded by real-time bank switch telemetry.*
> 
> *In production, Razorpay Optimizer maintains uptime indices across issuing banks (HDFC, SBI, ICICI, Axis). When a transaction fails with `GATEWAY_TIMEOUT`, Revive checks the bank's rolling 5-minute success rate curve and schedules the retry precisely when the gateway success rate climbs back above 90%."*

---

### Q4: How does Razorpay Revive respect TRAI and RBI communication guidelines?

**Answer:**
> *"We implemented a dedicated `FintechGuardrailEngine` with five active checks:*
> * **TRAI Quiet Hours**: Outbound customer communications (WhatsApp, SMS, Voice) are blocked between 9:00 PM and 8:00 AM IST. Any event arriving during quiet hours is automatically buffered in a priority queue for release at 8:01 AM IST.
> * **Customer Fatigue / Anti-Spam**: A 4-hour cooldown is enforced per customer ID across all channels.
> * **Max 3 Retries**: Hard stop after 3 attempts to prevent harassment and unnecessary interchange/messaging costs.
> * **Discount Caps**: Promotional recovery discounts are bounded to $\le 10\%$."*

---

### Q5: How would this scale to 10,000 transactions per second on Razorpay's production infrastructure?

**Answer:**
> *"Our production blueprint uses:*
> 1. **Kafka Event Partitioning**: Ingested gateway failure webhooks are partitioned by `merchant_id` to preserve per-merchant event ordering.
> 2. **Stateless Async Workers**: The classifier and guardrail evaluations run on async worker nodes (FastAPI / Rust) taking $<15\text{ms}$ per evaluation.
> 3. **Batch Aggregation & Long-term Sinks**: High-volume telemetry is written asynchronously to ClickHouse/Snowflake for real-time analytics, keeping the hot transaction path non-blocking."*
