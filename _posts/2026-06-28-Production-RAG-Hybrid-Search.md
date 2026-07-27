---
layout: post
title: Production RAG - Hybrid Search, Fusion and Reranking
image: /images/rag/04-hybrid-search/01-cosine-unit-circle.webp
series: "Production RAG"
categories: ["Deep Learning", "RAG"]
tags: [rag, embeddings, bm25, hnsw, reranking, vector-search]
published: true
---

Ask a RAG system *"how do I shut down an instance"* and keyword search returns nothing useful, because the documentation says "halt" and "stop". Ask it about `CEAMVCSRE3110002C` and semantic search drifts off into vaguely similar identifiers while keyword search finds the exact page instantly. Neither retriever is better. They have mirror-image blind spots, which is the entire argument for running both and merging the results.

{% include series-nav.html %}

## Embeddings and the dot product

An embedding maps text to a dense vector so that semantic proximity becomes geometric proximity. Retrieval ranks by cosine similarity — the angle between two vectors, ignoring magnitude.

![Cosine similarity on the unit circle](/images/rag/04-hybrid-search/01-cosine-unit-circle.webp)
_When vectors are normalized to unit length, the dot product is the cosine._

The identity `a·b = |a||b|cos θ` means that if both vectors have length 1, the dot product *is* the cosine. This is why production embedding models ship unit vectors: similarity becomes a bare dot product, which enables fast maximum-inner-product search, and magnitude noise disappears so only direction — meaning — matters.

A sentence-transformer bi-encoder tokenizes, runs a transformer, mean-pools the token vectors and normalizes. The magic is not the pooling; it is the **contrastive fine-tuning** that pulls paraphrases together and pushes unrelated text apart. `all-MiniLM-L6-v2` produces 384 dimensions and truncates input at around 256 tokens — note *truncates*, not chunks. Chunking is the ingestion layer's job, and a model that silently drops the second half of your chunk will not tell you about it.

The well-known blind spot: negation. "Start the cluster" and "stop the cluster" embed close together, because they share almost everything except the one word that inverts the meaning.

> **The embedding model is coupled to the store.** Queries must be embedded at search time by the same model *and version* that embedded the documents. Persist with one and reload with another and you get a silent failure — no error, just garbage similarity scores. Pin the embedding model version alongside the index, and store it on every row.
{: .prompt-danger }

If you move embeddings between services, skip JSON: it inflates floats three to four times. Base64 of the raw bytes is a fixed 1.33x and bit-exact — but decoding requires agreeing on dtype, endianness and count. In Python that is `np.frombuffer(b, '<f4')`; in Go it is `base64.StdEncoding` plus `binary.LittleEndian` plus `math.Float32frombits`, never a `float32()` cast.

## Sparse and dense

| | Sparse (BM25) | Dense (embeddings) |
|---|---|---|
| Dimensionality | Vocabulary size, mostly zeros | 384–4096, all non-zero |
| Matches on | Shared tokens | Meaning and proximity |
| Wins on | IDs, codes, proper nouns, rare exact strings | Synonyms, paraphrase |
| Blind to | Synonyms | Rare exact strings |

What makes keyword search fast is the **inverted index**: a map from term to the list of documents containing it — the transpose of the sparse term-document matrix. You touch only the query's terms, never the whole corpus. That is what powers FTS5 and every other BM25 engine.

Dense retrieval has no such shortcut, so exact nearest-neighbour search is O(N) per query. **HNSW** brings that to roughly O(log N) by combining a navigable small-world graph with a skip-list hierarchy of layers.

| Parameter | Controls | Trade-off |
|---|---|---|
| `M` | Links per node | Higher = better recall, more memory |
| `ef_construction` | Build-time search width | Higher = better graph, slower build |
| `ef_search` | Query-time search width | Higher = better recall, slower query |

> sqlite-vec does brute-force KNN, which is entirely fine up to roughly 10⁵–10⁶ vectors. Past that, graduate to an HNSW index — pgvector, Qdrant, Weaviate — where the graph prunes the search instead of scanning every vector. Choosing the distributed vector database on day one is a common way to spend three weeks on a problem you do not have yet.
{: .prompt-tip }

## Both arms in one SQLite file

```sql
CREATE TABLE chunks(id INTEGER PRIMARY KEY, doc_id TEXT, text TEXT);
CREATE VIRTUAL TABLE chunks_fts USING fts5(text, tokenize='porter unicode61');
CREATE VIRTUAL TABLE chunks_vec USING vec0(embedding float[384] distance_metric=cosine);

-- BM25: scores are NEGATIVE in FTS5, more negative = better
SELECT rowid, bm25(chunks_fts) AS score FROM chunks_fts
WHERE chunks_fts MATCH ? ORDER BY score LIMIT ?;

-- Semantic: sqlite-vec KNN; smaller distance = closer
SELECT rowid, distance FROM chunks_vec
WHERE embedding MATCH ? AND k = ? ORDER BY distance;
```

The two virtual tables join on a shared `rowid`. The FTS5 sign convention is worth a unit test on a known ranking — inverting it by accident produces a system that confidently retrieves the *least* relevant chunks, and everything downstream still works, so nothing errors.

## Fusion: RRF

Fusion merges two ranked lists into one. It is important to be clear about what it does not do: it adds no new relevance signal, it only recombines rankings the retrievers already produced.

