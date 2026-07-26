#!/usr/bin/env python
"""Create a new blog post with the correct front matter and conventions.

Usage:
    python tools/new_post.py "My Post Title" \
        --categories "Distributed Systems,Consensus" \
        --tags raft,consensus \
        [--series "Distributed Systems Papers"] \
        [--image /images/<topic>/<file>.png]

Conventions (see README.md):
  * Images live under images/<topic>/ and are referenced absolutely:
    ![Describe what the image shows](/images/<topic>/<file>.png)
  * Alt text is required for every image (accessibility + SEO).
  * If the post belongs to a series, pass --series and keep the
    {% include series-nav.html %} line right after the intro paragraph.
"""
import argparse
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)


def main() -> None:
    ap = argparse.ArgumentParser(description="Scaffold a new post")
    ap.add_argument("title", help="Post title")
    ap.add_argument("-c", "--categories", required=True,
                    help="Comma-separated, e.g. \"Distributed Systems,Consensus\"")
    ap.add_argument("-t", "--tags", required=True, help="Comma-separated, e.g. raft,consensus")
    ap.add_argument("-s", "--series", default=None, help="Series name (must match other parts exactly)")
    ap.add_argument("-i", "--image", default=None, help="Social preview image path, e.g. /images/topic/x.png")
    args = ap.parse_args()

    now = datetime.now().astimezone()
    date_file = now.strftime("%Y-%m-%d")
    date_fm = now.strftime("%Y-%m-%d %H:%M:%S %z")
    slug = slugify(args.title)
    path = ROOT / "_posts" / f"{date_file}-{slug}.md"
    if path.exists():
        raise SystemExit(f"error: {path} already exists")

    cats = ", ".join(f'"{c.strip()}"' for c in args.categories.split(","))
    tags = ", ".join(t.strip() for t in args.tags.split(","))

    fm = ["---", f"title: {args.title}", f"date: {date_fm}"]
    if args.series:
        fm.append(f'series: "{args.series}"')
    fm.append(f"categories: [{cats}]")
    fm.append(f"tags: [{tags}]")
    if args.image:
        img = args.image
        msys = re.match(r"^[A-Za-z]:/Program Files/Git(/.*)$", img)  # Git Bash path mangling
        if msys:
            img = msys.group(1)
        if not img.startswith("/"):
            img = "/" + img
        fm.append(f"image: {img}")
    fm.append("---")

    body = ["", "Write your introduction here — this first paragraph becomes the excerpt on the home page.", ""]
    if args.series:
        body += ["{% include series-nav.html %}", ""]
    body += [
        "### First section",
        "",
        "Content goes here.",
        "",
        "![Describe what the image shows](/images/<topic>/<file>.png)",
        "",
        "```python",
        "print(\"hello\")  # code with line numbers + copy button",
        "```",
        "{: file='example.py' }",
        "",
        "<!-- Optional front matter for this post:  math: true | mermaid: true  -->",
        "",
    ]

    path.write_text("\n".join(fm + body), encoding="utf-8", newline="\n")
    print(f"created {path.relative_to(ROOT)}")
    print("tips: {: file='name' } after a fence adds a filename label; use ```diff for before/after;")
    print("next: add images under images/<topic>/, write alt text for every image,")
    print("then preview with: bundle exec jekyll serve --livereload")


if __name__ == "__main__":
    main()
