"""
run_frontend.py – launches the Streamlit UI for the Fleet App.
"""

import os
import sys
import subprocess
from multiprocessing import freeze_support
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def run() -> None:
    """
    Starts Streamlit in headless mode.
    • `STREAMLIT_HOST`   – bind address (default: 0.0.0.0)
    • `STREAMLIT_PORT`   – port (default: 8501)
    • `STREAMLIT_RELOAD` – 'true' enables hot‑reload for dev
    """
    freeze_support()                     # Windows / PyInstaller safety
    host   = os.getenv("STREAMLIT_HOST",   "0.0.0.0")
    port   = os.getenv("STREAMLIT_PORT",   "8501")
    reload = os.getenv("STREAMLIT_RELOAD", "false").lower() == "true"

    cmd = [
        sys.executable, "-m", "streamlit", "run", "frontend/app.py",
        "--server.headless", "true",
        "--server.address", host,
        "--server.port", port,
    ]

    if reload:
        cmd += ["--server.runOnSave", "true"]

    logging.info("Launching Streamlit: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        logging.info("Streamlit stopped by user")
