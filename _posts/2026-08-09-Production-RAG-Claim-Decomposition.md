---
layout: post
title: "Production RAG - Part 9: Splitting an Answer into Claims"
image: /images/rag/09-claim-decomposition/01-decomposition-stages.webp
series: "Production RAG"
categories: ["LLM", "RAG"]
tags: [rag, hallucination, evaluation, nlp, llm]
published: true
---

[Part 7](/Production-RAG-Grounded-Generation/) argued that a groundedness gate has to score atomic claims and take the minimum, because a five-sentence answer with one fabrication averages out to a passing score. It then moved on, having left the hardest part unexamined: what exactly *is* a claim, and how do you get one out of a paragraph reliably enough that a threshold means anything?

That is this post — the first that goes back to deepen a step the build guide had to state and move past, rather than adding a new one. Decomposition quality bounds everything downstream, an inconsistent decomposer makes your gate threshold noise, and almost none of the difficulty is where people expect it.

{% include series-nav.html %}

> **Disclaimer.** This post is drafted with assistance from large language models (Claude Opus 4.8 and DeepSeek V4 Pro) based on conversations exploring production RAG concepts. All content has been reviewed, edited, and verified by a human author.
{: .prompt-info }

## There is no canonical decomposition

Start with the admission that makes the rest tractable: **there is no correct way to split a text into claims.**

*"The reranker, which runs on Bedrock, cut p95 from 400ms to 180ms"* is one claim, or three, or six, depending on where you draw the line. None of those is objectively right. So the deliverable is not an algorithm — it is a **contract** you write down, plus machinery that enforces it consistently.

Consistency matters more than correctness here. If the same answer decomposes into four claims today and seven tomorrow, it passes your gate today and fails tomorrow for reasons unrelated to its content, and every threshold you tuned is measuring your decomposer's mood.

### The granularity contract

> One claim = one predicate applied to its arguments, with all restrictive modifiers attached, at the finest granularity that is still independently falsifiable **and** independently actionable.

Two tests operationalize it:

- **Falsifiability.** Could the context make this claim false on its own? *"There is a reranker"* fails — it is a presupposition, not an assertion. Splitting it out manufactures a claim that is trivially true and wastes a verification call.
- **Actionability.** If this claim failed, would you strike or fix it *separately* from its neighbours? If two fragments would always be repaired together, they are one claim.

The linguistic rule doing most of the work is **restrictive versus non-restrictive modification**. *"The reranker used in the hybrid path"* is restrictive — it identifies *which* reranker, so it stays attached. *"The reranker, which runs on Bedrock"* is non-restrictive — it *asserts* something, so it becomes its own claim.

### Granularity is a gate-strictness knob

This is the part that surprises people. Finer decomposition raises `n`, and under a minimum gate every extra claim is another draw against your verifier's false-positive rate — `P(pass) = (1 - fpr)^n`, the compounding from part 7.

Splitting one sentence into six claims instead of three roughly doubles that sentence's false-positive exposure while buying very little extra hiding-room reduction. **Over-decomposition is not the safe direction.** It feels rigorous and it quietly blocks correct answers.

## Climb a ladder; don't build the top rung first

| Level | Method | LLM calls | Stability | Catches |
|---|---|---|---|---|
| **L0** | Whole answer | 0 | perfect | almost nothing |
| **L1** | One claim per sentence | 0 | perfect | most of the win over L0 |
| **L2** | L1 + rule-based clause splits | 0 | perfect | the main hiding spot |
| **L3** | Staged LLM decomposition + validation | 1–2 per answer | needs measurement | compound and cross-sentence cases |

L1 is not a toy. Sentence-level units already break the averaging problem, cost nothing, and are perfectly reproducible. Ship L1 in shadow mode, measure your leak rate, then look at *where* the surviving fabrications actually hide. If they are mostly buried in compound sentences and non-restrictive clauses, L2 is a day of work with a dependency parser.

Build L3 when you have evidence you need it, not before.

## L3 is four operations, not one

The single biggest reason naive decomposition prompts fail is that *"split this into atomic facts"* asks the model to do four different jobs in one pass, so it does all four badly.

![The four staged decomposition operations, with their two exits](/images/rag/09-claim-decomposition/01-decomposition-stages.webp)
_Two exits, and only one of them discards text. That asymmetry is the design._

**Selection** asks only whether the sentence contains anything checkable. Discourse markers, questions, pure instructions and pure opinion drop out. Cheap binary classification, and on a typical answer it removes a substantial minority of sentences before any of the expensive stages run.

