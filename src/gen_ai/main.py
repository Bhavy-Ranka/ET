import argparse
import os

# Load .env from the same directory as this script
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ModuleNotFoundError:
    pass  # rely on env vars already being exported

from rag import grievance_pipeline
from match import process_grievance_with_llm_filter


def run_pipeline(image_path, raw_location, user_text):
    payload = grievance_pipeline(image_path, raw_location, user_text)
    payload["image_path"] = image_path
    payload["raw_location"] = raw_location
    payload["user_text"] = user_text
    process_grievance_with_llm_filter(payload)
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the grievance intake -> matching pipeline."
    )
    parser.add_argument("--image", required=True, help="image_path")
    parser.add_argument("--location", required=True, help="Reported location")
    parser.add_argument("--text", required=True, help="User complaint text")
    args = parser.parse_args()

    run_pipeline(args.image, args.location, args.text)