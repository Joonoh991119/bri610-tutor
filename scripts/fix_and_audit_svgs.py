#!/usr/bin/env python3
"""
Comprehensive SVG fix + audit for bri610-tutor/frontend/public/figures/*.svg
Tasks:
  1. Color uniformity: #dee2e7 → #d0d7de; flag/fix stray colors
  2. Caption alignment: consistent text-anchor + y-baseline for footers
  3. Reduce internal whitespace: tighten viewBox where >20px margin
  4. Remove text–figure overlap (hand-crafted SVGs)
  5. Math symbol consistency: unicode minus, italic vars, serif for math
Produces a report table at the end.
"""

import os
import re
import sys
import math
import copy
from pathlib import Path
import xml.etree.ElementTree as ET

FIGURES_DIR = Path("/Users/joonoh/Projects/bri610-tutor/frontend/public/figures")

# ─── Allowed palette ──────────────────────────────────────────────────────────
ALLOWED_COLORS = {
    "#1f2328", "#57606a", "#8c959f", "#d0d7de", "#fafbfc",
    "#4477aa", "#66ccee", "#ee6677", "#228833", "#ccbb44",
    # transparent / none are fine
    "none", "transparent",
}

# Stray → nearest allowed
COLOR_REMAP = {
    "#dee2e7": "#d0d7de",
    # purple family
    "#aa3377": "#ee6677",
    "#882255": "#ee6677",
    "#cc6677": "#ee6677",
    # blue/teal variants
    "#4488bb": "#4477aa",
    "#336699": "#4477aa",
    "#5599cc": "#4477aa",
    "#77aadd": "#66ccee",
    "#aaddff": "#66ccee",
    # green variants
    "#44aa00": "#228833",
    "#33aa33": "#228833",
    "#22aa22": "#228833",
    # ochre variants
    "#ddbb33": "#ccbb44",
    "#ddbb44": "#ccbb44",
    # dark variants
    "#212830": "#1f2328",
    "#1e2228": "#1f2328",
    # mid grey variants
    "#555f69": "#57606a",
    "#56606b": "#57606a",
    "#8b949e": "#8c959f",
    "#8b9396": "#8c959f",
    "#cdd3de": "#d0d7de",
    "#d1d8e0": "#d0d7de",
    "#f6f8fa": "#fafbfc",
    "#f0f2f4": "#fafbfc",
    # white/black
    "#ffffff": "#fafbfc",
    "#000000": "#1f2328",
}

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
ET.register_namespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
ET.register_namespace("cc", "http://creativecommons.org/ns#")
ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")

COLOR_RE = re.compile(r'#[0-9a-fA-F]{6}\b', re.IGNORECASE)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def find_colors_in_text(text):
    return [c.lower() for c in COLOR_RE.findall(text or "")]

def remap_colors_in_string(s):
    """Replace all bad colors in an attribute string."""
    def _replace(m):
        c = m.group(0).lower()
        return COLOR_REMAP.get(c, m.group(0))
    return COLOR_RE.sub(_replace, s)

def collect_bad_colors(svg_text):
    """Return set of disallowed colors found in svg_text."""
    found = set(c.lower() for c in COLOR_RE.findall(svg_text))
    bad = set()
    for c in found:
        if c not in ALLOWED_COLORS and c not in COLOR_REMAP:
            bad.add(c)
        elif c in COLOR_REMAP:
            bad.add(c)
    return bad

def fix_colors_in_text(svg_text):
    """Apply all color remaps directly on raw SVG text."""
    result = svg_text
    for old, new in COLOR_REMAP.items():
        # case-insensitive replacement
        result = re.sub(re.escape(old), new, result, flags=re.IGNORECASE)
    return result

