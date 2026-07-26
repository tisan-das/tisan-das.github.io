# Site Improvement Roadmap (post-migration)

Status: Phases 0–4 complete (quick fixes, Chirpy migration, taxonomy, tooling/polish,
giscus-prep/pins/brand accent). The phases below are **independently shippable** —
pick in any order. Each notes effort (S/M/L) and risk.

Guiding constraints:
- **No theme vendoring** (don't copy theme layouts/includes into the repo) unless a
  payoff is impossible otherwise — every vendored file is upgrade debt.
- Everything below uses Chirpy v7 built-ins or our two sanctioned extension points:
  `assets/css/jekyll-theme-chirpy.scss` (custom CSS) and `_includes/series-nav.html`.

---

## Phase 5 — Reading experience: code, math, inline diagrams  (M) ✅ done

The core of a CS blog. Target: snippets and formulas look as good as the prose.

- [x] **Code font**: JetBrains Mono + ligatures, self-hosted woff2 under `assets/fonts/`.
- [x] **Rouge palette refresh**: GitHub-light / One-Dark token colors in our SCSS override
      (light + dark + system-dark modes).
- [x] **Filename labels**: `{: file='path' }` convention documented; `tools/new_post.py`
      template + README updated; ` ```diff ` called out for before/after.
- [x] **MathJax**: `math: true` + LaTeX on DNN, RNN, HashTable, Consistent Hashing,
      Union-Find, LSM-Tree (MSE/CE/GD, recurrence, load factor, $k/n$, $\alpha(n)$, etc.).
- [x] **Mermaid**: RAFT state + election sequence, rate-limiter token-bucket flow,
      consistent-hashing lookup flow. PNGs kept for pictorial figures.

## Phase 6 — Image & diagram polish  (M) ✅ done

- [x] **Dark-mode audit + variants**: `tools/phase6_images.py` classified all content
      images; generated 228 `*-dark.png` variants (white-bg → dark canvas, ink inverted);
      wired 221 light/dark pairs via Chirpy `{: .light }` / `{: .dark }`.
- [x] **Captions**: 239 italic captions mirrored from alt text under figures.
- [x] **Width normalization**: `{: .w-75 }` / `{: .w-50 }` on wide diagrams (≥1000px).
- [x] **Compression**: PNG optimize pass (PIL); modest savings on already-decent assets.
- [x] **Per-series og-images**: 13 cards under `assets/img/series/` + `_data/series.yml`;
      applied as `image:` on series posts that lacked a content image.

## Phase 7 — Typography & editorial voice  (S–M) ✅ done

- [x] **Body font**: Inter (self-hosted 400/500/600/700) — chosen over Source Serif for
      mixed code/diagram density; applied to body + headings via SCSS override.
- [x] **Callout pass**: 23+ notes/warnings/NB/worth-noting → Chirpy
      `{: .prompt-info|tip|warning }` blockquotes (`tools/phase7_editorial.py`).
- [x] **Collapsible solutions**: 108 `<details class="solution">` wrappers across 10
      algorithm problem-set posts; styled summary + open state in SCSS.
- [x] **Brand accent extension**: blockquote border, `::selection`, prompt-info border
      in logo purple (light/dark); tip stays teal for semantic contrast.
- [x] **Dark-mode QA**: structural check on top ~20 posts (light/dark pairs, details
      balance, prompt markup) — 0 issues.

## Phase 8 — Discovery, curation & engagement  (S)

- [ ] **Activate giscus**: enable Discussions, install app, paste category_id,
      `comments.provider: giscus`. (Pre-configured; see README.)
- [ ] **`/series/` tab**: new `_tabs/series.md` (layout page) with Liquid
      `group_by: "series"` over all posts + `_data/series.yml` for per-series
      descriptions. Renumber tab `order:` fields. No theme vendoring needed.
- [ ] **Reading paths**: curated tracks on the series page — e.g. "Distributed Systems:
      zero → papers" and "System Design interview track".
- [ ] **Search Console**: `webmaster_verifications.google` in `_config.yml` + submit
      `sitemap.xml`.
- [ ] (Optional, higher cost) **Home "featured series" section** — requires vendoring
      the home layout; only if the series tab feels insufficient.

---

## Explicit non-goals

- No additional theme switch; no heavy JS widgets/animations.
- No wholesale rewrite of post images to a single diagram tool — mixed media is fine;
  consistency comes from captions, sizing and dark-mode variants, not uniformity.
- Don't chase a custom home layout before Phase 8 proves it's needed.
