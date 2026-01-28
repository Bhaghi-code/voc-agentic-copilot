from typing import List, Dict

def generate_weekly_pm_brief(question: str, evidence: List[Dict]) -> str:
    # IMPORTANT: Return a STRING (markdown), not JSON/dict.

    evidence_ids = [str(e.get("evidence_id")) for e in evidence if e.get("evidence_id") is not None]
    evidence_ids_txt = ", ".join(evidence_ids) if evidence_ids else "None"

    md = f"""
## Weekly PM Brief — Payments Reliability

### This week’s headline
Investigate Android payment failures end-to-end and validate whether the issue is **technical**, **UX-driven**, or both.

### Why it matters
Payment failures directly impact **conversion**, **revenue**, and **user trust**. Android-specific issues can quietly grow if we don’t measure funnel drop-offs by platform.

### Evidence used
- Evidence IDs: {evidence_ids_txt}

### What we think is happening
- Users may be experiencing **confusing payment UI states** (success/failure ambiguity).
- There may be Android-only **handoff/auth/SDK** issues (e.g., 3DS, webview redirects, device/network variance).

### Metrics to watch
- Payment funnel by step (Android vs iOS): attempt → auth → confirm → success
- Failure reasons distribution (gateway codes mapped to user-visible errors)
- Drop-off rate at “confirm payment” step

### Proposed plan (next 5 days)
- Day 1–2: add logs + dashboard for Android payment steps
- Day 3: replicate on top devices/OS versions; capture screen recordings
- Day 4: ship quick UX patch for error states if needed
- Day 5: validate impact with funnel deltas + support ticket trend

### Risks / dependencies
- Payment provider SDK version differences
- Error mapping may be hiding true causes (generic “failed”)

### Draft Jira ticket (copy/paste)
**Title:** Investigate and Resolve Payment Failures on Android  
**Severity:** S2  
**Problem:** Reports of payment failures on Android with unclear cause; evidence suggests possible UI confusion patterns.  
**Acceptance Criteria:**  
- Funnel + error logging added for Android payment flow  
- Failure rate measured and compared vs iOS  
- Root cause identified (UX vs integration vs backend)  
- Fix deployed + verified via metrics improvement
"""
    return md.strip()
