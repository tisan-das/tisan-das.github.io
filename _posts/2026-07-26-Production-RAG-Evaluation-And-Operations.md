---
layout: post
title: "Production RAG - Part 8: Evaluation and Operations"
image: /images/rag/08-evaluation-ops/01-retrieval-confusion-matrix.webp
series: "Production RAG"
categories: ["LLM", "RAG"]
tags: [rag, evaluation, observability, security, agents, llm]
published: true
---

Seven posts of machinery, and none of it is trustworthy until you can answer one question: how do you know it works? RAG systems are unusually hostile to intuition here, because a broken one keeps returning fluent, confident, well-cited answers. There is no crash, no 500, no red line on a dashboard. This final post covers how you measure the thing, how you operate it safely, and the consolidated list of ways it breaks without telling you.

{% include series-nav.html %}

> **Disclaimer.** This post is drafted with assistance from large language models (Claude Opus 4.8 and DeepSeek V4 Pro) based on conversations exploring production RAG concepts. All content has been reviewed, edited, and verified by a human author.
{: .prompt-info }

## Every retrieval metric is one confusion matrix

For a given query, each chunk is either relevant or not, and either retrieved or not. Everything else is a ratio over those four boxes.

![The retrieval confusion matrix](/images/rag/08-evaluation-ops/01-retrieval-confusion-matrix.webp)
_A chunk that is never retrieved cannot be rescued by any later stage in the pipeline._

- **Recall@k** — of everything relevant, how much did the top-k contain? This is the retrieval-stage metric that matters most.
- **Precision@k** — of what you returned, how much was relevant? Noise dilutes the context window and invites the lost-in-the-middle effect.
- **Rank-aware metrics** — MRR (where does the first relevant hit land?) and nDCG (graded relevance, discounted by rank) matter because the generator attends more to the top of its context.

> F1 balances precision and recall, and that balance is exactly wrong *at the retrieval stage*. A false positive costs the reranker one candidate slot. A false negative costs the answer its evidence, permanently. Weight recall at retrieval — fetch generously — and precision at reranking — cut ruthlessly. A single number hiding two asymmetric costs is how teams optimize themselves into unanswerable queries.
{: .prompt-warning }

## Offline and online

**Offline** evaluation is a golden set of query-to-relevant-chunk pairs, re-run against every pipeline change. This is your regression suite: no chunker change, no embedding model swap, no threshold adjustment ships without it. **Online** evaluation is user feedback, answer acceptance, deflection and escalation rates on live traffic.

The central obstacle is well known: golden datasets are expensive to build and they go stale as the corpus and the query mix drift. Two mitigations, both worth doing:

**Synthetic query generation.** Have an LLM generate questions per chunk to bootstrap the set. Useful for getting started, but validate a sample by hand — synthetic questions tend to be suspiciously well-formed compared with what users actually type.

**Mine online traffic.** Real queries whose outcomes you can label — thumbs-down, escalated, abandoned — feed back into the offline set, which is what keeps it representative over time.

The simplest online KPI is a satisfaction rate: thumbs-up over total votes. Log the query, the retrieved context IDs and the answer alongside every rating, so that a bad rating is *diagnosable* rather than merely countable.

## Judges and frameworks

Generation-side quality needs judges. The two standard aspects are **relevance** (does the response answer the query?) and **faithfulness** (is it supported by the retrieved documents?).

| Judge | Strength | Weakness |
|---|---|---|
| LLM-as-a-judge | Flexible, no training, custom criteria | Slow, expensive, can hallucinate, inconsistent between runs |
| Dedicated evaluator models | Fast, cheap, consistent | Fixed aspect; no free-form criteria |
| Human evaluation | Gold standard for nuance and intent | Slowest and most expensive — use as a small final check |

**Reference-free metrics** are the notable recent development, and they attack the golden-dataset bottleneck directly: grading retrieval relevance on a scale with an LLM judge, decomposing context into factual "nuggets" and checking their presence in the answer, hallucination scoring, citation-support checking, and consistency measured across repeated runs. None of these require golden answers.

