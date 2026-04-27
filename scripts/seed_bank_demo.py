#!/usr/bin/env python3
"""
seed_bank_demo.py — minimal v0.5 demo seed.

Inserts 12 hand-curated, citation-grounded bank items spanning:
  - 3 topics: Nernst, HH gating, cable equation
  - 4 card types: recall / concept / application / proof
Each item has source citation, prompt+answer+rationale (KaTeX-ready Korean+EN).

Then registers an `srs_cards` row per item for user_id=1 so the FSRS queue
returns them on `/api/srs/queue`.

Optional --review flag runs each item through Multi-Lens Review (requires
OPENROUTER_API_KEY env). Without it, items are inserted as draft (then promoted
to active for demo).

Usage:
    python scripts/seed_bank_demo.py [--review] [--user-id 1]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Make backend importable
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))

from db_pool import acquire, release  # noqa: E402


SEEDS: list[dict] = [
    # ─── Nernst (L3) ─────────────────────────────────────────────────────
    {
        "topic": "Nernst",
        "card_type": "recall",
        "difficulty": 1,
        "bloom": "Remember",
        "prompt_md": "Nernst 평형 전위(equilibrium potential) 식을 한 줄로 적으시오. (단일 이온, 농도 기울기만)",
        "answer_md": r"$$E_X = \frac{RT}{zF} \ln\frac{[X]_o}{[X]_i}$$",
        "rationale_md": "단일 이온 X에 대해 농도-전위 평형이 성립할 때 Boltzmann 인자를 풀어 얻은 식. R=기체상수, T=절대온도, z=원자가, F=Faraday 상수.",
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 12},
        "priority_score": 0.95,
        "info_density": 0.9,
        "mastery_target": "Nernst",
    },
    {
        "topic": "Nernst",
        "card_type": "concept",
        "difficulty": 3,
        "bloom": "Understand",
        "prompt_md": "Nernst 식과 Goldman-Hodgkin-Katz(GHK) 식이 단일 이온일 때는 동일하지만, 다이온일 때 다른 결과를 주는 **이유**를 한 문장으로 설명하시오.",
        "answer_md": "Nernst는 단일 이온의 평형만, GHK는 여러 이온의 **상대적 투과도(permeability)** 가중 평균을 모두 고려하기 때문.",
        "rationale_md": "GHK는 막을 통과하는 각 이온의 P_i × [ion] 항을 합산해 전체 막전위를 계산. 단일 이온이면 그 항만 살아 Nernst와 같아진다.",
        "source_citation": {"kind": "textbook", "book": "Dayan_Abbott", "ch": 5, "page": 5},
        "priority_score": 0.88,
        "info_density": 0.85,
        "mastery_target": "Nernst_GHK",
    },
    {
        "topic": "Nernst",
        "card_type": "application",
        "difficulty": 3,
        "bloom": "Apply",
        "prompt_md": "체외 $[K^+]_o$를 5 mM에서 10 mM로 두 배 증가시키면 (체내 농도 $[K^+]_i = 140$ mM 유지), $E_K$는 **얼마나** 변하는가? (T=310 K, ln 2 ≈ 0.693)",
        "answer_md": r"약 **+18.5 mV** 변화. ($E_K = \frac{RT}{F}\ln([K]_o/[K]_i)$, $\Delta E_K = \frac{RT}{F}\ln 2 \approx 26.7 \cdot 0.693 \approx 18.5$ mV)",
        "rationale_md": "농도가 2배 → ln(2)만큼 더해지고, 인자 RT/F ≈ 26.7 mV at 310 K. 부호: o가 i보다 많아질수록 E_K는 더 양의 방향으로(덜 음수).",
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 14},
        "priority_score": 0.82,
        "info_density": 0.85,
        "mastery_target": "Nernst",
    },
    {
        "topic": "Nernst",
        "card_type": "proof",
        "difficulty": 4,
        "bloom": "Analyze",
        "prompt_md": "Nernst 식 $E_X = \\frac{RT}{zF}\\ln\\frac{[X]_o}{[X]_i}$를 **Boltzmann 분포 가정**에서 1단계 이상으로 유도하시오.",
        "answer_md": r"""1) 전기화학 평형: $\mu_o = \mu_i$
