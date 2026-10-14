import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# The folder containing this config.py file
PROJECT_DIR = Path(__file__).resolve().parent
ENV_FILE = PROJECT_DIR / ".env"

# Use an explicit path; avoids find_dotenv() errors in packaged apps
if ENV_FILE.is_file():
    load_dotenv(dotenv_path=ENV_FILE, override=False)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        f"Supabase configuration is missing. Checked: {ENV_FILE}. "
        "Ensure SUPABASE_URL and SUPABASE_KEY are set."
    )