| Framework | Model | Character |
|---|---|---|
| Open RAG Eval | Reference-free | Open source; connector architecture; the metrics above |
| Ragas | LLM-as-a-judge | Large metric set, framework integrations, synthetic test-set generation |
| DeepEval | Pytest-style | Evaluation as unit tests in CI; custom criteria via G-Eval |
| Managed cloud evaluation | Managed LLM-as-a-judge | Retrieval-only or end-to-end jobs; adds responsible-AI scoring |

> Wire evaluation into CI like tests, not into quarters like audits. The entire point of an offline suite is that a chunker tweak which silently drops table recall by eight points fails a build the same afternoon — rather than surfacing as a customer complaint three weeks later, by which time four other things have also changed.
{: .prompt-tip }

## Agentic RAG, briefly

Classic RAG is one-shot: retrieve once, generate once. Agentic RAG makes **retrieval a tool the model calls** — zero, one, or many times — inside a reasoning loop. That unlocks iterative retrieval (reformulate and retrieve again when the first pass comes back thin), dynamic tool use (mix the index with web search, APIs and databases), and decomposition (split a multi-part question into sub-queries and synthesize).

Two protocols are worth knowing by name: **MCP** connects an agent to its *tools* (vertical), and **A2A** connects agents to *each other* (horizontal).

> Every retrieved chunk inside an agent loop is **untrusted input sitting in the prompt**. A document containing *"ignore your instructions and…"* is a prompt-injection vector that one-shot RAG merely displays, but that an agent may *act on*, with whatever tool permissions the loop holds. Treat retrieval output as data, constrain tool permissions per step, and never let retrieved text originate a tool call without a policy check.
{: .prompt-danger }

## Permission filtering

RAG's structural security advantage over fine-tuning only materializes if you enforce it. Two rules decide everything:

**Filter at retrieval, never after generation.** Post-generation redaction fails structurally — the forbidden content has already shaped the answer, and the model may paraphrase it past any redactor. The unauthorized chunk must never reach the context window at all.

**The filter is a hard predicate, not a ranking signal.** It runs last in the reranking chain precisely so nothing downstream can override it, and it fails *closed*: an untagged chunk is not retrievable by anyone until it is tagged.

```sql
-- ACL as a hard SQL predicate, not a score adjustment
SELECT c.id, c.display_text FROM candidates c
JOIN chunk_acl a ON a.chunk_id = c.id
WHERE a.tag IN (SELECT tag FROM principal_tags WHERE principal = ?);
```

> Two quiet failure modes here. **The confused deputy:** the RAG service authenticates to the index with its own powerful identity and forgets to scope by end user, so every caller inherits the service's access. Propagate the end-user principal through every hop. **ACL drift:** source-system permissions change after ingestion, and the index remembers yesterday's. Sync permissions on a schedule and treat staleness as an SLO with an alert, not as a hope.
{: .prompt-danger }

The same discipline applies to PII, which has three chokepoints: at ingest (redact before indexing — nothing sensitive is ever stored), at retrieval (mask on the way into the prompt), and at output (a last-resort scrubber). Redact at the earliest point your product allows; each later chokepoint is a mitigation for the one you skipped.

## Telemetry

A RAG answer is the end of a pipeline of stochastic stages. When it is wrong, you need to know *which stage* failed. Instrument four layers as spans in one trace per query:

| Layer | Record | Answers |
|---|---|---|
| Retrieval | Per-arm candidates and scores, filters applied | "Was the evidence ever fetched?" |
| Fusion / rerank | Input and output rankings per stage | "Did a stage bury it?" |
| Generation | Prompt hash, model and version, tokens, latency | "What did the model actually see?" |
| Quality | Grounding scores, abstentions, escalations, feedback | "Was the answer any good?" |

