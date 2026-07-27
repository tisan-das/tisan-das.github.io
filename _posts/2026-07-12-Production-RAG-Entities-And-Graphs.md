---
layout: post
title: Production RAG - Entities and Knowledge Graphs
image: /images/rag/06-entities-graphs/01-two-retrieval-failures.png
series: "Production RAG"
categories: ["Deep Learning", "RAG"]
tags: [rag, knowledge-graph, ner, graphrag, entity-resolution]
published: true
---

At some point in every RAG project, a category of question stops working and no amount of tuning fixes it. Better chunking does not help. A stronger reranker does not help. The reason is that two completely different failures both present as *"the system could not answer"*, and only one of them is a retrieval-quality problem at all.

{% include series-nav.html %}

![Matching failure versus reachability failure](/images/rag/06-entities-graphs/01-two-retrieval-failures.png)
_Two failures, identical symptoms, opposite fixes. Diagnosing which one you have is the decision point for everything below._

**Matching failure.** The answer sits inside one chunk, but the chunk shares no vocabulary with the query — *"who can approve prod deploys?"* against a chunk titled "release sign-off authority". Retrieval never surfaces it. The fix is **chunk enrichment**.

**Reachability failure.** No single chunk contains the answer. It spans an incident report, a runbook and an ownership table, joined by a shared `site_id`. No retriever that scores chunks *independently* can assemble it, because no individual chunk is a good match for the whole question. The fix is **graph traversal**.

## What entity extraction buys you

Named-entity recognition tags spans of text as typed entities — products, services, regions, error codes, versions. For retrieval it buys three concrete things:

- **Precision filtering.** *"EKS pricing in eu-west-1"* can filter candidates to chunks tagged `service=EKS AND region=eu-west-1` before similarity scoring runs at all — the metadata filter from [part 1](/Production-RAG-Pipeline-Anatomy/), generated automatically.
- **Disambiguation.** The token `Lambda` means something different in a physics corpus and an AWS corpus. Typed entities carry what embeddings blur.
- **Graph edges.** Entities are the nodes. No entities, no graph.

> The pipeline is only as good as its weakest stage: extraction feeds normalization feeds indexing feeds retrieval. A 90%-accurate extractor with no normalization underperforms an 80% extractor with proper alias collapse, because the errors compound multiplicatively down the chain.
{: .prompt-warning }

## Model tiers and what they cost

Extraction runs in two places with very asymmetric budgets. At **ingest**, per chunk, once — you can afford a heavy model. At **query time**, per request, latency-critical — you cannot. Both must land on the same canonical IDs, or your filters silently match nothing.

| Tier | Examples | Character | Fits |
|---|---|---|---|
| Rules / gazetteer | Regex, Aho-Corasick over known names | Free, exact, zero recall beyond the list | Codes, IDs, SKUs |
| Classic NER | spaCy `en_core_web_sm` | Fast, generic types only | People, orgs, places |
| Zero-shot span models | GLiNER family | Arbitrary type labels at inference, no training | **Sweet spot for custom domains** |
| LLM extraction | Small hosted models | Best judgment; slow, priced per token | Relations, hard cases, teaching |

![Entity extraction cost per 100,000 chunks](/images/rag/06-entities-graphs/02-ner-extraction-cost.png)
_Log scale. Self-hosted tiers sit one to three orders of magnitude below hosted LLM extraction._

> The pattern that captures most of the value: **use an LLM once as a teacher, not forever as a worker.** Have a hosted model label 5–20k chunks, fine-tune a small span model on those labels, then run the student self-hosted across the corpus and at query time. You pay LLM prices for a bounded labelling job instead of an unbounded extraction bill.
{: .prompt-tip }

A small span model exported to ONNX with int8 quantization runs comfortably on CPU — roughly 150–300MB resident, tens of milliseconds per chunk. One operational note that saves real debugging time: pin intra-op threads (`OMP_NUM_THREADS=1` per worker) and scale by *process*, not by ONNX thread count. Oversubscription makes inference slower under concurrency, which looks exactly like a model problem and is not.

