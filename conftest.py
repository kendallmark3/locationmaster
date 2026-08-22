import sys
from pathlib import Path

# `hooks/` sits at the repo root, as a sibling of `services/api`, and is
# imported by both services/api/app/main.py and services/api/tests/. This
# guarantees the repo root is on sys.path no matter where pytest is invoked
# from, as a fallback to the pyproject.toml pythonpath setting.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
