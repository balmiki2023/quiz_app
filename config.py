"""Load Supabase configuration for development and packaged builds.

For public releases, set the public project URL and publishable/anon key below.
These values are intended to be public; never put a service-role/secret key here.
A local .env file overrides the public defaults during development/testing.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Public client configuration. Fill these before making a release build.
# A Supabase publishable key (or legacy anon key) is safe to expose only when
# Row Level Security and database permissions are correctly configured.
PUBLIC_SUPABASE_URL = ""
PUBLIC_SUPABASE_KEY = ""

def _environment_file_candidates() -> list[Path]:
    """Return likely locations for a local .env without relying on find_dotenv()."""
    candidates = [
        Path(__file__).resolve().parent / ".env",
        Path(sys.executable).resolve().parent / ".env",
        Path.cwd() / ".env",
    ]
    unique_candidates = []
    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_candidates.append(resolved)
    return unique_candidates

for _env_file in _environment_file_candidates():
    if _env_file.is_file():
        load_dotenv(dotenv_path=_env_file, override=False)
        break

SUPABASE_URL = os.getenv("SUPABASE_URL") or PUBLIC_SUPABASE_URL
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or PUBLIC_SUPABASE_KEY

if not SUPABASE_URL or not SUPABASE_KEY:
    checked_paths = ", ".join(
        str(path) for path in _environment_file_candidates()
    )
    raise RuntimeError(
        "Supabase configuration is missing. For development, provide a .env "
        "file with SUPABASE_URL and SUPABASE_KEY. For a public release, set "
        "PUBLIC_SUPABASE_URL and PUBLIC_SUPABASE_KEY in config.py. "
        f"Checked .env locations: {checked_paths}"
    )