2) 화학 퍼텐셜 분해: $\mu_X^0 + RT\ln[X] + zF\phi$
3) 양변 항 정리: $RT\ln[X]_o + zF\phi_o = RT\ln[X]_i + zF\phi_i$
4) 전위차로 정리: $E_X = \phi_i - \phi_o = \frac{RT}{zF}\ln\frac{[X]_o}{[X]_i}$""",
        "rationale_md": "각 단계: (1) 평형 조건, (2) 화학 퍼텐셜의 농도+전기 항 분리, (3) 좌·우변 분리, (4) 정의. 부호 주의: 일부 교재는 안-바깥 vs 바깥-안 정의가 다름.",
        "source_citation": {"kind": "textbook", "book": "Fundamental_Neuroscience", "ch": 5, "page": 102},
        "priority_score": 0.92,
        "info_density": 0.9,
        "mastery_target": "Nernst_derivation",
    },

    # ─── HH gating (L5) ──────────────────────────────────────────────────
    {
        "topic": "HH",
        "card_type": "recall",
        "difficulty": 2,
        "bloom": "Remember",
        "prompt_md": "Hodgkin–Huxley 모델에서 K$^+$ 채널 활성화 변수 $n$의 동역학(ODE)을 한 줄로 적으시오.",
        "answer_md": r"$$\frac{dn}{dt} = \alpha_n(V)(1-n) - \beta_n(V)\, n$$",
        "rationale_md": "각 단일 게이트가 열림(1) 또는 닫힘(0) 상태를 가질 확률을 $n$이라 두고, 열림율 $\\alpha_n$과 닫힘율 $\\beta_n$이 모두 V의 함수.",
        "source_citation": {"kind": "slide", "lecture": "L5", "page": 18},
        "priority_score": 0.95,
        "info_density": 0.95,
        "mastery_target": "HH_gating",
    },
    {
        "topic": "HH",
        "card_type": "concept",
        "difficulty": 3,
        "bloom": "Understand",
        "prompt_md": "HH 모델이 K$^+$ 채널 전류를 $\\bar g_K \\cdot n^4 (V - E_K)$로 쓰는 이유, 즉 **$n^4$의 의미**를 설명하시오.",
        "answer_md": "K$^+$ 채널은 4개의 동일한 전압-의존 서브유닛으로 구성되며, 각 서브유닛이 독립적으로 열릴 확률이 $n$. 채널이 전류를 통과시키려면 4개 모두 동시에 열려야 하므로 확률은 $n^4$.",
        "rationale_md": "Hodgkin & Huxley(1952)가 voltage-clamp에서 측정한 K-current의 sigmoidal 시간 경과를 fit하기 위해 도입. 실제 분자 구조와도 일치(Shaker tetramer).",
        "source_citation": {"kind": "slide", "lecture": "L5", "page": 22},
        "priority_score": 0.9,
        "info_density": 0.85,
        "mastery_target": "HH_gating",
    },
    {
        "topic": "HH",
        "card_type": "application",
        "difficulty": 4,
        "bloom": "Apply",
        "prompt_md": "HH 모델에서 Na$^+$ inactivation gate $h$를 0으로 고정시키면 (즉 inactivation 제거), 활동전위 파형(action potential)은 어떻게 변하는가? 한 가지 변화를 설명.",
        "answer_md": "탈분극 단계는 정상이지만 **재분극**이 K$^+$ current에만 의존하게 되고, Na$^+$ current가 지속되어 plateau 또는 더 긴 활동전위를 만든다. 또한 절대 불응기(refractory period)가 사라진다.",
        "rationale_md": "h-gate가 닫혀야 Na 채널이 inactivate되어 $-V$ 방향 회복이 가능. 제거 시 Na 전류가 계속 흘러 K로만 repolarize, 절대 불응기는 h의 회복에 기인하므로 함께 사라짐.",
        "source_citation": {"kind": "slide", "lecture": "L5", "page": 28},
        "priority_score": 0.85,
        "info_density": 0.88,
        "mastery_target": "HH_dynamics",
    },
    {
        "topic": "HH",
        "card_type": "proof",
        "difficulty": 5,
        "bloom": "Analyze",
        "prompt_md": "HH 게이트 ODE $\\frac{dn}{dt} = \\alpha_n(1-n) - \\beta_n n$의 정상상태값 $n_\\infty$와 시간상수 $\\tau_n$을 $\\alpha_n, \\beta_n$으로 표현하시오. (V를 고정으로 가정)",
        "answer_md": r"""$dn/dt = 0$ 조건: $\alpha_n(1-n_\infty) = \beta_n n_\infty$  →  $n_\infty = \frac{\alpha_n}{\alpha_n + \beta_n}$.
