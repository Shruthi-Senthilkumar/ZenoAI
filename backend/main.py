"""Compatibility shim — the real entrypoint is the root main.py.
Both test_main.py (`from main import app`) and
test_integration_subhiksha.py (`from backend.main import app`)
now resolve to the same single, fully-wired FastAPI instance.
"""
from main import app  # noqa: F401