**Disambiguation** is the stage everyone skips and the one that determines your false-unsupported rate. It handles referential ambiguity (*"it"*, *"this"*, *"the service"* with several candidate antecedents) and structural ambiguity (attachment, coordination scope). The design rule that makes it work is counterintuitive: **when the sentence cannot be disambiguated confidently, do not guess — exit and keep it whole.**

A confidently wrong referent produces a claim verified against the wrong evidence, which can fail *or pass* incorrectly. Keeping the sentence as one coarse claim loses resolution, not coverage. That is why the abstain path in the figure still produces a claim, while the selection path does not.

**Decomposition** splits an unambiguous sentence into propositions. **Decontextualization** rewrites each to stand alone. Keeping these two separate matters because the second has a specific failure mode — dropping conditions. *"If TLS is enabled, the handshake adds 2 RTT"* must never decontextualize to *"the handshake adds 2 RTT."* The antecedent of a conditional, the temporal scope and the subject qualifier all have to ride along.

Every emitted claim should satisfy four properties: **atomic** (exactly one verifiable predicate), **decontextualized** (no dangling pronouns), **faithful** (the decomposer must not repair, sharpen or soften the answer), and **traceable** (carries the span it came from).

## When does a coordination split?

Almost every genuine decomposition bug is a coordination handled wrongly, and the scope rules are not intuitive.

The **distributivity test** is mechanical: does the sentence still mean the same thing if you state each conjunct separately? *"Supports OAuth and SAML"* — yes, split. *"Combines BM25 with embeddings"* — no, that is a collective predicate, and splitting it asserts two things the answer never said. Markers that signal non-distributive coordination: *together, combined, respectively, between them, each other*, and comparatives.

**Negation is the trap that bites hardest**, because it is asymmetric:

- `¬(X ∨ Y)` distributes. *"Doesn't support cross-encoders or multi-vector"* legitimately becomes two claims.
- `¬(X ∧ Y)` does **not**. *"Doesn't support both X and Y"* is a single weaker assertion; splitting it fabricates two stronger claims your answer never made.

![Deciding whether a coordinated phrase splits, and how negation inverts the rule](/images/rag/09-claim-decomposition/02-coordination-rules.webp)
_Check for negation first. Applying the distributivity test to a negated phrase gets the answer backwards on exactly the cases that matter._

| Construction | Example | Rule |
|---|---|---|
| Clause coordination | "A ships in June and B is deprecated" | Split |
| VP coordination, shared subject | "listens on 8080 and requires TLS" | Split, copy the subject |
| Distributive argument coordination | "supports OAuth and SAML" | Split |
| Collective / reciprocal predicate | "combines BM25 with embeddings" | Keep whole |
| Negated disjunction | "doesn't support X or Y" | Split (De Morgan) |
| Negated conjunction | "doesn't support both X and Y" | Keep whole |
| Conditional | "if ACLs are on, add 15%" | One claim; antecedent rides along |
| Modal or hedge | "may reduce latency" | Preserve the modal verbatim |
| Quantified statement | "all workers retry twice" | One claim; never instantiate |
| Comparative | "A is faster than B" | One claim; needs both referents |
| Non-restrictive relative, appositive | "the reranker, which runs on Bedrock, …" | Split off |
| Restrictive modifier | "the reranker used in the hybrid path" | Keep attached |
| Attribution | "the docs recommend X" | One claim, typed as attribution |
| List item | stem + bullet | One claim per bullet, stem carried in |
| Table cell | row × column | One claim per cell, headers carried in |

That last row matters if your chunker is row-atomic for tables, as [part 3](/Production-RAG-Chunking/) recommends: claims derived from tabular content should be row-scoped too, or claim granularity and evidence granularity disagree and you manufacture spurious unsupported verdicts.

### A worked example

> The hybrid retriever combines BM25 with sqlite-vec embeddings, and because the Bedrock reranker was added in March it now cuts p95 latency from 400ms to 180ms. It doesn't support cross-encoder scoring or multi-vector retrieval. If ACL filtering is enabled, expect roughly 15% additional overhead.

| Source | Claim emitted | Rule |
|---|---|---|
| "combines BM25 with sqlite-vec embeddings" | The hybrid retriever combines BM25 with sqlite-vec embeddings. | Collective predicate — one claim, not two |
| "because the Bedrock reranker was added in March" | The Bedrock reranker was added in March. | Causal adjunct asserts a fact — split off |
| "it now cuts p95 latency from 400ms to 180ms" | The Bedrock reranker cut p95 latency from 400ms to 180ms. | Coreference resolved; the before/after pair is one measurement |
| the *because* linking those two | *(policy choice)* The latency reduction was caused by the reranker. | Inferential — extract or fold, but always the same way |
| "It doesn't support … or multi-vector" | **Abstain** — kept whole as one claim | "It" could be the retriever or the reranker |
| "If ACL filtering is enabled…" | If ACL filtering is enabled, the hybrid retriever adds roughly 15% overhead. | Conditional: antecedent rides along; "roughly" preserved |

