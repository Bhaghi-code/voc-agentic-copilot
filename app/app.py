import streamlit as st
from dataclasses import dataclass
from typing import Any, Optional
from io import BytesIO
import json
import re

# PDF (ReportLab)
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch

# Lottie
import requests
from streamlit_lottie import st_lottie

from scripts.search_feedback import search_feedback
from scripts.pm_agent import run_agentic_analysis
from scripts.weekly_pm_brief import generate_weekly_pm_brief


# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(
    page_title="Customer Feedback Intelligence Copilot",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------
# Lottie helpers
# ----------------------------
@st.cache_data(show_spinner=False)
def load_lottie_url(url: str):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


# You can replace these with any Lottie URLs you like
LOTTIE_SEARCH = "https://lottie.host/9d9c17c1-9d40-4a22-9c6f-0c4af0d6d173/6b1kFhW8sR.json"
LOTTIE_BRAIN  = "https://lottie.host/4a8d6128-fb1a-4f0d-bfe8-9c6d8f4dfc3f/6nX9vWwXyS.json"
LOTTIE_WEEK   = "https://lottie.host/ef4f8e2e-7a3a-4a02-9cc7-1f3d6e5f1bd7/4i0gqGvB1p.json"

lottie_search = load_lottie_url(LOTTIE_SEARCH)
lottie_brain = load_lottie_url(LOTTIE_BRAIN)
lottie_week = load_lottie_url(LOTTIE_WEEK)


# ----------------------------
# CSS (Pastel + Glassmorphism)
# ----------------------------
def inject_css():
    st.markdown(
        """
<style>
/* ---- Base colors ---- */
:root{
  --ink: #0f172a;
  --muted: #334155;
  --border: #e7e5ff;
  --card: rgba(255,255,255,0.75);
  --card-strong: rgba(255,255,255,0.85);
  --shadow: 0 12px 34px rgba(15,23,42,0.08);
  --grad-a: #fbf7ff;
  --grad-b: #f7fbff;
  --grad-c: #fbfffb;
}

/* Whole app background */
.stApp{
  background: linear-gradient(180deg, var(--grad-a) 0%, var(--grad-b) 50%, var(--grad-c) 100%) !important;
}

/* Typography */
html, body, [class*="css"]{
  color: var(--ink) !important;
}

/* Streamlit main container */
section.main > div { padding-top: 1.25rem; }

/* Sidebar */
[data-testid="stSidebar"]{
  background: rgba(255,255,255,0.70) !important;
  backdrop-filter: blur(10px);
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] *{
  color: var(--ink) !important;
}

/* Inputs */
.stTextInput > div > div,
.stTextArea > div > div,
.stSelectbox > div > div,
.stMultiSelect > div > div{
  background: var(--card-strong) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  box-shadow: none !important;
}
.stTextInput input, .stTextArea textarea{ color: var(--ink) !important; }

/* Slider label text */
.stSlider > div > div { color: var(--ink) !important; }

/* Buttons (gradient) */
.stButton button{
  border-radius: 14px !important;
  padding: 0.65rem 1rem !important;
  border: 0 !important;
  background: linear-gradient(90deg, #6d28d9 0%, #2563eb 100%) !important;
  color: #ffffff !important;
  box-shadow: var(--shadow) !important;
}
.stButton > button *{
  color: #ffffff !important;
  fill: #ffffff !important;
}
.stButton button:hover{ filter: brightness(1.05); }

/* Radio labels */
label, .stRadio div, .stRadio label{
  color: var(--ink) !important;
}

/* Metric cards */
[data-testid="stMetric"]{
  background: var(--card) !important;
  backdrop-filter: blur(10px);
  border: 1px solid var(--border) !important;
  border-radius: 18px !important;
  padding: 14px 14px 10px 14px !important;
  box-shadow: var(--shadow) !important;
}
[data-testid="stMetric"] *{ color: var(--ink) !important; }

/* Headings */
h1, h2, h3 { color: var(--ink) !important; }

/* Evidence cards */
.evidence-card{
  background: var(--card) !important;
  backdrop-filter: blur(10px);
  border: 1px solid var(--border) !important;
  border-radius: 18px;
  padding: 14px;
  margin-bottom: 10px;
  box-shadow: var(--shadow) !important;
}
.evidence-meta{
  color: var(--muted);
  font-size: 0.95rem;
  margin-bottom: 6px;
}
.evidence-text{
  color: var(--ink);
  font-size: 1rem;
  line-height: 1.5;
}

/* Divider */
hr{ border-top: 1px solid var(--border); }

/* Markdown bullets */
ul, li { color: var(--ink) !important; }

/* Subtle fade-in animation for main content */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.fade-in {
  animation: fadeUp 380ms ease-out;
}
</style>
        """,
        unsafe_allow_html=True
    )

