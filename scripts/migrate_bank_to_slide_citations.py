#!/usr/bin/env python3
"""
migrate_bank_to_slide_citations.py — enforces slide-only mandate on existing bank.

For each item in question_bank whose source_citation.kind is 'textbook',
rewrite the primary citation to the corresponding slide page (hand-mapped
based on the lecture content), and demote the textbook reference to a
'secondary' field (kept for optional further reading in rationale).

Idempotent: safe to run multiple times.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))
from db_pool import acquire, release  # noqa: E402


# Mapping: (topic, card_type) → new slide citation
# Slide page numbers chosen to match the lecture's coverage of that topic.
REMAP: dict[tuple[str, str], dict] = {
    ("HH",           "recall"):       {"kind": "slide", "lecture": "L5", "page": 5,
                                        "primary": "Hodgkin & Huxley 1952 J Physiol 117:500"},
    ("HH",           "concept"):      {"kind": "slide", "lecture": "L5", "page": 20,
                                        "primary": "Hodgkin & Huxley 1952; Kuo & Bean 1994 Neuron 12:819"},
    ("HH",           "proof"):        {"kind": "slide", "lecture": "L5", "page": 25,
                                        "primary": "Hodgkin & Huxley 1952; Schoppa & Sigworth 1998 J Gen Physiol 111:271"},
    ("cable",        "recall"):       {"kind": "slide", "lecture": "L6", "page": 10,
                                        "primary": "Rall 1962 Biophys J 2:145"},
    ("cable",        "concept"):      {"kind": "slide", "lecture": "L6", "page": 20,
                                        "primary": "Rall 1962; Mainen & Sejnowski 1996 Nature 382:363"},
    ("cable",        "proof"):        {"kind": "slide", "lecture": "L6", "page": 25,
                                        "primary": "Tuckwell 1988 Theoretical Neurobiology Vol.1 Ch.4"},
    ("Nernst",       "concept"):      {"kind": "slide", "lecture": "L3", "page": 20,
                                        "primary": "Hille 2001 Ion Channels of Excitable Membranes 3rd ed Ch.14"},
    ("Nernst",       "proof"):        {"kind": "slide", "lecture": "L3", "page": 25,
                                        "primary": "Goldman 1943 J Gen Physiol 27:37"},
    ("model_types",  "proof"):        {"kind": "slide", "lecture": "L7", "page": 40,
                                        "primary": "Wilson & Cowan 1972 Biophys J 12:1; Brunel 2000 J Comput Neurosci 8:183"},
}


def migrate() -> int:
    conn = acquire()
    n = 0
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, topic, card_type, source_citation, rationale_md
                FROM question_bank
                WHERE source_citation->>'kind' = 'textbook'
            """)
            rows = cur.fetchall()
            print(f"found {len(rows)} textbook-primary items needing migration")

            for (item_id, topic, card_type, citation, rationale) in rows:
                key = (topic, card_type)
                new_cite = REMAP.get(key)
                if not new_cite:
                    print(f"  [{item_id}] {topic} {card_type}: NO REMAP — skipping")
                    continue

                # Move textbook citation into 'secondary' field
                new_cite_full = {
                    **new_cite,
                    "secondary_textbook": {
                        "kind": "textbook",
                        "book": citation.get("book"),
                        "ch":   citation.get("ch"),
                        "page": citation.get("page"),
                    }
                }

                # Append optional further-reading note to rationale if not already there
                marker = "**더 깊이 보고 싶다면**"
                if marker not in (rationale or ""):
                    book_ref = citation.get("book", "").replace("_", " & ")
                    ch = citation.get("ch")
                    pg = citation.get("page")
                    addition = (f"\n\n{marker}: {book_ref} Ch.{ch} p.{pg} (참고용)" if ch else "")
                    new_rationale = (rationale or "") + addition
                else:
                    new_rationale = rationale

                cur.execute("""
                    UPDATE question_bank
                    SET source_citation = %s::jsonb, rationale_md = %s
                    WHERE id = %s
                """, (json.dumps(new_cite_full, ensure_ascii=False), new_rationale, item_id))
                n += 1
                print(f"  [{item_id}] {topic} {card_type} → [Slide {new_cite['lecture']} p.{new_cite['page']}]")

        conn.commit()
    finally:
        release(conn)
    return n


def verify() -> None:
    conn = acquire()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT source_citation->>'kind' AS kind, COUNT(*)
                FROM question_bank
                GROUP BY 1 ORDER BY 1
            """)
            print("\nFinal citation kind distribution:")
            for kind, count in cur.fetchall():
                print(f"  {kind:>10}: {count}")
    finally:
        release(conn)


if __name__ == "__main__":
    n = migrate()
    print(f"\nMigrated {n} item(s) to slide-primary citation.")
    verify()
