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

## Phase 6 — Image & diagram polish  (M)

- [ ] **Dark-mode audit**: script scans all images for near-black-on-transparent
      (invisible in dark mode) and glaring white backgrounds. Fix via per-mode variants:
      `![alt](x-dark.png){: .dark}` + `![alt](x.png){: .light}` (Chirpy built-in).
- [ ] **Captions**: italic line directly under an image renders as a styled caption
      (built-in). Script mirrors existing alt text as captions where meaningful.
- [ ] **Width normalization**: oversized screenshots get `{: .w-75 }` / `{: .w-50 }`.
- [ ] **Compression**: batch all PNGs through oxipng (or convert to WebP with PNG
      fallback) — expect 40–60% weight reduction. Keep source images untouched in git.
- [ ] **Per-series og-images**: extend the PIL social-card script (Phase 3) to render
      13 series-branded cards; set `image:` accordingly on series posts.

## Phase 7 — Typography & editorial voice  (S–M)

Taste-driven — review rendered output before shipping.

- [ ] **Body font**: Inter (modern sans) vs Source Serif 4 (long-form theory feel).
      Pick one; implement via SCSS override only.
- [ ] **Callout pass**: convert "*Note:*" / "*Important:*" / "*It's worth noting*"
      paragraphs across 87 posts into `{: .prompt-info }` / `.prompt-tip` /
      `.prompt-warning` blocks. Script candidates, human review before applying.
- [ ] **Collapsible solutions**: styled `<details><summary>Show solution</summary>…`
      for the algorithm problem-set posts (custom CSS + content pass).
- [ ] **Brand accent extension**: blockquote border, `::selection` color, prompt-block
      accents in logo purple `#44469D` (keep subtle; dark mode variants).
- [ ] **Dark-mode QA pass** over the ~20 most-trafficked posts (after Phase 6).

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
