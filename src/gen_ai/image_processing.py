import os
from google import genai
from PIL import Image

client = genai.Client(api_key="")

def extract_text(image_path):
    try:
        img = Image.open(image_path)
        response = client.models.generate_content(
               model="gemini-2.5-flash-lite",
            contents=["Extract the text from this image as clean string.", img]
        )
        
        print("-" * 20)
        print("Extracted Text:")
        print("-" * 20)
        print(response.text)
        
    except FileNotFoundError:
        print(f"Error: The file at {image_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")