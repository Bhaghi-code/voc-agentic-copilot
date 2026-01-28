# ✨ Customer Feedback Intelligence Copilot
**Agentic RAG → Evidence → Analysis → Jira-ready drafts**

A demo app that turns Voice-of-Customer feedback into:
1) **retrieved evidence** (via embeddings + pgvector),
2) **grounded agentic analysis**, and
3) a **Weekly PM Brief** you can export to PDF.

Built with **Streamlit**, **OpenAI embeddings**, and **Supabase Postgres + pgvector**.

---

## 🚀 What This Does
- Ask a PM question (e.g., “Why is payment failing on Android?”)
- Retrieve the most relevant feedback using **vector similarity**
- Generate:
  - **Evidence view** (top-k matches with similarity scores)
  - **Agentic Analysis** (grounded insights, hypotheses, next steps)
  - **Weekly PM Brief** (summary, trends, risks, recommendations)
- Export **Evidence / Analysis / Brief** as **PDF**

---

## ✨ Key Features
- **Semantic search (embeddings)** over feedback
- **Filters**: Platform, Country, Top-K
- **Agentic reasoning grounded in evidence** (no hallucinated claims)
- **PDF export** 
- **Pastel “glass” UI + Lottie animations** 

---

## 🧱 Architecture

### High-level flow
1. **Ingestion**: CSV feedback → embeddings → store in Supabase Postgres
2. **Retrieval**: user query → query embedding → `match_feedback()` pgvector search
3. **Synthesis**:
   - Evidence: render top-k matches
   - Agentic Analysis: LLM uses evidence as grounding
   - Weekly Brief: LLM summarizes into PM-friendly weekly format
4. **Export**: ReportLab generates PDFs from text (no raw JSON dumps)

### Diagram (ASCII)
```text
                ┌───────────────────────────┐
                │      feedback_seed.csv     │
                └─────────────┬─────────────┘
                              │
                              │ ingest_feedback.py
                              │  - embed each row
                              ▼
                ┌───────────────────────────┐
                │  Supabase Postgres (pgvector) │
                │  public.feedback             │
                │  - text, metadata, embedding │
                └─────────────┬─────────────┘
                              │
                              │ match_feedback(query_vec, filters)
                              ▼
┌───────────────────────────┐     ┌──────────────────────────────┐
│        Streamlit UI        │     │      OpenAI Embeddings        │
│ app/app.py                 │────►│ text-embedding-3-small        │
│ - query + filters          │     └──────────────────────────────┘
│ - evidence cards + metrics │
│ - agentic analysis         │────────► pm_agent.py (LLM)
│ - weekly PM brief          │────────► weekly_pm_brief.py (LLM)
│ - PDF export (ReportLab)   │
└───────────────────────────┘
