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

1. Create `_posts/YYYY-MM-DD-my-title.md` with front matter:

   ```yaml
   ---
   title: My Title
   date: YYYY-MM-DD HH:MM:SS +0530
   categories: [Distributed Systems]
   tags: [consensus, raft]
   ---
   ```

2. Put images under `images/<topic>/` and reference them absolutely: `![](/images/<topic>/diagram.png)`
3. Use fenced code blocks with a language tag (```` ```sql ````, ```` ```go ````, ```` ```cpp ````) — Chirpy adds line numbers and a copy button via Rouge.

## Local development

```sh
bundle install
bundle exec jekyll serve --livereload
```

## Deployment

Pushes to `master` build via GitHub Actions and deploy to GitHub Pages. Pushes to `develop` run the build as a check only.

## License

Content © Tisan Das. Theme: [Chirpy](https://github.com/cotes2020/jekyll-theme-chirpy) (MIT).