inject_css()


# ----------------------------
# Data structures
# ----------------------------
@dataclass
class EvidenceItem:
    evidence_id: str
    platform: str
    country: str
    rating: Optional[int]
    similarity: float
    text: str


# ----------------------------
# Helpers: Safe text conversion (PREVENT JSON IN PDF)
# ----------------------------
def to_readable_text(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x.strip()
    if isinstance(x, (int, float, bool)):
        return str(x)

    if isinstance(x, dict):
        lines = []
        for k, v in x.items():
            k2 = str(k).replace("_", " ").title()
            if isinstance(v, (dict, list)):
                lines.append(f"{k2}:\n{to_readable_text(v)}")
            else:
                lines.append(f"{k2}: {to_readable_text(v)}")
        return "\n".join(lines).strip()

    if isinstance(x, list):
        out = []
        for item in x:
            s = to_readable_text(item)
            if not s:
                continue
            out.append(f"- {s}")
        return "\n".join(out).strip()

    try:
        return json.dumps(x, indent=2, ensure_ascii=False)
    except Exception:
        return str(x)


# ----------------------------
# PDF generation (ReportLab)
# ----------------------------
def markdownish_to_flowables(md_text: str):
    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "Base",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        textColor="#111827",
        alignment=TA_LEFT,
        spaceAfter=6
    )
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=16, leading=20, spaceAfter=10)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=17, spaceAfter=8)
    h3 = ParagraphStyle("H3", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=11.5, leading=15, spaceAfter=6)

    flow = []
    lines = (md_text or "").splitlines()
    bullet_buf = []

    def flush_bullets():
        nonlocal bullet_buf
        if bullet_buf:
            items = [ListItem(Paragraph(re.sub(r"^[\\-\\*]\\s+", "", b), base)) for b in bullet_buf]
            flow.append(ListFlowable(items, bulletType="bullet", leftIndent=18))
            flow.append(Spacer(1, 6))
            bullet_buf = []

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_bullets()
            continue

        if line.startswith("### "):
            flush_bullets()
            flow.append(Paragraph(line[4:], h3))
            continue
        if line.startswith("## "):
            flush_bullets()
            flow.append(Paragraph(line[3:], h2))
            continue
        if line.startswith("# "):
            flush_bullets()
            flow.append(Paragraph(line[2:], h1))
            continue

        if line.startswith("- ") or line.startswith("* "):
            bullet_buf.append(line)
            continue

        flush_bullets()
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        flow.append(Paragraph(safe, base))

    flush_bullets()
    return flow


def build_pdf_bytes(title: str, content: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=title
    )

    full = f"# {title}\n\n{content.strip()}\n"
    flowables = markdownish_to_flowables(full)
    doc.build(flowables)
    return buffer.getvalue()


# ----------------------------
# Retrieval
# ----------------------------
def run_retrieval(query: str, platform: str | None, country: str | None, top_k: int):
    hits = search_feedback(
        query=query,
        top_k=top_k,
        country=(country.strip() or None) if country else None,
        platform=(platform.strip() or None) if platform else None,
        user_type=None,  # ok if your wrapper ignores/doesn't use
    )

    results = []
    for h in hits:
        results.append(EvidenceItem(
            evidence_id=str(h.get("id")),
            platform=h.get("platform") or "",
            country=h.get("country") or "",
            rating=h.get("rating"),
            similarity=float(h.get("similarity") or 0.0),
            text=(h.get("text") or "").strip(),
        ))
    return results


# ----------------------------
# UI — Header
# ----------------------------
head_left, head_right = st.columns([0.78, 0.22], vertical_alignment="center")

with head_left:
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("✨ Customer Feedback Intelligence Copilot")
    st.caption("Agentic RAG → Evidence → Analysis → Jira-ready drafts")
    st.markdown("</div>", unsafe_allow_html=True)

with head_right:
    # Small decorative lottie (search) in header
    if lottie_search:
        st_lottie(lottie_search, height=90, key="lottie_header", speed=1, loop=True)


# Top mode toggle
mode = st.radio(
    "Mode",
    ["Evidence", "Agentic Analysis", "Weekly PM Brief"],
    horizontal=True,
    index=0
)

# Sidebar controls
with st.sidebar:
    st.header("Controls")
    query = st.text_area("Ask a PM question", value="Why is payment failing on Android?", height=100)

    platform = st.selectbox("Platform filter", options=["", "Android", "iOS", "Web"], index=0)
    country = st.text_input("Country filter (optional)", value="")

    top_k = st.slider("Top K matches", min_value=3, max_value=15, value=6)

    # Animated cue next to button (tiny lottie optional)
    run_btn = st.button("Run Retrieval 🔎", use_container_width=True)


