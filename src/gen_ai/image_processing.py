import os
from PIL import Image

try:
    import google.generativeai as genai
except ModuleNotFoundError:
    genai = None


def _ensure_genai_configured():
    if genai is None:
        raise RuntimeError(
            "google-generativeai is not installed. Install it with: pip install google-generativeai"
        )
    if getattr(_ensure_genai_configured, "configured", False):
        return
    api_key = os.getenv("Gemini", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Please export it before calling extract_text()."
        )
    genai.configure(api_key=api_key)
    _ensure_genai_configured.configured = True


def extract_text(image_path):
    try:
        img = Image.open(image_path)
        prompt = (
            "Describe the civic issue in the given image (i.e. pothole, garbage, broken light). "
            "Provide details like severity and surroundings."
        )
        try:
            _ensure_genai_configured()
        except RuntimeError as exc:
            print(f"Image description skipped: {exc}")
            return None
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content([prompt, img])

        return response.text
    except FileNotFoundError:
        print(f"Error: The file at {image_path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
