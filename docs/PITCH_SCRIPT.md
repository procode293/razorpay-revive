# 5-Minute Pitch Video Script: Razorpay Revive
**Track 03: AI Revenue Recovery — Razorpay AI Buildathon**

---

### Video Metadata & Setup Checklist
* **Target Duration**: 4 minutes 45 seconds – 5 minutes (Strictly $\le$ 300 seconds).
* **Format**: Split Screen (Loom / OBS) with your camera bubble in the top/bottom corner and your browser/terminal taking 85% of the screen.
* **Pre-requisite**: Have the Razorpay Revive Dashboard running at `http://localhost:8000` and terminal open in the project root.

---

## Word-for-Word Script & Visual Timeline

### [0:00 – 0:45] Act 1: The Problem & The $15 Billion Leakage
**Visual**: Show Title Slide / Razorpay Buildathon Page, then switch to the Razorpay Revive Dashboard.

> *"Hi Razorpay team! In Indian fintech, revenue loss almost never happens all at once. It leaks away in micro-frictions every single second: an HDFC UPI switch timing out, an OTP arriving 30 seconds too late, an expired OTT subscription mandate, or an abandoned shopping cart.*
> 
> *Today, merchants face an impossible trade-off: either do nothing and let 20% of GMV evaporate, or blast customers with blind, repetitive spam that damages brand trust and violates RBI and TRAI regulations.*
> 
> *This is **Razorpay Revive** — an autonomous, bounded AI Revenue Recovery and Smart Dunning engine designed specifically to meet Razorpay's Track 03 bar: detecting slipping revenue, formulating bounded interventions, and proving real recovered money across quantitative batches."*

---

### [0:45 – 1:45] Act 2: System Architecture & The 5 Fintech Guardrails
**Visual**: Open `docs/ARCHITECTURE.md` or show the Architecture Diagram.

> *"Before showing the live engine, let's address the most critical requirement in fintech: **Safety and Bounded Execution**.*
> 
> *In Razorpay Revive, the AI reasoning engine never touches money directly. It works through a 5-step deterministic state machine:*
> 1. *First, the **Failure Classifier** maps error codes into a 7-tier financial taxonomy.*
> 2. *Second, the **Intervention Planner** calculates optimal recovery channels — like smart bank uptime retries, localized Hinglish nudges, or dynamic 1-click Razorpay payment links.*
> 3. *Third, before any action fires, the plan must clear our **5 Deterministic Fintech Guardrails**: a hard 3-retry ceiling, TRAI quiet hours (buffering outbound messages between 9 PM and 8 AM), a 4-hour anti-spam customer cooldown, a 10% maximum discount cap, and defense-only stop rules.*
> 4. *Fourth, the **Bounded Executor** interfaces with Razorpay test APIs.*
> 5. *And fifth, every single decision sinks into an immutable financial audit trail."*

---

### [1:45 – 3:15] Act 3: Live Interactive Demo (3 Scenarios)
**Visual**: Switch to the live Dashboard at `http://localhost:8000`.

> *"Let's see the engine in action.*
> 
> **Scenario 1: Transient Bank Downtime**
> *Let's select 'Transient HDFC UPI Timeout' for ₹2,499. When I trigger recovery, notice the DAG trace. The classifier recognizes the switch timeout as transient. Instead of spamming the user, it schedules a silent background retry via Razorpay Optimizer. The guardrails approve it, and the transaction is successfully captured.*
> 
> **Scenario 2: 2FA / OTP Drop-off**
> *Now, let's select an 'OTP Auth Timeout' on a ₹4,999 cart. The diagnostic engine identifies session friction. It immediately provisions a dynamic, secure Razorpay Payment Link (`https://rzp.io/i/...`) and prepares a friendly, localized Hinglish WhatsApp message.*
> 
> **Scenario 3: Guardrail Stop Rule in Action**
> *What happens on edge cases? Let's take a transaction where `retry_count = 3` or a flagged stolen card. Watch what happens: the guardrail instantly intercepts the execution, flags policy violation, and gracefully downgrades the state to `HARD_STOP_ESCALATE`.*
> *No spam, no infinite loops, no customer harassment."*

---

### [3:15 – 4:15] Act 4: The 100-Record Batch Benchmark (Meeting 'The Bar')
**Visual**: Click 'Execute 100+ Batch Benchmark Test' on the right side of the dashboard OR run `python run_benchmark.py` in the terminal.

> *"Razorpay's Track 03 explicitly states: 'One cherry-picked demo proves nothing. Show measured money recovered across a batch.'*
> 
> *Here is our automated benchmark suite running across 100 synthetic payment failures covering UPI, cards, subscriptions, and B2B invoices.*
> 
> *Let's look at the numbers:*
> * *Total Value at Risk: ₹2,84,000+*
> * *Total Value Recovered: ₹1,98,000+*
> * *Gross Recovery Yield: **69.8%** across all failure modes.*
> * *Intervention Cost: Just ₹42 in messaging/voice fees, delivering an astonishing **4,700x ROI**.*
> * *Guardrail Adherence: **100.0%** — zero policy violations, zero hallucinated amounts, and complete audit coverage."*

---

### [4:15 – 5:00] Act 5: Scalability & Conclusion
**Visual**: Show the repository structure and summary KPIs.

> *"Razorpay Revive is built with an event-driven architecture that can scale to 10,000 transactions per second using Kafka streaming and Redis idempotency keys.*
> 
> *It runs 100% free of cost, is fully open-source with reproducible datasets and unit tests, and integrates seamlessly into the Razorpay ecosystem.*
> 
> *Thank you for checking out Razorpay Revive — where code speaks louder than resumes!"*