Reciprocal Rank Fusion:

```text
score(d) = SUM over lists L of  1 / (k + rank_L(d))       # k ≈ 60
```

![Reciprocal Rank Fusion across two ranked lists](/images/rag/04-hybrid-search/02-rrf-fusion.webp)
_RRF uses ranks only. Documents found by both retrievers rise, without any score normalization._

| | RRF | Weighted average |
|---|---|---|
| Uses | Ranks | Raw scores |
| Needs normalization | No | Yes, and min-max is fragile |
| Document missing from one list | No penalty | Imputed as 0, so penalized |

RRF rewards consensus and handles a single-list find gracefully — an additive bonus, never a penalty. It also avoids the entire question of how to compare a negative BM25 score with a cosine distance, which is a genuinely annoying problem to solve properly.

> **Fusion cannot fix a shared mistake.** When both retrievers have the same blind spot — negation is the classic — both rank the wrong chunk highly, and RRF's consensus reward *amplifies* the error. Fusion has no independent view of relevance. Only a reranker does. That is the core reason you still need one after RRF.
{: .prompt-warning }

## Reranking

A reranker re-scores one candidate list using a stronger, independent judgment. Unlike fusion, it generates a genuinely new signal by re-reading the query against each document — and it uses the opposite architecture from the retriever.

![Bi-encoder versus cross-encoder](/images/rag/04-hybrid-search/03-bi-vs-cross-encoder.webp)
_Bi-encoder: encode separately, compare with cosine — scalable. Cross-encoder: encode jointly, read a score off [CLS] — accurate._

The cross-encoder concatenates `[CLS] query [SEP] doc [SEP]` into a single sequence, so every query token attends to every document token, and a linear head emits one relevance score. That token-level interaction catches exactly what a bi-encoder cannot: "stop" contradicting "start", a qualifier that inverts a claim, a date that does not match.

The framing worth internalising is that embedding similarity is computed *post hoc* between two independently encoded texts, and never exploits the attention mechanism at all. Joint encoding does. The price is one forward pass per candidate, which is why a reranker runs on the top-N shortlist and never on the corpus.

### MMR, the diversity reranker

Maximum marginal relevance dates to 1998 — redundancy in search results long predates LLMs. It reorders for *coverage* rather than relevance: each candidate earns points for query relevance and loses points for similarity to what has already been picked.

```text
MMR(d) = λ · sim(d, q)  -  (1 - λ) · max sim(d, d_selected)
```

![Top-k versus MMR selection](/images/rag/04-hybrid-search/04-mmr-diversity.webp)
_Top-k clusters near-duplicates around the query; MMR spreads its selections across the candidate cloud._

This matters more than it looks. Five chunks saying the same thing waste your context budget and give the generator no new information, while a sixth chunk holding the qualifier that changes the answer sits just below the cutoff.

## Chaining rerankers

Production stacks chain rerankers, because each one optimizes a different objective and the order is not commutative.

| Stage | Optimizes | Scope | Pool |
|---|---|---|---|
| 1. Cross-encoder | Relevance | Per-chunk | 50 → 20 |
| 2. MMR | Diversity | Per-set | 20 → 8 |
| 3. Custom rules | Business logic | Domain | 8 → 5 |

Three principles fix that order. Run cheap-and-crude before expensive-and-precise, on progressively smaller sets. Run diversity on an *already relevant* set, or MMR will faithfully diversify garbage. And put hard business rules last — permission filtering especially — so that nothing downstream can override them.

## Running a cross-encoder from Go

There is no first-class pure-Go cross-encoder: the tokenizer, the model and the forward pass are Python and PyTorch machinery. Three options:

| Option | Shape | Verdict |
|---|---|---|
| ONNX export | onnxruntime bindings plus a Go tokenizer | Real, but CGo and tokenizer-drift risk |
| Python sidecar | Wrap in FastAPI, call over localhost | **Recommended — zero drift** |
| Hosted API | Managed rerank endpoints | Least code; data leaves the box |

```python
from fastapi import FastAPI
from sentence_transformers import CrossEncoder

model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
app = FastAPI()

@app.post("/rerank")
def rerank(body: dict):
    pairs = [(body["query"], c) for c in body["chunks"]]
    return {"scores": model.predict(pairs).tolist()}
```

The tokenizer-drift risk in the ONNX path is worth spelling out: if your Go tokenizer disagrees with the one the model was trained with — on a subword split, on Unicode normalization, on how it handles an unknown character — scores degrade quietly and only on the inputs where they disagree. The sidecar costs one hop and removes the entire class of problem.

The [next post](/Production-RAG-Multimodal/) leaves text behind and looks at images, tables screenshotted into PDFs, and why the architecture that is cheapest to ingest is usually the most expensive to run.

## References

1. Ofer Mendelevitch and Forrest Sheng Bao, *Hands-On RAG for Production*, O'Reilly Media, 2026
2. Cormack, Clarke and Buettcher, *Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods*, SIGIR 2009
3. Carbonell and Goldstein, *The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries*, SIGIR 1998
4. Malkov and Yashunin, *Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs*, IEEE TPAMI 2020
5. Khattab and Zaharia, *ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT*, SIGIR 2020
6. [Sentence-Transformers cross-encoder documentation](https://www.sbert.net/examples/applications/cross-encoder/README.html)
