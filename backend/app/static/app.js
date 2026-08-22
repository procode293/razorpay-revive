/**
 * Razorpay Revive — Frontend Dashboard Logic
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    fetchMetrics();
    fetchAuditLogs();
});

function formatINR(val) {
    return '₹' + Number(val || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

async function fetchMetrics() {
    try {
        const res = await fetch('/api/metrics');
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById('kpi-at-risk').textContent = formatINR(data.total_at_risk_inr);
        document.getElementById('kpi-recovered').textContent = formatINR(data.total_recovered_inr);
        document.getElementById('kpi-rate').textContent = (data.recovery_rate_pct || 0).toFixed(1) + '%';
        document.getElementById('kpi-net-value').textContent = formatINR(data.net_value_saved_inr);
        document.getElementById('kpi-guardrail').textContent = (data.guardrail_compliance_pct || 100).toFixed(1) + '%';
        document.getElementById('kpi-recovered-count').textContent = `${data.recovered_count || 0} of ${data.total_events || 0} saved`;
    } catch (err) {
        console.error('Failed to fetch metrics:', err);
    }
}

async function fetchAuditLogs() {
    const list = document.getElementById('audit-feed-list');
    try {
        const res = await fetch('/api/audit-logs?limit=25');
        if (!res.ok) return;
        const data = await res.json();

        if (!data.traces || data.traces.length === 0) {
            list.innerHTML = `<div class="text-center py-6 text-slate-500 text-xs">No audit logs found. Run a simulation or benchmark above.</div>`;
            return;
        }

        list.innerHTML = data.traces.map(t => {
            const isRec = t.status === 'RECOVERED';
            const isRetry = t.status === 'SCHEDULED_RETRY';
            const isEsc = t.status === 'ESCALATED' || t.status === 'BLOCKED_BY_GUARDRAIL';
            const badgeBg = isRec ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                            isRetry ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                            'bg-amber-500/10 text-amber-400 border-amber-500/20';

            return `
                <div class="bg-[#091224] border border-slate-800 rounded-lg p-3 text-xs space-y-1.5 hover:border-slate-700 transition">
                    <div class="flex items-center justify-between">
                        <span class="font-semibold text-slate-200">${t.customer_name || 'Customer'} (Order #${t.order_id || 'N/A'})</span>
                        <span class="px-2 py-0.5 rounded-full border text-[10px] font-semibold ${badgeBg}">${t.status}</span>
                    </div>
                    <div class="flex items-center justify-between text-slate-400">
                        <span>${t.category} &bull; ${t.payment_method}</span>
                        <span class="font-mono text-slate-200">${formatINR(t.amount)} &rarr; <span class="${isRec ? 'text-emerald-400 font-bold' : ''}">${formatINR(t.money_recovered)}</span></span>
                    </div>
                    ${t.payment_link ? `<div class="text-blue-400 truncate text-[11px]"><a href="${t.payment_link}" target="_blank" class="hover:underline flex items-center space-x-1"><span>🔗 ${t.payment_link}</span></a></div>` : ''}
                </div>
            `;
        }).join('');
    } catch (err) {
        console.error('Failed to fetch audit logs:', err);
    }
}

async function runSimulation() {
    const btn = document.getElementById('btn-simulate');
    const scenario = document.getElementById('scenario-select').value;
    const amount = parseFloat(document.getElementById('amount-input').value) || 2499;
    const retryCount = parseInt(document.getElementById('retry-select').value) || 0;

    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">&#9696;</span> Diagnosing & Executing...`;

    try {
        const res = await fetch('/api/recovery/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenario_type: scenario,
                amount: amount,
                retry_count: retryCount
            })
        });

        if (!res.ok) throw new Error('Simulation API failed');
        const data = await res.json();

        renderDecisionTrace(data);
        fetchMetrics();
        fetchAuditLogs();
    } catch (err) {
        alert('Simulation error: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="sparkles" class="w-4 h-4 mr-2 inline"></i><span>Trigger Autonomous Recovery Loop</span>`;
        lucide.createIcons();
    }
}

function renderDecisionTrace(data) {
    const container = document.getElementById('decision-trace-container');
    const eventIdSpan = document.getElementById('trace-event-id');
    
    eventIdSpan.textContent = `Event #${data.event.event_id}`;

    const diag = data.diagnosis;
    const plan = data.plan;
    const verdict = data.guardrail_verdict;
    const exec = data.execution;

    const isRec = exec.status === 'RECOVERED';
    const isRetry = exec.status === 'SCHEDULED_RETRY';
    const statusColor = isRec ? 'text-emerald-400' : isRetry ? 'text-blue-400' : 'text-amber-400';

    container.innerHTML = `
        <!-- Step 1: Ingested Event -->
        <div class="bg-[#091224] border border-slate-800 rounded-lg p-3 text-xs space-y-1">
            <div class="flex items-center space-x-2 text-slate-400">
                <span class="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-[10px]">1</span>
                <span class="font-semibold text-slate-200">Failure Ingestion & Error Code Parsing</span>
            </div>
            <div class="pl-7 text-slate-300">
                Received error <code class="bg-slate-800 text-amber-300 px-1 py-0.5 rounded">${data.event.error_code}</code> for ${data.event.customer.name} (Amount: <b>${formatINR(data.event.amount)}</b>, Method: <b>${data.event.payment_method}</b>, Retry Count: <b>${data.event.retry_count}</b>).
            </div>
        </div>

        <!-- Step 2: Diagnostic Reasoning -->
        <div class="bg-[#091224] border border-slate-800 rounded-lg p-3 text-xs space-y-1">
            <div class="flex items-center space-x-2 text-slate-400">
                <span class="w-5 h-5 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold text-[10px]">2</span>
                <span class="font-semibold text-slate-200">Failure Taxonomy Classification</span>
                <span class="ml-auto text-[10px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 font-mono">Confidence: ${(diag.confidence_score * 100).toFixed(0)}%</span>
            </div>
            <div class="pl-7 text-slate-300 space-y-1">
                <div><b>Category:</b> <span class="text-purple-300">${diag.category}</span> (${diag.is_transient ? 'Transient' : 'Permanent'})</div>
                <div class="text-slate-400 italic font-sans">${diag.root_cause_explanation}</div>
            </div>
        </div>

        <!-- Step 3: Dynamic Plan Formulation -->
        <div class="bg-[#091224] border border-slate-800 rounded-lg p-3 text-xs space-y-1">
            <div class="flex items-center space-x-2 text-slate-400">
                <span class="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-[10px]">3</span>
                <span class="font-semibold text-slate-200">Formulate Intervention Strategy</span>
            </div>
            <div class="pl-7 text-slate-300 space-y-1">
                <div><b>Action:</b> <span class="text-indigo-300 font-mono">${plan.action_type}</span> on channel <b>${plan.channel}</b> (Delay: ${plan.delay_minutes}m)</div>
                <div><b>Unit Economics:</b> Est. Success: <b>${(plan.expected_success_probability * 100).toFixed(0)}%</b> | Cost: <b>${formatINR(plan.cost_of_intervention_inr)}</b></div>
                ${plan.discount_percentage > 0 ? `<div class="text-amber-300 font-medium">Incentive: ${plan.discount_percentage}% bounded promo discount applied.</div>` : ''}
            </div>
        </div>

        <!-- Step 4: Guardrail Verification -->
        <div class="bg-[#091224] border border-slate-800 rounded-lg p-3 text-xs space-y-1">
            <div class="flex items-center space-x-2 text-slate-400">
                <span class="w-5 h-5 rounded-full bg-teal-500/20 text-teal-400 flex items-center justify-center font-bold text-[10px]">4</span>
                <span class="font-semibold text-slate-200">Deterministic Safety & Compliance Guardrails</span>
                <span class="ml-auto text-[10px] px-1.5 py-0.5 rounded font-bold ${verdict.is_approved ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}">
                    ${verdict.is_approved ? 'APPROVED' : 'BLOCKED'}
                </span>
            </div>
            <div class="pl-7 text-slate-300 space-y-1">
                <div class="text-teal-300">${verdict.mitigation_applied || 'Passed all checks'}</div>
                ${verdict.rejection_reason ? `<div class="text-red-400 font-semibold">${verdict.rejection_reason}</div>` : ''}
            </div>
        </div>

        <!-- Step 5: Bounded Action Execution & Audit Sink -->
        <div class="bg-[#091224] border border-slate-800 rounded-lg p-3 text-xs space-y-1">
            <div class="flex items-center space-x-2 text-slate-400">
                <span class="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-[10px]">5</span>
                <span class="font-semibold text-slate-200">Action Execution & Immutable Sinking</span>
                <span class="ml-auto text-[10px] font-bold ${statusColor}">${exec.status}</span>
            </div>
            <div class="pl-7 text-slate-300 space-y-1">
                <div class="font-medium text-slate-200">Recovered: <span class="${isRec ? 'text-emerald-400 font-bold' : ''}">${formatINR(exec.money_recovered_inr)}</span> (Net Value: ${formatINR(exec.net_value_saved_inr)})</div>
                ${exec.payment_link_url ? `<div>Razorpay Dynamic Link: <a href="${exec.payment_link_url}" target="_blank" class="text-blue-400 hover:underline">${exec.payment_link_url}</a></div>` : ''}
                ${exec.razorpay_reference_id ? `<div class="text-slate-400 font-mono text-[10px]">Ref ID: ${exec.razorpay_reference_id}</div>` : ''}
            </div>
        </div>
    `;
    lucide.createIcons();
}

async function runBatchBenchmark() {
    const btn = document.getElementById('btn-benchmark');
    const container = document.getElementById('benchmark-results-container');
    const tbody = document.getElementById('benchmark-table-body');

    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">&#9696;</span> Evaluating 100+ Transactions...`;

    try {
        const res = await fetch('/api/benchmark/run', { method: 'POST' });
        if (!res.ok) throw new Error('Benchmark failed');
        const summary = await res.json();

        container.classList.remove('hidden');

        tbody.innerHTML = Object.entries(summary.breakdown_by_category).map(([cat, d]) => {
            return `
                <tr class="hover:bg-slate-800/40">
                    <td class="p-2 font-mono text-slate-200">${cat}</td>
                    <td class="p-2">${d.count}</td>
                    <td class="p-2">${formatINR(d.at_risk_inr)}</td>
                    <td class="p-2 text-emerald-400 font-semibold">${formatINR(d.recovered_inr)}</td>
                    <td class="p-2 font-bold ${d.recovery_rate_pct > 60 ? 'text-emerald-400' : 'text-blue-400'}">${d.recovery_rate_pct.toFixed(1)}%</td>
                </tr>
            `;
        }).join('');

        fetchMetrics();
        fetchAuditLogs();
    } catch (err) {
        alert('Benchmark error: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="play" class="w-4 h-4 mr-2 inline"></i><span>Execute 100+ Batch Benchmark Test</span>`;
        lucide.createIcons();
    }
}

async function resetLogs() {
    if (!confirm('Clear all audit logs?')) return;
    await fetch('/api/audit-logs/clear', { method: 'POST' });
    fetchMetrics();
    fetchAuditLogs();
}
