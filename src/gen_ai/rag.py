import json
<<<<<<< HEAD
import os
=======
>>>>>>> 84c412f33d79e60708c499460e282bbfec2d7301
import re
from groq import Groq
from image_processing import extract_text

<<<<<<< HEAD
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


def _get_groq_client():
    api_key = os.getenv("Groq", "").strip()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Please export it before calling grievance_pipeline()."
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
    # De-duplicate while preserving order
    seen = set()
    normalized = []
    for tag in tags:
        lower = tag.lower()
        if lower not in seen:
            seen.add(lower)
            normalized.append(lower)
    return normalized[:8]


def _normalize_location(value):
    return _normalize_whitespace(value)


def _safe_json_loads(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def _severity_to_priority(severity):
    return {"Low": 1, "Medium": 2, "High": 3}.get(severity, 2)
=======
qroq_api = ""
groq_client = Groq(api_key=qroq_api)
>>>>>>> 84c412f33d79e60708c499460e282bbfec2d7301


def grievance_pipeline(image_path, raw_location, user_text):
    image_description = extract_text(image_path)
<<<<<<< HEAD
    if not image_description:
        image_description = "Image description unavailable."

    prompt = f"""
    You are a Municipal Grievance Analyzer. Combine the following inputs into a structured JSON report.

    1. User Input: "{user_text}"
    2. Image Description: "{image_description}"
    3. Reported Location: "{raw_location}"

    Rules:
    - Output JSON only (no markdown).
    - Category must be one of: Waste Management, Road, Water, Electricity, Others.
    - Severity must be one of: Low, Medium, High.
    - Keep the location clean but do not invent new details.

    Output Format:
    {{
    "issue_title": "Short descriptive title",
    "detailed_description": "Comprehensive summary combining user text and image details",
    "category": "Waste Management / Road / Water / Electricity / Others",
    "severity": "Low / Medium / High",
    "formatted_location": "Cleaned address or coordinates",
    "tags": ["tag1", "tag2"]
    }}
    """

    groq_client = _get_groq_client()
=======

    prompt = f"""
     You are a Municipal Grievance Analyzer. Combine the following inputs into a structured JSON report.

     1. User Input: "{user_text}"
     2. Image Description: "{image_description}"
     3. Reported Location: "{raw_location}"
     Output Format (JSON only):
     {{
          "issue_title": "Short descriptive title",
          "detailed_description": "Comprehensive summary combining user text and image details",
          "category": "Waste Management / Road / Water / Electricity / Others",
          "severity": "Low / Medium / High",
          "formatted_location": "Cleaned address or coordinates",
          "tags": ["tag1", "tag2"]
     }}
     """

>>>>>>> 84c412f33d79e60708c499460e282bbfec2d7301
    chat_completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"},
    )

<<<<<<< HEAD
    payload = _safe_json_loads(chat_completion.choices[0].message.content)

    issue_title = _normalize_whitespace(payload.get("issue_title")) or "Civic Issue"
    detailed_description = _normalize_whitespace(
        payload.get("detailed_description")
    ) or _normalize_whitespace(user_text)
    category = _normalize_category(payload.get("category"))
    severity = _normalize_severity(payload.get("severity"))
    formatted_location = _normalize_location(
        payload.get("formatted_location") or raw_location
    )
    tags = _normalize_tags(payload.get("tags"))

    return {
        "issue_title": issue_title,
        "detailed_description": detailed_description,
        "category": category,
        "severity": severity,
        "formatted_location": formatted_location,
        "tags": tags,
        "priority": _severity_to_priority(severity),
        "report_count": 1,
        "status": "open",
        "raw_location": _normalize_location(raw_location),
        "image_path": image_path,
    }
=======
    return json.loads(chat_completion.choices[0].message.content)

result = grievance_pipeline(
    "Newport_Whitepit_Lane_pot_hole.jpg",
    "Near IIT Indore Gate 2",
    "Road pe bahut bada gadda hai",
)
print(result)
>>>>>>> 84c412f33d79e60708c499460e282bbfec2d7301
