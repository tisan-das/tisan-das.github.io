# Gems of Coding

Personal tech blog of Tisan Das — notes on designing large-scale distributed systems, databases, algorithms, and everything in between.

**Live at [gemsofcoding.com](https://gemsofcoding.com)**

Built with [Jekyll](https://jekyllrb.com/) and the [Chirpy theme](https://github.com/cotes2020/jekyll-theme-chirpy), hosted on GitHub Pages (built via GitHub Actions).

## Topics covered

- **Distributed Systems** — consensus (Raft, Byzantine), replication, GFS, Zookeeper, DynamoDB, Aurora, Kafka
- **System Design** — rate limiter, consistent hashing, key-value store, URL shortener, web crawler, notification system
- **Databases** — PostgreSQL internals & isolation models, LSM trees, DDIA chapter notes, NoSQL
- **Algorithms** — problem sets on binary trees, binary search, BFS, sliding window, union-find, game theory (C++/Go)
- **Security** — XSS, CSRF, XXE, injection, DoS
- **Deep Learning** — neural network and RNN fundamentals
- **Misc** — design patterns, Docker, Kubernetes, NGINX, 12-factor apps

## Repository structure

```
_posts/                 # blog posts, named YYYY-MM-DD-title.md
_tabs/                  # sidebar pages (about, archives, categories, tags)
images/                 # post images, organized by topic folder
assets/img/favicons/    # favicon set generated from images/avatar.svg
_config.yml             # site configuration (Chirpy)
Gemfile                 # Ruby dependencies (jekyll-theme-chirpy)
.github/workflows/      # GitHub Actions build & deploy
```

## Writing a new post

Use the generator:

```sh
python tools/new_post.py "My Post Title" \
    --categories "Distributed Systems,Consensus" \
    --tags raft,consensus \
    --series "Distributed Systems Papers"   # optional
```

Or create `_posts/YYYY-MM-DD-my-title.md` by hand:

```yaml
---
title: My Title
date: YYYY-MM-DD HH:MM:SS +0530
series: "Distributed Systems Papers"    # optional, must match other parts exactly
categories: ["Distributed Systems", "Consensus"]
tags: [raft, consensus]
image: /images/<topic>/diagram.png      # optional, per-post social preview
---

Intro paragraph (becomes the home-page excerpt).

{% include series-nav.html %}            # only for series posts, after the intro
```

### Conventions

- **Images**: store under `images/<topic>/`, reference absolutely, and **always write alt text**:
  `![Raft leader election timeline](/images/raft/election.png)`
- **Code**: fenced blocks with a language tag (```` ```sql ````, ```` ```go ````, ```` ```cpp ````) — Chirpy adds line numbers and a copy button. Add `{: file='name.ext' }` right after a fence for a filename label; use ```` ```diff ```` for before/after snippets
- **Math**: set `math: true` in front matter, then `$$...$$` blocks and `$...$` inline (MathJax)
- **Diagrams**: set `mermaid: true` in front matter and use ```` ```mermaid ```` fences for sequence/flow/state diagrams — they follow dark mode automatically. Use PNGs for pictorial figures
- **Categories**: pick an existing top-level + subcategory pair where possible (see the Categories tab)
- **Series**: reuse the exact series name; the nav box builds itself

## Local development

```sh
bundle install
bundle exec jekyll serve --livereload
```

## Enabling comments (giscus)

Comments are powered by [giscus](https://giscus.app) (GitHub Discussions). One-time setup (~3 minutes):

1. Repo **Settings → General → Features → enable Discussions**
2. Install the [giscus app](https://github.com/apps/giscus) on this repo (only this repository)
3. Open [giscus.app](https://giscus.app):
   - Repository: `tisan-das/tisan-das.github.io`
   - Category: **Announcements** (only maintainers can create new discussion threads)
   - Copy **category id** (`data-category-id`)
4. In `_config.yml` under `comments`:
   - set `provider: giscus`
   - set `giscus.category_id: "..."` (paste the id)
5. Push to `master` and hard-refresh a post — the comment box appears at the bottom

Already filled in for you: `giscus.repo`, `giscus.repo_id` (`R_kgDOId0yPg`), mapping, lang, reactions.

## Google Search Console

1. [Search Console](https://search.google.com/search-console) → Add property → URL prefix `https://gemsofcoding.com`
2. Verification method **HTML tag** → copy only the `content="..."` value
3. Paste into `_config.yml` → `webmaster_verifications.google`
4. Push, click **Verify**, then **Sitemaps** → submit `https://gemsofcoding.com/sitemap.xml`

## Deployment

Pushes to `master` build via GitHub Actions and deploy to GitHub Pages. Pushes to `develop` run the build as a check only.

## License

Content © Tisan Das. Theme: [Chirpy](https://github.com/cotes2020/jekyll-theme-chirpy) (MIT).
