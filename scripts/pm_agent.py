from typing import List, Dict

def run_agentic_analysis(question: str, evidence: List[Dict]) -> str:
    # In your real version, call your LLM here.
    # IMPORTANT: Return a STRING (markdown), not JSON/dict.

    evidence_lines = []
    for e in evidence:
        evidence_lines.append(
            f"- Evidence #{e.get('evidence_id','?')} ({e.get('platform','?')} {e.get('country','?')}, sim {e.get('similarity',0):.3f}): {e.get('text','')}"
        )

    md = f"""
## Summary
Payment failures on Android may be caused by a mix of **UI confusion** (users think payment failed, abandon, or mis-tap) and **platform-specific integration issues** (SDK, network, or auth differences).

## What the evidence suggests
{chr(10).join(evidence_lines) if evidence_lines else "- No evidence retrieved."}

## Likely root-cause buckets
- **UI/UX:** confusing CTA, unclear error states, payment method selection friction, redirect issues
- **Integration:** Android SDK mismatch, webview/3DS handoff problems, billing permissions, play services
- **Backend:** idempotency handling, gateway error mapping, retries causing double-fail perception

## Recommended next steps
- Add **structured logging** on Android payment flow (start → method selected → auth → confirmation).
- Compare Android vs iOS funnel: **attempt rate, auth-fail rate, drop-off step**.
- Run targeted testing on Android devices with varied OS versions + network conditions.

## Follow-up questions
- Are there Android-specific error logs or user reports tied to payment failures?
- Is Android payment UI identical to iOS, or are there platform-specific differences?
- What is the payment failure rate on Android vs iOS?
"""
    return md.strip()
