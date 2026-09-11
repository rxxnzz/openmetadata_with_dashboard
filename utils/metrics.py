from collections import Counter
import difflib
from datetime import datetime
import pandas as pd


MANDATORY_FIELDS = ["description", "owners", "tags", "domains"]


def _has_value(entity: dict, field: str) -> bool:
    val = entity.get(field)
    if field in ("tags", "owners", "domains"):
        return bool(val)  # non-empty list
    if isinstance(val, dict):
        return bool(val)
    return bool(val)


FIELD_LABELS = {
    "description": "Deskripsi",
    "owners": "Owner",
    "tags": "Tags",
    "domains": "Domain",
}


def score_single_entity(entity: dict) -> dict:

    breakdown = {f: _has_value(entity, f) for f in MANDATORY_FIELDS}
    filled = sum(1 for ok in breakdown.values() if ok)
    score = round(100 * filled / len(MANDATORY_FIELDS), 1)
    missing = [f for f, ok in breakdown.items() if not ok]
    return {"score": score, "breakdown": breakdown, "missing_fields": missing}


def compute_freshness(entity: dict) -> dict:

    ts = entity.get("updatedAt")
    if not ts:
        return {"last_updated": None, "days_since_update": None, "status": "Tidak diketahui"}
    try:
        dt = datetime.fromtimestamp(ts / 1000)
    except (TypeError, ValueError, OSError):
        return {"last_updated": None, "days_since_update": None, "status": "Tidak diketahui"}
    days = (datetime.now() - dt).days
    if days <= 30:
        status = "Fresh"
    elif days <= 90:
        status = "Mulai usang"
    else:
        status = "Usang (stale)"
    return {"last_updated": dt, "days_since_update": days, "status": status}


def compute_completeness_score(entities: list[dict]) -> pd.DataFrame:
    rows = []
    for e in entities:
        filled = sum(1 for f in MANDATORY_FIELDS if _has_value(e, f))
        score = round(100 * filled / len(MANDATORY_FIELDS), 1)
        missing = [f for f in MANDATORY_FIELDS if not _has_value(e, f)]
        rows.append(
            {
                "name": e.get("fullyQualifiedName") or e.get("name"),
                "entityType": e.get("_entityType"),
                "score": score,
                "missing_fields": ", ".join(missing) if missing else "-",
                "needs_alert": len(missing) > 0,
            }
        )
    return pd.DataFrame(rows)


def compute_growth_by_month(entities: list[dict]) -> pd.DataFrame:
    rows = []
    for e in entities:
        ts = e.get("updatedAt") or e.get("created")
        if not ts:
            continue
        try:
            dt = datetime.fromtimestamp(ts / 1000)
        except (TypeError, ValueError):
            continue
        rows.append(dt.strftime("%Y-%m"))
    if not rows:
        return pd.DataFrame(columns=["month", "count"])
    counts = Counter(rows)
    df = pd.DataFrame(sorted(counts.items()), columns=["month", "count"])
    return df


def compute_owner_distribution(entities: list[dict]) -> pd.DataFrame:
    counter = Counter()
    for e in entities:
        owners = e.get("owners") or []
        for owner in owners:
            counter[owner.get("name") or owner.get("displayName") or "unknown"] += 1
    df = pd.DataFrame(counter.most_common(), columns=["owner", "dataset_count"])
    return df


def compute_no_owner(entities: list[dict]) -> pd.DataFrame:
    rows = [
        {"name": e.get("fullyQualifiedName") or e.get("name"), "entityType": e.get("_entityType")}
        for e in entities
        if not e.get("owners")
    ]
    return pd.DataFrame(rows)


def compute_service_distribution(entities: list[dict]) -> pd.DataFrame:
    counter = Counter()
    for e in entities:
        fqn = e.get("fullyQualifiedName", "")
        service = fqn.split(".")[0] if fqn else "unknown"
        counter[service] += 1
    return pd.DataFrame(counter.most_common(), columns=["service", "dataset_count"])


def compute_classification_population(entities: list[dict]) -> pd.DataFrame:
    counter = Counter()
    for e in entities:
        seen_classifications_this_entity = set()
        for tag in e.get("tags", []) or []:
            tag_fqn = tag.get("tagFQN", "")
            classification = tag_fqn.split(".")[0] if "." in tag_fqn else tag_fqn
            if classification and classification not in seen_classifications_this_entity:
                counter[classification] += 1
                seen_classifications_this_entity.add(classification)
    return pd.DataFrame(counter.most_common(), columns=["classification", "dataset_count"])


def compute_domain_distribution(entities: list[dict]) -> pd.DataFrame:
    counter = Counter()
    for e in entities:
        domains = e.get("domains") or []
        if not domains:
            counter["No Domain"] += 1
        else:
            for d in domains:
                counter[d.get("name") or d.get("displayName") or "No Domain"] += 1
    return pd.DataFrame(counter.most_common(), columns=["domain", "dataset_count"])
