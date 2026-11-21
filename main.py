#!/usr/bin/env python3
"""Entry program for the make.fun news-image bounty (Python 3.13, stdlib only).

The broadsheet is rendered ahead of time by render.py (Pillow) and committed as
entry.png. The sandbox has no third-party packages and no network, so this
program simply copies the committed image to the output directory. Copying the
same bytes makes the two required runs byte-identical.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

os.makedirs(OUT_DIR, exist_ok=True)
# Copy raw bytes so both runs emit exactly the committed image, byte for byte.
with open(SRC, "rb") as fh:
    payload = fh.read()
with open(os.path.join(OUT_DIR, "entry.png"), "wb") as fh:
    fh.write(payload)
