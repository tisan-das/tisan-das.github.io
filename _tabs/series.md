---
title: Series
icon: fas fa-layer-group
order: 3
---

Long-form notes are grouped into series so you can read them in order. Start with a **reading path** below, or jump into any series.

## Reading paths

Curated tracks across posts (not only within one series).

### 1. Distributed systems — zero → papers

Build intuition, then read the classics.

1. {% assign p = site.posts | where: "title", "CAP Theorem" | first %}{% if p %}[CAP Theorem]({{ p.url | relative_url }}){% else %}CAP Theorem{% endif %} — consistency, availability, partition tolerance
2. {% assign p = site.posts | where: "title", "RAFT Consensus Algorithm" | first %}{% if p %}[RAFT Consensus Algorithm]({{ p.url | relative_url }}){% else %}RAFT{% endif %} — leader election and log replication
3. {% assign p = site.posts | where: "title", "Introduction to Map-Reduce" | first %}{% if p %}[Map-Reduce]({{ p.url | relative_url }}){% else %}Map-Reduce{% endif %} — batch compute at scale
4. {% assign p = site.posts | where: "title", "Introduction to Google File System" | first %}{% if p %}[Google File System]({{ p.url | relative_url }}){% else %}GFS{% endif %} — distributed storage
5. {% assign p = site.posts | where: "title", "Designing Distributed Systems - Single Node Patterns" | first %}{% if p %}[Single-node patterns]({{ p.url | relative_url }}){% else %}Single-node patterns{% endif %} — sidecar, ambassador, adapter
6. {% assign p = site.posts | where: "title", "Amazon DynamoDB - Architecture" | first %}{% if p %}[DynamoDB Architecture]({{ p.url | relative_url }}){% else %}DynamoDB{% endif %} — highly available key-value design
7. {% assign p = site.posts | where: "title", "Byzantine Consensus" | first %}{% if p %}[Byzantine Consensus]({{ p.url | relative_url }}){% else %}Byzantine Consensus{% endif %} — when nodes lie

Then continue with the full [Distributed Systems Papers](#distributed-systems-papers) and [Designing Distributed Systems](#designing-distributed-systems) series.

### 2. System design interview track

Work through the case studies in publishing order.

1. {% assign p = site.posts | where: "title", "Fundamentals of System Design - Concurrency and Parallelism" | first %}{% if p %}[Concurrency & parallelism]({{ p.url | relative_url }}){% else %}Concurrency{% endif %}
2. {% assign p = site.posts | where: "title", "Fundamentals of System Design - Failure Models" | first %}{% if p %}[Failure models]({{ p.url | relative_url }}){% else %}Failure models{% endif %}
3. {% assign p = site.posts | where: "title", "System Design - Rate Limiter" | first %}{% if p %}[Rate limiter]({{ p.url | relative_url }}){% else %}Rate limiter{% endif %}
4. {% assign p = site.posts | where: "title", "Introduction to Consistent Hashing" | first %}{% if p %}[Consistent hashing]({{ p.url | relative_url }}){% else %}Consistent hashing{% endif %}
5. {% assign p = site.posts | where: "title", "System Design - Design Key-Value Store" | first %}{% if p %}[Key-value store]({{ p.url | relative_url }}){% else %}KV store{% endif %}
6. {% assign p = site.posts | where: "title", "System Design - Design a Unique ID Generator for Distributed Systems" | first %}{% if p %}[Unique ID generator]({{ p.url | relative_url }}){% else %}Unique ID{% endif %}
7. {% assign p = site.posts | where: "title", "System Design - Design a URL Shortener" | first %}{% if p %}[URL shortener]({{ p.url | relative_url }}){% else %}URL shortener{% endif %}
8. {% assign p = site.posts | where: "title", "System Design - Web Crawler" | first %}{% if p %}[Web crawler]({{ p.url | relative_url }}){% else %}Web crawler{% endif %}
9. {% assign p = site.posts | where: "title", "System Design - Notification System" | first %}{% if p %}[Notification system]({{ p.url | relative_url }}){% else %}Notifications{% endif %}

### 3. Data internals track

Storage engines and databases from first principles.

1. {% assign p = site.posts | where: "title", "Introduction to Hash Table Internals" | first %}{% if p %}[Hash table internals]({{ p.url | relative_url }}){% else %}Hash tables{% endif %}
2. {% assign p = site.posts | where: "title", "Log-Structured Merge (LSM) tree" | first %}{% if p %}[LSM trees]({{ p.url | relative_url }}){% else %}LSM{% endif %}
3. {% assign p = site.posts | where: "title", "DDIA - Chap03 - Storage and Retrieval" | first %}{% if p %}[DDIA — Storage & retrieval]({{ p.url | relative_url }}){% else %}DDIA ch.3{% endif %}
4. {% assign p = site.posts | where: "title", "PostgreSQL - Isolation Levels" | first %}{% if p %}[Postgres isolation]({{ p.url | relative_url }}){% else %}Postgres isolation{% endif %}
5. {% assign p = site.posts | where: "title", "Postgres Internals I" | first %}{% if p %}[Postgres internals]({{ p.url | relative_url }}){% else %}Postgres internals{% endif %}
6. {% assign p = site.posts | where: "title", "DDIA - Chap05 - Replication" | first %}{% if p %}[DDIA — Replication]({{ p.url | relative_url }}){% else %}DDIA ch.5{% endif %}

### 4. Algorithms practice track

Problem sets in C++ (solutions collapsed — open when you want them).

1. [Binary Tree Problems](#binary-tree-problems)
2. [Binary Search Problems](#binary-search-problems)
3. [BFS Problems](#bfs-problems)
4. {% assign p = site.posts | where: "title", "Problem Sets on Sliding Window" | first %}{% if p %}[Sliding window]({{ p.url | relative_url }}){% else %}Sliding window{% endif %}
5. {% assign p = site.posts | where: "title", "Union-Find Problem Sets" | first %}{% if p %}[Union-Find]({{ p.url | relative_url }}){% else %}Union-Find{% endif %}
6. {% assign p = site.posts | where: "title", "Stack Problems - Part I" | first %}{% if p %}[Stack problems]({{ p.url | relative_url }}){% else %}Stack{% endif %}
7. {% assign p = site.posts | where: "title", "Problem Sets on Game Theory" | first %}{% if p %}[Game theory]({{ p.url | relative_url }}){% else %}Game theory{% endif %}

---

## All series

{% assign catalog = site.data.series | sort: "order" %}
{% for s in catalog %}
### {{ s.name }}
{: #{{ s.slug }} }

{{ s.description }}

{% assign parts = site.posts | where: "series", s.name | sort: "date" %}
{% if parts.size == 0 %}
_No posts tagged with this series yet._
{% else %}
**{{ parts.size }} part{% if parts.size != 1 %}s{% endif %}**

{% for post in parts %}
{{ forloop.index }}. [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%b %Y" }}
{% endfor %}
{% endif %}

{% endfor %}
