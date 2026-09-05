/**
 * Razorpay Revive — Advanced Frontend Dashboard Logic
 * Features: Fully Interactive Customer Phone Simulator, Chart.js Analytics, Bank Telemetry, Policy Sliders
 */

// ══════════════════════════════════════════
// GLOBAL PHONE & APP STATE
// ══════════════════════════════════════════
let currentPhoneState = {
    customerName: 'Aarav Sharma',
    amount: 2499,
    discountApplied: 0,
    payLink: 'https://rzp.io/i/revive_live',
    orderId: 'ORD-7291',
    status: 'PENDING',
    isVoice: false,
    messages: []
};

let currentPhoneMode = 'whatsapp';

// ══════════════════════════════════════════
// INIT ON LOAD
// ══════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    fetchMetrics();
    fetchAuditLogs();
    fetchTelemetry();
    initDefaultPhoneSimulator();
    updatePhoneClock();
    setInterval(updatePhoneClock, 30000);
});

function formatINR(val) {
    const num = Number(val) || 0;
    return '₹' + num.toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

function updatePhoneClock() {
    const clock = document.getElementById('phone-clock');
    if (clock) {
        const now = new Date();
        clock.textContent = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
    }
}

function getMerchantPolicy() {
    return {
        max_retries: parseInt(document.getElementById('slider-retries')?.value || 3),
        max_discount_percentage: parseFloat(document.getElementById('slider-discount')?.value || 10),
        enforce_quiet_hours: document.getElementById('chk-quiet-hours')?.checked ?? true,
        anti_spam_cooldown_hours: parseInt(document.getElementById('slider-cooldown')?.value || 4),
        b2b_voice_threshold_inr: parseFloat(document.getElementById('slider-b2b')?.value || 50000),
    };
}

// ══════════════════════════════════════════
// KPI METRICS
// ══════════════════════════════════════════
async function fetchMetrics() {
    try {
        const res = await fetch('/api/metrics');
        if (!res.ok) return;
        const data = await res.json();
        document.getElementById('kpi-at-risk').textContent = formatINR(data.total_at_risk_inr);
        document.getElementById('kpi-recovered').textContent = formatINR(data.total_recovered_inr);
        document.getElementById('kpi-rate').textContent = (Number(data.recovery_rate_pct) || 0).toFixed(1) + '%';
        document.getElementById('kpi-net-value').textContent = formatINR(data.net_value_saved_inr);
        document.getElementById('kpi-guardrail').textContent = (Number(data.guardrail_compliance_pct) || 100).toFixed(1) + '%';
        document.getElementById('kpi-recovered-count').textContent = `${data.recovered_count || 0} of ${data.total_events || 0} saved`;
    } catch (err) { console.error('Metrics error:', err); }
}

// ══════════════════════════════════════════
// AUDIT LOGS
// ══════════════════════════════════════════
async function fetchAuditLogs() {
    const list = document.getElementById('audit-feed-list');
    if (!list) return;
    try {
        const res = await fetch('/api/audit-logs?limit=25');
        if (!res.ok) return;
        const data = await res.json();
        if (!data.traces || data.traces.length === 0) {
            list.innerHTML = `<div class="text-center py-6 text-slate-500 text-xs">No audit logs found. Run a simulation or benchmark.</div>`;
            return;
        }
        list.innerHTML = data.traces.map(t => {
            const isRec = t.status === 'RECOVERED';
            const isRetry = t.status === 'SCHEDULED_RETRY';
            const badgeBg = isRec ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                            isRetry ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                            'bg-amber-500/10 text-amber-400 border-amber-500/20';
            return `
                <div class="bg-[#091224] border border-slate-800 rounded-lg p-3 text-xs space-y-1.5 hover:border-slate-700 transition">
                    <div class="flex items-center justify-between">
                        <span class="font-semibold text-slate-200">${t.customer_name || 'Customer'} (#${t.order_id || 'N/A'})</span>
                        <span class="px-2 py-0.5 rounded-full border text-[10px] font-semibold ${badgeBg}">${t.status}</span>
                    </div>
                    <div class="flex items-center justify-between text-slate-400">
                        <span>${t.category} &bull; ${t.payment_method}</span>
                        <span class="font-mono text-slate-200">${formatINR(t.amount)} &rarr; <span class="${isRec ? 'text-emerald-400 font-bold' : ''}">${formatINR(t.money_recovered)}</span></span>
                    </div>
                </div>`;
        }).join('');
    } catch (err) { console.error('Audit error:', err); }
}

// ══════════════════════════════════════════
// BANK TELEMETRY HEATMAP
// ══════════════════════════════════════════
async function fetchTelemetry() {
    const grid = document.getElementById('telemetry-grid');
    if (!grid) return;
    try {
        const res = await fetch('/api/optimizer/telemetry');
        if (!res.ok) return;
        const data = await res.json();
        const banks = data.telemetry || [];
        grid.innerHTML = banks.map(b => {
            const uptime = Math.min(100, Math.max(0, b.uptime_pct + (Math.random() * 4 - 2))).toFixed(1);
            const latency = Math.max(50, Math.round(b.latency_ms + (Math.random() * 100 - 50)));
            const isHealthy = uptime > 90;
            const isCongested = uptime > 70 && uptime <= 90;
            const statusColor = isHealthy ? 'text-emerald-400' : isCongested ? 'text-amber-400' : 'text-red-400';
            const statusBg = isHealthy ? 'bg-emerald-500' : isCongested ? 'bg-amber-500' : 'bg-red-500';
            const barColor = isHealthy ? 'bg-emerald-500' : isCongested ? 'bg-amber-500' : 'bg-red-500';
            return `
                <div class="bg-[#091224] border border-slate-800 rounded-lg p-3 text-xs space-y-2">
                    <div class="flex items-center justify-between">
                        <span class="font-semibold text-slate-200 text-[11px]">${b.bank}</span>
                        <span class="w-2 h-2 rounded-full ${statusBg} ${isHealthy ? '' : 'animate-pulse'}"></span>
                    </div>
                    <div class="text-slate-400 text-[10px]">${b.rail}</div>
                    <div class="w-full bg-slate-800 rounded-full h-1.5">
                        <div class="${barColor} h-1.5 rounded-full telemetry-bar" style="width: ${uptime}%"></div>
                    </div>
                    <div class="flex justify-between text-[10px]">
                        <span class="${statusColor} font-bold">${uptime}%</span>
                        <span class="text-slate-500">${latency}ms</span>
                    </div>
                </div>`;
        }).join('');
    } catch (err) { console.error('Telemetry error:', err); }
}

// ══════════════════════════════════════════
// PHONE SIMULATOR LOGIC & INTERACTIVITY
// ══════════════════════════════════════════

function switchPhoneMode(mode) {
    currentPhoneMode = mode;
    const whatsappScreen = document.getElementById('phone-whatsapp-screen');
    const voiceScreen = document.getElementById('phone-voice-screen');
    const tabWhatsapp = document.getElementById('phone-tab-whatsapp');
    const tabVoice = document.getElementById('phone-tab-voice');

    if (mode === 'whatsapp') {
        whatsappScreen?.classList.remove('hidden');
        whatsappScreen?.classList.add('flex');
        voiceScreen?.classList.add('hidden');
        voiceScreen?.classList.remove('flex');

        tabWhatsapp?.classList.add('bg-[#075e54]', 'text-white');
        tabWhatsapp?.classList.remove('text-slate-400');
        tabVoice?.classList.remove('bg-[#075e54]', 'text-white');
        tabVoice?.classList.add('text-slate-400');
    } else {
        voiceScreen?.classList.remove('hidden');
        voiceScreen?.classList.add('flex');
        whatsappScreen?.classList.add('hidden');
        whatsappScreen?.classList.remove('flex');

        tabVoice?.classList.add('bg-[#075e54]', 'text-white');
        tabVoice?.classList.remove('text-slate-400');
        tabWhatsapp?.classList.remove('bg-[#075e54]', 'text-white');
        tabWhatsapp?.classList.add('text-slate-400');
    }
}

function initDefaultPhoneSimulator() {
    currentPhoneState = {
        customerName: 'Aarav Sharma',
        amount: 2499,
        discountApplied: 0,
        payLink: 'https://rzp.io/i/revive_live',
        orderId: 'ORD-7291',
        status: 'PENDING',
        isVoice: false
    };

    const initialData = {
        event: { amount: 2499, customer: { name: 'Aarav Sharma' } },
        plan: {
            channel: 'WHATSAPP',
            discount_percentage: 5,
            message_payload: 'Namaste Aarav! Aapka ₹2,499 ka payment session OTP timeout ki wajah se pura nahi hua. Humne aapke liye 1-click Razorpay payment link generate kiya hai. Complete karein:'
        },
        execution: {
            status: 'PENDING',
            payment_link_url: 'https://rzp.io/i/revive_live'
        }
    };
    renderPhoneChat(initialData);
}

function renderPhoneChat(data) {
    const chatArea = document.getElementById('phone-chat-area');
    if (!chatArea) return;

    const plan = data.plan || {};
    const event = data.event || {};
    const exec = data.execution || {};
    const isVoice = plan.channel === 'VOICE_BOT';
    const isBlocked = exec.status === 'BLOCKED_BY_GUARDRAIL' || exec.status === 'ESCALATED';
    const customerName = (event.customer?.name || 'Customer').split(' ')[0];
    const timeStr = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

    currentPhoneState.customerName = customerName;
    currentPhoneState.amount = event.amount || 2499;
    currentPhoneState.payLink = exec.payment_link_url || 'https://rzp.io/i/revive_live';
    currentPhoneState.discountApplied = 0;
    currentPhoneState.isVoice = isVoice;

    // Update Voice Bot Screen elements in case user views it
    const voiceCaller = document.getElementById('voice-caller-name');
    const voiceScript = document.getElementById('voice-script-text');
    if (voiceCaller) voiceCaller.textContent = `${event.customer?.name || 'Customer'} (${formatINR(event.amount)})`;
    if (voiceScript) voiceScript.textContent = `"${plan.message_payload || `Namaste ${customerName} ji! Razorpay Revive accounts team se call hai. Aapka payment of ${formatINR(event.amount)} pending hai...`}"`;

    if (isVoice) {
        switchPhoneMode('voice');
        if (window.lucide) lucide.createIcons();
        return;
    } else {
        switchPhoneMode('whatsapp');
    }

    if (isBlocked) {
        chatArea.innerHTML = `
            <div class="text-center py-6 space-y-3">
                <div class="w-12 h-12 rounded-full bg-red-500/20 border border-red-500/40 flex items-center justify-center mx-auto">
                    <i data-lucide="shield-alert" class="w-6 h-6 text-red-400"></i>
                </div>
                <div class="text-red-400 text-xs font-semibold">Guardrail Security Stop Triggered</div>
                <div class="text-slate-400 text-[10px] px-3 bg-[#0f172a] p-2 rounded-lg border border-slate-800">
                    ${data.guardrail_verdict?.rejection_reason || 'Policy ceiling reached. Outbound outreach blocked to prevent spam.'}
                </div>
            </div>`;
        if (window.lucide) lucide.createIcons();
        return;
    }

    const msg = (plan.message_payload || `Namaste ${customerName}! Aapka ${formatINR(event.amount)} ka payment pura nahi ho paya. Niche diye button se 1-click me pay karein:`)
        .replace('{payment_link}', '');

    chatArea.innerHTML = `
        <div class="text-center text-slate-500 text-[9px] py-1 mb-1">Today</div>
        
        <!-- Business message bubble -->
        <div class="chat-bubble-green px-3 py-2 text-[11px] text-slate-200 max-w-[240px] leading-relaxed shadow">
            ${msg}
            <div class="text-right text-[8px] text-green-300 mt-1">${timeStr} ✓✓</div>
        </div>

        <!-- Interactive Quick Action Buttons -->
        <div class="flex flex-col space-y-1.5 mt-2 ml-1" id="phone-quick-actions">
            <button type="button" onclick="simulatePayNow(${currentPhoneState.amount})" id="btn-phone-pay" class="w-full py-2 px-3 rounded-lg bg-[#25d366] hover:bg-[#20bd5a] text-[#075e54] font-bold text-[11px] shadow flex items-center justify-center space-x-1.5 transition transform active:scale-95">
                <i data-lucide="credit-card" class="w-3.5 h-3.5"></i>
                <span id="btn-phone-pay-label">Pay ${formatINR(currentPhoneState.amount)} via UPI Now</span>
            </button>
            <div class="flex space-x-1.5">
                <button type="button" onclick="applyCouponCode(5)" id="btn-phone-coupon" class="flex-1 py-1.5 px-2 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-400 text-[10px] font-medium transition flex items-center justify-center space-x-1">
                    <i data-lucide="tag" class="w-3 h-3"></i>
                    <span>Apply 5% Off</span>
                </button>
                <button type="button" onclick="switchPhoneMode('voice')" class="py-1.5 px-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-medium transition flex items-center justify-center space-x-1">
                    <i data-lucide="phone" class="w-3 h-3 text-emerald-400"></i>
                    <span>Call AI</span>
                </button>
            </div>
        </div>

        <div id="phone-dynamic-chat-stream" class="space-y-2 pt-2"></div>
    `;

    if (window.lucide) lucide.createIcons();
}

// ══════════════════════════════════════════
// INTERACTIVE PHONE ACTIONS
// ══════════════════════════════════════════

// 1. Simulate Instant In-Phone UPI Payment
function simulatePayNow(amount) {
    const payBtn = document.getElementById('btn-phone-pay');
    const payBtnLabel = document.getElementById('btn-phone-pay-label');
    const stream = document.getElementById('phone-dynamic-chat-stream');
    const actions = document.getElementById('phone-quick-actions');
    const timeStr = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

    if (payBtn) {
        payBtn.disabled = true;
        payBtn.classList.add('opacity-80');
        payBtn.innerHTML = `<span class="animate-spin inline-block mr-1.5">&#9696;</span> Connecting GooglePay / PhonePe...`;
    }

    setTimeout(() => {
        // Play payment success synthesizer chime via Web Audio API!
        playPaymentSuccessChime();

        if (actions) actions.classList.add('hidden');

        const payRef = 'pay_' + Math.random().toString(36).substring(2, 9).toUpperCase();

        if (stream) {
            stream.innerHTML += `
                <!-- Customer sent payment -->
                <div class="flex justify-end">
                    <div class="chat-bubble-white px-3 py-1.5 text-[11px] text-slate-200 max-w-[200px] shadow">
                        💳 Paid ${formatINR(amount)} via UPI Autopay
                        <div class="text-right text-[8px] text-slate-500 mt-0.5">${timeStr}</div>
                    </div>
                </div>

                <!-- Instant Razorpay Receipt Confirmation -->
                <div class="chat-bubble-green px-3 py-2 text-[11px] text-slate-200 max-w-[240px] leading-relaxed shadow border border-emerald-400/30">
                    <div class="font-bold text-emerald-300 flex items-center space-x-1">
                        <i data-lucide="check-circle-2" class="w-3.5 h-3.5"></i>
                        <span>Payment Received!</span>
                    </div>
                    <div class="text-[10px] text-slate-300 mt-1">
                        Thank you, ${currentPhoneState.customerName}! Your payment of <b>${formatINR(amount)}</b> is confirmed.
                    </div>
                    <div class="text-[9px] text-green-300 font-mono mt-1 pt-1 border-t border-emerald-700/50">
                        Ref: ${payRef} • Order ID: ${currentPhoneState.orderId}
                    </div>
                    <div class="text-right text-[8px] text-green-300 mt-0.5">${timeStr} ✓✓</div>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
        }

        // Dynamically increment dashboard metrics in real-time!
        incrementDashboardMetrics(amount);

        // Auto-scroll chat to bottom
        const chatArea = document.getElementById('phone-chat-area');
        if (chatArea) chatArea.scrollTop = chatArea.scrollHeight;
    }, 1200);
}

// 2. Interactive 5% Coupon Discount
function applyCouponCode(discountPct) {
    if (currentPhoneState.discountApplied > 0) return;

    const discountAmount = Math.round(currentPhoneState.amount * (discountPct / 100));
    const newAmount = currentPhoneState.amount - discountAmount;
    currentPhoneState.amount = newAmount;
    currentPhoneState.discountApplied = discountPct;

    const stream = document.getElementById('phone-dynamic-chat-stream');
    const couponBtn = document.getElementById('btn-phone-coupon');
    const payBtnLabel = document.getElementById('btn-phone-pay-label');
    const timeStr = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

    if (couponBtn) {
        couponBtn.disabled = true;
        couponBtn.classList.add('opacity-50');
        couponBtn.innerHTML = `✓ 5% Applied`;
    }

    if (payBtnLabel) {
        payBtnLabel.textContent = `Pay ${formatINR(newAmount)} via UPI Now`;
    }

    if (stream) {
        stream.innerHTML += `
            <div class="flex justify-end">
                <div class="chat-bubble-white px-2.5 py-1 text-[10px] text-slate-200">
                    Applied code REVIVE5 🎁
                </div>
            </div>
            <div class="chat-bubble-green px-3 py-1.5 text-[10px] text-slate-200 max-w-[220px]">
                🎉 <b>Coupon REVIVE5 applied!</b> You saved <b>${formatINR(discountAmount)}</b>. Updated payable amount: <b>${formatINR(newAmount)}</b>.
                <div class="text-right text-[8px] text-green-300 mt-0.5">${timeStr} ✓✓</div>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
    }

    const chatArea = document.getElementById('phone-chat-area');
    if (chatArea) chatArea.scrollTop = chatArea.scrollHeight;
}

// 3. Interactive Working Text Reply Field
function handleCustomerSendMessage(event) {
    event.preventDefault();
    const input = document.getElementById('phone-message-input');
    if (!input || !input.value.trim()) return;

    const userText = input.value.trim();
    input.value = '';

    const stream = document.getElementById('phone-dynamic-chat-stream');
    const timeStr = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

    if (stream) {
        // Render customer user bubble
        stream.innerHTML += `
            <div class="flex justify-end">
                <div class="chat-bubble-white px-3 py-1.5 text-[11px] text-slate-200 max-w-[210px] shadow">
                    ${userText}
                    <div class="text-right text-[8px] text-slate-500 mt-0.5">${timeStr}</div>
                </div>
            </div>
            <div id="phone-typing-indicator" class="chat-bubble-green px-3 py-2 text-[10px] text-green-200 w-16 shadow">
                <span class="typing-dot">●</span> <span class="typing-dot">●</span> <span class="typing-dot">●</span>
            </div>
        `;
    }

    const chatArea = document.getElementById('phone-chat-area');
    if (chatArea) chatArea.scrollTop = chatArea.scrollHeight;

    // AI Agent Smart Context-Aware Response
    setTimeout(() => {
        const typing = document.getElementById('phone-typing-indicator');
        if (typing) typing.remove();

        let aiReply = '';
        const lower = userText.toLowerCase();

        if (lower.includes('discount') || lower.includes('offer') || lower.includes('coupon')) {
            applyCouponCode(5);
            return;
        } else if (lower.includes('fail') || lower.includes('why') || lower.includes('karan') || lower.includes('issue')) {
            aiReply = `Aapke issuing bank switch (HDFC/SBI) me temporary downtime tha. Abhi gateway clear hai — aap bina kisi issue ke dubara pay kar sakte hain.`;
        } else if (lower.includes('later') || lower.includes('kal') || lower.includes('baad me') || lower.includes('remind')) {
            aiReply = `Bilkul! Humne aapka order 24 ghante ke liye reserve kar diya hai. Kal subah 10:00 AM par aapko ek safe reminder bhej denge.`;
        } else if (lower.includes('call') || lower.includes('phone') || lower.includes('voice') || lower.includes('talk')) {
            switchPhoneMode('voice');
            return;
        } else if (lower.includes('pay') || lower.includes('done') || lower.includes('paid')) {
            simulatePayNow(currentPhoneState.amount);
            return;
        } else {
            aiReply = `Namaste ${currentPhoneState.customerName}! Aap niche diye button se direct UPI ya Credit Card use karke checkout complete kar sakte hain.`;
        }

        if (stream) {
            stream.innerHTML += `
                <div class="chat-bubble-green px-3 py-2 text-[11px] text-slate-200 max-w-[240px] leading-relaxed shadow">
                    ${aiReply}
                    <div class="text-right text-[8px] text-green-300 mt-1">${timeStr} ✓✓</div>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
        }

        if (chatArea) chatArea.scrollTop = chatArea.scrollHeight;
    }, 700);
}

// 4. Synthesizer Chime for Payment Success (Web Audio API - Zero External Files)
function playPaymentSuccessChime() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const now = ctx.currentTime;

        const osc1 = ctx.createOscillator();
        const gain1 = ctx.createGain();
        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(523.25, now); // C5
        osc1.frequency.exponentialRampToValueAtTime(783.99, now + 0.15); // G5
        osc1.frequency.exponentialRampToValueAtTime(1046.50, now + 0.3); // C6
        gain1.gain.setValueAtTime(0.2, now);
        gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.45);

        osc1.connect(gain1);
        gain1.connect(ctx.destination);
        osc1.start(now);
        osc1.stop(now + 0.45);
    } catch (e) {
        console.warn('Web Audio not supported or blocked:', e);
    }
}

// 5. Speech Synthesis for Voice Bot (Web Speech API)
function playVoiceAudio() {
    const btnLabel = document.getElementById('voice-audio-btn-label');
    const textToSpeak = `Namaste! Yeh Acme Corp accounts department se Razorpay Revive AI assistant hai. Aapka payment pending hai. Kya aap abhi payment complete karna chahte hain?`;

    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(textToSpeak);
        utterance.rate = 0.95;
        utterance.pitch = 1.0;

        if (btnLabel) btnLabel.textContent = '🔊 Playing Agent Audio...';

        utterance.onend = () => {
            if (btnLabel) btnLabel.textContent = '🔊 Listen to AI Agent Voice';
        };

        utterance.onerror = () => {
            if (btnLabel) btnLabel.textContent = '🔊 Listen to AI Agent Voice';
        };

        window.speechSynthesis.speak(utterance);
    } else {
        alert('Voice simulation audio:\n\n' + textToSpeak);
    }
}

function recordPromiseToPay() {
    alert('✅ Promise-to-Pay Recorded!\n\nCustomer committed to payment settlement within 48 hours. Follow-up dunning reminder scheduled for Monday 10:00 AM IST.');
    switchPhoneMode('whatsapp');
}

function hangUpVoiceCall() {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    switchPhoneMode('whatsapp');
}

function incrementDashboardMetrics(amount) {
    const atRiskEl = document.getElementById('kpi-at-risk');
    const recEl = document.getElementById('kpi-recovered');
    const netEl = document.getElementById('kpi-net-value');

    const currentRec = parseFloat((recEl?.textContent || '0').replace(/[^0-9.-]+/g, '')) || 0;
    const newRec = currentRec + amount;

    if (recEl) recEl.textContent = formatINR(newRec);
    if (netEl) netEl.textContent = formatINR(newRec);
}

// ══════════════════════════════════════════
// SIMULATION
// ══════════════════════════════════════════
async function runSimulation() {
    const btn = document.getElementById('btn-simulate');
    const scenario = document.getElementById('scenario-select').value;
    const amount = parseFloat(document.getElementById('amount-input').value) || 2499;
    const retryCount = parseInt(document.getElementById('retry-select').value) || 0;

    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">&#9696;</span> Diagnosing...`;

    try {
        const res = await fetch('/api/recovery/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenario_type: scenario,
                amount: amount,
                retry_count: retryCount,
                policy: getMerchantPolicy(),
            })
        });
        if (!res.ok) { const t = await res.text(); throw new Error(`HTTP ${res.status}: ${t}`); }
        const data = await res.json();
        renderDecisionTrace(data);
        renderPhoneChat(data);
        await fetchMetrics();
        await fetchAuditLogs();
    } catch (err) {
        alert('Simulation error: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="sparkles" class="w-4 h-4"></i><span>Trigger Recovery Loop</span>`;
        if (window.lucide) lucide.createIcons();
    }
}

// ══════════════════════════════════════════
// DECISION TRACE DAG
// ══════════════════════════════════════════
function renderDecisionTrace(data) {
    const container = document.getElementById('decision-trace-container');
    const eventIdSpan = document.getElementById('trace-event-id');
    if (eventIdSpan && data?.event?.event_id) eventIdSpan.textContent = `Event #${data.event.event_id}`;

    const diag = data.diagnosis || {};
    const plan = data.plan || {};
    const verdict = data.guardrail_verdict || {};
    const exec = data.execution || {};
    const isRec = exec.status === 'RECOVERED';
    const isRetry = exec.status === 'SCHEDULED_RETRY';
    const statusColor = isRec ? 'text-emerald-400' : isRetry ? 'text-blue-400' : 'text-amber-400';

    container.innerHTML = `
        <div class="bg-[#091224] border border-slate-800 rounded-lg p-3 text-xs space-y-1">
            <div class="flex items-center space-x-2 text-slate-400">
                <span class="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-[10px]">1</span>
                <span class="font-semibold text-slate-200">Failure Ingestion</span>
            </div>
            <div class="pl-7 text-slate-300">
                Error <code class="bg-slate-800 text-amber-300 px-1 py-0.5 rounded text-[10px]">${data.event?.error_code || 'N/A'}</code> for ${data.event?.customer?.name || 'Customer'} (${formatINR(data.event?.amount)}, Retry: ${data.event?.retry_count || 0})
            </div>
        </div>
        <div class="bg-[#091224] border border-slate-800 rounded-lg p-3 text-xs space-y-1">
            <div class="flex items-center space-x-2 text-slate-400">
                <span class="w-5 h-5 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold text-[10px]">2</span>
                <span class="font-semibold text-slate-200">Classification</span>
                <span class="ml-auto text-[10px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 font-mono">${((diag.confidence_score || 0) * 100).toFixed(0)}%</span>
            </div>
            <div class="pl-7 text-slate-300"><b class="text-purple-300">${diag.category || 'N/A'}</b> (${diag.is_transient ? 'Transient' : 'Permanent'})<br><span class="text-slate-400 italic text-[10px]">${diag.root_cause_explanation || ''}</span></div>
        </div>
        <div class="bg-[#091224] border border-slate-800 rounded-lg p-3 text-xs space-y-1">
            <div class="flex items-center space-x-2 text-slate-400">
                <span class="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-[10px]">3</span>
                <span class="font-semibold text-slate-200">Intervention</span>
            </div>
            <div class="pl-7 text-slate-300"><span class="text-indigo-300 font-mono text-[10px]">${plan.action_type || 'N/A'}</span> via <b>${plan.channel || 'N/A'}</b> (${plan.delay_minutes || 0}m delay)<br>Success: <b>${((plan.expected_success_probability || 0) * 100).toFixed(0)}%</b> | Cost: <b>${formatINR(plan.cost_of_intervention_inr)}</b>${(plan.discount_percentage || 0) > 0 ? ` | <span class="text-amber-300">${plan.discount_percentage}% discount</span>` : ''}</div>
        </div>
        <div class="bg-[#091224] border border-slate-800 rounded-lg p-3 text-xs space-y-1">
            <div class="flex items-center space-x-2 text-slate-400">
                <span class="w-5 h-5 rounded-full bg-teal-500/20 text-teal-400 flex items-center justify-center font-bold text-[10px]">4</span>
                <span class="font-semibold text-slate-200">Guardrails</span>
                <span class="ml-auto text-[10px] px-1.5 py-0.5 rounded font-bold ${verdict.is_approved ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}">${verdict.is_approved ? 'APPROVED' : 'BLOCKED'}</span>
            </div>
            <div class="pl-7 text-slate-300"><span class="text-teal-300 text-[10px]">${verdict.mitigation_applied || 'Passed all checks'}</span>${verdict.rejection_reason ? `<br><span class="text-red-400 text-[10px]">${verdict.rejection_reason}</span>` : ''}</div>
        </div>
        <div class="bg-[#091224] border border-slate-800 rounded-lg p-3 text-xs space-y-1">
            <div class="flex items-center space-x-2 text-slate-400">
                <span class="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-[10px]">5</span>
                <span class="font-semibold text-slate-200">Execution</span>
                <span class="ml-auto text-[10px] font-bold ${statusColor}">${exec.status || 'EXECUTED'}</span>
            </div>
            <div class="pl-7 text-slate-300">Recovered: <span class="${isRec ? 'text-emerald-400 font-bold' : ''}">${formatINR(exec.money_recovered_inr)}</span> (Net: ${formatINR(exec.net_value_saved_inr)})${exec.payment_link_url ? `<br><a href="${exec.payment_link_url}" target="_blank" class="text-blue-400 hover:underline text-[10px]">${exec.payment_link_url}</a>` : ''}</div>
        </div>`;
    if (window.lucide) lucide.createIcons();
}

// ══════════════════════════════════════════
// CHARTS (Chart.js)
// ══════════════════════════════════════════
let categoryBarChart = null;
let channelDonutChart = null;

function renderCharts(summary) {
    const catCtx = document.getElementById('chart-category-bar')?.getContext('2d');
    if (!catCtx) return;

    const cats = Object.entries(summary.breakdown_by_category || {});
    const catLabels = cats.map(([k]) => k.replace(/_/g, ' ').replace(/\b\w/g, c => c));
    const catRecovered = cats.map(([, v]) => v.recovered_inr || 0);
    const catAtRisk = cats.map(([, v]) => v.at_risk_inr || 0);

    if (categoryBarChart) categoryBarChart.destroy();
    categoryBarChart = new Chart(catCtx, {
        type: 'bar',
        data: {
            labels: catLabels,
            datasets: [
                { label: 'At Risk (₹)', data: catAtRisk, backgroundColor: 'rgba(239,68,68,0.3)', borderColor: 'rgba(239,68,68,0.8)', borderWidth: 1 },
                { label: 'Recovered (₹)', data: catRecovered, backgroundColor: 'rgba(16,185,129,0.4)', borderColor: 'rgba(16,185,129,0.9)', borderWidth: 1 },
            ]
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } } }, title: { display: true, text: 'Recovery by Failure Category', color: '#e2e8f0', font: { size: 12 } } },
            scales: { x: { ticks: { color: '#64748b', font: { size: 8 }, maxRotation: 45 }, grid: { color: '#1e293b' } }, y: { ticks: { color: '#64748b', font: { size: 9 } }, grid: { color: '#1e293b' } } }
        }
    });

    const chCtx = document.getElementById('chart-channel-donut')?.getContext('2d');
    if (!chCtx) return;

    const channels = Object.entries(summary.channel_breakdown || {});
    const chLabels = channels.map(([k]) => k);
    const chValues = channels.map(([, v]) => v.recovered_inr || 0);
    const chColors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4'];

    if (channelDonutChart) channelDonutChart.destroy();
    channelDonutChart = new Chart(chCtx, {
        type: 'doughnut',
        data: { labels: chLabels, datasets: [{ data: chValues, backgroundColor: chColors.slice(0, chLabels.length), borderWidth: 0 }] },
        options: {
            responsive: true,
            cutout: '60%',
            plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 9 }, padding: 8 } }, title: { display: true, text: 'Revenue by Channel', color: '#e2e8f0', font: { size: 11 } } }
        }
    });

    const statsEl = document.getElementById('chart-summary-stats');
    if (statsEl) {
        statsEl.innerHTML = `
            <div class="text-3xl font-bold text-emerald-400">${summary.gross_recovery_rate_pct?.toFixed(1) || 0}%</div>
            <div class="text-xs text-slate-400 mt-1">Gross Recovery</div>
            <div class="text-xl font-bold text-purple-400 mt-3">${summary.roi_multiple?.toFixed(0) || 0}x</div>
            <div class="text-xs text-slate-400 mt-1">ROI Multiple</div>
            <div class="text-sm font-bold text-blue-400 mt-3">${formatINR(summary.net_economic_value_inr)}</div>
            <div class="text-xs text-slate-400 mt-1">Net Value</div>`;
    }
}

