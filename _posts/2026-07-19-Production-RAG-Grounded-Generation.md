---
layout: post
title: "Production RAG - Part 7: Grounded Generation"
image: /images/rag/07-grounded-generation/01-correction-loop.webp
series: "Production RAG"
categories: ["LLM", "RAG"]
tags: [rag, hallucination, llm, guardrails, caching]
math: true
published: true
---

Retrieval can succeed completely and the answer can still be wrong. The model receives five relevant chunks and asserts a sixth thing that none of them support — a plausible number, a policy that does not exist, a qualifier it invented to make the answer read better. This is a different failure from anything in the previous six posts, and it needs its own machinery, because nothing upstream can detect it.

{% include series-nav.html %}

> **Disclaimer.** This post is drafted with assistance from large language models (Claude Opus 4.8 and DeepSeek V4 Pro) based on conversations exploring production RAG concepts. All content has been reviewed, edited, and verified by a human author.
{: .prompt-info }

## Hallucination detection as an NLI problem

The useful reframing is natural language inference. Premise: the retrieved context. Hypothesis: the generated answer. Does the premise entail the hypothesis?

Once framed that way, you do not need a large model to check it. A small model fine-tuned for factual consistency — Vectara's HHEM is the widely used example — returns a 0–1 score and runs in milliseconds. Dedicated evaluator models of this kind are faster, cheaper and *more consistent* than asking an LLM to judge the same question, which matters because you want to run this on every answer rather than a sample.

```python
from transformers import AutoModelForSequenceClassification

model = AutoModelForSequenceClassification.from_pretrained(
    "vectara/hallucination_evaluation_model", trust_remote_code=True)

# pairs are (premise, hypothesis) — here, (context, answer)
model.predict([(retrieved_context, generated_answer)])
# tensor([0.91])   ~0.9 grounded, ~0.1 unsupported
```

Two API details bite. It is `model.predict(pairs)`, not `model(pairs)`. And the current release is HHEM-2.1-Open, built on flan-t5-base — the older `sentence_transformers.CrossEncoder` path belongs to HHEM-1.0 and needs `revision="hhem-1.0-open"` pinned, which you do not want, because 1.0 caps the premise at 512 tokens and a retrieved chunk will routinely exceed that. The relation is also **asymmetric**: *"I visited Iowa"* counts as hallucinated given *"I visited the United States"*, while the reverse is consistent. Premise first, hypothesis second, always.

### Check claims, not whole answers

A five-sentence answer containing one fabrication averages out to a middling score that a whole-answer check waves straight through. So split the answer into atomic claims and score each one separately. What to do with the resulting numbers is then not a matter of taste, because grounding has a logical shape and the reduction falls out of it:

```text
grounded(claim)   ⟺   ∃ chunk ∈ context : supports(chunk, claim)
grounded(answer)  ⟺   ∀ claim ∈ answer  : grounded(claim)
```

Replace the boolean `supports` with a continuous score and relax the quantifiers. The standard continuous form of ∃ is `max`, and of ∀ is `min`:

$$ \mathrm{score} \;=\; \min_{\text{claim}} \; \max_{\text{chunk}} \; s(\text{chunk},\, \text{claim}) $$

Which is four lines once you score the full matrix in one batched call rather than a loop:

```python
import numpy as np

pairs  = [(chunk, claim) for claim in claims for chunk in chunks]
scores = np.asarray(model.predict(pairs)).reshape(len(claims), len(chunks))

per_claim = scores.max(axis=1)                          # is there ANY support
citations = [chunks[i] for i in scores.argmax(axis=1)]  # which chunk gave it
gate      = float(per_claim.min())                      # does EVERY claim hold
```

![Scoring every claim against every chunk, then reducing by max and min](/images/rag/07-grounded-generation/03-alignment-matrix.webp)
_The `argmax` along each row is free citation data — the chunk that best supports that claim._

Each operator earns its place through a monotonicity property. **Max is non-decreasing in the evidence set**: adding a chunk can only raise a claim's score, so retrieving more can never make a grounded claim look ungrounded. **Min is non-increasing in the claim set**: adding a claim can only lower the answer's score, so saying more can only expose you to more risk.

Averaging over chunks breaks the first property and quietly answers a question nobody asked — *how much of the retrieved context is about this claim?* That is a relevance measure, and under it improving recall degrades your groundedness number. It is how teams end up reducing `k` to make a dashboard look better.

> **A hard minimum has a price.** The answer passes only if every claim passes, so verifier false positives compound: at a 2% per-claim false-positive rate, a twenty-claim answer is flagged about a third of the time. That is not the design failing — it is the design finally measuring what the mean was hiding — but it is precisely why the action on failure has to be repair rather than rejection.
{: .prompt-warning }

