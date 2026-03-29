import subprocess
import time
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(ROOT, "src")

def run_services():
    print("🚀 Starting Gen-AI Hackathon Stack...")

    env = {
        **os.environ,
        "PYTHONPATH": ":".join([
            os.path.join(SRC, "gen_ai"),    # for ai_main, rag, match
            os.path.join(SRC, "backend"),   # for database, authentication
        ])
    }

    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app",
         "--host", "127.0.0.1", "--port", "8000"],
        stdout=None,
        stderr=None,
        text=True,
        cwd=SRC,
        env=env
    )

    time.sleep(3)

    frontend_process = subprocess.Popen(
        ["streamlit", "run", os.path.join(SRC, "frontend", "app.py")],
        stdout=None,
        stderr=None,
        text=True,
        cwd=ROOT
    )

    print("✅ Services running!")
    print("👉 Backend:  http://127.0.0.1:8000")
    print("👉 Frontend: http://localhost:8501")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    run_services()