Note the second sentence. In isolation the De Morgan rule says split — but the referent is genuinely ambiguous, and disambiguation fires *first* and blocks the split. **That ordering is the entire point of staging.**

The fourth row is the one worth arguing about. Splitting a causal adjunct into two bare facts is lossy: the answer asserted that the reranker *caused* the improvement, and two independent claims never say so. Whichever way you rule, write it into the contract — an unstated policy here is how a decomposer quietly stops being faithful, and your own coverage check is what should catch it.

## The validation gauntlet

The decomposer is an LLM, so it hallucinates, drops content and quietly "fixes" things. Most of your decomposition quality comes not from a better prompt but from checking the output.

| Check | Catches |
|---|---|
| Span validity | Invented claims — source offsets must resolve, content words must overlap the span |
| Numeric fidelity | Silent rounding: every number, version and identifier in the claim appears in the answer after normalization |
| Entity fidelity | Invented entities not in the answer or the resolved-referent map |
| Anaphora | Failed decontextualization — parse for unbound pronouns and deictics |
| Atomicity | Under-decomposition — >1 finite verb with clause coordination |
| Triviality | Over-decomposition — bare existence assertions and tautologies |
| Coverage | Dropped content — content-word coverage of verifiable spans below threshold |
| Entailment | Content drift — answer ⊨ claim, via cheap NLI |
| Dedup | Facts repeated across sentences — embedding near-duplicate collapse |

**The fail-safe direction is the critical design choice.** A claim that fails validation falls back to the whole sentence; it is never discarded. Dropping it means that text never gets verified — a silent hole in a gate whose entire premise is that every proposition gets checked.

Numeric fidelity deserves the emphasis. A decomposer that turns *"cut p95 from 412ms to 180ms"* into *"cut p95 to roughly 180ms"* produces a claim that verifies as supported while the answer the user reads contains a number nobody checked. That is the worst available outcome: the gate reports green on text it never examined.

> **Use a different model than the generator.** Self-decomposition is tempting — the generator knows its own intent and has no coreference problem — but it is not adversarially robust. A generator that fabricated something will happily omit it from its own claim list. Decompose the *rendered* answer too, the one the user sees, after all post-processing, or your offsets point at text that no longer exists.
{: .prompt-danger }

Two more call-design details worth the line: give the abstain option a **schema slot** (`{"ambiguous": true, "reason": "..."}`), because a model that can only emit claims will emit a guessed one; and few-shot on the **traps** rather than the easy cases — six to eight examples covering negated conjunction, collective predicates, conditionals and non-restrictive relatives beats fifty ordinary ones.

## Measuring the decomposer

**Stability first.** Run the decomposer *k* times on the same answer at temperature 0 and compute Jaccard similarity of the normalized claim sets. Below about 0.85, the same answer sometimes passes and sometimes fails your gate for reasons unrelated to its content. Track it as a health metric — it drifts when you change models.

**Claim-count distribution.** A long right tail means some answers are getting shattered, and those are blocked at a much higher rate than their quality warrants. A distribution tight around 1.0 claims per sentence means your decomposer is silently doing L1, and you are paying LLM prices for it.

For quality proper you need a gold set — roughly 100 answers decomposed by hand — and then recall (fraction of gold claims present, matched by entailment rather than string), precision, atomicity rate and self-containedness rate. Expensive once, and there is no substitute.

> The metric that ultimately justifies the work is the downstream one: does **leak rate** fall when you move from L1 to L2 to L3? If it does not, finer decomposition is buying you claim count and false blocks, and nothing else.
{: .prompt-tip }

## What comes next

Decomposition produces the claims. The next post covers what they get verified *against* — the frozen context bundle, why retrieval must hand the verifier identifiers rather than text, and the re-ingest race that fails a correct answer for reasons that have nothing to do with the answer.

## References

1. Min et al., *FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation*, EMNLP 2023
2. Metropolitansky and Larson, *Towards Effective Extraction and Evaluation of Factual Claims* (Claimify), arXiv:2502.10855
3. Song et al., *VeriScore: Evaluating the Factuality of Verifiable Claims in Long-Form Text Generation*, arXiv:2406.19276
4. Wei et al., *Long-form Factuality in Large Language Models* (SAFE), arXiv:2403.18802
5. Chen et al., *Dense X Retrieval: What Retrieval Granularity Should We Use?*, arXiv:2312.06648
