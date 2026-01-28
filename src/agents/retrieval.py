import os
from typing import Optional, List, Dict, Any
import psycopg
from openai import OpenAI

client = OpenAI()

def embed_text(text: str, model: str) -> list[float]:
    resp = client.embeddings.create(model=model, input=text)
    return resp.data[0].embedding

def search_feedback(
    question: str,
    top_k: int = 6,
    platform: Optional[str] = None,
    country: Optional[str] = None,
) -> List[Dict[str, Any]]:
    db_url = os.getenv("SUPABASE_DB_URL")
    embed_model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

    q_emb = embed_text(question, embed_model)

    filters = []
    params = {"q_emb": q_emb, "k": top_k}

    if platform and platform.strip():
        filters.append("platform = %(platform)s")
        params["platform"] = platform.strip()

    if country and country.strip():
        filters.append("country = %(country)s")
        params["country"] = country.strip()

    where_clause = ("where " + " and ".join(filters)) if filters else ""

    sql = f"""
    select
      id,
      country,
      platform,
      rating,
      text,
      1 - (embedding <=> %(q_emb)s) as score
    from public.feedback
    {where_clause}
    order by embedding <=> %(q_emb)s
    limit %(k)s;
    """

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    results = []
    for (id_, country_, platform_, rating_, text_, score_) in rows:
        results.append({
            "id": id_,
            "country": country_,
            "platform": platform_,
            "rating": rating_,
            "text": text_,
            "score": float(score_),
        })

    return results
