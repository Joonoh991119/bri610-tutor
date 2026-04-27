"""
Gamification rules engine — pure functions, no DB.

XP awards, level thresholds, badge logic, and level-up celebrations.
No side effects: callers in main.py own the DB writes.

Level formula: cumulative XP to reach level L = sum(100 * k^1.4 for k in 1..L-1)
i.e., going from level 1→2 costs floor(100*1^1.4)=100 xp,
        level 2→3 costs floor(100*2^1.4)=264 xp, etc.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional


# ─── XP ───────────────────────────────────────────────────────────────────────

_XP_TABLE = {1: 0, 2: 5, 3: 10, 4: 15}


def award_xp(rating: int) -> int:
    """1=Again 0xp, 2=Hard 5xp, 3=Good 10xp, 4=Easy 15xp."""
    return _XP_TABLE.get(rating, 0)


# ─── Level ────────────────────────────────────────────────────────────────────

def _xp_for_level(level: int) -> int:
    """Cumulative XP needed to reach `level` (1-indexed; level 1 starts at 0 xp)."""
    if level <= 1:
        return 0
    return sum(math.floor(100 * (k ** 1.4)) for k in range(1, level))


def compute_level(xp: int) -> int:
    """Given total XP, return the current level (1-indexed, no cap)."""
    level = 1
    while _xp_for_level(level + 1) <= xp:
        level += 1
    return level


def xp_to_next_level(xp: int) -> dict:
    """Returns {level, xp_current_level, xp_next_level, pct} for UI progress bar."""
    level = compute_level(xp)
    floor_xp = _xp_for_level(level)
    ceil_xp  = _xp_for_level(level + 1)
    span = ceil_xp - floor_xp
    earned = xp - floor_xp
    pct = round((earned / span * 100) if span > 0 else 100, 1)
    return {
        "level": level,
        "xp_current_level": earned,
        "xp_next_level": span,
        "pct": pct,
    }


# ─── Badges ───────────────────────────────────────────────────────────────────

_BADGE_META = {
    "first_card":     "첫 카드",
    "streak_3":       "3일 연속",
    "streak_7":       "7일 연속",
    "streak_30":      "30일 연속",
    "concept_mover":  "개념 마스터 (세션 5개)",
    "derive_master":  "증명 연속 3개",
    "early_bird":     "이른 아침 공부",
    "nightowl":       "야간 학습자",
}


def check_badges(state: dict, recent_review: dict) -> list[str]:
    """
    Rule-based badge checker. Returns list of badge_ids NEWLY earned.

    `state` keys (from users row + session context):
        existing_badges: list[str]  — already-held badge ids
        streak_days: int
        total_reviews: int          — including this one
        session_concept_good: int   — concept cards rated ≥3 in current session
        session_proof_streak: int   — proof cards rated ≥3 consecutively in session

    `recent_review` keys:
        rating: int
        card_type: str              — 'recall'|'concept'|'application'|'proof'
        reviewed_at_hour: int       — hour in local time (0-23), supplied by caller
    """
    existing = set(state.get("existing_badges") or [])
    newly: list[str] = []

    def _award(badge_id: str):
        if badge_id not in existing:
            newly.append(badge_id)
            existing.add(badge_id)

    total        = state.get("total_reviews", 0)
    streak       = state.get("streak_days", 0)
    rating       = recent_review.get("rating", 0)
    card_type    = recent_review.get("card_type", "")
    hour         = recent_review.get("reviewed_at_hour", 12)
    s_concept_g  = state.get("session_concept_good", 0)
    s_proof_str  = state.get("session_proof_streak", 0)

    if total >= 1:
        _award("first_card")
    if streak >= 3:
        _award("streak_3")
    if streak >= 7:
        _award("streak_7")
    if streak >= 30:
        _award("streak_30")
    if card_type == "concept" and rating >= 3 and s_concept_g >= 5:
        _award("concept_mover")
    if card_type == "proof" and rating >= 3 and s_proof_str >= 3:
        _award("derive_master")
    if hour < 8:
        _award("early_bird")
    if hour >= 23:
        _award("nightowl")

    return newly


# ─── Level-up celebration ─────────────────────────────────────────────────────

_LEVEL_TITLES = {
    2:  ("뉴런 초보", "막전위 이해 완료!"),
    3:  ("활동전위 입문자", "Na⁺ 채널의 비밀을 파헤쳤어요"),
    5:  ("케이블 이론가", "전달 지연이 더 이상 무섭지 않아요"),
    7:  ("HH 모델러", "gating 변수 마스터"),
    10: ("컴뉴 탐험가", "10레벨 돌파!"),
    15: ("시냅스 설계자", "시냅스 plasticity까지 정복"),
    20: ("뉴런쌤 제자", "뉴런쌤도 인정하는 실력이에요"),
}


def level_up_celebration(old_level: int, new_level: int) -> Optional[dict]:
    """Returns {title, subtitle} if a notable level was crossed, else None."""
    if new_level <= old_level:
        return None
    # Find highest notable threshold crossed
    hit = None
    for threshold, (title, subtitle) in sorted(_LEVEL_TITLES.items()):
        if old_level < threshold <= new_level:
            hit = (title, subtitle)
    if hit:
        return {"title": f"레벨 {new_level} 달성! {hit[0]}", "subtitle": hit[1]}
    # Generic celebration for every level up
    return {"title": f"레벨 {new_level} 달성!", "subtitle": "계속 이 기세로!"}
