# ✨ Customer Feedback Intelligence Copilot
**Agentic RAG → Evidence → Analysis → Jira-ready drafts**

### 🎬 Product Demo

[![Watch the demo](https://img.youtube.com/vi/09MXo9UeQpw.jpg)](https://youtu.be/09MXo9UeQpw))

▶️ Click to watch a short demo showing how Customer Feedback Intelligence Copilot turns raw Voice-of-Customer feedback into retrieved evidence, agentic analysis, and PM-ready outputs.


An app that turns Voice-of-Customer feedback into:
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

## 🗄️ Database Function (Supabase)
🗄️ Supabase Setup SQL (Schema + Indexes)

```sql
-- 1. Enable vector extension (needed for embeddings)
create extension if not exists vector;

-- 2. Create feedback table (Voice of Customer data)
create table if not exists public.feedback (
  id bigserial primary key,
  source text not null default 'app_reviews',
  country text,
  platform text,
  rating int,
  user_type text,
  created_at date,
  text text not null,
  embedding vector(1536)
);

-- 3. Indexes for fast filtering
create index if not exists feedback_created_at_idx on public.feedback (created_at);
create index if not exists feedback_country_idx on public.feedback (country);
create index if not exists feedback_platform_idx on public.feedback (platform);

-- 4. Vector index for semantic search
create index if not exists feedback_embedding_idx
on public.feedback
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

```

🧠 Supabase Retrieval Function (match_feedback)

```sql
create or replace function public.match_feedback (
  query_embedding vector(1536),
  match_count int default 5,
  country_filter text default null,
  platform_filter text default null,
  min_rating int default null
)
returns table (
  id bigint,
  content text,
  country text,
  platform text,
  rating int,
  similarity float
)
language sql stable
as $$
  select
    f.id,
    f.text as content,
    f.country,
    f.platform,
    f.rating,
    1 - (f.embedding <=> query_embedding) as similarity
  from public.feedback f
  where
    (country_filter is null or f.country = country_filter)
    and (platform_filter is null or f.platform = platform_filter)
    and (min_rating is null or f.rating >= min_rating)
  order by f.embedding <=> query_embedding
  limit match_count;
$$;


```

## 🧩 Repo Structure

```text

voc-agentic-copilot/
  app/
    app.py                  # Streamlit UI
  scripts/
    ingest_feedback.py      # CSV → embeddings → Supabase
    search_feedback.py      # query → embedding → match_feedback()
    pm_agent.py             # agentic analysis (LLM)
    weekly_pm_brief.py      # weekly PM brief generator (LLM)
  data/
    feedback_seed.csv       # seed feedback
  requirements.txt
  .env.example

```

## ⚙️ Setup
Dependencies

```bash

pip install -r requirements.txt
pip install streamlit-lottie requests

```

Environment configuration

```bash

cp .env.example .env
OPENAI_API_KEY=...
OPENAI_EMBED_MODEL=text-embedding-3-small
SUPABASE_DB_URL=postgresql://...

```

## 🛡️ Responsible AI Guardrails

* All analysis is grounded in retrieved evidence
* No raw JSON or hidden prompts in PDFs
* Filters applied at retrieval time (platform, country, rating)

## 🗺️ Roadmap

* Theme clustering & trend analysis
* Time-series VOC insights
* Jira ticket auto-creation

### Diagram
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




