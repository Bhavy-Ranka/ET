import json
import os
import re

try:
    import psycopg2
except ModuleNotFoundError:
    psycopg2 = None

try:
    from groq import Groq
except ModuleNotFoundError:
    Groq = None

try:
    import google.genai as google_genai
except ModuleNotFoundError:
    genai = None

DB_CONFIG = {
    "dbname": os.getenv("PGDATABASE", "hack"),
    "user": os.getenv("PGUSER", "db"),
    "password": os.getenv("PGPASSWORD", "0808"),
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
}

ALLOWED_CATEGORIES = {
    "waste management": "Waste Management",
    "waste": "Waste Management",
    "garbage": "Waste Management",
    "road": "Road",
    "pothole": "Road",
    "water": "Water",
    "sewage": "Water",
    "electricity": "Electricity",
    "power": "Electricity",
    "others": "Others",
}
ALLOWED_SEVERITIES = {"low": "Low", "medium": "Medium", "high": "High"}
DEFAULT_CATEGORY = "Others"
DEFAULT_SEVERITY = "Medium"
MAX_CANDIDATES = 5
SIMILARITY_THRESHOLD = 0.20


_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# text-embedding-004 lives on v1beta; generate_content models live on v1
_embed_client = None
_generate_client = None


def _get_embed_client():
    """Client for embeddings — must use v1beta (text-embedding-004 not on v1)."""
    global _embed_client
    if google_genai is None:
        raise RuntimeError("google-genai is not installed. Run: pip install google-genai")
    if _embed_client is not None:
        return _embed_client
    _embed_client = google_genai.Client(
        api_key=_GEMINI_API_KEY,
        http_options={"api_version": "v1beta"},
    )
    return _embed_client


def _get_generate_client():
    """Client for generate_content — uses stable v1 endpoint."""
    global _generate_client
    if google_genai is None:
        raise RuntimeError("google-genai is not installed. Run: pip install google-genai")
    if _generate_client is not None:
        return _generate_client
    _generate_client = google_genai.Client(
        api_key=_GEMINI_API_KEY,
        http_options={"api_version": "v1"},
    )
    return _generate_client


def _get_groq_client():
    api_key = os.getenv("GROK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Please export it before calling llm_location_check()."
        )
    return Groq(api_key=api_key)


