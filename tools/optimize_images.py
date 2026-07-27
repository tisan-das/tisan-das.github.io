"""
Batch-convert content images under images/ to WebP.

- Downscales anything wider than MAX_WIDTH (content column is ~750px,
  so 1400px covers ~1.9x retina) — this is what actually reduces
  decoded/GPU memory, not the format change alone.
- Encodes WebP at QUALITY (diagrams/screenshots stay crisp; ~80-90%
  smaller than the source PNGs).
- Keeps alpha channel when the source has one.
- Deletes the original only after the .webp is written and non-empty.

Idempotent: skips files whose .webp sibling already exists.
Run:  python tools/optimize_images.py
"""

import os
import sys
from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..", "images")
MAX_WIDTH = 1400
QUALITY = 90
EXTS = (".png", ".jpg", ".jpeg")


def has_alpha(im):
    if im.mode in ("RGBA", "LA"):
        return True
    if im.mode == "P" and "transparency" in im.info:
        return True
    return False


def convert(path):
    base, _ = os.path.splitext(path)
    out = base + ".webp"
    if os.path.exists(out):
        return None

    im = Image.open(path)
    im.load()

    if has_alpha(im):
        im = im.convert("RGBA")
    else:
        im = im.convert("RGB")

    w, h = im.size
    if w > MAX_WIDTH:
        im = im.resize((MAX_WIDTH, round(h * MAX_WIDTH / w)), Image.LANCZOS)

    im.save(out, "WEBP", quality=QUALITY, method=6)

    if os.path.getsize(out) == 0:
        os.remove(out)
        raise RuntimeError(f"empty output for {path}")

    old_size = os.path.getsize(path)
    os.remove(path)
    return old_size, os.path.getsize(out), (w, h), im.size


def main():
    total_old = total_new = count = downscaled = 0
    failures = []
    for dirpath, _, files in os.walk(ROOT):
        for name in sorted(files):
            if not name.lower().endswith(EXTS):
                continue
            path = os.path.join(dirpath, name)
            try:
                result = convert(path)
            except Exception as e:  # noqa: BLE001
                failures.append((path, str(e)))
                continue
            if result is None:
                continue
            old_size, new_size, old_dim, new_dim = result
            total_old += old_size
            total_new += new_size
            count += 1
            if new_dim != old_dim:
                downscaled += 1

    print(f"converted: {count} files ({downscaled} downscaled to <= {MAX_WIDTH}px wide)")
    print(f"size: {total_old/1e6:.1f}MB -> {total_new/1e6:.1f}MB "
          f"({100 * total_new / total_old:.0f}% of original)" if total_old else "nothing to do")
    if failures:
        print(f"\n{len(failures)} FAILURES:")
        for path, err in failures:
            print(f"  {path}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