## Normalization is the whole game

Raw extractions are surface forms. Retrieval needs identities.

![Entity alias collapse](/images/rag/06-entities-graphs/03-entity-linking.png)
_The query-time extractor must land on the same canonical ID, whichever surface form the user happened to type._

```sql
CREATE TABLE entities(
  id TEXT PRIMARY KEY,        -- 'aws:eks'
  type TEXT, canonical TEXT,  -- 'service', 'Amazon EKS'
  aliases TEXT                -- JSON: ["EKS","Elastic Kubernetes Service","k8s cluster"]
);
CREATE TABLE chunk_entities(
  chunk_id INTEGER, entity_id TEXT, count INTEGER,
  PRIMARY KEY(chunk_id, entity_id)
);
```

Wire entities into retrieval in increasing order of aggression: **boost** (add score weight to candidates sharing the query's entities — safe), **filter** (restrict candidates to matching chunks — precise, brittle), **expand** (add alias surface forms to the keyword query — a recall win). Start with boost. Graduate a query pattern to filter only once you have measured extraction precision for that pattern.

> Filtering fails *closed*. One missed extraction at query time and the filter excludes every relevant chunk — the user gets an empty answer, and nothing errored. Always carry a fallback: if the filtered candidate set is empty or suspiciously small, rerun unfiltered.
{: .prompt-danger }

## Chunk enrichment

For matching failures, enrichment appends synthetic retrieval handles to a chunk at ingest time: a one-line summary, likely user questions, alias expansions, canonical entity names. The handles are indexed. They are never displayed.

```sql
-- index_text is what retrieval sees.  display_text is what the user sees.
UPDATE chunks SET index_text =
  heading_path || x'0a' || enrichment || x'0a' || overlap_prefix || x'0a' || body;

-- Column weights keep synthetic text from outbidding real text:
-- bm25(chunks_fts, 4.0 /* body */, 1.5 /* enrichment */, 2.0 /* heading */)
```

> **Index text and display text must be different columns.** Every synthetic addition — overlap, heading ancestry, enrichment — improves retrieval and pollutes citation. The moment you concatenate them into one stored string, users start seeing repeated sentences and machine-written questions inside quoted evidence. This is the load-bearing schema decision of the entire ingest side, and it is nearly free if you make it early and painful to retrofit if you do not.
{: .prompt-tip }

## Graph-hybrid retrieval

For reachability failures, store typed edges alongside the chunks and traverse at query time.

```sql
CREATE TABLE nodes(id TEXT PRIMARY KEY, type TEXT, label TEXT);
CREATE TABLE edges(
  src TEXT, rel TEXT, dst TEXT,
  chunk_id INTEGER,                       -- provenance: which chunk asserted this edge
  PRIMARY KEY(src, rel, dst, chunk_id)
);
```

The flow: extract entities from the query, seed nodes, expand one or two hops, collect the chunks that assert the traversed edges, and merge that chunk set into the fusion pool alongside the BM25 and vector candidates. Provenance on every edge is non-negotiable — the graph *finds* the chunks, but the chunks remain the evidence the answer cites.

> **The hub problem.** One node — `aws`, `prod`, `production` — connected to everything makes two-hop expansion return half the corpus. Cap fan-out per node, penalize high-degree nodes during expansion, or drop hub-typed nodes from traversal entirely. Without this, graph retrieval degrades into noise precisely on the biggest corpora, which is where you wanted it most.
{: .prompt-warning }

Before committing to typed edges, try the cheap middle ground: **co-occurrence linking**, connecting entities that appear in the same chunk with no relation typing at all. It answers *"what is connected to X?"* surprisingly well, costs one SQL join, and its failures tell you whether typed relations are worth extracting.

## Automating graph construction

Hand-building a graph does not scale. Extracting triples with an LLM and trusting them does not survive contact with reality. The pipeline that works has five stages — and the emphasis is misplaced in most write-ups, because **linking, not extraction, is where graphs die**.

![Reachable facts versus hop count under fragmentation](/images/rag/06-entities-graphs/05-graph-coverage-vs-hops.png)
_With entities fragmented across surface forms, reachable facts collapse geometrically with hop count. At four forms per entity, a three-hop question sees under 2% of the graph._

**1 — Ontology first.** A small typed schema — node types, relation types, domain and range constraints — written *before* extraction. Constrained output is dramatically cleaner than "extract entities and relationships".

**2 — Extraction with a span gate.** Every triple must quote the text span that asserts it, and any triple whose span does not appear verbatim in the chunk is rejected. This single validation kills most hallucinated edges, and it costs one string comparison.

**3 — Blocking.** Entity resolution is pairwise-quadratic, so you never compare all pairs.

![Pairwise comparisons with and without blocking](/images/rag/06-entities-graphs/04-blocking-comparisons.png)
_Blocking turns five billion comparisons into single-digit millions._

**4 — Scoring and union-find.** Score candidate pairs on name similarity, type agreement, alias overlap, embedding similarity and shared neighbours. Merge above a high bar using union-find so merges are transitive. Route the uncertain middle band to human review; below the band, leave them split.

**5 — Incremental linking.** New documents link into the existing graph using the same blocking and scoring against existing canonical entities, rather than triggering a rebuild.

> **The merge policy is asymmetric.** A wrong merge — two real entities fused into one — silently corrupts every traversal through that node and is close to impossible to detect afterwards. A missed merge merely costs recall and is fixable the moment someone notices. Set the auto-merge threshold high, keep humans on the middle band, and prefer split over fused everywhere.
{: .prompt-danger }

Build order for the whole entity and graph investment, cheapest first — and stop at the first level that fixes the failures you actually observe: gazetteer plus alias table → chunk enrichment → co-occurrence edges → typed relations from the span-gated extractor → full entity-resolution machinery.

## GraphRAG and global questions

Everything above answers *local* questions: facts near identifiable entities. A different class of query defeats chunk retrieval entirely — **global, sensemaking questions** such as *"what are the dominant failure themes across this corpus?"* No chunk contains the answer, because the answer is a property of the corpus as a whole.

![The GraphRAG indexing and query pipeline](/images/rag/06-entities-graphs/06-graphrag-stages.png)
_An LLM builds the graph, communities are detected, summaries are written per community, and answering is map-reduce over relevant summaries._

An LLM extracts entities and relations with no predefined schema and builds the graph. Community-detection algorithms find clusters of densely connected entities. An LLM writes summaries for each community at multiple hierarchy levels, from narrow subtopics up to broad themes. At query time the engine selects the relevant community summaries, generates a partial answer from each, and a final call synthesizes them.

> GraphRAG's cost lives at *indexing* time, and it is steep — a published worked example prices a twenty-document sample at roughly $6, extrapolating past $500 for eighteen hundred documents, before a single query is asked. Reserve it for corpora where global questions are genuinely asked. For entity-anchored questions, the graph-hybrid retrieval above answers at a fraction of the cost. The two are complements, not competitors.
{: .prompt-warning }

The [next post](/Production-RAG-Grounded-Generation/) assumes retrieval finally works, and asks the question that then becomes urgent: is the answer actually supported by what was retrieved?

## References

1. Ofer Mendelevitch and Forrest Sheng Bao, *Hands-On RAG for Production*, O'Reilly Media, 2026
2. Edge et al., *From Local to Global: A Graph RAG Approach to Query-Focused Summarization*, Microsoft Research 2024 — [github.com/microsoft/graphrag](https://github.com/microsoft/graphrag)
3. Zaratiana et al., *GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer*, NAACL 2024 — [github.com/urchade/GLiNER](https://github.com/urchade/GLiNER)
4. Traag, Waltman and van Eck, *From Louvain to Leiden: Guaranteeing Well-Connected Communities*, Scientific Reports 2019
5. Christen, *Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection*, Springer 2012