// ══════════════════════════════════════════
// BATCH BENCHMARK
// ══════════════════════════════════════════
async function runBatchBenchmark() {
    const btn = document.getElementById('btn-benchmark');
    const container = document.getElementById('benchmark-results-container');
    const tbody = document.getElementById('benchmark-table-body');

    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">&#9696;</span> Evaluating 100+ Transactions...`;

    try {
        const res = await fetch('/api/benchmark/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ policy: getMerchantPolicy() }),
        });
        if (!res.ok) { const t = await res.text(); throw new Error(`HTTP ${res.status}: ${t}`); }
        const summary = await res.json();

        if (container) container.classList.remove('hidden');
        if (tbody && summary.breakdown_by_category) {
            tbody.innerHTML = Object.entries(summary.breakdown_by_category).map(([cat, d]) => {
                const rate = Number(d?.recovery_rate_pct) || 0;
                return `<tr class="hover:bg-slate-800/40">
                    <td class="p-2 font-mono text-slate-200 text-[10px]">${cat}</td>
                    <td class="p-2">${d?.count || 0}</td>
                    <td class="p-2">${formatINR(d?.at_risk_inr)}</td>
                    <td class="p-2 text-emerald-400 font-semibold">${formatINR(d?.recovered_inr)}</td>
                    <td class="p-2 font-bold ${rate > 60 ? 'text-emerald-400' : 'text-blue-400'}">${rate.toFixed(1)}%</td>
                </tr>`;
            }).join('');
        }

        renderCharts(summary);
        await fetchMetrics();
        await fetchAuditLogs();
    } catch (err) {
        alert('Benchmark error: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="play" class="w-4 h-4"></i><span>Execute 100+ Batch Benchmark</span>`;
        if (window.lucide) lucide.createIcons();
    }
}

// ══════════════════════════════════════════
// RESET LOGS
// ══════════════════════════════════════════
async function resetLogs() {
    if (!confirm('Clear all audit logs?')) return;
    try {
        await fetch('/api/audit-logs/clear', { method: 'POST' });
        await fetchMetrics();
        await fetchAuditLogs();
        initDefaultPhoneSimulator();
    } catch (err) { console.error('Reset error:', err); }
}
