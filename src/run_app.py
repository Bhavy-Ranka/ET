import subprocess
import time
import sys
import os

def run_services():
    print("🚀 Starting Gen-AI Hackathon Stack...")

    # 1. Start FastAPI Backend (Uvicorn)
    # We use 'backend.main:app' assuming you are in the 'src' directory
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # Give the backend a few seconds to start up
    time.sleep(3)

    # 2. Start Streamlit Frontend
    frontend_process = subprocess.Popen(
        ["streamlit", "run", "frontend/app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print("✅ Services are running!")
    print("👉 Backend: http://127.0.0.1:8000")
    print("👉 Frontend: http://localhost:8501")

    try:
        # Keep the script alive while processes run
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    run_services()