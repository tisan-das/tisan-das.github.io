#!/usr/bin/env python
"""Phase 7: convert callouts to Chirpy prompts; wrap problem-set solutions in <details>."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"

# Single-line callouts → prompt blocks
# Groups: prefix kind, rest of line
SINGLE = re.compile(
    r"^(?P<pre>(?:\*\*)?(?:Note|Warning|Important|Tip)(?:\*\*)?|"
    r"NB|It's worth noting that|It's also worth noting that|"
    r"It is worth noting that|Worth noting that)"
    r"(?P<sep>\s*(?::|\s+)\s*|\s+)"
    r"(?P<body>\S.*)$"
)

PROMPT = {
    "note": "info",
    "nb": "info",
    "important": "warning",
    "warning": "warning",
    "tip": "tip",
    "it's worth noting that": "tip",
    "it's also worth noting that": "tip",
    "it is worth noting that": "tip",
    "worth noting that": "tip",
}

PROBLEM_SETS = [
    "2024-08-17-Binary-Tree-Algo-Part-1.md",
    "2024-09-22-Binary-Tree-Algo-Part-2.md",
    "2024-09-22-Stack-Problems-Part-1.md",
    "2024-11-24-Union-Find-Problem-Set-Part-1.md",
    "2025-01-19-Binary-Search-Problem-Set-Part-1.md",
    "2025-03-09-Binary-Search-Problem-Set-Part-2.md",
    "2025-03-16-BFS-Problem-Set-Part-1.md",
    "2025-04-01-BFS-Problem-Set-Part-2.md",
    "2025-07-14-Game-Theory-Problem-Set.md",
    "2025-07-14-Sliding-Window-Problem-Set.md",
]


def normalize_kind(pre: str) -> str:
    p = pre.replace("*", "").strip().lower()
    if p.startswith("note"):
        return "note"
    return p


def to_prompt(kind: str, body: str) -> list[str]:
    cls = PROMPT.get(kind, "info")
    # Strip redundant leading "that" leftovers handled by regex body
    body = body.strip()
    # Chirpy: blockquote + attribute list
    return [f"> {body}", f"{{: .prompt-{cls} }}", ""]


def convert_callouts(text: str) -> tuple[str, int]:
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = 0
    in_fence = False
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            i += 1
            continue
        if in_fence:
            out.append(line)
            i += 1
            continue

        # Multi-line "Notes:" / "NB:" followed by list items
        if re.match(r"^(Notes|NB):\s*$", line.strip()):
            items: list[str] = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if re.match(r"^(\d+\.|-|\*)\s+\S", nxt.strip()) or (
                    nxt.startswith(" ") and nxt.strip()
                ):
                    items.append(nxt.strip())
                    j += 1
                    continue
                if nxt.strip() == "" and items:
                    # allow one blank inside list? stop on blank
                    break
                break
            if items:
                out.append("> **Note**")
                for it in items:
                    # normalize bullets to markdown list inside blockquote
                    it2 = re.sub(r"^\d+\.\s*", "", it)
                    it2 = re.sub(r"^[-*]\s*", "", it2)
                    out.append(f"> - {it2}")
                out.append("{: .prompt-info }")
                out.append("")
                n += 1
                i = j
                continue

        m = SINGLE.match(line.strip())
        if m:
            kind = normalize_kind(m.group("pre"))
            body = m.group("body").strip()
            # Special case: "Note: ... variable:" followed by a fence — keep as prompt for the sentence only
            if kind in PROMPT or kind == "note":
                # Avoid converting if already a prompt attribute nearby
                if i + 1 < len(lines) and "prompt-" in lines[i + 1]:
                    out.append(line)
                    i += 1
                    continue
                out.extend(to_prompt(kind if kind != "note" else "note", body))
                n += 1
                i += 1
                continue

        # **Note**: body  (already covered by SINGLE with optional **)
        out.append(line)
        i += 1

    return "\n".join(out), n


def wrap_solutions(text: str) -> tuple[str, int]:
    """Wrap fenced code blocks under ###/#### problem headings (prose may sit in between)."""
    if '<details class="solution"' in text and text.count('<details class="solution"') > 3:
        # already largely converted — still wrap any remaining bare fences after headings
        pass

    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = 0
    in_problem = False  # true after a ###/#### until next same-or-higher heading at file level

    while i < len(lines):
        line = lines[i]

        if re.match(r"^#{3,4}\s+\S", line):
            in_problem = True
            out.append(line)
            i += 1
            continue

        # leaving problem region on thematic break / references heading
        if re.match(r"^#{1,2}\s+", line):
            in_problem = False

        # skip fences already inside details (detect open details without close)
        if in_problem and line.startswith("```"):
            # don't wrap if previous non-empty emitted line is summary or details or inside
            prev = next((x for x in reversed(out) if x.strip()), "")
            if "</details>" in prev or prev.startswith("```"):
                pass
            # if we're already inside an open details block in out, skip
            open_d = sum(1 for x in out if '<details class="solution"' in x)
            close_d = sum(1 for x in out if "</details>" in x)
            if open_d > close_d:
                out.append(line)
                i += 1
                continue

            fence_lang = line.strip()
            k = i + 1
            body_lines = []
            while k < len(lines) and not (
                lines[k].startswith("```") and lines[k].strip() == "```"
            ):
                body_lines.append(lines[k])
                k += 1
            if k < len(lines) and lines[k].strip() == "```":
                out.append('<details class="solution" markdown="1">')
                out.append("<summary>Show solution</summary>")
                out.append("")
                out.append(fence_lang)
                out.extend(body_lines)
                out.append("```")
                out.append("")
                out.append("</details>")
                n += 1
                i = k + 1
                continue

        out.append(line)
        i += 1
    return "\n".join(out), n


def main():
    callout_total = sol_total = 0

    for post in sorted(POSTS.glob("*.md")):
        raw = post.read_text(encoding="utf-8")
        m = re.match(r"^(---\n.*?\n---\n)(.*)$", raw, re.S)
        if not m:
            continue
        head, body = m.group(1), m.group(2)
        body2, c = convert_callouts(body)
        callout_total += c

        if post.name in PROBLEM_SETS:
            body2, s = wrap_solutions(body2)
            sol_total += s

        if body2 != body:
            post.write_text(head + body2, encoding="utf-8", newline="\n")

    print(f"callouts converted: {callout_total}")
    print(f"solutions wrapped: {sol_total}")


if __name__ == "__main__":
    main()
