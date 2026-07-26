#!/usr/bin/env python
"""Phase 6: image audit, dark variants, captions, width classes, compression, series cards."""
from __future__ import annotations

import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"
IMAGES = ROOT / "images"
AUDIT = ROOT / "tools" / "_img_audit.json"
SERIES_DIR = ROOT / "assets" / "img" / "series"
DARK_SUFFIX = "-dark"  # foo.png -> foo-dark.png

IMG_MD = re.compile(
    r"^(!\[([^\]]*)\]\((/images/[^)\s]+)([^)]*)\))(\s*\{:[^}]*\})?\s*$"
)
CAPTION_RE = re.compile(r"^_[^_].*_$")
FENCE_RE = re.compile(r"^```")


# ---------------------------------------------------------------------------
# 1. Audit
# ---------------------------------------------------------------------------

def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def audit_image(path: Path) -> dict:
    rel = path.relative_to(ROOT).as_posix()
    try:
        im = Image.open(path)
        im.load()
    except Exception as e:
        return {"path": rel, "error": str(e)}

    w, h = im.size
    mode = im.mode
    has_alpha = mode in ("RGBA", "LA") or (mode == "P" and "transparency" in im.info)
    rgba = im.convert("RGBA")

    pts = [
        (2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3),
        (w // 2, 2), (w // 2, h - 3), (2, h // 2), (w - 3, h // 2),
    ]
    corners = [rgba.getpixel(pt) for pt in pts if 0 <= pt[0] < w and 0 <= pt[1] < h]
    avg_corner = sum(lum(c) for c in corners) / max(1, len(corners))
    avg_alpha = sum(c[3] for c in corners) / max(1, len(corners))

    step = max(1, min(w, h) // 40)
    dark_opaque = light_opaque = colored = transparent = total = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b, a = rgba.getpixel((x, y))
            total += 1
            if a < 30:
                transparent += 1
                continue
            L = lum((r, g, b))
            sat = max(r, g, b) - min(r, g, b)
            if sat > 30:
                colored += 1
            elif L < 50:
                dark_opaque += 1
            elif L > 200:
                light_opaque += 1

    white_bg = avg_corner > 230 and avg_alpha > 200
    transparent_dark = (
        (transparent / max(1, total) > 0.12)
        and dark_opaque > light_opaque
        and avg_corner < 100
    )

    risk = None
    if white_bg and (dark_opaque + colored) > max(1, light_opaque) * 0.25:
        risk = "white_bg_diagram"
    elif transparent_dark or (
        has_alpha and dark_opaque > total * 0.04 and light_opaque < dark_opaque
    ):
        risk = "dark_on_transparent"
    elif white_bg:
        risk = "white_bg_soft"

    return {
        "path": rel,
        "w": w,
        "h": h,
        "bytes": path.stat().st_size,
        "white_bg": white_bg,
        "risk": risk,
        "has_alpha": has_alpha,
    }


def run_audit() -> list[dict]:
    results = []
    for p in sorted(IMAGES.rglob("*")):
        if p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            continue
        results.append(audit_image(p))
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    ctr = Counter(r.get("risk") for r in results)
    print("audit:", dict(ctr), "total", len(results))
    print(
        "wide>=1400:", sum(1 for r in results if r.get("w", 0) >= 1400),
        "very_wide>=2000:", sum(1 for r in results if r.get("w", 0) >= 2000),
        "png_mb:", round(sum(r.get("bytes", 0) for r in results if r["path"].endswith(".png")) / 1e6, 2),
    )
    return results


# ---------------------------------------------------------------------------
# 2. Dark variants
# ---------------------------------------------------------------------------

DARK_BG = (30, 30, 46, 255)       # near Chirpy dark card
LIGHT_FG = (220, 220, 230, 255)


def make_dark_variant(src: Path, dest: Path) -> bool:
    """Create a dark-mode friendly version of a diagram (numpy bulk ops)."""
    im = Image.open(src).convert("RGBA")
    arr = np.asarray(im).astype(np.uint16)
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    L = (0.2126 * r + 0.7152 * g + 0.0722 * b)
    sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)

    opaque = a >= 30
    sample = opaque[:: max(1, opaque.shape[0] // 50), :: max(1, opaque.shape[1] // 50)]
    sat_s = sat[:: max(1, sat.shape[0] // 50), :: max(1, sat.shape[1] // 50)]
    # rough mono vs color on opaque samples
    op_s = opaque[:: max(1, opaque.shape[0] // 50), :: max(1, opaque.shape[1] // 50)]
    colorish = int(np.sum(op_s & (sat_s > 35)))
    mono = int(np.sum(op_s & (sat_s <= 35)))
    mostly_mono = mono >= colorish * 1.5

    out = arr.copy()
    # transparent → dark bg
    tmask = a < 10
    out[tmask, 0] = DARK_BG[0]
    out[tmask, 1] = DARK_BG[1]
    out[tmask, 2] = DARK_BG[2]
    out[tmask, 3] = 255

    # white / near-white background → dark canvas
    wmask = (~tmask) & (L > 235) & (sat < 25)
    out[wmask, 0] = DARK_BG[0]
    out[wmask, 1] = DARK_BG[1]
    out[wmask, 2] = DARK_BG[2]

    if mostly_mono:
        # black ink → light ink
        bmask = (~tmask) & (~wmask) & (L < 60) & (sat < 30)
        out[bmask, 0] = LIGHT_FG[0]
        out[bmask, 1] = LIGHT_FG[1]
        out[bmask, 2] = LIGHT_FG[2]
        # gray ink → inverted gray
        gmask = (~tmask) & (~wmask) & (~bmask) & (sat < 30)
        inv = np.clip(255 - L, 40, 230).astype(np.uint16)
        out[gmask, 0] = inv[gmask]
        out[gmask, 1] = inv[gmask]
        out[gmask, 2] = inv[gmask]
    else:
        # colored: brighten very dark pixels slightly
        dmask = (~tmask) & (~wmask) & (L < 40)
        out[dmask, 0] = np.minimum(255, (out[dmask, 0] * 1.6)).astype(np.uint16)
        out[dmask, 1] = np.minimum(255, (out[dmask, 1] * 1.6)).astype(np.uint16)
        out[dmask, 2] = np.minimum(255, (out[dmask, 2] * 1.6)).astype(np.uint16)

    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out.astype(np.uint8), "RGBA").save(
        dest, format="PNG", optimize=True, compress_level=9
    )
    return True


def dark_path_for(src_rel: str) -> str:
    """images/foo/bar.png -> images/foo/bar-dark.png"""
    p = Path(src_rel)
    return str(p.with_name(p.stem + DARK_SUFFIX + p.suffix)).replace("\\", "/")


def generate_dark_variants(audit: list[dict]) -> dict[str, str]:
    """risk path -> dark relative path. Only for white_bg_diagram + dark_on_transparent."""
    mapping = {}
    targets = [
        r for r in audit
        if r.get("risk") in ("white_bg_diagram", "dark_on_transparent", "white_bg_soft")
        and not r["path"].endswith(f"{DARK_SUFFIX}.png")
        and DARK_SUFFIX not in Path(r["path"]).stem
    ]
    print(f"generating dark variants for {len(targets)} images...")
    for i, r in enumerate(targets, 1):
        src = ROOT / r["path"]
        drel = dark_path_for(r["path"])
        dest = ROOT / drel
        if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime:
            mapping[r["path"]] = drel
            continue
        try:
            make_dark_variant(src, dest)
            mapping[r["path"]] = drel
        except Exception as e:
            print("  FAIL", r["path"], e)
        if i % 40 == 0:
            print(f"  ...{i}/{len(targets)}")
    print(f"dark variants ready: {len(mapping)}")
    return mapping


# ---------------------------------------------------------------------------
# 3–4. Rewrite post markdown: captions, width, light/dark pairs
# ---------------------------------------------------------------------------

def width_class(w: int | None) -> str:
    if not w:
        return ""
    if w >= 2000:
        return ".w-50"
    if w >= 1400:
        return ".w-75"
    if w >= 1000:
        return ".w-75"
    return ""


def process_posts(audit: list[dict], dark_map: dict[str, str]) -> None:
    """Idempotent-ish: strips prior Phase-6 captions/attrs on image lines, then rewrites."""
    by_path = {r["path"]: r for r in audit if "path" in r}
    stats = Counter()

    # Match image line with optional kramdown attr
    img_line = re.compile(
        r"^!\[([^\]]*)\]\((/images/[^)\s]+)([^)]*)\)(?:\s*\{:([^}]*)\})?\s*$"
    )

    for post in sorted(POSTS.glob("*.md")):
        text = post.read_text(encoding="utf-8")
        m = re.match(r"^(---\n.*?\n---\n)(.*)$", text, re.S)
        if not m:
            continue
        head, body = m.group(1), m.group(2)
        lines = body.split("\n")
        out: list[str] = []
        in_fence = False
        i = 0
        while i < len(lines):
            line = lines[i]
            if FENCE_RE.match(line.strip()):
                in_fence = not in_fence
                out.append(line)
                i += 1
                continue
            if in_fence:
                out.append(line)
                i += 1
                continue

            mm = img_line.match(line)
            if not mm:
                # drop orphan captions that sit alone after we rebuild (handled below)
                out.append(line)
                i += 1
                continue

            alt, path, _extra, attr_body = mm.group(1), mm.group(2), mm.group(3), mm.group(4)
            rel = path.lstrip("/")

            # Skip standalone dark-variant lines from a previous run — regenerated with pairs
            if DARK_SUFFIX in Path(rel).stem:
                # if previous line in out was the light twin, skip this dark line (will recreate)
                i += 1
                # also skip following caption if present
                if i < len(lines) and CAPTION_RE.match(lines[i].strip()):
                    i += 1
                continue

            meta = by_path.get(rel, {})
            # if missing (new dark not in audit), try without -dark
            w = meta.get("w")
            dark_rel = dark_map.get(rel)

            classes: list[str] = []
            wc = width_class(w)
            if wc:
                classes.append(wc)
                stats["width"] += 1

            # consume existing caption on next non-empty line (we'll rewrite)
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            existing_caption = None
            skip_to = i + 1
            if j < len(lines) and CAPTION_RE.match(lines[j].strip()):
                existing_caption = lines[j].strip().strip("_").strip()
                skip_to = j + 1
            # also skip a following dark-pair line from prior run
            if skip_to < len(lines):
                dm = img_line.match(lines[skip_to])
                if dm and DARK_SUFFIX in Path(dm.group(2).lstrip("/")).stem:
                    skip_to += 1
                    if skip_to < len(lines) and CAPTION_RE.match(lines[skip_to].strip()):
                        skip_to += 1

            if dark_rel:
                light_classes = classes + [".light"]
                dark_classes = classes + [".dark"]
                out.append(f"![{alt}]({path})" + "{: " + " ".join(light_classes) + " }")
                out.append(f"![{alt}](/{dark_rel})" + "{: " + " ".join(dark_classes) + " }")
                stats["dark_pair"] += 1
            else:
                if classes:
                    out.append(f"![{alt}]({path})" + "{: " + " ".join(classes) + " }")
                else:
                    out.append(f"![{alt}]({path})")

            caption = (alt or existing_caption or "").strip()
            skip_captions = {"", "image", "image info", "diagram", "img"}
            if caption.lower() not in skip_captions:
                out.append(f"_{caption}_")
                stats["caption"] += 1

            i = skip_to

        # drop consecutive duplicate blank lines lightly
        cleaned: list[str] = []
        for ln in out:
            if ln == "" and cleaned and cleaned[-1] == "":
                continue
            cleaned.append(ln)
        post.write_text(head + "\n".join(cleaned), encoding="utf-8", newline="\n")

    print("post rewrites:", dict(stats))


# ---------------------------------------------------------------------------
# 5. PNG compression (in-place, optimize)
# ---------------------------------------------------------------------------

def compress_pngs(audit: list[dict]) -> None:
    pngs = [r for r in audit if r.get("path", "").endswith(".png") and "error" not in r]
    # also compress newly created dark variants
    for p in IMAGES.rglob("*-dark.png"):
        rel = p.relative_to(ROOT).as_posix()
        if not any(r.get("path") == rel for r in pngs):
            pngs.append({"path": rel})

    before = after = 0
    n = 0
    for r in pngs:
        path = ROOT / r["path"]
        if not path.exists():
            continue
        try:
            b0 = path.stat().st_size
            im = Image.open(path)
            # preserve format quirks
            if im.mode == "P":
                im = im.convert("RGBA")
            tmp = path.with_suffix(".png.tmp")
            save_kwargs = {"optimize": True, "compress_level": 9}
            if path.suffix.lower() == ".png":
                im.save(tmp, format="PNG", **save_kwargs)
            else:
                continue
            b1 = tmp.stat().st_size
            if b1 < b0:
                tmp.replace(path)
                before += b0
                after += b1
                n += 1
            else:
                tmp.unlink(missing_ok=True)
                before += b0
                after += b0
        except Exception as e:
            print("compress fail", r["path"], e)
    saved = before - after
    print(f"compress: touched_better={n} saved_mb={saved/1e6:.2f} ({100*saved/max(1,before):.1f}%)")


# ---------------------------------------------------------------------------
# 6. Series social cards
# ---------------------------------------------------------------------------

SERIES = [
    ("Distributed Systems Papers", "Classic papers: Raft, GFS, DynamoDB, …"),
    ("System Design Case Studies", "Rate limiter, KV store, crawler, …"),
    ("Designing Distributed Systems", "Patterns from Brendan Burns"),
    ("Web Security", "XSS, CSRF, XXE, injection, DoS"),
    ("Designing Data-Intensive Applications", "Chapter notes on DDIA"),
    ("Design Patterns", "GoF creational, structural, behavioral"),
    ("Docker", "Containers from first principles"),
    ("Binary Tree Problems", "Problem sets in C++"),
    ("Binary Search Problems", "Problem sets in C++"),
    ("BFS Problems", "Graph BFS problem sets"),
    ("LLM & RAG", "Large language models & retrieval"),
    ("Deep Learning Fundamentals", "DNN and sequence models"),
    ("PostgreSQL", "Isolation levels & internals"),
]

PURPLE = (68, 70, 157)
WHITE = (255, 255, 255)
LIGHT = (216, 216, 240)
GREEN = (74, 222, 128)


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)


def fit_font(draw, text, font_path, start, max_w):
    size = start
    while size > 14:
        f = ImageFont.truetype(font_path, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return ImageFont.truetype(font_path, 14)


def render_series_card(name: str, blurb: str, dest: Path) -> None:
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), PURPLE)
    d = ImageDraw.Draw(img)

    # logo disc (same geometry as site avatar, scaled)
    S = 280 / 512
    ox, oy = 90, (H - 280) // 2

    def bx(v):
        return ox + v * S

    def by(v):
        return oy + v * S

    d.ellipse([ox, oy, ox + 512 * S, oy + 512 * S], fill=PURPLE, outline=WHITE, width=5)
    d.ellipse([bx(131), by(131), bx(381), by(381)], fill=WHITE)
    d.rectangle([ox, by(193), ox + 512 * S, by(319)], fill=PURPLE)
    try:
        f_logo = ImageFont.truetype("C:/Windows/Fonts/arialbi.ttf", int(131 * S))
        f_title_path = "C:/Windows/Fonts/arialbd.ttf"
        f_body_path = "C:/Windows/Fonts/arial.ttf"
    except OSError:
        f_logo = ImageFont.load_default()
        f_title_path = f_body_path = None

    if f_title_path:
        d.text((bx(256) - 383 * S / 2, by(299)), "TISAN", font=f_logo, fill=WHITE, anchor="ls")
        tx, max_w = 430, W - 430 - 50
        # wrap series name if needed
        f_title = fit_font(d, name if len(name) < 28 else name[:28], f_title_path, 64, max_w)
        # simple wrap
        words = name.split()
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if d.textlength(trial, font=f_title) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        y = 180
        for ln in lines[:3]:
            d.text((tx, y), ln, font=f_title, fill=WHITE)
            y += int(f_title.size * 1.15)
        f_blurb = fit_font(d, blurb, f_body_path, 32, max_w)
        d.text((tx, y + 16), blurb, font=f_blurb, fill=LIGHT)
        f_url = ImageFont.truetype(f_title_path, 28)
        d.text((tx, H - 90), "gemsofcoding.com · series", font=f_url, fill=GREEN)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, format="PNG", optimize=True)


def generate_series_cards() -> list[dict]:
    SERIES_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, blurb in SERIES:
        slug = slugify(name)
        dest = SERIES_DIR / f"{slug}.png"
        render_series_card(name, blurb, dest)
        rows.append({
            "name": name,
            "slug": slug,
            "description": blurb,
            "image": f"/assets/img/series/{slug}.png",
        })
        print("series card:", dest.name)
    # write _data/series.yml
    data = ROOT / "_data" / "series.yml"
    lines = ["# Series catalog (Phase 6) — used by series tab / social cards\n"]
    for r in rows:
        lines.append(f"- name: \"{r['name']}\"\n")
        lines.append(f"  slug: {r['slug']}\n")
        lines.append(f"  description: \"{r['description']}\"\n")
        lines.append(f"  image: {r['image']}\n")
    data.write_text("".join(lines), encoding="utf-8", newline="\n")
    print("wrote", data.relative_to(ROOT))
    return rows


def apply_series_images_to_posts_without_image(series_rows: list[dict]) -> None:
    """If a series post has no image: front matter, use the series card."""
    by_name = {r["name"]: r for r in series_rows}
    n = 0
    for post in POSTS.glob("*.md"):
        text = post.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
        if not m:
            continue
        fm_raw, body = m.group(1), m.group(2)
        # crude parse
        if re.search(r"^image:", fm_raw, re.M):
            continue
        sm = re.search(r'^series:\s*"([^"]+)"', fm_raw, re.M)
        if not sm:
            continue
        row = by_name.get(sm.group(1))
        if not row:
            continue
        lines = fm_raw.split("\n")
        # insert after title
        for i, l in enumerate(lines):
            if l.startswith("title:"):
                lines.insert(i + 1, f"image: {row['image']}")
                break
        else:
            lines.append(f"image: {row['image']}")
        post.write_text("---\n" + "\n".join(lines) + "\n---\n" + body, encoding="utf-8", newline="\n")
        n += 1
    print(f"series image applied to {n} posts lacking image:")


def main():
    print("=== AUDIT ===")
    audit = run_audit()
    print("=== DARK VARIANTS ===")
    dark_map = generate_dark_variants(audit)
    # re-audit is expensive; skip
    print("=== POST REWRITES (captions / width / light-dark) ===")
    process_posts(audit, dark_map)
    print("=== COMPRESS ===")
    # refresh audit paths to include dark variants for compress list
    audit2 = audit + [{"path": v} for v in dark_map.values()]
    compress_pngs(audit2)
    print("=== SERIES CARDS ===")
    rows = generate_series_cards()
    apply_series_images_to_posts_without_image(rows)
    print("DONE")


if __name__ == "__main__":
    main()
