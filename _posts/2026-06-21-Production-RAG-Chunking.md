---
layout: post
title: "Production RAG - Part 3: Chunking for Retrieval"
image: /images/rag/03-chunking/01-chunk-boundary-failure.webp
series: "Production RAG"
categories: ["LLM", "RAG"]
tags: [rag, chunking, bm25, retrieval, ingestion]
published: true
---

A chunk is the smallest thing retrieval can return. You never get half a chunk, and never a chunk plus a bit of its neighbour. Whatever boundaries you draw at ingestion time are permanent — they define the set of answers your system is capable of producing at all. Which means a badly placed cut does not degrade an answer. It makes the answer impossible.

{% include series-nav.html %}

![A chunk boundary that destroys the answer](/images/rag/03-chunking/01-chunk-boundary-failure.webp)
_Neither chunk can answer the question. The information was in the corpus; the boundary removed it._

The goal of a chunker is therefore not "pieces of roughly 1,800 characters". It is that **every piece can stand alone**.

## Two judges, two different views

Chunks are selected by two mechanisms that look at completely different properties, and understanding both is what makes the rules below feel inevitable rather than arbitrary.

**Vector search** collapses a chunk to a single point in embedding space. A chunk containing two unrelated things lands somewhere between them, close to neither. A chunk stripped of context lands somewhere meaningless.

**BM25** counts matching terms and divides by length. The length correction is necessary — otherwise long documents would always win — but it overshoots at the extremes. With FTS5's defaults, the `dl / avgdl` term swings the denominator roughly fivefold between a 42-character fragment and a 1,780-character table.

![BM25 length normalization across chunk sizes](/images/rag/03-chunking/02-bm25-length-normalization.webp)
_Relative BM25 score for one identical term match at four chunk lengths. The orphan fragment nearly doubles the score of the full table it was cut from._

> The intuition worth carrying: BM25 is asking *"what fraction of this chunk is about your query?"* A 42-character chunk entirely about `32x` beats a 1,780-character chunk that is two percent about `32x`. This single mechanism is behind two of the three chunking rules below.
{: .prompt-tip }

## The strategy landscape

Five families, in rough order of sophistication:

| Strategy | Idea | Weakness |
|---|---|---|
| Fixed-size | Cut every N characters, with overlap | Breaks sentences and structure; overlap adds redundancy |
| Sentence / paragraph | Cut on linguistic boundaries | Uneven sizes; still misses higher-level context |
| Recursive | Hierarchy of delimiters: paragraphs → sentences → clauses | Depends on delimiter quality; still ignores semantics |
| Document-structure | Cut on headings and sections | Needs well-structured documents |
| Semantic | Cluster sentences by embedding similarity | Expensive; unpredictable sizes; hard to debug |

Two findings are worth knowing before you spend a sprint on the fancy end of that table.

First, published benchmark evidence (BEIR, RAGBench) shows fixed-size and semantic chunking performing **indistinguishably** on retrieval tasks. The caveat matters — those benchmarks contain short, pre-RAG-era passages, and the gap may well reopen on long documents — but it should make you spend the complexity budget where it demonstrably pays.

Second, when judging chunking through *generation* quality rather than retrieval metrics, remember the **"lost in the middle"** effect: LLMs attend most to the beginning and the end of their context. A chunking strategy can look worse purely because its chunks happened to rank into the middle of the context window. Do not conclude a strategy is better from generation metrics alone.

The chunker described below is document-structure chunking made table-aware. It captures the structural wins without semantic chunking's cost.

## Three content types, three different failures

Prose, tables and OCR text each violate "every chunk must stand alone" for a different reason. There is no single fix because there is no single failure.

| Content type | How it breaks | Treatment |
|---|---|---|
| Prose | Meaning flows across the cut | ~150-character overlap, snapped to word boundaries |
| Tables | Rows are meaningless without their header | Row-atomic; repeat header on every fragment |
| OCR text | Content is guessed, not read | Quarantined from overlap and heading inheritance |

### Prose: make the cut unclean

- **Snap to a word boundary.** Slicing at exactly 150 bytes cuts mid-word and mid-rune. A truncated token becomes a real FTS5 token that matches nothing. Walk back to the nearest space, and decode the last rune properly so multi-byte characters never split.
- **Never overlap into a table.** A tail landing inside a table prepends half a pipe row, which is broken markdown. Skip the overlap for that pair — a table chunk is already self-contained.
- **Store the overlap separately from the body.** Index `heading_path + overlap_prefix + body`, but display and cite only `body`. Retrieval gets the context benefit; the user never sees the same sentence twice.

### Tables: two rules prose does not need

A table's meaning is not in its rows — it is in the relationship between rows and header. So never cut mid-row (a half-row is corrupt, not merely incomplete), and repeat the header row on every fragment. A headerless fragment shows the answering model four bare numbers with no idea which one is a vCPU count and which is a price.

The subtler failure is the one the BM25 chart predicts. A table that spills 42 characters past the limit sheds a one-row runt, and that runt then *outranks* the table it came from on the very query it half-answers.

