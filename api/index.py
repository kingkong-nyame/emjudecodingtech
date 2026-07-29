"""Vercel serverless entrypoint.

Vercel's Python runtime imports this module and looks for a WSGI callable
named `app`. The Flask application itself lives at the repository root, so the
root is placed on sys.path before importing it.

Do not run this file directly — use `flask run` for local development.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app  # noqa: E402

# Alias for WSGI servers that look for `application` instead.
application = app