> **Groundedness is not truth.** These models score consistency with the retrieved context, nothing more. If retrieval fetched an outdated document, a perfectly grounded answer is still factually wrong. Garbage in, grounded garbage out — retrieval quality is a separate and prior problem, which is why it got six posts before this one.
{: .prompt-warning }

### Thresholds, and what the score is worth

Use the score to *route*, not to decide: accept above roughly 0.8, reject below roughly 0.2, and escalate the band between them to an LLM judge. Tune both ends against your own labelled set by watching two curves — leak rate, and the share of claims you are paying LLM prices for. An internal engineering assistant and a customer-facing financial tool will not land on the same numbers.

That shape matters because the small model is weaker than its reputation. On RAGTruth-QA, the public benchmark closest to a RAG workload, HHEM-2.1-Open catches a little over half of the hallucinations and roughly a third of what it flags is wrong. It *matches* GPT-4 zero-shot there — 74.3% balanced accuracy against 74.1%, with GPT-4 in fact slightly ahead on recall — which tells you this is a remarkable model for 0.1B parameters, not that the problem is solved. **It is a tier in a cascade, not the gate.** Keep a deterministic check in front of it too: NLI-derived models are historically weak on negation and numbers, so a claim carrying a version string or a figure should hit exact matching before the model ever sees it.

> When the escalation band hands a claim to an LLM judge, make the judge **quote before it rules** — return the supporting sentence verbatim, then the verdict — and check in code that the quote actually appears in the retrieved text. A judge that answers "supported" but cannot produce a span that exists has confabulated the support, and you have converted a model-quality problem into a free deterministic catch. A judge citing a chunk id that was never in the context is louder still; log that case separately.
{: .prompt-tip }

## The correction loop

Detection tells you an answer is bad. Correction repairs it, and it is worth doing properly rather than simply regenerating — regeneration re-rolls the dice and can produce *new* hallucinations, in a loop that has no reason to terminate.

![The claim-level hallucination correction loop](/images/rag/07-grounded-generation/01-correction-loop.webp)
_Routing happens per claim, not per answer — which is the whole reason a partial repair is possible instead of a rewrite._

- **Decompose** the answer into atomic claims — one checkable fact each. Decomposition quality bounds everything downstream, so this step deserves more attention than it usually gets — enough that [part 9](/Production-RAG-Claim-Decomposition/) is devoted to it.
- **Score** each claim against the retrieved context.
- **Route** by score: high, keep; middle, minimally edit toward what the context actually says, then re-verify the edit; low, drop.
- **Reassemble** the surviving claims and apply an **abstention policy**. If too little survives, say so: *"the sources don't support a complete answer."*

> Never let the corrector *add* information. If the context lacks a fact, the claim is dropped — not replaced by the corrector's own knowledge. Otherwise you have moved the hallucination one layer down, where it is harder to see and carries an implicit stamp of verification. Absence of evidence is handled by dropping, never by asserting a negation the context also does not support.
{: .prompt-danger }

A correct refusal outranks a fluent fabrication. This is easy to agree with and hard to ship, because abstention looks like failure on every dashboard that counts answered queries. Track abstention rate as a *quality* metric, not an error metric, and it becomes much easier to defend.

## Routing and confidence gating

Not every query needs the frontier model. A router classifies difficulty and dispatches accordingly — cheap model for simple lookups, expensive model for genuinely hard synthesis — with an escalation path for when the cheap model's answer looks unreliable.

![Cascading LLM router with escalation](/images/rag/07-grounded-generation/02-llm-router-cascade.webp)
_The escalation edge is what makes router misclassification recoverable rather than permanent._

| Confidence signal | Cost | Note |
|---|---|---|
| Token logprobs | Free with generation | Well-calibrated for short factual answers |
| Self-rated confidence | One extra prompt | Crude; models overrate themselves |
| Groundedness vs retrieved context | One cross-encoder call | **Best single signal in a RAG stack** |
| Answer-set agreement | N generations | Strong, but N times the cost |

The third row is the interesting one, and it is specific to RAG. In a general chat product you have no ground truth to compare an answer against. In a RAG system you do: the retrieved context. That makes the grounding score do double duty — it is both your hallucination gate and your routing signal, from the same model call.

> Bias escalation toward *over*-escalating. The cost of wrongly escalating is a few cents. The cost of a wrong answer delivered confidently by the cheap model is trust, which you spend once. Log every escalation decision, too: the escalation rate is itself a health metric, and a sudden rise tells you the cheap model, the retriever, or the query mix has changed.
{: .prompt-tip }

## Semantic caching

An exact-string cache misses paraphrases, and users paraphrase constantly. A semantic cache embeds the query and serves a stored answer when a previous query lands within a similarity threshold. Hit rates on real traffic are substantial.

