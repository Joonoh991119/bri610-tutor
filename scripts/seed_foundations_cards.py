#!/usr/bin/env python3
"""
seed_foundations_cards.py — foundational physics+math cards for the BRI610 bank.

These cards build from first principles (Q=CV, I=dQ/dt, Ohm's law, 1st-order
linear ODE) up to the membrane equation, with explicit biological correspondence
(lipid bilayer = capacitor, open ion channels = resistors). Each card embeds an
inline SVG schematic in academic ink (deep-blue strokes on paper).

Slide grounding: L3 p.13 (lipid bilayer / capacitor analogy), L3 p.17–19
(membrane capacitance + I_C = C dV/dt), L3 p.21–22 (membrane resistance,
specific R_m), L3 p.23 (τ_m = R_m C_m).

Idempotent: re-running skips duplicates by (topic, card_type, mastery_target).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))
from db_pool import acquire, release  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────
# Reusable SVG schematics — academic ink palette, 480px wide
# ─────────────────────────────────────────────────────────────────────────

SVG_BILAYER_CAPACITOR = """
<figure>
<svg viewBox="0 0 480 200" xmlns="http://www.w3.org/2000/svg" style="font-family: var(--font-sans); font-size: 13px;">
  <!-- Two parallel plates representing lipid bilayer -->
  <rect x="60" y="55"  width="360" height="14" fill="none" stroke="#1a1a20" stroke-width="1.5"/>
  <rect x="60" y="131" width="360" height="14" fill="none" stroke="#1a1a20" stroke-width="1.5"/>
  <!-- Phospholipid head circles -->
  <g fill="#1a5c8e">
    <circle cx="80"  cy="62" r="3.5"/><circle cx="110" cy="62" r="3.5"/><circle cx="140" cy="62" r="3.5"/>
    <circle cx="170" cy="62" r="3.5"/><circle cx="200" cy="62" r="3.5"/><circle cx="230" cy="62" r="3.5"/>
    <circle cx="260" cy="62" r="3.5"/><circle cx="290" cy="62" r="3.5"/><circle cx="320" cy="62" r="3.5"/>
    <circle cx="350" cy="62" r="3.5"/><circle cx="380" cy="62" r="3.5"/><circle cx="410" cy="62" r="3.5"/>
    <circle cx="80"  cy="138" r="3.5"/><circle cx="110" cy="138" r="3.5"/><circle cx="140" cy="138" r="3.5"/>
    <circle cx="170" cy="138" r="3.5"/><circle cx="200" cy="138" r="3.5"/><circle cx="230" cy="138" r="3.5"/>
    <circle cx="260" cy="138" r="3.5"/><circle cx="290" cy="138" r="3.5"/><circle cx="320" cy="138" r="3.5"/>
    <circle cx="350" cy="138" r="3.5"/><circle cx="380" cy="138" r="3.5"/><circle cx="410" cy="138" r="3.5"/>
  </g>
  <!-- Charge symbols on each plate -->
  <g fill="#8a2a3b" font-weight="700" text-anchor="middle">
    <text x="120" y="48">+</text><text x="200" y="48">+</text><text x="280" y="48">+</text><text x="360" y="48">+</text>
  </g>
  <g fill="#1a5c8e" font-weight="700" text-anchor="middle">
    <text x="120" y="172">−</text><text x="200" y="172">−</text><text x="280" y="172">−</text><text x="360" y="172">−</text>
  </g>
  <!-- E field arrow -->
  <path d="M240 76 L240 124" stroke="#4f4f57" stroke-width="1.2" marker-end="url(#arrow)" fill="none"/>
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L6,4 L0,8 z" fill="#4f4f57"/>
    </marker>
  </defs>
  <text x="252" y="105" fill="#4f4f57" font-style="italic">E</text>
  <!-- Side labels -->
  <text x="40" y="68" text-anchor="end" fill="#1a1a20">extracellular</text>
  <text x="40" y="144" text-anchor="end" fill="#1a1a20">cytoplasm</text>
  <text x="240" y="20" text-anchor="middle" fill="#1a1a20" font-weight="600">lipid bilayer ≈ parallel-plate capacitor</text>
  <text x="240" y="195" text-anchor="middle" fill="#4f4f57" font-style="italic">3–4 nm thick → C_m ≈ 1 μF/cm²</text>
