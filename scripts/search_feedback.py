import os
from dotenv import load_dotenv
import psycopg
from openai import OpenAI

load_dotenv()

_client = None

def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY in .env")
        _client = OpenAI(api_key=api_key)
    return _client

def embed(text: str) -> list[float]:
    model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    client = get_client()
    r = client.embeddings.create(model=model, input=text)
    return r.data[0].embedding

def search_feedback(
    query: str,
    top_k: int = 5,
    country: str | None = None,
    platform: str | None = None,
    user_type: str | None = None,
) -> list[dict]:
    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        raise RuntimeError("Missing SUPABASE_DB_URL in .env")

    query = (query or "").strip()
    if not query:
        return []

    qvec = embed(query)

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select * from match_feedback(
                    %s::vector(1536),
                    %s,
                    %s,
                    %s,
                    %s
                );
                """,
                (qvec, top_k, country, platform, user_type),
            )
            rows = cur.fetchall()

    # IMPORTANT: adjust the unpacking order if your SQL returns different order
    results = []
    for (id_, content, country, platform, rating, similarity) in rows:
        results.append({
            "id": id_,
            "text": content,
            "country": country,
            "platform": platform,
            "rating": rating,
            "similarity": float(similarity),
        })
    return results


# Optional CLI still works
if __name__ == "__main__":
    q = input("Ask a question: ").strip()
    hits = search_feedback(q, top_k=5)
    for h in hits:
        print(f"- [{h['similarity']:.3f}] #{h['id']} ({h['country']}, {h['platform']}, rating={h['rating']}) {h['text'][:120]}")