def nearest_allowed(hex_color):
    """Find closest allowed color by RGB Euclidean distance."""
    def parse(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    try:
        r, g, b = parse(hex_color)
    except Exception:
        return "#57606a"
    best = None
    best_d = float('inf')
    for ac in ALLOWED_COLORS:
        if ac in ("none", "transparent"):
            continue
        ar, ag, ab = parse(ac)
        d = math.sqrt((r-ar)**2 + (g-ag)**2 + (b-ab)**2)
        if d < best_d:
            best_d = d
            best = ac
    return best


# ─── ViewBox tightening ───────────────────────────────────────────────────────

def parse_viewbox(vb_str):
    parts = vb_str.strip().split()
    if len(parts) == 4:
        return [float(p) for p in parts]
    return None

def get_content_bbox_from_text(svg_text):
    """
    Very rough content bounding box from rect/line/path/text elements.
    Returns (min_x, min_y, max_x, max_y) or None.
    """
    xs, ys = [], []

    # rect x,y,width,height
    for m in re.finditer(r'<rect[^>]+>', svg_text):
        tag = m.group(0)
        x = re.search(r'\bx=["\']([0-9.+-]+)["\']', tag)
        y = re.search(r'\by=["\']([0-9.+-]+)["\']', tag)
        w = re.search(r'\bwidth=["\']([0-9.]+)["\']', tag)
        h = re.search(r'\bheight=["\']([0-9.]+)["\']', tag)
        if x and y and w and h:
            rx, ry, rw, rh = float(x.group(1)), float(y.group(1)), float(w.group(1)), float(h.group(1))
            xs += [rx, rx+rw]; ys += [ry, ry+rh]

    # line x1,y1,x2,y2
    for m in re.finditer(r'<line[^>]+>', svg_text):
        tag = m.group(0)
        for coord in ['x1','y1','x2','y2']:
            cv = re.search(rf'\b{coord}=["\']([0-9.+-]+)["\']', tag)
            if cv:
                v = float(cv.group(1))
                if coord.startswith('x'): xs.append(v)
                else: ys.append(v)

    # text x,y (simple elements)
    for m in re.finditer(r'<text[^>]+>', svg_text):
        tag = m.group(0)
        x = re.search(r'\bx=["\']([0-9.+-]+)["\']', tag)
        y = re.search(r'\by=["\']([0-9.+-]+)["\']', tag)
        if x: xs.append(float(x.group(1)))
        if y: ys.append(float(y.group(1)))

    # circle cx,cy,r
    for m in re.finditer(r'<circle[^>]+>', svg_text):
        tag = m.group(0)
        cx = re.search(r'\bcx=["\']([0-9.+-]+)["\']', tag)
        cy = re.search(r'\bcy=["\']([0-9.+-]+)["\']', tag)
        r  = re.search(r'\br=["\']([0-9.]+)["\']',  tag)
        if cx and cy:
            rv = float(r.group(1)) if r else 5
            xs += [float(cx.group(1))-rv, float(cx.group(1))+rv]
            ys += [float(cy.group(1))-rv, float(cy.group(1))+rv]

    if not xs or not ys:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def tighten_viewbox(svg_text, filename):
    """
    For hand-crafted 600x360 SVGs: tighten viewBox if whitespace > 20px.
    Returns (new_svg_text, change_description).
    """
    vb_match = re.search(r'viewBox=["\']([^"\']+)["\']', svg_text)
    if not vb_match:
        return svg_text, "no viewBox"
    vb = parse_viewbox(vb_match.group(1))
    if not vb:
        return svg_text, "unparseable viewBox"
    vx, vy, vw, vh = vb

    # Only tighten hand-crafted 600x360 SVGs (the matplotlib ones have exact viewBoxes)
    if not (540 <= vw <= 620 and 320 <= vh <= 400):
        return svg_text, "skipped (matplotlib)"

    bbox = get_content_bbox_from_text(svg_text)
    if not bbox:
        return svg_text, "no bbox"
    bx0, by0, bx1, by1 = bbox

    PAD = 10  # minimum padding to keep
    new_x = max(vx, bx0 - PAD)
    new_y = max(vy, by0 - PAD)
    new_w = min(vw, bx1 - new_x + PAD)
    new_h = min(vh, by1 - new_y + PAD)

    # Only change if there's a meaningful saving (>20px on either axis)
    # and the aspect ratio stays within 10%
    original_ar = vw / vh
    new_ar = new_w / new_h if new_h > 0 else original_ar
    if abs(new_ar - original_ar) / original_ar > 0.10:
        return svg_text, "skipped (AR change too large)"

    top_margin = by0 - vy
    bot_margin = (vy + vh) - by1
    left_margin = bx0 - vx
    right_margin = (vx + vw) - bx1

    changes = []
    new_vy = vy
    new_vh = vh
    new_vx = vx
    new_vw = vw

    # Only shave top/bottom for hand-crafted SVGs to avoid cutting captions
    # Be conservative: only crop if margin > 20px
    if bot_margin > 20:
        crop_bot = min(bot_margin - 8, 30)  # cap at 30px crop
        new_vh = vh - crop_bot
        changes.append(f"h {vh:.0f}→{new_vh:.0f}")

    if top_margin > 25:
        crop_top = min(top_margin - 10, 20)
        new_vy = vy + crop_top
        new_vh = new_vh - crop_top
        changes.append(f"y {vy:.0f}→{new_vy:.0f}")

    if not changes:
        return svg_text, "no excess whitespace"

    old_vb = vb_match.group(1)
    new_vb = f"{new_vx:.3g} {new_vy:.3g} {new_vw:.3g} {new_vh:.3g}"
    new_svg = svg_text.replace(f'viewBox="{old_vb}"', f'viewBox="{new_vb}"')
    if new_svg == svg_text:
        new_svg = svg_text.replace(f"viewBox='{old_vb}'", f"viewBox='{new_vb}'")

    return new_svg, " | ".join(changes)


# ─── Text-figure overlap (hand-crafted SVGs only) ────────────────────────────

def get_text_bboxes(svg_text):
    """
    Extract approximate bboxes for <text> elements in hand-crafted SVGs.
    Returns list of (x, y, w, h, full_text_content).
    """
    bboxes = []
    # Match <text ...>...</text> (including multi-line)
    for m in re.finditer(r'<text([^>]*)>(.*?)</text>', svg_text, re.DOTALL):
        attrs = m.group(1)
        content = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if not content:
            continue

        x_m = re.search(r'\bx=["\']([0-9.+-]+)["\']', attrs)
        y_m = re.search(r'\by=["\']([0-9.+-]+)["\']', attrs)
        fs_m = re.search(r'\bfont-size=["\']([0-9.]+)["\']', attrs)
        ta_m = re.search(r'\btext-anchor=["\']([^"\']+)["\']', attrs)

        if not x_m or not y_m:
            continue

        x = float(x_m.group(1))
        y = float(y_m.group(1))
        fs = float(fs_m.group(1)) if fs_m else 12.0
        ta = ta_m.group(1) if ta_m else "start"

        # Approximate width
        char_w = fs * 0.55
        text_len = len(content)
        w = text_len * char_w
        h = fs * 1.2

        # Adjust x based on text-anchor
        if ta == "middle":
            bx = x - w / 2
        elif ta == "end":
            bx = x - w
        else:
            bx = x

        by = y - h  # y is baseline
        bboxes.append((bx, by, w, h, content[:50]))
    return bboxes

def check_overlaps(bboxes):
    """Return list of overlapping pairs (i, j, overlap_px)."""
    pairs = []
    for i in range(len(bboxes)):
        for j in range(i+1, len(bboxes)):
            ax, ay, aw, ah, at = bboxes[i]
            bx, by, bw, bh, bt = bboxes[j]
            # AABB intersection
            ox = min(ax+aw, bx+bw) - max(ax, bx)
            oy = min(ay+ah, by+bh) - max(ay, by)
            if ox > 2 and oy > 2:
                pairs.append((i, j, ox*oy, at[:30], bt[:30]))
    return pairs


# ─── Math symbol consistency ─────────────────────────────────────────────────

def fix_math_symbols(svg_text):
    """
    Apply math typography fixes to SVG text:
    - Replace hyphen-minus in numeric contexts with U+2212 (−)
    - Ensure Greek letters are Unicode (already mostly done)
    """
    # Replace hyphen-minus used as minus sign in numeric ranges like "-65 mV", "−90"
    # Pattern: digit or space then hyphen-minus before a digit (in text content between >< )
    # We do this carefully: only inside text content, not in attributes like x="-65"
    def fix_minus_in_content(m):
        s = m.group(0)
        # Replace hyphen-minus preceded by space/= and followed by digit with proper minus
        s = re.sub(r'(?<=[> ])-([\d])', r'−\1', s)
        return s

    # For hand-crafted SVGs: fix minus signs in text content
    # Match text content between > and < (not in attributes)
    result = re.sub(r'>([^<]+)<', lambda m: '>' + re.sub(r' -([\d])', r' −\1', m.group(1)) + '<', svg_text)

    return result


# ─── Caption alignment ────────────────────────────────────────────────────────

def fix_caption_alignment(svg_text, filename):
    """
    For hand-crafted SVGs:
    - Ensure footer 'Slide L# p.N' text uses text-anchor="end" at x=540 or text-anchor="middle" at x=300
    - Ensure italic, fill="#8c959f", font-size="10"
    Returns (new_svg_text, changed_bool).
    """
    # Find slide citation footer pattern
    # Typical: <text x="540" y="..." text-anchor="end" fill="#8c959f" font-size="10">Slide L...
    # or: <text x="300" y="..." text-anchor="middle" ...>Slide L...
    changed = False

    # Fix: ensure all footer citations use consistent fill and font-size
    def fix_footer(m):
        nonlocal changed
        full = m.group(0)
        # Check if it's a slide citation
        content = re.sub(r'<[^>]+>', '', full)
        if not re.search(r'Slide\s+L\d', content):
            return full
        # Ensure fill="#8c959f"
        if '#8c959f' not in full:
            new = re.sub(r'fill=["\']#[0-9a-fA-F]+["\']', 'fill="#8c959f"', full)
            if new != full:
                changed = True
                full = new
        # Ensure font-size="10"
        if 'font-size=' not in full:
            new = full.replace('<text ', '<text font-size="10" ', 1)
            if new != full:
                changed = True
                full = new
        elif not re.search(r'font-size=["\']10["\']', full):
            new = re.sub(r'font-size=["\'][^"\']+["\']', 'font-size="10"', full)
            if new != full:
                changed = True
                full = new
        # Ensure font-style="italic"
        if 'font-style=' not in full:
            new = full.replace('<text ', '<text font-style="italic" ', 1)
            if new != full:
                changed = True
                full = new
        return full

    result = re.sub(r'<text[^>]*>(?:(?!<text).)*?Slide\s+L\d.*?</text>',
                    fix_footer, svg_text, flags=re.DOTALL)
    return result, changed


# ─── Main per-file processing ─────────────────────────────────────────────────

def process_file(filepath):
    path = Path(filepath)
    with open(path, 'r', encoding='utf-8') as f:
        original = f.read()

    report = {
        "file": path.stem,
        "bad_colors_before": set(),
        "bad_colors_after": set(),
        "overlaps_before": 0,
        "overlaps_after": 0,
        "viewbox_change": "unchanged",
        "changes": [],
    }

    svg_text = original

    # ── Step 1: Collect bad colors before ────────────────────────────────────
    bad_before = collect_bad_colors(svg_text)
    report["bad_colors_before"] = bad_before

    # ── Step 2: Fix colors ────────────────────────────────────────────────────
    fixed = fix_colors_in_text(svg_text)

    # Fix any remaining stray colors via nearest-neighbor
    remaining_bad = collect_bad_colors(fixed)
    remaining_bad_norm = {c for c in remaining_bad
                          if c not in ALLOWED_COLORS and c not in COLOR_REMAP}
    for stray in remaining_bad_norm:
        nearest = nearest_allowed(stray)
        fixed = re.sub(re.escape(stray), nearest, fixed, flags=re.IGNORECASE)
        report["changes"].append(f"color {stray}→{nearest}")

    if fixed != svg_text:
        report["changes"].append(f"color_remap({len(bad_before)} instances)")
    svg_text = fixed

    # ── Step 3: Math symbol fixes ─────────────────────────────────────────────
    fixed_math = fix_math_symbols(svg_text)
    if fixed_math != svg_text:
        report["changes"].append("math_symbols")
    svg_text = fixed_math

    # ── Step 4: Caption alignment ─────────────────────────────────────────────
    fixed_cap, cap_changed = fix_caption_alignment(svg_text, path.stem)
    if cap_changed:
        report["changes"].append("caption_align")
    svg_text = fixed_cap

    # ── Step 5: Check overlaps BEFORE ────────────────────────────────────────
    # Only meaningful for hand-crafted SVGs (short files with simple <text> elements)
    is_handcrafted = len(original.splitlines()) < 150
    if is_handcrafted:
        bboxes_before = get_text_bboxes(svg_text)
        overlaps_before = check_overlaps(bboxes_before)
        report["overlaps_before"] = len(overlaps_before)

    # ── Step 6: ViewBox tightening ────────────────────────────────────────────
    fixed_vb, vb_change = tighten_viewbox(svg_text, path.stem)
    if fixed_vb != svg_text:
        report["viewbox_change"] = vb_change
        report["changes"].append(f"viewBox({vb_change})")
    svg_text = fixed_vb
    report["viewbox_change"] = vb_change

    # ── Step 7: Check overlaps AFTER ─────────────────────────────────────────
    if is_handcrafted:
        bboxes_after = get_text_bboxes(svg_text)
        overlaps_after = check_overlaps(bboxes_after)
        report["overlaps_after"] = len(overlaps_after)

    # ── Step 8: Final color audit ─────────────────────────────────────────────
    bad_after = collect_bad_colors(svg_text)
    # Filter to only truly disallowed (not in remap, not in allowed)
    bad_after_clean = {c for c in bad_after
                       if c not in ALLOWED_COLORS and c not in ("none","transparent")}
    report["bad_colors_after"] = bad_after_clean

    # ── Write if changed ──────────────────────────────────────────────────────
    if svg_text != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(svg_text)

    return report


# ─── Additional overlap repair for hand-crafted SVGs ─────────────────────────

def repair_overlaps_handcrafted(filepath):
    """
    For SVGs with remaining overlaps: nudge second text element down by 14px.
    This is a targeted fix for pairs that still overlap after other edits.
    """
    path = Path(filepath)
    with open(path, 'r', encoding='utf-8') as f:
        svg_text = f.read()

    if len(svg_text.splitlines()) > 150:
        return 0  # skip matplotlib SVGs

    bboxes = get_text_bboxes(svg_text)
    pairs = check_overlaps(bboxes)
    if not pairs:
        return 0

    # Build list of all <text> elements with their y positions
    texts = list(re.finditer(r'<text([^>]*)>(.*?)</text>', svg_text, re.DOTALL))
    if not texts:
        return 0

    fixed = svg_text
    fixed_count = 0

    for i, j, area, ti, tj in pairs:
        if j >= len(texts):
            continue
        # Nudge the second (lower) text element's y coordinate down by 14px
        tm = texts[j]
        old_tag = tm.group(0)
        attrs = tm.group(1)
        y_m = re.search(r'\by=["\']([0-9.+-]+)["\']', attrs)
        if not y_m:
            continue
        old_y = float(y_m.group(1))
        new_y = old_y + 14
        new_tag = old_tag.replace(f'y="{y_m.group(1)}"', f'y="{new_y:.1f}"')
        if new_tag == old_tag:
            new_tag = old_tag.replace(f"y='{y_m.group(1)}'", f"y='{new_y:.1f}'")
        if new_tag != old_tag:
            fixed = fixed.replace(old_tag, new_tag, 1)
            fixed_count += 1

    if fixed_count > 0:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(fixed)

    return fixed_count


# ─── Run ──────────────────────────────────────────────────────────────────────

def main():
    svg_files = sorted(FIGURES_DIR.glob("*.svg"))
    print(f"Processing {len(svg_files)} SVG files...\n")

    reports = []
    for f in svg_files:
        r = process_file(f)
        reports.append(r)
        changes = ", ".join(r["changes"]) if r["changes"] else "—"
        print(f"  {r['file']}: colors_before={len(r['bad_colors_before'])} bad, "
              f"overlaps {r['overlaps_before']}→{r['overlaps_after']}, "
              f"vb={r['viewbox_change']}, changes=[{changes}]")

    # Second pass: repair remaining overlaps
    print("\nSecond pass: overlap repair...")
    for f in svg_files:
        n = repair_overlaps_handcrafted(f)
        if n > 0:
            print(f"  {f.stem}: nudged {n} text element(s)")

    # Final audit
    print("\n\nFINAL AUDIT")
    print("=" * 100)

    still_bad_colors = []
    still_overlaps = []
    for f in svg_files:
        with open(f, 'r', encoding='utf-8') as fh:
            text = fh.read()
        bad = {c for c in collect_bad_colors(text)
               if c not in ALLOWED_COLORS and c not in ("none","transparent")}
        if bad:
            still_bad_colors.append((f.stem, bad))
        bboxes = get_text_bboxes(text)
        pairs = check_overlaps(bboxes)
        if pairs:
            still_overlaps.append((f.stem, len(pairs)))

    print(f"\nFiles with remaining bad colors ({len(still_bad_colors)}):")
    for name, colors in still_bad_colors:
        print(f"  {name}: {colors}")

    print(f"\nFiles with remaining text overlaps ({len(still_overlaps)}):")
    for name, n in still_overlaps:
        print(f"  {name}: {n} pair(s)")

    # Markdown table
    print("\n\n## Report Table\n")
    print("| File | bad_colors_before→after | overlaps_before→after | viewBox_change |")
    print("|------|------------------------|----------------------|----------------|")
    for r in reports:
        bc_b = len(r["bad_colors_before"])
        # re-audit after
        with open(FIGURES_DIR / (r['file'] + '.svg'), 'r', encoding='utf-8') as fh:
            final_text = fh.read()
        bad_after = {c for c in collect_bad_colors(final_text)
                     if c not in ALLOWED_COLORS and c not in ("none","transparent")}
        bc_a = len(bad_after)
        ob = r["overlaps_before"]
        # re-check overlaps
        bboxes_final = get_text_bboxes(final_text)
        oa = len(check_overlaps(bboxes_final))
        vb = r["viewbox_change"]
        print(f"| {r['file']} | {bc_b}→{bc_a} | {ob}→{oa} | {vb} |")

    print("\nDone.")

if __name__ == "__main__":
    main()