</svg>
<figcaption>Fig 1. Phospholipid bilayer separates intra/extracellular charge — geometrically a parallel-plate capacitor. The 3–4 nm thickness sets the very high specific capacitance C_m ≈ 1 μF/cm².</figcaption>
</figure>
"""

SVG_RC_PARALLEL = """
<figure>
<svg viewBox="0 0 480 220" xmlns="http://www.w3.org/2000/svg" style="font-family: var(--font-sans); font-size: 13px;">
  <!-- Top rail (extracellular) -->
  <line x1="60" y1="40" x2="420" y2="40" stroke="#1a1a20" stroke-width="1.5"/>
  <!-- Bottom rail (cytoplasm) -->
  <line x1="60" y1="180" x2="420" y2="180" stroke="#1a1a20" stroke-width="1.5"/>
  <!-- Capacitor branch -->
  <line x1="160" y1="40" x2="160" y2="100" stroke="#1a1a20" stroke-width="1.5"/>
  <line x1="135" y1="100" x2="185" y2="100" stroke="#1a1a20" stroke-width="2"/>
  <line x1="135" y1="118" x2="185" y2="118" stroke="#1a1a20" stroke-width="2"/>
  <line x1="160" y1="118" x2="160" y2="180" stroke="#1a1a20" stroke-width="1.5"/>
  <text x="195" y="115" fill="#1a5c8e" font-weight="600">C_m</text>
  <text x="195" y="132" fill="#4f4f57" font-style="italic" font-size="11">membrane capacitance</text>
  <!-- Resistor branch (zigzag) -->
  <line x1="280" y1="40" x2="280" y2="80" stroke="#1a1a20" stroke-width="1.5"/>
  <polyline points="280,80 270,86 290,98 270,110 290,122 270,134 290,146 280,152" fill="none" stroke="#1a1a20" stroke-width="1.5"/>
  <line x1="280" y1="152" x2="280" y2="180" stroke="#1a1a20" stroke-width="1.5"/>
  <text x="305" y="115" fill="#1a5c8e" font-weight="600">R_m</text>
  <text x="305" y="132" fill="#4f4f57" font-style="italic" font-size="11">open-channel resistance</text>
  <!-- Battery (E_rest) -->
  <line x1="280" y1="155" x2="280" y2="160" stroke="#1a1a20"/>
  <line x1="270" y1="160" x2="290" y2="160" stroke="#1a1a20" stroke-width="2"/>
  <line x1="275" y1="166" x2="285" y2="166" stroke="#1a1a20" stroke-width="2"/>
  <text x="305" y="166" fill="#4f4f57" font-style="italic" font-size="11">V_rest</text>
  <!-- Current source I_inj on the right -->
  <circle cx="380" cy="110" r="14" fill="none" stroke="#b16413" stroke-width="1.5"/>
  <line x1="380" y1="103" x2="380" y2="117" stroke="#b16413" stroke-width="1.5" marker-end="url(#arr2)"/>
  <line x1="380" y1="40" x2="380" y2="96" stroke="#b16413" stroke-width="1.5"/>
  <line x1="380" y1="124" x2="380" y2="180" stroke="#b16413" stroke-width="1.5"/>
  <text x="402" y="115" fill="#b16413" font-weight="600">I_inj</text>
  <defs>
    <marker id="arr2" markerWidth="7" markerHeight="7" refX="3" refY="6" orient="auto">
      <path d="M0,0 L3,6 L6,0 z" fill="#b16413"/>
    </marker>
  </defs>
  <!-- Membrane labels -->
  <text x="20"  y="44" fill="#1a1a20">out</text>
  <text x="20"  y="184" fill="#1a1a20">in</text>
  <text x="240" y="20" text-anchor="middle" fill="#1a1a20" font-weight="600">membrane = parallel RC + driver</text>
  <text x="240" y="210" text-anchor="middle" fill="#4f4f57" font-style="italic">C_m: lipid bilayer · R_m: 1 / Σ open-channel conductance · I_inj: pipette / synapse</text>
</svg>
<figcaption>Fig 2. Single-compartment passive membrane as a parallel RC circuit. Capacitive branch stores charge across the bilayer; resistive branch carries leakage through open ion channels at rest. Injected current I_inj is split between the two branches according to KCL.</figcaption>
</figure>
"""

SVG_RC_CHARGING_CURVE = """
<figure>
<svg viewBox="0 0 480 240" xmlns="http://www.w3.org/2000/svg" style="font-family: var(--font-sans); font-size: 12px;">
  <!-- Axes -->
  <line x1="60" y1="200" x2="440" y2="200" stroke="#1a1a20" stroke-width="1.2"/>
  <line x1="60" y1="40"  x2="60"  y2="200" stroke="#1a1a20" stroke-width="1.2"/>
  <text x="240" y="225" text-anchor="middle" fill="#1a1a20">time t</text>
  <text x="40"  y="120" text-anchor="end"   fill="#1a1a20" transform="rotate(-90, 40, 120)">V(t)</text>
  <!-- V_rest baseline -->
  <line x1="60" y1="180" x2="440" y2="180" stroke="#4f4f57" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="445" y="184" fill="#4f4f57">V_rest</text>
  <!-- V_∞ asymptote -->
  <line x1="60" y1="60"  x2="440" y2="60"  stroke="#1a5c8e" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="445" y="64" fill="#1a5c8e">V_∞ = V_rest + R_m I_inj</text>
  <!-- Charging curve V(t) = V_∞ + (V_0 - V_∞) e^(-t/τ) with V_0 = V_rest -->
  <path d="M 60 180
           Q 100 100, 160 78
           Q 220 65, 280 62
           Q 340 60.5, 440 60"
        fill="none" stroke="#8a2a3b" stroke-width="2"/>
  <!-- t = τ marker -->
  <line x1="160" y1="200" x2="160" y2="195" stroke="#1a1a20"/>
  <line x1="160" y1="78"  x2="160" y2="200" stroke="#4f4f57" stroke-width="0.8" stroke-dasharray="2,3"/>
  <text x="160" y="216" text-anchor="middle" fill="#1a1a20">τ_m</text>
  <text x="170" y="92" fill="#4f4f57">63%</text>
  <!-- t = 0+ tangent -->
  <line x1="60" y1="180" x2="120" y2="125" stroke="#b16413" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="110" y="118" fill="#b16413">slope = I_inj / C_m</text>
  <text x="240" y="20" text-anchor="middle" fill="#1a1a20" font-weight="600">RC charging — single membrane to step current</text>