Sample payloads, not signals: keep scores and rankings for 100% of traffic, and full prompt and context payloads for a small sample plus every failure. Pin and log every model version — embedding, reranker, generator, judge — on every trace. And alert on *distribution shifts* (retrieval score histograms, escalation rate, abstention rate) rather than only on errors, because almost nothing in this stack throws one.

## The consolidated silent-failure list

Every entry below appeared somewhere in this series. Together they are the reason the operating discipline looks paranoid.

| Silent failure | Post | Detection |
|---|---|---|
| Parser subprocess falls back to flat text | 2 | Metric and warning on fallback activation |
| Gibberish ratio computed after normalization, so always 0.0 | 2 | CI assertion on raw-text ordering |
| `\s+` normalization destroys every table | 2 | Table-count regression in the eval set |
| Shifted CMap indexed as clean text | 2 | Lexicon tier plus seeded garble tests |
| Orphan table runt outranks its own table | 3 | Minimum chunk size floor; length histogram |
| Embedding model changed, index not re-embedded | 4 | `embedder_version` mismatch check |
| BM25 sign confusion — FTS5 scores are negative | 4 | Unit test on a known ranking |
| Both retrievers share a blind spot; RRF amplifies it | 4 | Reranker disagreement rate |
| Embedding model silently truncates long chunks | 4 | Assert chunk token count < model max before embedding |
| Image exceeds the vision cap, transcription is invented | 5 | Log image dimension distribution at ingest |
| Entity filter matches nothing, producing empty answers | 6 | Empty-after-filter fallback and counter |
| Hub node floods two-hop traversal | 6 | Fan-out cap and degree monitoring |
| Wrong entity merge corrupts every traversal through it | 6 | High auto-merge bar; human review band |
| Semantic cache serves the negated query | 7 | Tight threshold; cache-hit audit sample |
| Stale cache after document re-ingestion | 7 | Key by document-set version; flush on re-ingest |
| Cache shared across permission scopes leaks data | 7 | Cache key must include permission scope or be per-principal |
| Confused deputy — service identity, not user identity | 8 | Principal propagated on every trace |
| ACL drift — index remembers old permissions | 8 | Staleness SLO and sync alerts |

## Build order

If you are starting from scratch, this ordering keeps every stage shippable and — critically — puts the measurement infrastructure before the sophistication that needs measuring.

![Recommended build order for a production RAG system](/images/rag/08-evaluation-ops/02-build-order.webp)
_Stage 4 is the one people skip. It is also the one that makes stages 5 through 12 anything other than guesswork._

Resist building stage 9 before stage 4 exists to tell you whether it helped. Graph retrieval and chunk enrichment are answers to *specific observed failures*, and without an evaluation set you cannot tell which failure you have — which takes you right back to [part 6](/Production-RAG-Entities-And-Graphs/), where the two failures look identical from outside and want opposite fixes.

## The through-line

Five principles carry the whole series, and every technique in it is one of them wearing a specific costume.

- **Boundaries are permanent.** Chunk cuts, image tile cuts, entity merges — whatever you fix at ingest defines what retrieval can ever return.
- **Index text and display text are different things.** Retrieval wants synthetic help; users and citations must never see it.
- **Trust is a property you track, not assume.** Extracted, transcribed and generated content each carry provenance, and reconstructed content never contaminates the signals of trusted content.
- **Optimize the recurring cost bucket.** Query-side costs run forever; ingest runs once. Pay once to make forever cheap.
- **Recall and permissions are never allowed to fail silently.** A missed chunk and a leaked chunk are the two unrecoverable errors. Everything else is tunable.

## References

1. Ofer Mendelevitch and Forrest Sheng Bao, *Hands-On RAG for Production*, O'Reilly Media, 2026
2. [Open RAG Eval](https://github.com/vectara/open-rag-eval)
3. [Ragas documentation](https://docs.ragas.io/)
4. [DeepEval](https://github.com/confident-ai/deepeval)
5. Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models*, ICLR 2023
6. [Model Context Protocol specification](https://modelcontextprotocol.io/)
7. [OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
