

import os
import requests
from functools import lru_cache

OM_HOST_URL = os.getenv("OM_HOST_URL", "http://localhost:8585/api")
OM_JWT_TOKEN = os.getenv("OM_JWT_TOKEN", "")

HEADERS = {
    "Authorization": f"Bearer {OM_JWT_TOKEN}",
    "Content-Type": "application/json",
}


def _get(path: str, params: dict | None = None) -> dict:
    url = f"{OM_HOST_URL}{path}"
    resp = requests.get(url, headers=HEADERS, params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_entities(
    entity_type: str = "tables",
    fields: str = "owners,tags,description,domains,extension,followers",
    page_size: int = 100,
    max_pages: int = 50,
) -> list[dict]:
    results = []
    after = None
    for _ in range(max_pages):
        params = {"limit": page_size, "fields": fields}
        if after:
            params["after"] = after
        data = _get(f"/v1/{entity_type}", params=params)
        results.extend(data.get("data", []))
        after = data.get("paging", {}).get("after")
        if not after:
            break
    return results


def get_all_data_assets(fields: str = "owners,tags,description,domains,extension,followers") -> tuple[list[dict], list[str]]:
    asset_types = ["tables", "topics", "dashboards", "mlmodels"]
    all_assets = []
    errors = []
    for t in asset_types:
        try:
            entities = get_entities(entity_type=t, fields=fields)
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            body = e.response.text[:300] if e.response is not None else ""
            errors.append(f"{t}: HTTP {status} - {body}")
            entities = []
        except requests.exceptions.ConnectionError as e:
            errors.append(f"{t}: connection error - {e}")
            entities = []
        for e in entities:
            e["_entityType"] = t.rstrip("s")
        all_assets.extend(entities)
    return all_assets, errors


@lru_cache(maxsize=1)
def get_classification_list() -> list[dict]:
    data = _get("/v1/classifications", params={"limit": 100})
    return data.get("data", [])


def get_tags_for_classification(classification_name: str) -> list[dict]:
    data = _get("/v1/tags", params={"parent": classification_name, "limit": 100})
    return data.get("data", [])


def get_domains() -> list[dict]:
    try:
        data = _get("/v1/domains", params={"limit": 100})
        return data.get("data", [])
    except requests.HTTPError:
        return []


ENTITY_TYPE_ENDPOINTS = {
    "table": "tables",
    "topic": "topics",
    "dashboard": "dashboards",
    "mlmodel": "mlmodels",
}


def get_entity_by_fqn(entity_type: str, fqn: str, fields: str = "owners,tags,description,domains,extension,followers") -> dict:
    endpoint = ENTITY_TYPE_ENDPOINTS.get(entity_type, "tables")
    return _get(f"/v1/{endpoint}/name/{fqn}", params={"fields": fields})


def get_entity_versions(entity_type: str, entity_id: str) -> list[dict]:
    import json as _json

    endpoint = ENTITY_TYPE_ENDPOINTS.get(entity_type, "tables")
    data = _get(f"/v1/{endpoint}/{entity_id}/versions")
    raw_versions = data.get("versions", [])
    parsed = []
    for v in raw_versions:
        if isinstance(v, str):
            try:
                v = _json.loads(v)
            except _json.JSONDecodeError:
                continue
        parsed.append(v)
    parsed.sort(key=lambda x: x.get("updatedAt", 0), reverse=True)
    return parsed


def search_entities(query: str, tags: list[str] | None = None, index: str = "table_search_index", size: int = 25) -> dict:
    q = query.strip() or "*"
    filters = ""
    if tags:
        tag_clause = " OR ".join([f'tags.tagFQN:"{t}"' for t in tags])
        filters = f" AND ({tag_clause})"
    params = {
        "q": f"{q}{filters}",
        "index": index,
        "size": size,
        "from": 0,
    }
    return _get("/v1/search/query", params=params)
