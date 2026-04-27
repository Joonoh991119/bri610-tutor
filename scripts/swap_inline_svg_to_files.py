#!/usr/bin/env python3
"""
swap_inline_svg_to_files.py — replace inline SVG <figure> blocks in foundation
cards with <img src="/figures/...svg"> references to the publication-quality
standalone SVGs in frontend/public/figures/.

Why: inline SVG bloats card prompt_md by ~6-8 KB each and is harder to maintain.
External file references stay crisp at any zoom (still SVG, browser-native),
and the Markdown renderer (rehype-raw + react-markdown) handles <img> natively.
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))
from db_pool import acquire, release  # noqa: E402


# Each entry: (mastery_target, figure-file-name, alt-text, caption-md)
FIGURE_REPLACEMENTS = [
    ("capacitance_definition", "bilayer_capacitor.svg",
     "Phospholipid bilayer as parallel-plate capacitor",
     "Fig 1. Phospholipid bilayer separates intra/extracellular charge — geometrically a parallel-plate capacitor. The 3–4 nm thickness sets the very high specific capacitance C_m ≈ 1 μF/cm², universal across animal cell types."),
    ("ohms_law_membrane", "ohmic_iv.svg",
     "Ohmic ionic current I-V relation",
     "Fig 4. Ohmic ionic current. Open ion channels give a linear I-V relation with slope equal to channel conductance g_X. Current vanishes when V = E_X (the ion's reversal potential, set by Nernst). The driving force V − E_X is the deviation from equilibrium that pushes ions through the open channel."),
    ("rc_circuit_membrane", "membrane_rc_circuit.svg",
     "Equivalent-circuit diagram of single-compartment passive membrane",
     "Fig 2. Single-compartment passive membrane as a parallel RC circuit. Capacitive branch stores charge across the bilayer; resistive branch carries leakage through open ion channels at rest. Injected current I_inj is split between the two branches according to KCL."),
    ("rc_charging_curve", "rc_charging_curve.svg",
     "RC charging curve — passive membrane response to step current",
     "Fig 3. Capacitor-charging curve solving τ_m dV/dt = -(V - V_rest) + R_m I_inj with V(0) = V_rest. At t = 0⁺ the slope is I_inj / C_m (capacitor takes all the current; leak hasn't engaged). At t = τ_m the response has covered 63% of the gap to V_∞. As t → ∞ leak balances injection."),
]


def swap():
    conn = acquire()
    swapped = 0
    try:
        with conn.cursor() as cur:
            for mt, fname, alt, caption in FIGURE_REPLACEMENTS:
                cur.execute("""
                    SELECT id, prompt_md FROM question_bank
                    WHERE mastery_target = %s AND topic = 'foundations'
                """, (mt,))
                row = cur.fetchone()
                if not row:
                    print(f"  no card for mastery_target={mt}; skipping")
                    continue
                cid, body = row

                # Replace ALL inline <figure>...</figure> blocks with the external img reference.
                # The block is multiline; use re.DOTALL.
                new_block = (
                    f'<figure>\n'
                    f'<img src="/figures/{fname}" alt="{alt}" '
                    f'style="max-width:100%;height:auto;display:block;margin:0 auto;background:#ffffff;border-radius:6px;border:1px solid var(--color-border-soft);" />\n'
                    f'<figcaption>{caption}</figcaption>\n'
                    f'</figure>'
                )
                new_body = re.sub(
                    r'<figure>\s*<svg[^>]*>.*?</svg>\s*<figcaption>.*?</figcaption>\s*</figure>',
                    new_block, body, count=1, flags=re.DOTALL,
                )
                if new_body == body:
                    print(f"  card {cid} ({mt}): no <figure>...</figure> block found")
                    continue

                cur.execute("UPDATE question_bank SET prompt_md = %s WHERE id = %s", (new_body, cid))
                swapped += 1
                print(f"  card {cid} ({mt}) → {fname}  (saved {len(body) - len(new_body)} chars)")
        conn.commit()
    finally:
        release(conn)
    return swapped


if __name__ == "__main__":
    n = swap()
    print(f"\nswapped {n} card(s) from inline SVG to external file references")