def _normalize_whitespace(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def _normalize_category(value):
    if not value:
        return DEFAULT_CATEGORY
    key = _normalize_whitespace(value).lower()
    for hint, canonical in ALLOWED_CATEGORIES.items():
        if hint in key:
            return canonical
    return DEFAULT_CATEGORY


def _normalize_severity(value):
    if not value:
        return DEFAULT_SEVERITY
    key = _normalize_whitespace(value).lower()
    for hint, canonical in ALLOWED_SEVERITIES.items():
        if hint in key:
            return canonical
    return DEFAULT_SEVERITY


def _normalize_tags(value):
    if not value:
        return []
    if isinstance(value, str):
        parts = re.split(r"[;,/|]", value)
        tags = [p.strip() for p in parts if p.strip()]
    elif isinstance(value, list):
        tags = [str(t).strip() for t in value if str(t).strip()]
    else:
        tags = [str(value).strip()]
    seen = set()
    normalized = []
    for tag in tags:
        lower = tag.lower()
        if lower not in seen:
            seen.add(lower)
            normalized.append(lower)
    return normalized[:8]


def _tokenize_location(value):
    text = _normalize_whitespace(value).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [
        t
        for t in text.split()
        if t not in {"near", "at", "in", "the", "and", "of", "on"}
    ]
    return tokens


def _simple_location_match(new_loc, candidates):
    new_tokens = _tokenize_location(new_loc)
    if not new_tokens:
        return None
    new_text = " ".join(new_tokens)
    for candidate in candidates:
        cand_tokens = _tokenize_location(candidate.get("location", ""))
        if not cand_tokens:
            continue
        cand_text = " ".join(cand_tokens)
        if new_text in cand_text or cand_text in new_text:
            return candidate["id"]
        overlap = len(set(new_tokens) & set(cand_tokens))
        union = len(set(new_tokens) | set(cand_tokens))
        if union and (overlap / union) >= 0.6:
            return candidate["id"]
    return None


def _normalize_payload(payload):
    data = dict(payload or {})
    data["issue_title"] = (
        _normalize_whitespace(data.get("issue_title")) or "Civic Issue"
    )
    data["detailed_description"] = _normalize_whitespace(
        data.get("detailed_description")
    ) or _normalize_whitespace(data.get("user_text"))
    if not data["detailed_description"]:
        data["detailed_description"] = data["issue_title"]
    data["category"] = _normalize_category(data.get("category"))
    data["severity"] = _normalize_severity(data.get("severity"))
    data["formatted_location"] = _normalize_whitespace(
        data.get("formatted_location") or data.get("raw_location")
    )
    data["tags"] = _normalize_tags(data.get("tags"))
    data.setdefault("priority", _severity_to_priority(data["severity"]))
    data.setdefault("report_count", 1)
    data.setdefault("status", "open")
    return data


def _severity_to_priority(severity):
    return {"Low": 1, "Medium": 2, "High": 3}.get(severity, 2)


def _safe_json_loads(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def _format_vector(vector):
    return "[" + ",".join(f"{v:.6f}" for v in vector) + "]"


def _get_column_info(cur):
    cur.execute(
        """
        SELECT column_name, data_type, udt_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'grievances';
        """
    )
    return {row[0]: {"data_type": row[1], "udt_name": row[2]} for row in cur.fetchall()}


def _prepare_tags_value(tags, column_info):
    if not column_info:
        return tags
    data_type = column_info.get("data_type")
    if data_type in {"json", "jsonb"}:
        return json.dumps(tags)
    if data_type == "ARRAY":
        return tags
    return ", ".join(tags)


def _prepare_embedding_value(vector, column_info):
    if not column_info:
        return vector, ""
    if column_info.get("udt_name") == "vector":
        return _format_vector(vector), "::vector"
    return vector, ""


def _fetch_candidates(cur, vector_value, category, columns, include_category=True):
    filters = []
    params = [vector_value]

    if "status" in columns:
        filters.append("status = 'open'")
    if include_category and "category" in columns:
        filters.append("category = %s")
        params.append(category)

    where_sql = f"WHERE {' AND '.join(filters)}" if filters else ""

    cur.execute(
        f"""
        SELECT id, formatted_location, embedding <=> %s::vector AS distance
        FROM grievances
        {where_sql}
        ORDER BY distance ASC
        LIMIT %s;
        """,
        (*params, MAX_CANDIDATES),
    )
    return cur.fetchall()


# Embedding models to try in order — text-embedding-004 needs paid tier,
# embedding-001 works on all free-tier keys.
_EMBEDDING_MODELS = [
    "models/gemini-embedding-001",
    "models/text-embedding-004",
]

def get_embedding(text):
    client = _get_embed_client()
    last_exc = None
    for model in _EMBEDDING_MODELS:
        try:
            result = client.models.embed_content(
                model=model,
                contents=text,
            )
            return result.embeddings[0].values
        except Exception as exc:
            print(f"Embedding model {model!r} failed: {exc}")
            last_exc = exc
    raise RuntimeError(f"All embedding models failed. Last error: {last_exc}")


def llm_location_check(new_loc, existing_locs_with_ids):
    """
    Sends the new location and a list of candidate locations to Groq.
    Returns the ID of the matching location, or None.
    """
    prompt = f"""
    You are a location matching expert for a city management system.
    New Report Location: "{new_loc}"
    
    Existing Candidate Locations:
    {json.dumps(existing_locs_with_ids, indent=2)}
    
    Task: Determine if the New Report Location refers to the SAME physical spot as any of the candidates.
    Consider landmarks, sectors, and common variations (e.g., 'Main Gate' and 'Entrance').
    
    Return ONLY a JSON object with:
    {{
        "match_found": boolean,
        "matching_id": integer or null,
        "reason": "short explanation"
    }}
    """

    if not _normalize_whitespace(new_loc):
        return {"match_found": False, "matching_id": None, "reason": "No location"}

    try:
        groq_client = _get_groq_client()
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",  # Groq is very fast for this
            response_format={"type": "json_object"},
        )
        return _safe_json_loads(chat_completion.choices[0].message.content)
    except Exception as exc:
        match_id = _simple_location_match(new_loc, existing_locs_with_ids)
        return {
            "match_found": match_id is not None,
            "matching_id": match_id,
            "reason": f"LLM fallback: {exc}",
        }


def process_grievance_with_llm_filter(new_json):
    # 1. Prepare Data
    normalized = _normalize_payload(new_json)

    if psycopg2 is None:
        print("psycopg2 is not installed; skipping grievance DB operations.")
        return normalized

    new_vector = get_embedding(normalized["detailed_description"])

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        columns = _get_column_info(cur)
        if "embedding" not in columns or "formatted_location" not in columns:
            save_as_new_issue(cur, normalized, new_vector, columns)
            conn.commit()
            return
        if columns.get("embedding", {}).get("udt_name") != "vector":
            save_as_new_issue(cur, normalized, new_vector, columns)
            conn.commit()
            return

        vector_value, _ = _prepare_embedding_value(new_vector, columns.get("embedding"))

        # 2. Stage 1: Get top 5 potential candidates by category and basic vector similarity
        candidates = _fetch_candidates(
            cur,
            vector_value,
            normalized["category"],
            columns,
            include_category=True,
        )

        if not candidates:
            candidates = _fetch_candidates(
                cur,
                vector_value,
                normalized["category"],
                columns,
                include_category=False,
            )
            if not candidates:
                save_as_new_issue(cur, normalized, new_vector, columns)
                conn.commit()
                return

        # Prepare candidates for LLM
        loc_candidates = [{"id": c[0], "location": c[1]} for c in candidates]

        # 3. Stage 2: LLM Location Check
        print(
            f"Checking location similarity for: {normalized['formatted_location']}..."
        )
        loc_result = llm_location_check(
            normalized["formatted_location"], loc_candidates
        )

        if loc_result["match_found"]:
            match_id = loc_result["matching_id"]
            # Find the distance of this specific match from our candidates list
            match_distance = next((c[2] for c in candidates if c[0] == match_id), None)

            # 4. Stage 3: Final Similarity Threshold
            # Even if location matches, the issue must be semantically similar (e.g., not 'pothole' vs 'broken light')
            if match_distance is not None and match_distance < SIMILARITY_THRESHOLD:
                updates = ["report_count = report_count + 1"]
                params = []
                if "priority" in columns:
                    updates.append("priority = COALESCE(priority, %s) + 1")
                    params.append(_severity_to_priority(normalized["severity"]))
                cur.execute(
                    f"UPDATE grievances SET {', '.join(updates)} WHERE id = %s",
                    (*params, match_id),
                )
                print(f"MATCH CONFIRMED by LLM & Vector. Updated ID: {match_id}")
            else:
                print(
                    "Location matched, but issue description is too different. Creating new."
                )
                save_as_new_issue(cur, normalized, new_vector, columns)
        else:
            print("LLM found no matching locations. Creating new issue.")
            save_as_new_issue(cur, normalized, new_vector, columns)

        conn.commit()

    finally:
        cur.close()
        conn.close()


def save_as_new_issue(cur, data, vector, columns):
    fields = []
    placeholders = []
    values = []

    def add_field(name, value, cast=""):
        fields.append(name)
        placeholders.append(f"%s{cast}")
        values.append(value)

    if "issue_title" in columns:
        add_field("issue_title", data["issue_title"])
    if "detailed_description" in columns:
        add_field("detailed_description", data["detailed_description"])
    if "category" in columns:
        add_field("category", data["category"])
    if "severity" in columns:
        add_field("severity", data["severity"])
    if "formatted_location" in columns:
        add_field("formatted_location", data["formatted_location"])
    if "raw_location" in columns:
        add_field("raw_location", data.get("raw_location"))
    if "image_path" in columns:
        add_field("image_path", data.get("image_path"))
    if "tags" in columns:
        tags_value = _prepare_tags_value(data.get("tags", []), columns.get("tags"))
        add_field("tags", tags_value)
    if "embedding" in columns:
        embedding_value, cast = _prepare_embedding_value(
            vector, columns.get("embedding")
        )
        add_field("embedding", embedding_value, cast)
    if "priority" in columns:
        add_field("priority", data.get("priority"))
    if "report_count" in columns:
        add_field("report_count", data.get("report_count", 1))
    if "status" in columns:
        add_field("status", data.get("status", "open"))

    if not fields:
        raise RuntimeError(
            "No compatible columns found in grievances table for insertion."
        )
    
    print(fields)
    print(placeholders)
    print(values)

    insert_sql = f"""
        INSERT INTO grievances ({', '.join(fields)})
        VALUES ({', '.join(placeholders)})
    """
    cur.execute(insert_sql, tuple(values))