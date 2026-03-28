import json
import re
from groq import Groq
from image_processing import extract_text

qroq_api = ""
groq_client = Groq(api_key=qroq_api)


def grievance_pipeline(image_path, raw_location, user_text):
    image_description = extract_text(image_path)

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

    chat_completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"},
    )

    return json.loads(chat_completion.choices[0].message.content)

result = grievance_pipeline(
    "Newport_Whitepit_Lane_pot_hole.jpg",
    "Near IIT Indore Gate 2",
    "Road pe bahut bada gadda hai",
)
print(result)
