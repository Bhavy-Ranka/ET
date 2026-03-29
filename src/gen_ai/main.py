import argparse

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
    parser.add_argument("--image", required=True, help="")
    parser.add_argument("--location", required=True, help="Reported location")
    parser.add_argument("--text", required=True, help="User complaint text")
    args = parser.parse_args()

    run_pipeline(args.image, args.location, args.text)
