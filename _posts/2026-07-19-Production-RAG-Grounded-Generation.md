---
layout: post
title: "Production RAG - Part 7: Grounded Generation"
image: /images/rag/07-grounded-generation/01-correction-loop.webp
series: "Production RAG"
categories: ["LLM", "RAG"]
tags: [rag, hallucination, llm, guardrails, caching]
published: true
---

Retrieval can succeed completely and the answer can still be wrong. The model receives five relevant chunks and asserts a sixth thing that none of them support — a plausible number, a policy that does not exist, a qualifier it invented to make the answer read better. This is a different failure from anything in the previous six posts, and it needs its own machinery, because nothing upstream can detect it.

{% include series-nav.html %}

> **Disclaimer.** This post was drafted with assistance from large language models (Claude Opus 4.8 and DeepSeek V4 Pro) based on conversations exploring production RAG concepts. All content has been reviewed, edited, and verified by a human author.
{: .prompt-info }

## Hallucination detection as an NLI problem

The useful reframing is natural language inference. Premise: the retrieved context. Hypothesis: the generated answer. Does the premise entail the hypothesis?

Once framed that way, you do not need a large model to check it. A small cross-encoder fine-tuned for factual consistency — Vectara's HHEM is the widely used example — returns a 0–1 score and runs in milliseconds. Dedicated evaluator models of this kind are faster, cheaper and *more consistent* than asking an LLM to judge the same question, which matters because you want to run this on every answer rather than a sample.

```python
from sentence_transformers import CrossEncoder

model = CrossEncoder("vectara/hallucination_evaluation_model", trust_remote_code=True)
score = model.predict([(retrieved_context, generated_answer)])
# ~0.9 grounded, ~0.1 unsupported
```

Two things determine whether this actually works in production.

**Check claims, not whole answers.** A five-sentence answer containing one fabrication averages out to a middling score that a whole-answer check waves straight through. Split the answer into atomic claims, score each one against the context, and gate on the *minimum* rather than the mean.

> **Groundedness is not truth.** These models score consistency with the retrieved context, nothing more. If retrieval fetched an outdated document, a perfectly grounded answer is still factually wrong. Garbage in, grounded garbage out — retrieval quality is a separate and prior problem, which is why it got six posts before this one.
{: .prompt-warning }

Reasonable starting thresholds: 0.8 and above passes, 0.5–0.8 warns or triggers regeneration, below 0.5 blocks or abstains. Tune per product risk — an internal engineering assistant and a customer-facing financial tool do not want the same number.

## The correction loop

Detection tells you an answer is bad. Correction repairs it, and it is worth doing properly rather than simply regenerating — regeneration re-rolls the dice and can produce *new* hallucinations, in a loop that has no reason to terminate.

![The claim-level hallucination correction loop](/images/rag/07-grounded-generation/01-correction-loop.webp)
_Each claim is kept, minimally edited, or dropped. Every edit is re-verified before it replaces the original._

- **Decompose** the answer into atomic claims — one checkable fact each. Decomposition quality bounds everything downstream, so this step deserves more attention than it usually gets.
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

## What comes next

The [final post](/Production-RAG-Evaluation-And-Operations/) covers how you know any of this is working: retrieval metrics and their asymmetries, offline and online evaluation, agentic RAG, permission filtering, and the consolidated list of failures that produce no error.

## References

1. Ofer Mendelevitch and Forrest Sheng Bao, *Hands-On RAG for Production*, O'Reilly Media, 2026
2. [Vectara HHEM — hallucination evaluation model](https://huggingface.co/vectara/hallucination_evaluation_model)
3. Min et al., *FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation*, EMNLP 2023
4. Es et al., *RAGAS: Automated Evaluation of Retrieval Augmented Generation*, EACL 2024
5. Chen et al., *FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance*, 2023