</svg>
<figcaption>Fig 3. Capacitor-charging curve solving τ_m dV/dt = -(V - V_rest) + R_m I_inj with V(0) = V_rest. At t = 0⁺ the slope is I_inj / C_m (capacitor takes all the current; leak hasn't engaged). At t = τ_m the response has covered 63% of the gap to V_∞. As t → ∞ leak balances injection.</figcaption>
</figure>
"""

SVG_OHMS_VI = """
<figure>
<svg viewBox="0 0 420 220" xmlns="http://www.w3.org/2000/svg" style="font-family: var(--font-sans); font-size: 12px;">
  <!-- Axes -->
  <line x1="50" y1="180" x2="380" y2="180" stroke="#1a1a20" stroke-width="1.2"/>
  <line x1="200" y1="30"  x2="200" y2="200" stroke="#1a1a20" stroke-width="1.2"/>
  <text x="375" y="195" fill="#1a1a20">V (mV)</text>
  <text x="208" y="40" fill="#1a1a20">I (nA)</text>
  <!-- V = E (reversal) marker on x-axis -->
  <line x1="280" y1="175" x2="280" y2="185" stroke="#1a1a20"/>
  <text x="280" y="200" text-anchor="middle" fill="#4f4f57">E_X</text>
  <!-- I-V line through (E_X, 0) -->
  <line x1="80" y1="80" x2="380" y2="170" stroke="#1a5c8e" stroke-width="2"/>
  <text x="320" y="155" fill="#1a5c8e" font-weight="600">slope = g_X = 1/R_X</text>
  <!-- driving force marker -->
  <line x1="240" y1="180" x2="240" y2="148" stroke="#b16413" stroke-width="1.2"/>
  <text x="245" y="165" fill="#b16413" font-style="italic">driving force V − E_X</text>
  <text x="245" y="148" fill="#b16413">→ I_X</text>
  <!-- Labels -->
  <text x="200" y="20" text-anchor="middle" fill="#1a1a20" font-weight="600">single-channel I-V (Ohmic, slope = conductance)</text>
  <text x="200" y="216" text-anchor="middle" fill="#4f4f57" font-style="italic">I_X = g_X (V − E_X);  zero current at V = E_X</text>
</svg>
<figcaption>Fig 4. Ohmic ionic current. Open ion channels give a linear I-V relation with slope equal to channel conductance g_X. Current vanishes when V = E_X (the ion's reversal potential, set by Nernst). The driving force V − E_X is the deviation from equilibrium that pushes ions through the open channel.</figcaption>
</figure>
"""


# ─────────────────────────────────────────────────────────────────────────
# Foundation cards (8 items)
# ─────────────────────────────────────────────────────────────────────────

SEEDS: list[dict] = [
    {
        "topic": "foundations",
        "card_type": "recall",
        "difficulty": 1,
        "bloom": "Remember",
        "mastery_target": "capacitance_definition",
        "prompt_md": (
            "**Setup.** 두 도체가 절연체로 분리되어 있을 때, 양쪽에 쌓이는 전하 $Q$ 와 그 사이의 전위차 $V$ 사이의 비를 정전용량(capacitance) $C$ 로 정의한다.\n\n"
            f"{SVG_BILAYER_CAPACITOR}\n\n"
            "(a) 정전용량 $C$ 의 정의식과 SI 단위를 적으시오.\n"
            "(b) 위 그림의 lipid bilayer를 이런 capacitor로 모델링했을 때, 두 \"plate\"는 각각 무엇이고, "
            "두 plate를 분리하는 \"insulator\"는 무엇인가? 이 분리 거리가 $C$ 에 어떤 영향을 주는가?"
        ),
        "answer_md": (
            "(a) $$\\boxed{Q = C V \\quad\\Longleftrightarrow\\quad C = \\frac{Q}{V}}$$\n"
            "단위: $[C] = \\mathrm{F}\\,(\\text{Farad}) = \\mathrm{C/V}$. 신경과학에서는 흔히 $\\mu\\mathrm{F}$ 또는 $\\mathrm{nF}$ 사용.\n\n"
            "(b) Lipid bilayer의 capacitor 대응:\n"
            "  - **상부 plate** = 세포막 외부면을 따라 정렬된 전하 (extracellular leaflet 표면).\n"
            "  - **하부 plate** = 세포막 내부면을 따라 정렬된 반대 부호 전하 (cytoplasmic leaflet 표면).\n"
            "  - **insulator** = lipid bilayer 자체의 hydrophobic core (3–4 nm 두께, 이온 통과 거의 불가).\n\n"
            "분리 거리 효과: 평행판 capacitor 공식 $C = \\varepsilon A / d$ 에서 $d$ (분리 거리)에 *반비례*. Bilayer 두께가 매우 작으므로 (3–4 nm) 단위 면적당 정전용량(specific capacitance) $C_m$ 이 매우 크다 — **세포막의 전형값 1 μF/cm²**, 같은 면적 macroscopic capacitor보다 훨씬 큼."
        ),
        "rationale_md": (
            "$Q = CV$ 는 단순 기억할 식이 아니라 *capacitor의 정의 그 자체*다. 어떤 capacitor든 \"같은 전압을 만들기 위해 얼마나 많은 전하를 양쪽에 분리시켜야 하는가\" 를 정량화. "
            "**뉴런에서의 의미**: 막전위 $V_m$ 을 1 mV 변화시키려면 막 양쪽에 약간의 전하 불균형 ($Q = C_m V_m$) 이 필요하고, 이 불균형은 ion channel 을 통한 전류 흐름으로만 만들 수 있다 — 이 사실이 다음 카드의 $I_C = C \\, dV/dt$ 출발점이다.\n\n"
            "**흔한 오개념**: $Q$ 가 양쪽 plate에 따로따로 존재하는 정전기 charge 가 아닌 *그 차이*라는 점. 한쪽 plate에 +Q가 쌓이면 반대쪽에 -Q가 induced됨 (charge conservation). 막의 경우 cytoplasm 쪽 음전하 ↔ extracellular 쪽 양전하."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 13,
                             "secondary_lecture": "L3", "secondary_page": 17,
                             "primary": "Hille 2001 Ion Channels of Excitable Membranes"},
        "priority_score": 0.99,
        "info_density": 0.92,
    },

    {
        "topic": "foundations",
        "card_type": "proof",
        "difficulty": 2,
        "bloom": "Understand",
        "mastery_target": "capacitive_current",
        "prompt_md": (
            "**Setup.** $Q = CV$ 에서 출발하여 capacitor를 통과하는 전류 $I_C$ 를 시간 도함수로 표현하고자 한다.\n\n"
            "(a) $Q = CV$ 의 양변을 시간 $t$ 로 미분하라. $C$ 가 시간에 무관하다고 가정한다.\n"
            "(b) 전류 $I = dQ/dt$ 의 정의를 적용하여 capacitor 전류 공식 $I_C = C \\, dV/dt$ 를 얻으라.\n"
            "(c) 이 결과를 뉴런에 적용했을 때 무엇을 의미하는가? \"막전위가 안 변하면 ($dV/dt = 0$) capacitive current도 0\" 이라는 사실의 직관적 설명을 한 문장으로 답하라."
        ),
        "answer_md": (
            "(a) $\\frac{d}{dt}(Q) = \\frac{d}{dt}(CV) = C \\frac{dV}{dt}$ \n"
            "  ($C$ 는 상수로 빠져나옴.)\n\n"
            "(b) 좌변 $dQ/dt$ 는 $I$ 의 정의이므로:\n"
            "$$\\boxed{I_C = C \\, \\frac{dV}{dt}}$$\n\n"
            "(c) **직관**: 막전위가 일정($dV/dt = 0$)하면 양쪽 plate에 쌓인 전하가 변하지 않으므로 capacitor를 통과하는 알짜 전류는 0. *변화*하는 전하만이 *전류*다. 막전위가 *움직일 때만* capacitor가 전류를 \"먹는다.\"\n\n"
            "$L3$ p.20 슬라이드 예시: $C_m = 1\\,\\mathrm{nF}$ 뉴런에 $1\\,\\mathrm{nA}$ 흘리면 막전위 변화율은 $1\\,\\mathrm{nA} / 1\\,\\mathrm{nF} = 1\\,\\mathrm{V/s} = 1\\,\\mathrm{mV/ms}$."
        ),
        "rationale_md": (
            "이 한 줄 유도가 모든 막 dynamics의 출발점이다. $I_C = C dV/dt$ 가 막을 *시간 변화에 저항하는 lowpass filter* 로 만들고, 이로부터 막 시상수 $\\tau_m$ 의 의미가 따라온다.\n\n"
            "**흔한 오개념**: \"capacitor가 전류를 *통과시킨다*\" 라는 표현. 사실 capacitor 내부로 전하는 *흐르지 않는다* (절연체이므로). 외부 회로에서 한쪽 plate로 전하가 쌓이면 반대쪽 plate에서 같은 양의 반대 부호 전하가 *밀려나간다*. 외부에서 보면 전류가 통과하는 것처럼 보이지만 내부적으로는 *charge displacement*. 이 차이는 양자/electromagnetism 수준에서 중요하나 회로 분석 수준에서는 동등.\n\n"
            "**연결**: 뉴런 모델에서 $I_C$ 는 \"외부 입력 전류 중 막 양쪽 plate 충전에 들어가는 부분\". 나머지는 ion channel을 통해 흘러나간다 — 이것이 $I_{inj} = I_C + I_{leak}$ 라는 KCL 식이고, 막 방정식의 KCL 출발."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 19,
                             "secondary_lecture": "L3", "secondary_page": 20},
        "priority_score": 0.99,
        "info_density": 0.93,
    },

    {
        "topic": "foundations",
        "card_type": "concept",
        "difficulty": 2,
        "bloom": "Understand",
        "mastery_target": "ohms_law_membrane",
        "prompt_md": (
            "**Setup.** 옴 법칙(Ohm's law) $I = V/R$ 을 뉴런 막에 적용하려면 두 가지를 보정해야 한다: (1) 단일 저항이 아니라 다수의 ion channel 이 *병렬* 연결, (2) 각 ion에 *고유 평형 전위* $E_X$ 가 있어 \"V = 0\" 이 아닌 \"V = E_X\" 일 때 전류가 0.\n\n"
            f"{SVG_OHMS_VI}\n\n"
            "(a) 단일 ion 종류 $X$ 에 대한 회로 등가 옴 법칙을 적으시오. (V−E_X 의 의미를 설명)\n"
            "(b) 그림에서 *기울기*가 의미하는 물리량은 무엇인가? 단위와 함께 답하라.\n"
            "(c) **뉴런 대응**: 같은 ion 종류 $X$ 에 대한 채널 $N_X$ 개가 모두 동시에 열려 있으면, 전체 conductance와 저항은 어떻게 표현되는가?"
        ),
        "answer_md": (
            "(a) Ohmic ion current:\n"
            "$$I_X = g_X \\, (V - E_X) = \\frac{V - E_X}{R_X}.$$\n"
            "여기서 $g_X = 1/R_X$ 는 **conductance**, $V - E_X$ 는 **driving force** (평형으로부터의 전압 편차). $V = E_X$ 일 때 driving force = 0이므로 알짜 ion 전류 = 0 (이온이 들어가는 만큼 나옴 — 평형).\n\n"
            "(b) 그림의 직선 기울기는 conductance $g_X$. 단위 $[g] = \\mathrm{S}\\,(\\text{Siemens}) = 1/\\Omega$. 신경과학에서는 흔히 $\\mathrm{nS}$ 또는 $\\mathrm{pS}$ (단일 채널). 단일 NMDA 채널 ≈ 50 pS, K_v 채널 ≈ 10–20 pS.\n\n"
            "(c) **병렬 conductance 합산**:\n"
            "$$g_X^{\\text{total}} = N_X \\cdot g_X^{\\text{single}}.$$\n"
            "옴의 법칙에서 *저항이 병렬 연결되면 conductance가 더해진다*. 따라서 $N_X$ 개의 같은 채널이 동시에 열리면 전체 conductance는 $N_X \\cdot g_X^{\\text{single}}$, 전체 저항은 $1 / (N_X g_X^{\\text{single}})$.\n"
            "단일 컴파트먼트 막 수준에서 specific conductance $\\bar g_X = N_X g_X^{\\text{single}} / A$ (per area). HH 모델의 $\\bar g_K, \\bar g_{Na}$ 가 정확히 이 양."
        ),
        "rationale_md": (
            "**핵심 통찰**: \"$V$ = 0 일 때 전류 0\" 가 아니라 \"$V$ = $E_X$ 일 때 전류 0\". 평형 전위가 $V$ 좌표축 *원점이 아닌 곳에 있는* 옴 법칙. 이 shift 가 모든 ion-driven 막 dynamics 의 핵심.\n\n"
            "**흔한 오개념**: \"$E_X$ 가 0이면 안 되나?\" — 아니다. 농도 기울기가 자연 평형을 만들어내고 그 평형은 $V \\neq 0$ 인 곳. K⁺ 에서는 $E_K \\approx -90$ mV, Na⁺에서는 $E_{Na} \\approx +60$ mV. 다른 평형이 다른 곳에 있기 때문에 ion channel을 *동시에 다르게 열고 닫음으로써* 막전위를 능동적으로 제어할 수 있다 — HH model 의 전제.\n\n"
            "**연결**: 다음 카드 (RC 회로) 에서 capacitor와 \"all ion channel resistors in parallel\" 이 어떻게 결합되는지 본다. 각 ion 종류의 contribution은 $I_X = g_X(V-E_X)$ 로 동일 형태."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 22,
                             "secondary_lecture": "L3", "secondary_page": 33,
                             "primary": "Hille 2001 Ch.1"},
        "priority_score": 0.97,
        "info_density": 0.95,
    },

    {
        "topic": "foundations",
        "card_type": "concept",
        "difficulty": 2,
        "bloom": "Understand",
        "mastery_target": "rc_circuit_membrane",
        "prompt_md": (
            "**Setup.** 막은 capacitor (lipid bilayer)와 resistor (열린 ion channel들)이 *병렬*로 연결된 1차 RC 회로다. 외부에서 전류 $I_{inj}$ 를 주입하면 KCL에 의해 두 갈래로 나뉜다.\n\n"
            f"{SVG_RC_PARALLEL}\n\n"
            "(a) 위 회로에 KCL을 적용하여 $I_{inj} = I_C + I_R$ 를 두 element 식으로 적으시오 ($I_C, I_R$ 각각 풀어쓰기).\n"
            "(b) 양변을 정리하여 1차 ODE 형태 $C_m \\, dV/dt = ?$ 로 적으시오. 이것이 *막 방정식*이다.\n"
            "(c) **뉴런 대응**: 만약 모든 ion channel이 닫혀 ($R_m \\to \\infty$) capacitor만 남는다면 $V$ 는 어떻게 거동하는가? 반대로 capacitor가 없다면 ($C_m = 0$) $V$ 는 어떻게 거동하는가? — 두 극한이 막의 dynamic을 어떻게 *결정*하는지 설명."
        ),
        "answer_md": (
            "(a) **KCL 적용** (입력 = 두 branch 합산):\n"
            "$$I_{inj} = \\underbrace{C_m \\frac{dV}{dt}}_{I_C} + \\underbrace{\\frac{V - V_{rest}}{R_m}}_{I_R}.$$\n\n"
            "(b) **막 방정식** (1차 ODE):\n"
            "$$\\boxed{C_m \\frac{dV}{dt} = -\\frac{V - V_{rest}}{R_m} + I_{inj}.}$$\n"
            "양변에 $R_m$ 곱하고 $\\tau_m = R_m C_m$ 도입:\n"
            "$$\\tau_m \\frac{dV}{dt} = -(V - V_{rest}) + R_m I_{inj}.$$\n\n"
            "(c) **두 극한의 의미**:\n"
            "  - **모든 채널 닫힘** ($R_m \\to \\infty$, $I_R \\to 0$): $C_m dV/dt = I_{inj}$ → $V(t) = V_0 + (I_{inj}/C_m) t$ — 시간에 따라 *선형으로 무한정* 증가. 누설이 없으므로 자기-안정화 메커니즘이 사라진다.\n"
            "  - **Capacitor 없음** ($C_m = 0$): KCL → $I_{inj} = (V - V_{rest})/R_m$ → $V = V_{rest} + R_m I_{inj}$ 즉시. 시간 상수가 0이라 *순간적으로* 정상상태에 도달.\n\n"
            "두 극한 모두 비물리적 (실제 막은 *둘 다* 가짐). 막 dynamic의 본질은 **capacitor가 막전위를 정상상태로 향하는 즉각 변화로부터 *지연*시킨다**: $\\tau_m$ 라는 time scale을 도입해 1차 lowpass filter를 만든다. $\\tau_m$ ≈ 10–100 ms 가 EPSP/IPSP 시간 스케일을 결정 — 너무 짧으면 입력 통합 안 되고, 너무 길면 빠른 패턴 손실."
        ),
        "rationale_md": (
            "**핵심 통찰**: 막의 *capacitor*와 *resistor*는 단지 회로 부품이 아니라 *서로 다른 시간 스케일* 의 메모리. Capacitor는 직전 전하 상태를 \"기억\" (느린 변화), resistor는 즉각 ion 흐름 (빠른 응답). 둘이 결합하면 RC = lowpass = *시간 통합 (temporal integration)* 이라는 신호처리 기능이 생긴다.\n\n"
            "**흔한 오개념**: 막 방정식이 \"임의로 정의된\" 모델이 아니라 *옴 법칙 + capacitor 정의 + KCL* 만으로 *유도되는* 결과라는 점을 못 보는 것. 과학적으로 막이 RC 회로처럼 행동하는 것은 *가정*이 아니라 *측정 가능한 사실* (Cole & Curtis 1936).\n\n"
            "**연결**: HH 모델 (L5 p.4)은 정확히 이 식의 우변에 voltage-dependent active conductance 항 $g_K(V,t)(V-E_K) + g_{Na}(V,t)(V-E_{Na})$ 를 추가한다. 우변 구조는 동일, 다만 각 ion의 conductance가 시간/전압에 의존."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 23,
                             "secondary_lecture": "L5", "secondary_page": 4},
        "priority_score": 0.99,
        "info_density": 0.97,
    },

    {
        "topic": "foundations",
        "card_type": "proof",
        "difficulty": 3,
        "bloom": "Apply",
        "mastery_target": "first_order_ode_homogeneous",
        "prompt_md": (
            "**Setup.** 1차 선형 동질 ODE $\\tau \\, dy/dt = -y$ 를 만나는 모든 1학년 물리/생리 문제 (radioactive decay, RC discharge, gating variable approach to 0) 의 *공통 해법*을 익혀야 한다.\n\n"
            "(a) 분리변수법(separation of variables)으로 ODE를 풀라. 적분상수를 $A$ 로 두라.\n"
            "(b) 초기조건 $y(0) = y_0$ 를 적용해 $A$ 를 결정하라.\n"
            "(c) 폐형 해 $y(t) = y_0 e^{-t/\\tau}$ 가 다음 두 성질을 가짐을 보이라:\n"
            "  - $t = 0$ 에서 $y = y_0$ ✓\n"
            "  - $t = \\tau$ 에서 $y$ 는 처음 값의 약 **37%** 로 감소 ($1/e$).\n"
            "(d) **반감기 $T_{1/2}$**와 시간상수 $\\tau$ 의 관계 $T_{1/2} = \\tau \\ln 2 \\approx 0.693\\,\\tau$ 를 유도하라."
        ),
        "answer_md": (
            "(a) **분리변수**:\n"
            "$\\frac{dy}{y} = -\\frac{dt}{\\tau}$. 양변 적분: $\\ln |y| = -t/\\tau + C_1$.\n"
            "지수화: $y(t) = A e^{-t/\\tau}$, 단 $A = \\pm e^{C_1}$ (적분상수, 부호 흡수).\n\n"
            "(b) **경계조건**: $y(0) = A \\cdot 1 = A$. 따라서 $A = y_0$.\n"
            "$$\\boxed{y(t) = y_0 \\, e^{-t/\\tau}.}$$\n\n"
            "(c) **두 성질**:\n"
            "  - $y(0) = y_0 \\cdot e^0 = y_0$. ✓\n"
            "  - $y(\\tau) = y_0 \\cdot e^{-1} = y_0 / e \\approx 0.368\\, y_0$. **약 37%로 감소**. ✓\n\n"
            "(d) **반감기**: $y(T_{1/2}) = y_0 / 2$ 인 시각.\n"
            "$y_0 / 2 = y_0 e^{-T_{1/2}/\\tau}$ → $1/2 = e^{-T_{1/2}/\\tau}$ → $T_{1/2}/\\tau = \\ln 2$.\n"
            "$$\\boxed{T_{1/2} = \\tau \\ln 2 \\approx 0.693\\, \\tau.}$$\n"
            "예: $\\tau_m = 20$ ms 인 뉴런의 EPSP 반감기 ≈ 14 ms."
        ),
        "rationale_md": (
            "**Universal pattern**: $\\tau \\, dy/dt = -y$ 는 \"현재 값에 *비례*하는 속도로 0을 향해 감소\" 라는 자연 현상의 정확한 수학적 표현. 이 패턴이 등장하는 곳:\n"
            "  - 방사성 붕괴 ($N(t) = N_0 e^{-\\lambda t}$, $\\tau = 1/\\lambda$)\n"
            "  - RC capacitor discharge ($V(t) = V_0 e^{-t/RC}$)\n"
            "  - HH gating variable이 0을 향할 때 (극한 $n_\\infty(V) = 0$ 가정)\n"
            "  - 약물 혈중 농도 1차 elimination\n\n"
            "**흔한 실수**: $\\tau$ 와 \"반감기\" 를 같게 보는 것 — 실제로는 $T_{1/2} = 0.693\\,\\tau$ 로 항상 더 짧다. \"63% 감소까지 1 $\\tau$\" 와 \"50% 감소까지 0.69 $\\tau$\" 두 표현 모두 자주 쓰이므로 둘 다 익숙해야 한다.\n\n"
            "**연결**: 다음 카드는 비동질 항이 추가된 일반 형태 $\\tau dy/dt = -y + B$ — 막 방정식 그 자체. 변수 변환으로 위 동질 형태로 환원되는 것이 핵심 트릭."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 23,
                             "secondary_lecture": "L5", "secondary_page": 22,
                             "primary": "표준 1차 ODE 분리변수법"},
        "priority_score": 0.96,
        "info_density": 0.92,
    },

    {
        "topic": "foundations",
        "card_type": "proof",
        "difficulty": 3,
        "bloom": "Apply",
        "mastery_target": "first_order_ode_inhomogeneous",
        "prompt_md": (
            "**Setup.** 일반화된 1차 선형 ODE $\\tau \\, dy/dt = -y + B$ ($B$ 는 시간 상수). 막 방정식 ($B = R_m I_{inj} + V_{rest}$ 등), HH gating ODE ($B = \\alpha n_\\infty$), 약리학 (drug input + clearance) 등 어디나 등장.\n\n"
            "(a) 정상상태 (steady state) 값 $y_\\infty$ 를 $dy/dt = 0$ 조건으로 구하라.\n"
            "(b) 변수 변환 $u(t) = y(t) - y_\\infty$ 도입. 이 ODE 를 *동질* ODE $\\tau du/dt = -u$ 로 환원하라 (앞 카드 결과를 사용 가능).\n"
            "(c) 이전 카드 (a)의 결과 $u(t) = u_0 e^{-t/\\tau}$ 을 $y$ 로 되돌려, 초기조건 $y(0) = y_0$ 일 때 폐형 해를 적으라.\n"
            "(d) **두 sanity check**: $t = 0$ 와 $t \\to \\infty$ 극한에서 답이 각각 $y_0$ 과 $y_\\infty$ 가 됨을 확인."
        ),
        "answer_md": (
            "(a) **정상상태**: $0 = -y_\\infty + B$ → $y_\\infty = B$.\n\n"
            "(b) **변수 변환**: $u = y - y_\\infty$, 그러므로 $du/dt = dy/dt$.\n"
            "원 ODE의 우변: $-y + B = -(u + y_\\infty) + B = -u + (B - y_\\infty) = -u + 0 = -u$.\n"
            "$$\\tau \\frac{du}{dt} = -u.$$\n\n"
            "(c) 이전 카드 결과: $u(t) = u(0) e^{-t/\\tau}$. 초기 $u(0) = y_0 - y_\\infty$. 변환 되돌리기:\n"
            "$$\\boxed{y(t) = y_\\infty + (y_0 - y_\\infty) \\, e^{-t/\\tau}.}$$\n\n"
            "(d) **Sanity check**:\n"
            "  - $t = 0$: $y(0) = y_\\infty + (y_0 - y_\\infty) \\cdot 1 = y_0$ ✓\n"
            "  - $t \\to \\infty$: $e^{-t/\\tau} \\to 0$, $y(\\infty) = y_\\infty$ ✓\n\n"
            "**중요한 특수 케이스**: $y_0 = 0$ (\"휴지 상태에서 출발\") → $y(t) = y_\\infty (1 - e^{-t/\\tau})$ — \"capacitor charging curve\" 표준형."
        ),
        "rationale_md": (
            "이 한 카드가 BRI610 강의의 *대부분의 폐형 해*를 한 번에 설명한다:\n"
            "  - **막 방정식 step response**: $y \\equiv V$, $\\tau \\equiv \\tau_m$, $y_\\infty \\equiv V_{rest} + R_m I_{inj}$.\n"
            "  - **HH gating $n(t)$ at fixed $V$**: $y \\equiv n$, $\\tau \\equiv \\tau_n(V)$, $y_\\infty \\equiv n_\\infty(V)$.\n"
            "  - **Cable equation 정상상태 spatial**: 시간 → 공간으로 변수 교체.\n\n"
            "**핵심 트릭**: 비동질 ODE를 푸는 *유일한 정공법*은 *변수 변환으로 동질로 환원* 또는 *적분인자(integrating factor)*. 변수 변환이 더 직관적이고 외울 거리가 적다. 이 패턴이 한 번 손에 익으면 BRI610의 모든 1차 ODE 문제는 *3분 안에 풀 수 있다*.\n\n"
            "**흔한 실수**: 변수 변환 단계에서 $du/dt$ 와 $dy/dt$ 가 같음을 안 알아채는 것 ($y_\\infty$ 가 시간 상수이므로). 또 적분상수를 잘못 두는 것 — $A = y_0 - y_\\infty$ 가 맞다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 23,
                             "secondary_lecture": "L5", "secondary_page": 22},
        "priority_score": 0.99,
        "info_density": 0.96,
    },

    {
        "topic": "foundations",
        "card_type": "concept",
        "difficulty": 2,
        "bloom": "Apply",
        "mastery_target": "rc_charging_curve",
        "prompt_md": (
            "**Setup.** 앞 두 카드 (capacitor 정의, 1차 ODE 일반해)를 결합하면 막의 *step current 응답*을 그릴 수 있다.\n\n"
            f"{SVG_RC_CHARGING_CURVE}\n\n"
            "(a) 위 그림에서 *세 가지 시간 영역*을 식별하고, 각 영역에서 어떤 *물리적 균형*이 일어나는지 한 줄씩 설명하라:\n"
            "  - 영역 ①: $t = 0^+$ (직후 — 위 그림의 주황색 접선 부분)\n"
            "  - 영역 ②: $t = \\tau_m$ 근방 (capacitor 충전과 누설 균형 천이)\n"
            "  - 영역 ③: $t \\gg \\tau_m$ (정상상태)\n\n"
            "(b) 그림에서 **63%** 표시는 무엇이며, 왜 정확히 그 값인가?\n"
            "(c) **연결**: 만약 $I_{inj}$ 를 step (계단)이 아닌 *짧은 pulse* (예: 1 ms 동안만)로 주면 $V(t)$ 곡선은 어떻게 달라지는가? (정성적으로 한 문단)"
        ),
        "answer_md": (
            "(a) **세 영역 균형**:\n"
            "  - **① $t = 0^+$**: capacitor가 모든 input current를 받는다 (leak는 아직 활성화 안 됨, $V \\approx V_{rest}$). $C_m dV/dt \\approx I_{inj}$. 초기 기울기는 *최대* $I_{inj}/C_m$.\n"
            "  - **② $t \\approx \\tau_m$**: capacitor가 충전되며 $V$ 가 상승. 누설 전류 $(V - V_{rest})/R_m$ 가 켜져 입력의 일부를 상쇄. 곡선이 위로 오목해지며 점근선을 향해 굽어든다.\n"
            "  - **③ $t \\gg \\tau_m$**: 정상상태 도달, $dV/dt = 0$, capacitor 멈춤, 누설이 모든 input 을 처리: $I_{inj} = (V_\\infty - V_{rest})/R_m$.\n\n"
            "(b) **63% 표시**: $V(\\tau_m) - V_{rest} = (V_\\infty - V_{rest})(1 - e^{-1}) \\approx 0.632\\,(V_\\infty - V_{rest})$. 즉 1 시간 상수 후 $V$ 는 정상상태까지의 거리의 *63.2%* 를 채운다. $1 - 1/e$ 의 numerical value.\n\n"
            "(c) **Pulse 응답 (정성적)**: pulse가 켜진 동안 $V$ 는 위 그림처럼 오르기 시작 ($t = 0^+$ 기울기 $I_{inj}/C_m$). pulse 가 끝난 시점 $t_{off}$ (예: 1 ms) 에서 $V$ 가 도달한 값을 $V^*$ 라 하자. 이후 $I_{inj} = 0$ 이므로 막은 $V_{rest}$ 로 *지수 감쇠*: $V(t) = V_{rest} + (V^* - V_{rest})e^{-(t-t_{off})/\\tau_m}$. \n\n"
            "  $\\tau_m \\gg t_{off}$ (긴 시간상수 / 짧은 pulse) 인 경우 — *integrate-and-fire 영역* — $V^*$ 는 $V_\\infty$ 보다 훨씬 작고 (capacitor가 채 충전되기 전에 pulse 끝남), 응답은 거의 *triangular*. 이것이 *temporal integration* 의 본질: 짧은 EPSP 들이 누적되어 spike threshold 도달 가능."
        ),
        "rationale_md": (
            "이 곡선의 모양을 *직관적으로* 머리에 그릴 수 있어야 BRI610의 후속 모든 막 동역학 그림을 이해할 수 있다. EPSP, IPSP, action potential 의 기본 \"오르고 내림\" 모양이 모두 이 곡선의 변형.\n\n"
            "**흔한 오개념 1**: $V$ 가 step input 시 즉시 $V_\\infty$ 로 점프한다고 그리는 것. 아니다 — capacitor가 *필연적으로 지연을 도입*. 이 지연이 없으면 spike timing 자체가 정의 불가.\n"
            "**흔한 오개념 2**: 반대로 \"$\\tau$ 는 끝점에 도달하는 시간\" 이라고 생각하는 것. $\\tau$ 는 *63%*만 채우는 시간; 99% 도달하려면 $\\sim 5\\tau$ 필요.\n\n"
            "**연결**: integrate-and-fire (LIF) 모델 (L7 p.10–14) 은 이 곡선이 spike threshold에 닿을 때까지 시간을 ISI 로 정의. Cable equation (L6 p.10) 은 이 시간 곡선이 공간에 펼쳐진 *공간 곡선*."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 20,
                             "secondary_lecture": "L7", "secondary_page": 12},
        "priority_score": 0.97,
        "info_density": 0.94,
    },

    {
        "topic": "foundations",
        "card_type": "concept",
        "difficulty": 2,
        "bloom": "Understand",
        "mastery_target": "neuron_circuit_correspondence",
        "prompt_md": (
            "**Setup.** \"막 방정식\" 은 추상적 수식이 아니라 뉴런 *생물물리* 의 직접적 번역이다. 다음 표를 완성하시오 — 회로 element 가 *어떤 분자/구조* 에 대응하는지, *어떤 측정값* 으로 결정되는지.\n\n"
            "| 회로 element | 신경막의 대응 분자/구조 | 결정 요인 (어떻게 측정?) | 전형적 값 |\n"
            "|---|---|---|---|\n"
            "| $C_m$ (specific) | ? | ? | ? |\n"
            "| $R_m$ (specific) | ? | ? | ? |\n"
            "| $\\tau_m$ | (조합) | (조합) | ? |\n"
            "| 입력 $I_{inj}$ | ? | ? | ? |\n"
            "| $V_{rest}$ | ? | ? | ? |"
        ),
        "answer_md": (
            "| 회로 element | 신경막의 대응 분자/구조 | 결정 요인 (측정) | 전형적 값 |\n"
            "|---|---|---|---|\n"
            "| **$C_m$** (specific) | **lipid bilayer 의 hydrophobic core** (3–4 nm, 절연체) | 평행판 capacitor 공식 $C = \\varepsilon A / d$; 측정은 charge/voltage 비율 (impedance 분석) | **≈ 1 μF/cm²** — 거의 모든 세포에서 *상수*, bilayer 두께가 보존되기 때문 |\n"
            "| **$R_m$** (specific) | **휴지 상태에서 *열린* ion channel 들의 conductance 합산의 역수** (주로 K leak channels, K2P 채널) | 작은 step current에 대한 voltage 변화로 측정 (slope of V-I in subthreshold) | $1\\,\\text{M}\\Omega \\cdot \\text{cm}^2 \\sim 1\\,\\text{G}\\Omega \\cdot \\text{cm}^2$ — 세포마다 **변동 큼** (10×–1000×). 채널 발현이 \"활성도\" 를 정함 |\n"
            "| **$\\tau_m = R_m C_m$** | (위 두 양의 곱) | $R_m$ 측정 × $C_m$ 측정, 또는 직접 step current에 대한 e-folding time | **10–100 ms** — $C_m$ 가 거의 상수이므로 $\\tau_m$ 의 변화는 $R_m$ 의 변화에 따른다 |\n"
            "| **$I_{inj}$** | 외부 자극: pipette 전류 주입, 시냅스 입력 ( PSPs), 광유전학 channelrhodopsin 등 | 패치-clamp amplifier, 자연 입력은 시냅스 conductance 변화 | $\\sim$ 10 pA – 수 nA |\n"
            "| **$V_{rest}$** | 모든 *열린* ion channel의 평형 전위들의 *가중 평균* (GHK 방정식). K leak이 dominant 이므로 $V_{rest} \\approx E_K$ | $V_{rest}$ 직접 측정 (silent neuron, current-clamp at zero) | $-65 \\sim -80$ mV |"
        ),
        "rationale_md": (
            "**핵심 통찰**: $C_m$ 은 거의 *불변*하지만 $R_m$ 은 세포마다 *극단적으로 다름*. 따라서 **$\\tau_m$ 의 차이는 본질적으로 ion channel 분포의 차이**. 신경계 다양성의 절반 이상이 이 한 변수에 인코딩됨.\n\n"
            "**흔한 오개념**: $V_{rest}$ 가 \"고유 상수\" 라고 생각하는 것. 실제로는 *능동적으로 유지되는 동적 평형* — Na/K ATPase 가 농도 기울기를 유지하고, K leak 채널이 그 기울기를 막전위로 \"읽어내는\" 결과. ATP 공급이 끊기면 $V_{rest}$ 가 0을 향해 무너진다 (ischemic depolarization).\n\n"
            "**연결**: HH model 은 이 표에서 $R_m$ 만 변경: 더 이상 *상수* 가 아니라 *전압-시간 의존 함수*. $C_m, V_{rest}, I_{inj}$ 는 그대로. 따라서 HH 의 \"비선형성\" 은 단 한 element 의 거동 변화에서 나온다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 22,
                             "secondary_lecture": "L3", "secondary_page": 26,
                             "primary": "Cole & Curtis 1936; Hodgkin & Huxley 1939"},
        "priority_score": 0.98,
        "info_density": 0.96,
    },
]


def insert_cards(items):
    conn = acquire()
    try:
        with conn.cursor() as cur:
            ids = []
            for it in items:
                # Skip if same (topic, card_type, mastery_target) already exists
                cur.execute("""
                    SELECT id FROM question_bank
                    WHERE topic = %s AND card_type = %s AND mastery_target = %s
                    LIMIT 1
                """, (it["topic"], it["card_type"], it.get("mastery_target")))
                if cur.fetchone():
                    print(f"  skip dup: {it['topic']}/{it['card_type']}/{it.get('mastery_target')}")
                    continue

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
                ids.append(cur.fetchone()[0])
            for bid in ids:
                cur.execute("""
                    INSERT INTO srs_cards (user_id, bank_item_id, state)
                    VALUES (1,%s,'New')
                    ON CONFLICT (user_id, bank_item_id) DO NOTHING
                """, (bid,))
        conn.commit()
        return ids
    finally:
        release(conn)


if __name__ == "__main__":
    ids = insert_cards(SEEDS)
    print(f"\ninserted {len(ids)} foundation cards: ids {ids}")
    for it in SEEDS:
        print(f"  [foundations / {it['card_type']:>7s} / d={it['difficulty']}]  {it['mastery_target']}")
