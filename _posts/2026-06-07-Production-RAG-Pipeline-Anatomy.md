---
layout: post
title: Production RAG - Anatomy of the Pipeline
image: /images/rag/01-foundations/01-rag-pipeline.webp
series: "Production RAG"
categories: ["Deep Learning", "RAG"]
tags: [rag, llm, retrieval, vector-search, system-design, embeddings]
published: true
---

Retrieval-augmented generation looks deceptively simple. Split the documents, embed the pieces, search for the closest ones, paste them into a prompt. A working prototype takes an afternoon. What takes considerably longer is the gap between that prototype and a system that stays accurate when the corpus grows from a hundred documents to a hundred thousand, when the PDFs stop being clean, and when someone asks a question whose answer is spread across three documents. This series walks through that gap, in build order.

{% include series-nav.html %}

> **Reference stack.** The reference implementation assumed throughout is a Go service using [sqlite-vec](https://github.com/asg017/sqlite-vec) for dense vectors, SQLite's [FTS5](https://www.sqlite.org/fts5.html) for BM25 keyword search, and a hosted model provider for embeddings, vision transcription and generation. None of the ideas are specific to that stack, but having a concrete one keeps the discussion honest about cost and failure modes.
{: .prompt-info }

## Why retrieval instead of fine-tuning

The first question worth settling is why the knowledge should live in an index rather than in the model's weights. Fine-tuning — continuing a pre-trained model's training on private data — is the alternative most teams evaluate first, and it has three structural problems when used as a knowledge store.

![RAG compared with fine-tuning](/images/rag/01-foundations/02-rag-vs-finetuning.webp)
_Fine-tuning puts knowledge in weights; RAG puts it in an index. The consequences show up in updates, access control and provenance._

**Expertise and risk.** Fine-tuning is genuinely difficult. It risks overfitting, regressions in the model's general competence, and interference with the vendor's own post-training (SFT, RLHF). Many teams also discover their data is neither large enough nor clean enough for it to work.

**Refresh cost.** Enterprise data changes constantly. If your corpus updates daily, you are looking at either daily GPU spend or a permanently stale model. Re-ingesting a changed document into an index costs a few cents.

**Access control.** This is the one that ends the debate in most organisations. Once you fine-tune on documents from engineering, HR, finance and legal, the knowledge is a single undifferentiated blob. There is no mechanism to prevent the model from answering an engineer's question using confidential HR content, because the weights do not remember which document a fact came from. With RAG, permissions are metadata on chunks, and the filter runs at query time before anything reaches the model.

> None of this forbids fine-tuning. A domain-tuned model can be an excellent *generator* inside a RAG stack. The mistake is using weights as the knowledge store.
{: .prompt-tip }

The same reasoning applies to the "long context kills RAG" argument. Dumping an entire corpus into a million-token context window is slow, expensive on every single query, and unfiltered — the model still has to find the relevant part, only now it pays for the whole corpus each time. Retrieval is what selects the right fraction of the corpus per question. Large context windows make RAG more useful, not obsolete, because they raise the ceiling on how much retrieved evidence you can afford to pass along.

## The two flows: ingestion and query

Everything in this series hangs off one pipeline with two halves. **Ingestion** runs once per document: parse, chunk, embed, index. **Query** runs per request: retrieve, fuse, rerank, generate.

![The end-to-end RAG pipeline](/images/rag/01-foundations/01-rag-pipeline.webp)
_A single query flows left to right. Each stage narrows and improves the candidate set produced by the stage before it._

Two details about the query flow are worth fixing in mind early, because they get skipped in most introductions.

### The retrieval query is not the user query

Consider the request *"Write a poem based on my travels in 2025."* It contains a command (*write a poem*) and a context need (*my travels in 2025*). If you embed the whole string and search with it, you retrieve poems — documents that look like the command — rather than travel notes. The system then writes a poem based on other poems.

The fix is **query rewriting**: transform the user query into a *retrieval query* that contains only the part that should hit the index, and leave the command in the generation prompt. This is one of the cheapest wins available on the query side, and it is the only query-side lever that changes *what gets retrieved at all*. Everything else — fusion, reranking — merely reorders candidates the retrievers already produced.

### Metadata travels with every chunk

Query rewriting can also emit a **metadata filter**: a structural constraint applied as a database predicate, entirely separate from similarity scoring. Suppose a chat log is ingested with each message tagged `{"who": "user"}` or `{"who": "AI"}`. The question *"According to the AI, where does the President of France live?"* splits into a semantic query plus a filter `who = "AI"`. User messages are excluded before scoring even begins.

That only works if the metadata survives ingestion. `doc_id`, source URI, page number and access-control tags have to travel from parser to chunk to index. Structure that looks like styling noise during parsing is frequently exactly the metadata a later filter needs — the `class` attribute in that chat log being the obvious example.

```sql
-- metadata is not decoration; three different features depend on it
CREATE TABLE chunks(
  id INTEGER PRIMARY KEY,
  doc_id TEXT,          -- citations, and cascading deletes on re-ingest
  page INTEGER,         -- citations again
  type TEXT,            -- text | table | image_transcript
  text TEXT
);
CREATE TABLE chunk_acl(chunk_id INTEGER, tag TEXT);  -- permission filtering
```

## The two governing questions: findability and sufficiency

A retrieval system can fail in exactly two places, and nearly every technique in the rest of this series defends one of them.

**Can the retriever find the right chunk?** Extraction fidelity, chunk boundaries, chunk enrichment, hybrid search, entity indexes and graph traversal all serve *findability*.

**Once found, does the chunk contain enough to answer?** Standalone chunks, repeated table headers, overlap between neighbours and heading ancestry all serve *sufficiency*.

A third question arrives the moment answers reach real users — *is the answer actually supported by what was retrieved?* — and it needs its own machinery, because generation can fail even when retrieval succeeded perfectly. That is [part 7](/Production-RAG-Grounded-Generation/).

> The defining property of RAG failure modes is that they produce no error. A broken text layer, a chunk boundary in the wrong place, an embedding model swapped without re-indexing — the system keeps returning fluent answers while quality quietly degrades. That is why so much of this series is about detection rather than construction.
{: .prompt-warning }

## What comes next

The next post starts where every real pipeline starts and where most of them silently break: getting trustworthy text out of a PDF. A PDF is not a document in any structured sense — it is a list of instructions for placing glyphs at coordinates — and the ways that goes wrong are more interesting than they sound.

## References

1. Ofer Mendelevitch and Forrest Sheng Bao, *Hands-On RAG for Production*, O'Reilly Media, 2026
2. [sqlite-vec — a vector search extension for SQLite](https://github.com/asg017/sqlite-vec)
3. [SQLite FTS5 full-text search](https://www.sqlite.org/fts5.html)
4. Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, NeurIPS 2020
5. [BM25 — The Scoring Function](https://en.wikipedia.org/wiki/Okapi_BM25), Wikipedia
