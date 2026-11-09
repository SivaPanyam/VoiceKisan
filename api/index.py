import sys
from pathlib import Path

# Add backend directory to sys.path so existing modules import cleanly
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.append(str(backend_dir))

from main import app
