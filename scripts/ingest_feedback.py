import os
import csv
from datetime import date
from dotenv import load_dotenv
import psycopg
from openai import OpenAI

# ---------- Config ----------
TABLE_NAME = "public.feedback"
CSV_PATH = os.path.join("data", "feedback_seed.csv")

def require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}. Check your .env file.")
    return v

def main():
    load_dotenv()

    db_url = require_env("SUPABASE_DB_URL")
    api_key = require_env("OPENAI_API_KEY")

    embed_model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

    client = OpenAI(api_key=api_key)

    # Connect to Supabase Postgres
    with psycopg.connect(db_url) as conn:
        conn.autocommit = True

        # Safety: If script is re-run, keep it idempotent by deleting rows for same seed source/date range
        # For MVP, we’ll just wipe and reinsert everything.
        with conn.cursor() as cur:
            cur.execute(f"delete from {TABLE_NAME};")

        rows_inserted = 0

        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for r in reader:
                text = (r.get("text") or "").strip()
                if not text:
                    continue

                # 1) Create embedding
                emb = client.embeddings.create(
                    model=embed_model,
                    input=text
                ).data[0].embedding  # list[float] length 1536

                # 2) Insert into DB
                source = (r.get("source") or "app_reviews").strip()
                country = (r.get("country") or "").strip() or None
                platform = (r.get("platform") or "").strip() or None
                user_type = (r.get("user_type") or "").strip() or None

                rating_raw = (r.get("rating") or "").strip()
                rating = int(rating_raw) if rating_raw.isdigit() else None

                created_at_raw = (r.get("created_at") or "").strip()
                created_at = created_at_raw if created_at_raw else None

                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        insert into {TABLE_NAME}
                          (source, country, platform, rating, user_type, created_at, text, embedding)
                        values
                          (%s, %s, %s, %s, %s, %s, %s, %s::vector)
                        """,
                        (source, country, platform, rating, user_type, created_at, text, emb),
                    )

                rows_inserted += 1
                print(f"Inserted {rows_inserted}: {country=} {platform=} {rating=} | {text[:60]}...")

        print(f"\n Done. Inserted {rows_inserted} rows into {TABLE_NAME}.")

if __name__ == "__main__":
    main()