ODE 재정리: $\frac{dn}{dt} = -(\alpha_n + \beta_n) n + \alpha_n = -\frac{1}{\tau_n}(n - n_\infty)$  →  $\tau_n = \frac{1}{\alpha_n + \beta_n}$.""",
        "rationale_md": "선형 1차 ODE의 정상상태와 시간상수. 핵심은 우변을 $-(α+β)(n - α/(α+β))$ 형태로 묶어내는 단계. 차원 분석: $τ_n$은 [time], $\\alpha_n,\\beta_n$은 [1/time].",
        "source_citation": {"kind": "textbook", "book": "Dayan_Abbott", "ch": 5, "page": 9},
        "priority_score": 0.95,
        "info_density": 0.95,
        "mastery_target": "HH_steady_state",
    },

    # ─── Cable equation (L6) ─────────────────────────────────────────────
    {
        "topic": "cable",
        "card_type": "recall",
        "difficulty": 2,
        "bloom": "Remember",
        "prompt_md": "Cable 방정식의 **공간 길이 상수(length constant)** $\\lambda$의 정의식을 적으시오. ($d$: 축삭 직경, $R_m$: 비저항(specific membrane resistance), $R_i$: 축내 비저항)",
        "answer_md": r"$$\lambda = \sqrt{\dfrac{d \cdot R_m}{4 R_i}}$$",
        "rationale_md": "막을 RC 분포 회로로 모델링하고 정상상태에서 $\\partial^2 V/\\partial x^2$를 풀어 얻은 1차원 감쇠 거리.",
        "source_citation": {"kind": "slide", "lecture": "L6", "page": 12},
        "priority_score": 0.92,
        "info_density": 0.9,
        "mastery_target": "cable",
    },
    {
        "topic": "cable",
        "card_type": "concept",
        "difficulty": 3,
        "bloom": "Understand",
        "prompt_md": "Cable equation의 직관: 호스에 비유했을 때, **$\\lambda$가 큰** 뉴런이 신호를 더 멀리 전달하는 이유를 두 문장으로.",
        "answer_md": "$\\lambda$가 크면 막저항 $R_m$이 크거나 축내저항 $R_i$가 작거나, 또는 직경이 굵음 — 즉 누설(membrane leak)은 적고 길이 방향 전류는 잘 흐름. 결과적으로 신호가 감쇠 없이 더 멀리 전달.",
        "rationale_md": "정원 호스 분석: 호스(축삭) 굵기 $\\propto d$, 호스 안쪽 마찰 $\\propto R_i$, 호스 옆구리 구멍 $\\propto 1/R_m$. 구멍 적고 굵으면 끝까지 도달.",
        "source_citation": {"kind": "slide", "lecture": "L6", "page": 14},
        "priority_score": 0.85,
        "info_density": 0.8,
        "mastery_target": "cable_intuition",
    },
    {
        "topic": "cable",
        "card_type": "application",
        "difficulty": 4,
        "bloom": "Apply",
        "prompt_md": "축삭 직경을 두 배로 키우면 length constant $\\lambda$는 몇 배가 되는가? (다른 매개변수 동일)",
        "answer_md": r"$\sqrt{2} \approx 1.41$배. ($\lambda \propto \sqrt{d}$)",
        "rationale_md": "$\\lambda = \\sqrt{d R_m / 4 R_i}$이므로 $d$가 2배면 $\\sqrt{2}$ 배. 굵은 축삭이 신호 전달이 빠르고 멀리 가는 정량적 근거.",
        "source_citation": {"kind": "slide", "lecture": "L6", "page": 16},
        "priority_score": 0.78,
        "info_density": 0.85,
        "mastery_target": "cable",
    },
    {
        "topic": "cable",
        "card_type": "proof",
        "difficulty": 5,
        "bloom": "Analyze",
        "prompt_md": "정상상태(steady state) cable equation $\\lambda^2 \\frac{d^2 V}{dx^2} = V$의 일반 해를 구하고, $V(0)=V_0,\\ V(\\infty)=0$ 경계조건에서 닫힌 형태 해를 적으시오.",
        "answer_md": r"""특성 방정식 $\lambda^2 r^2 = 1$ → $r = \pm 1/\lambda$.