```go
const (
    runtFrac     = 0.25 // a chunk under 25% of max is a runt
    overflowFrac = 1.25 // merging may push a chunk to 125% of max
)

func coalesceRunts(chunks []chunk, max int) []chunk {
    for i := len(chunks) - 1; i > 0; i-- { // backward: a merge can create a new runt
        if float64(chunks[i].chars) >= runtFrac*float64(max) { continue }
        if float64(chunks[i-1].chars+chunks[i].chars) > overflowFrac*float64(max) {
            continue // pathologically long - leave it alone
        }
        chunks[i-1] = mergeChunks(chunks[i-1], chunks[i])
        chunks = append(chunks[:i], chunks[i+1:]...)
    }
    return chunks
}
```

> Accept a slightly oversized chunk rather than a runt. Then generalise the rule: enforce a hard minimum chunk size of around 200 characters everywhere, with the single exception of a document that produces exactly one chunk. Any chunk below that floor is a length-normalization hazard regardless of what produced it.
{: .prompt-tip }

Note the loop runs **backward over the whole chunk list**, not forward and not per-section. A mid-section table can shed a runt too, and merging one runt can make the previous chunk newly eligible.

### OCR text: quarantine, not repair

Prose and table chunks contain text *read* from the PDF. An OCR chunk contains text a vision model *guessed* from a picture. The risk is not incompleteness but wrongness — and overlap and heading inheritance are precisely the channels that would spread that wrongness into content you trust.

| How it would leak | Rule that blocks it |
|---|---|
| OCR text bleeds into a clean neighbour | No overlap into or out of transcribed sections |
| An invented heading becomes an ancestor | Transcribed headings are never carried forward |
| Page number lost from the citation | Headings demoted so `## Page N` survives |

> The through-line across all three rules: reconstructed content is welcome in the index, but it is never allowed to contaminate the retrieval signals of content you trust. A single marker string — `"(transcribed"` — carries this from the extractor, through normalization, into the chunker, into the database row, and out to the answering prompt, where it lets the model hedge instead of stating a possibly-misread number as fact. One string, four consumers, no shared schema.
{: .prompt-tip }

## Block segmentation

The single most important implementation change from a naive chunker: **chunk boundaries are only ever placed at block boundaries.** Split the section body on blank lines, classify each block, and treat the block as the atom. A fourteen-row pricing table is one ~900-character block — packed whole, or split at row boundaries, but never at character 1,800.

Block type is recoverable from the assembled markdown itself, which keeps chunking a pure function of a string:

```go
// A GFM table row is a pipe line whose NEXT line is the |---|---| separator.
// The two-line lookahead is what distinguishes a real table from prose with a pipe.
func isTableStart(line, next string) bool {
    return pipeLine.MatchString(line) && separatorLine.MatchString(next)
}

// A linearized table row: two or more 'Header: value' pairs joined by pipes.
var linearRow = regexp.MustCompile(`^[^|:]{1,40}: .+( \| [^|:]{1,40}: .+)+$`)

// OCR content announces itself in the heading the extractor wrote.
func isTranscribed(heading string) bool {
    return strings.Contains(heading, "(transcribed")
}
```

Resist the temptation to have the extractor emit typed spans instead. The moment extraction and chunking share a schema, every extractor change becomes a chunker change — and the OCR path has to fake structure it does not actually have.

## Heading ancestry

Prefixing each chunk with its heading ancestry is one of the cheapest large wins available. Chunk three of a section, stripped of its heading, is a floating paragraph the embedding cannot place. Prepending `Compute pricing > Page 12 > Reserved instances` fixes that for both retrieval arms at once.

Maintain a heading stack with one extra bit per frame — `inheritable bool`, set false for transcribed headings. An OCR-synthesized heading labels its own chunks perfectly well, but a vision model's invented heading for page 12 has no authority over native text on page 13.

## Three numbers to keep in config

`maxChunkChars` (1,800 is a reasonable default), `chunkOverlapChars` (150), and the runt floor (200 characters, or 25% of max). Log the chunk-length distribution after every ingestion run — a sudden shift in that histogram is either a corpus change or a regression, and you want to know which one before your users do.

## What comes next

The [next post](/Production-RAG-Hybrid-Search/) moves to the query side: what these chunks actually get compared against, and why you need two retrievers plus a reranker rather than one very good one.

## References

1. Ofer Mendelevitch and Forrest Sheng Bao, *Hands-On RAG for Production*, O'Reilly Media, 2026
2. Renyi Qu, Ruixuan Tu and Forrest Sheng Bao, *Is Semantic Chunking Worth the Computational Cost?*, EMNLP 2024
3. Liu et al., *Lost in the Middle: How Language Models Use Long Contexts*, TACL 2024
4. Thakur et al., *BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models*, NeurIPS 2021
5. [SQLite FTS5 — the BM25 implementation](https://www.sqlite.org/fts5.html#the_bm25_function)
