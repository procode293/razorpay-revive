"""Vercel Serverless Function Entrypoint for Razorpay Revive."""
import os
import sys
from pathlib import Path

# Setup paths for Vercel serverless environment
root_dir = Path(__file__).parent.parent.resolve()
backend_dir = (root_dir / "backend").resolve()

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
