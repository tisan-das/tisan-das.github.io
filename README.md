# Gems of Coding

Personal tech blog of Tisan Das — notes on designing large-scale distributed systems, databases, algorithms, and everything in between.

**Live at [gemsofcoding.com](https://gemsofcoding.com)**

Built with [Jekyll](https://jekyllrb.com/) and hosted on GitHub Pages.

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
_posts/       # blog posts, named YYYY-MM-DD-title.md
images/       # post images, organized by topic folder
_layouts/     # page templates
_includes/    # analytics, meta, icons
_sass/        # stylesheets
_config.yml   # site configuration
```

## Writing a new post

1. Create `_posts/YYYY-MM-DD-my-title.md` with front matter:

   ```yaml
   ---
   layout: post
   title: My Title
   ---
   ```

2. Put images under `images/<topic>/` and reference them relatively: `![](../images/<topic>/diagram.png)`
3. Use fenced code blocks with a language tag (```` ```sql ````, ```` ```go ````, ```` ```cpp ````) for syntax highlighting via Rouge.
4. Push to GitHub — Pages builds and deploys automatically.

## License

Content © Tisan Das. Theme structure originally based on [Jekyll Now](https://github.com/barryclark/jekyll-now) (MIT).
