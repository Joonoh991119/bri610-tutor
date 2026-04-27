#!/usr/bin:env python3
"""
seed_bank_v2_grounded.py — slide-content-grounded PhD bank, hallucination-audited.

Every item's `source_citation` points to a slide page whose actual content
(verified against the `slides` table) covers the item's question. Items that
referenced material NOT in the slides (Rall 3/2-law, Wilson-Cowan, Mensi GIF
MLE, Fisher-information CRLB, Mutual-Info bit calculations) have been replaced
with items grounded in slide-actual content.

This script REPLACES the bank (delete + reinsert). Run after backend is up.
Usage:  python scripts/seed_bank_v2_grounded.py
"""
from __future__ import annotations
import argparse, asyncio, json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "backend"))
from db_pool import acquire, release  # noqa: E402

SEEDS: list[dict] = []