# Session state
if "evidence" not in st.session_state:
    st.session_state.evidence = []
if "analysis_text" not in st.session_state:
    st.session_state.analysis_text = ""
if "weekly_text" not in st.session_state:
    st.session_state.weekly_text = ""


# Retrieval action (with spinner)
if run_btn:
    with st.spinner("Retrieving evidence..."):
        st.session_state.evidence = run_retrieval(query, platform or None, country.strip() or None, top_k)
        # clear downstream outputs when new retrieval happens
        st.session_state.analysis_text = ""
        st.session_state.weekly_text = ""


# Metrics row
col1, col2, col3 = st.columns(3)
matches = len(st.session_state.evidence)
top_score = max([e.similarity for e in st.session_state.evidence], default=0.0)
filter_label = f"{platform or 'All'} / {country.strip() or 'All'}"

col1.metric("Matches", matches)
col2.metric("Top score", f"{top_score:.3f}")
col3.metric("Filters", filter_label)

st.divider()


# ----------------------------
# Main content
# ----------------------------
if mode == "Evidence":
    st.header("🔎 Retrieved Evidence")

    if matches > 0:
        evidence_md = []
        for e in st.session_state.evidence:
            evidence_md.append(
                f"## Evidence #{e.evidence_id}\n"
                f"- Platform: {e.platform}\n"
                f"- Country: {e.country}\n"
                f"- Rating: {e.rating if e.rating is not None else 'N/A'}\n"
                f"- Similarity: {e.similarity:.3f}\n\n"
                f"{e.text}\n"
            )

        pdf_bytes = build_pdf_bytes("Retrieved Evidence", "\n".join(evidence_md))
        st.download_button(
            "Download Evidence (PDF) ⬇️",
            data=pdf_bytes,
            file_name="retrieved_evidence.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    for e in st.session_state.evidence:
        st.markdown(
            f"""
<div class="evidence-card fade-in">
  <div class="evidence-meta">
    <b>#{e.evidence_id}</b> &nbsp;•&nbsp; sim: {e.similarity:.3f} &nbsp;•&nbsp; {e.platform} {e.country} &nbsp;•&nbsp; rating: {e.rating if e.rating is not None else "N/A"}
  </div>
  <div class="evidence-text">{e.text}</div>
</div>
""",
            unsafe_allow_html=True
        )

elif mode == "Agentic Analysis":
    # optional lottie decoration
    headA, iconA = st.columns([0.8, 0.2], vertical_alignment="center")
    with headA:
        st.header("🧠 Agentic Analysis")
    with iconA:
        if lottie_brain:
            st_lottie(lottie_brain, height=75, key="lottie_brain", speed=1, loop=True)

    if matches == 0:
        st.info("Run retrieval first so the agent has evidence to ground the analysis.")
    else:
        if st.button("Generate Agentic Analysis", use_container_width=True):
            with st.spinner("Generating analysis..."):
                analysis = run_agentic_analysis(
                    question=query,
                    evidence=[e.__dict__ for e in st.session_state.evidence]
                )
                st.session_state.analysis_text = to_readable_text(analysis)

        if st.session_state.analysis_text:
            st.markdown(f'<div class="fade-in">{st.session_state.analysis_text}</div>', unsafe_allow_html=True)

            pdf_bytes = build_pdf_bytes("Agentic Analysis", st.session_state.analysis_text)
            st.download_button(
                "Download Agentic Analysis (PDF) ⬇️",
                data=pdf_bytes,
                file_name="agentic_analysis.pdf",
                mime="application/pdf",
                use_container_width=True
            )

elif mode == "Weekly PM Brief":
    headW, iconW = st.columns([0.8, 0.2], vertical_alignment="center")
    with headW:
        st.header("🗓️ Weekly PM Brief")
    with iconW:
        if lottie_week:
            st_lottie(lottie_week, height=75, key="lottie_week", speed=1, loop=True)

    if matches == 0:
        st.info("Run retrieval first so the brief is grounded in evidence.")
    else:
        if st.button("Generate Weekly PM Brief", use_container_width=True):
            with st.spinner("Generating brief..."):
                brief = generate_weekly_pm_brief(
                    question=query,
                    evidence=[e.__dict__ for e in st.session_state.evidence]
                )
                st.session_state.weekly_text = to_readable_text(brief)

        if st.session_state.weekly_text:
            st.markdown(f'<div class="fade-in">{st.session_state.weekly_text}</div>', unsafe_allow_html=True)

            pdf_bytes = build_pdf_bytes("Weekly PM Brief", st.session_state.weekly_text)
            st.download_button(
                "Download Weekly PM Brief (PDF) ⬇️",
                data=pdf_bytes,
                file_name="weekly_pm_brief.pdf",
                mime="application/pdf",
                use_container_width=True
            )
