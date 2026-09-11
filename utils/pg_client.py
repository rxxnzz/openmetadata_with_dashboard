import os
import json
from contextlib import contextmanager
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


def _pg_config() -> dict:
    return dict(
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", "5432"),
        dbname=os.getenv("PG_DB", "governance_analytics"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", ""),
    )


@contextmanager
def get_conn():
    config = _pg_config()
    if not config["password"]:
        raise RuntimeError(
            "PG_PASSWORD kosong/tidak terbaca dari .env. Cek: (1) file .env ada di root "
            "project, (2) PG_PASSWORD terisi, (3) tidak ada spasi/tanda kutip aneh di .env."
        )
    conn = psycopg2.connect(**config)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema(schema_path: str = "sql/schema.sql"):
    with open(schema_path, "r") as f:
        ddl = f.read()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)


def log_search(user_id: str, keyword: str, tags_filter: list[str], result_count: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO search_log (user_id, keyword, tags_filter, result_count)
                   VALUES (%s, %s, %s, %s)""",
                (user_id, keyword, json.dumps(tags_filter), result_count),
            )


def log_view(user_id: str, dataset_fqn: str, dataset_name: str, entity_type: str = "table"):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO dataset_view_log (user_id, dataset_fqn, dataset_name, entity_type)
                   VALUES (%s, %s, %s, %s)""",
                (user_id, dataset_fqn, dataset_name, entity_type),
            )


def toggle_favorite(user_id: str, dataset_fqn: str, dataset_name: str, entity_type: str = "table") -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM dataset_favorite WHERE user_id=%s AND dataset_fqn=%s",
                (user_id, dataset_fqn),
            )
            row = cur.fetchone()
            if row:
                cur.execute("DELETE FROM dataset_favorite WHERE id=%s", (row[0],))
                return False
            cur.execute(
                """INSERT INTO dataset_favorite (user_id, dataset_fqn, dataset_name, entity_type)
                   VALUES (%s, %s, %s, %s)""",
                (user_id, dataset_fqn, dataset_name, entity_type),
            )
            return True


def is_favorited(user_id: str, dataset_fqn: str) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM dataset_favorite WHERE user_id=%s AND dataset_fqn=%s",
                (user_id, dataset_fqn),
            )
            return cur.fetchone() is not None


def get_top_search_keywords(limit: int = 10, days: int = 90):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT keyword, COUNT(*) AS cnt
                   FROM search_log
                   WHERE searched_at >= NOW() - (%s || ' days')::interval
                   GROUP BY keyword
                   ORDER BY cnt DESC
                   LIMIT %s""",
                (days, limit),
            )
            return cur.fetchall()


def get_most_used_search_tags(limit: int = 10, days: int = 90):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT tag, COUNT(*) AS cnt
                   FROM search_log, jsonb_array_elements_text(tags_filter) AS tag
                   WHERE searched_at >= NOW() - (%s || ' days')::interval
                   GROUP BY tag
                   ORDER BY cnt DESC
                   LIMIT %s""",
                (days, limit),
            )
            return cur.fetchall()


def get_most_viewed(limit: int = 10, days: int = 90):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT dataset_fqn, dataset_name, COUNT(*) AS views
                   FROM dataset_view_log
                   WHERE viewed_at >= NOW() - (%s || ' days')::interval
                   GROUP BY dataset_fqn, dataset_name
                   ORDER BY views DESC
                   LIMIT %s""",
                (days, limit),
            )
            return cur.fetchall()


def get_most_favorited(limit: int = 10):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT dataset_fqn, dataset_name, COUNT(*) AS favorites
                   FROM dataset_favorite
                   GROUP BY dataset_fqn, dataset_name
                   ORDER BY favorites DESC
                   LIMIT %s""",
                (limit,),
            )
            return cur.fetchall()


def get_dataset_growth_by_month():
    raise NotImplementedError("Use metrics.compute_growth_by_month(entities) instead")