Three things to get right:

**The threshold is a correctness knob, not a performance knob.** Set it too loose and *"how do I start the cluster"* serves the cached answer for *"how do I stop the cluster"* — embeddings blur negation, as [part 4](/Production-RAG-Hybrid-Search/) covered. Start tight, around 0.97 cosine, and loosen only with measurement in front of you.

**Invalidate on ingest.** A cached answer is stale the moment the underlying documents change. Key cache entries by the document-set version, or flush affected entries during re-ingestion.

**Scope by permissions.** A cache shared across users with different access rights is a data-leak channel — the cache key must include the permission scope, or the cache must be per-principal. This is the kind of bug that passes every functional test and surfaces in an audit.

> Every one of the three failures above returns a fast, fluent, plausible answer. A cache is the one component in a RAG stack that can be simultaneously the biggest latency win and the most quietly dangerous, because it bypasses every guardrail you built in the rest of this post.
{: .prompt-warning }

## Citation provenance

If a chunk reaches the user's answer, what do you tell them about where it came from? In this pipeline the answer is three columns — `doc_id`, `page`, and `type` — and the last two take real work to get right.

### Storing versus showing

The chunk's `text` column serves two consumers that want different things: the search index and embedder want the body text only, while the answering prompt wants a header derived from the provenance columns.

```go
func contextBlock(c Chunk, d Doc) string {
    hdr := fmt.Sprintf("[%s] Source: %s, page %d", c.CiteID, d.Title, c.Page)
    if c.Type == TypeImageTranscript {
        hdr += " (transcribed from a scanned image — figures may be misread)"
    }
    return hdr + "\n" + c.Text
}
```

The header is derived at request time, not baked into the indexed text. That means you can rewrite the hedge wording, add a confidence score, or use different phrasing for a different model — without re-ingesting a single document.

### The citation round trip

```text
prompt block   →  [c_8f21] Source: report, page 4 (transcribed)
model answer   →  the scan shows 18,142 crore [c_8f21]
resolver       →  look up c_8f21 → doc_id, page, type
user sees      →  FY24 Report, p.4 — figure read from a scan
```

Two things make or break this loop. The model must emit the **chunk id**, not paraphrase the source — "according to the FY24 report" with no bracketed id resolves to nothing. Instruct citation by id, then validate: any id in the answer that isn't in the retrieved set is a fabricated citation.

Second, **the id you cite with is not the id you join on.** The integer primary key from [part 4](/Production-RAG-Hybrid-Search/) is a rowid — it is what FTS5 and `vec0` join against, and cascading deletes on re-ingest regenerate it, so a citation logged yesterday resolves to nothing today. Durable citations need a second column, derived from content rather than from insertion order:

```sql
ALTER TABLE chunks ADD COLUMN cite_id TEXT UNIQUE;   -- 'c_8f21'
-- computed in application code, not SQL:
--   cite_id = 'c_' + hash(doc_id, page, normalized_text)[:4]
-- a re-ingest that does not change the text produces the same value,
-- so a saved answer still resolves months later
```

`cite_id` is what enters the prompt and comes back in the answer; the integer key never leaves the database. If your citations are session-scoped — a chat nobody will revisit — the rowid alone is fine. Decide which of the two you are building, rather than discovering it when someone opens a six-month-old link.

### Three decisions to make explicitly

- **`page = null`.** Cite at document level, or drop the chunk from context. Never render it as "page 0."
- **Chunks that straddle pages.** Pick one rule — the page of the first character, or a stored range — and stick to it, because the user will click through and expect to see the sentence there.
- **Render the hedge from the column, not just the prose.** The OCR caveat currently appears only if the model chooses to write it, and models drop caveats under length pressure. Since `type` is on the row, put a badge on the citation chip in the UI — then the warning is deterministic and the model's prose is a bonus.

## What comes next

The [next post](/Production-RAG-Evaluation-And-Operations/) covers how you know any of this is working: retrieval metrics and their asymmetries, offline and online evaluation, agentic RAG, permission filtering, and the consolidated list of failures that produce no error.

## References

1. Ofer Mendelevitch and Forrest Sheng Bao, *Hands-On RAG for Production*, O'Reilly Media, 2026
2. [Vectara HHEM — hallucination evaluation model](https://huggingface.co/vectara/hallucination_evaluation_model)
3. Min et al., *FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation*, EMNLP 2023
4. Es et al., *RAGAS: Automated Evaluation of Retrieval Augmented Generation*, EACL 2024
5. Laban et al., *SummaC: Re-Visiting NLI-based Models for Inconsistency Detection in Summarization*, TACL 2022 — the alignment-matrix formulation
6. Chen et al., *FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance*, 2023