일반 해: $V(x) = A e^{x/\lambda} + B e^{-x/\lambda}$.
$V(\infty)=0$ → $A = 0$. $V(0)=V_0$ → $B = V_0$.
따라서 $V(x) = V_0 e^{-x/\lambda}$.""",
        "rationale_md": "분포 회로의 정상상태 해는 지수 감쇠. $\\lambda$가 작을수록 빠르게 0으로 감쇠. 시간 의존성을 추가하려면 PDE $\\lambda^2 V_{xx} - \\tau V_t - V = 0$를 풀어야 함.",
        "source_citation": {"kind": "textbook", "book": "Dayan_Abbott", "ch": 6, "page": 3},
        "priority_score": 0.95,
        "info_density": 0.95,
        "mastery_target": "cable_derivation",
    },
]


def insert_bank_items(items: list[dict]) -> list[int]:
    conn = acquire()
    inserted_ids: list[int] = []
    try:
        with conn.cursor() as cur:
            for it in items:
                cur.execute("""
                    INSERT INTO question_bank
                      (topic, card_type, difficulty, bloom, prompt_md, answer_md,
                       rationale_md, source_citation, priority_score, info_density,
                       mastery_target, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,'active')
                    RETURNING id
                """, (
                    it["topic"], it["card_type"], it["difficulty"], it["bloom"],
                    it["prompt_md"], it["answer_md"], it["rationale_md"],
                    json.dumps(it["source_citation"], ensure_ascii=False),
                    it["priority_score"], it["info_density"],
                    it.get("mastery_target"),
                ))
                inserted_ids.append(cur.fetchone()[0])
        conn.commit()
    finally:
        release(conn)
    return inserted_ids


def register_srs(user_id: int, bank_ids: list[int]) -> int:
    conn = acquire()
    n = 0
    try:
        with conn.cursor() as cur:
            for bid in bank_ids:
                cur.execute("""
                    INSERT INTO srs_cards (user_id, bank_item_id, state)
                    VALUES (%s,%s,'New')
                    ON CONFLICT (user_id, bank_item_id) DO NOTHING
                """, (user_id, bid))
                n += cur.rowcount or 0
        conn.commit()
    finally:
        release(conn)
    return n


async def review_with_multi_lens(items: list[dict]) -> list[dict]:
    """Optional pass: run each item through Multi-Lens once. Marks rejected as 'manual_review'."""
    from review import multi_lens_review, Artifact
    out: list[dict] = []
    for it in items:
        a = Artifact(
            kind="question",
            text=f"문항: {it['prompt_md']}\n\n정답: {it['answer_md']}\n\n해설: {it['rationale_md']}",
            citation=it["source_citation"],
            declared_difficulty=it["difficulty"],
            declared_bloom=it["bloom"],
        )
        res = await multi_lens_review(a, max_rounds=2)
        out.append({**it, "_review_status": res.status, "_review_rounds": res.rounds})
        print(f"  [{it['topic']:>8s} {it['card_type']:>11s}] → {res.status} ({res.rounds} rounds, {res.elapsed_ms} ms)")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--review", action="store_true",
                   help="run Multi-Lens Review on each item before insert (requires OPENROUTER_API_KEY)")
    p.add_argument("--user-id", type=int, default=1)
    args = p.parse_args()

    items = SEEDS
    print(f"Seeding {len(items)} bank items …")
    if args.review:
        if not os.environ.get("OPENROUTER_API_KEY"):
            print("WARN: OPENROUTER_API_KEY not set; --review will fall back to local Ollama or fail")
        items = asyncio.run(review_with_multi_lens(items))
        n_manual = sum(1 for it in items if it.get("_review_status") == "manual_review")
        print(f"  {n_manual} items flagged for manual review (kept active for demo)")

    bank_ids = insert_bank_items(items)
    print(f"  inserted {len(bank_ids)} bank rows: ids {bank_ids[0]}..{bank_ids[-1]}")
    n_cards = register_srs(args.user_id, bank_ids)
    print(f"  registered {n_cards} SRS cards for user_id={args.user_id}")

    # Quick sanity check
    print("\nTopic × type coverage:")
    by_topic: dict[str, dict[str, int]] = {}
    for it in items:
        by_topic.setdefault(it["topic"], {}).setdefault(it["card_type"], 0)
        by_topic[it["topic"]][it["card_type"]] += 1
    for topic, types in by_topic.items():
        print(f"  {topic:>8}: {types}")


if __name__ == "__main__":
    main()
