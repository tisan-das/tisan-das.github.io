---
layout: post
title: "Inference Engineering - Part 3: Where the Representation Lives"
image: /images/inference/03-where-representation-lives/02-where-representation-lives.webp
series: "Inference Engineering"
series_part: 3
categories: ["LLM", "Inference"]
tags: [llm, transformers, attention, decoder-only, kv-cache, architecture]
published: true
---

Many times, you would come across the claim that "the encoder builds an internal representation of the input." However, most modern LLMs are decoder-only. So do they just… not have one?

They do. The premise is what's wrong: building a representation was never the encoder's special job. Every transformer stack builds one, and in a decoder-only model it has a very concrete home: the key-value (KV) cache from [Part 2](/Inference-Engineering-What-Actually-Runs-The-Model/), the 320 KB per token that decides how many users fit on a GPU.

So the thing that seems to be missing is exactly what Part 2 spent its time budgeting memory for. This post connects the two, and shows why a single triangular mask is what makes that cache possible at all.

{% include series-nav.html %}

> **Disclaimer.** This post is drafted with assistance from large language models (Claude Opus 5 and DeepSeek V4.1 Flash) based on conversations exploring LLM training and inference. All content has been reviewed, edited, and verified by a human author.
{: .prompt-info }

## An encoder block and a decoder block are made of the same parts

Self-attention, an MLP (the feed-forward block), residual connections, normalization. Same code, same shapes. There are exactly two differences.

**The first difference is how the attention mask is used.**

![Bidirectional and causal attention masks side by side](/images/inference/03-where-representation-lives/01-attention-masks.webp)
_The first of the two differences, and in code it is a single line._

**The second difference is cross-attention.** In a classic encoder-decoder, the decoder has an extra attention sublayer where queries come from the decoder but keys and values come from the encoder's output. More on that below.

So "encoder" does not mean "the representation-building part". It means "the stack that reads with an unrestricted mask, and whose output another stack attends into."

## Where the representation actually lives

Feed a prompt into Llama and here is what physically exists in memory.

![A grid of layers by token positions, every cell a contextualized vector](/images/inference/03-where-representation-lives/02-where-representation-lives.webp)
_There is no smaller, purer representation hiding inside an encoder somewhere. This grid is it._

For an 80-layer model with a 1,000-token prompt, that grid holds 80,000 vectors. That **is** the internal representation.

> **This grid is what the KV cache stores.** At every layer, each cell is turned into a key and a value, and the **KV cache** keeps those. So the cache is this grid in projected form. When vLLM does prefix caching, it is reusing the model's representation of your prompt instead of rebuilding it. The 320 KB per token from [Part 2](/Inference-Engineering-What-Actually-Runs-The-Model/) is exactly this.
{: .prompt-tip }

## Why decoder-only won

Four reasons, roughly in order of importance.

**1. Every position produces a training signal.**

A model learns only from the positions where it makes a prediction and gets graded on it. Every other position is context: it gets read, but nothing is learned from it directly.

Take the sentence *The cat sat on the mat and slept*.

- **BERT (masked LM)** hides roughly 15% of the words, say *sat* and *mat*, and is graded only on guessing those two. The other six words are read and then contribute nothing to the grade.
- **GPT (causal LM)** is graded at every position: given *The*, predict *cat*; given *The cat*, predict *sat*; and so on to the end. That is seven graded guesses from the same eight words.

The causal mask is what makes this cheap. Because each position sees only the previous tokens, all seven guesses come out of **one** forward pass with no cheating: no position can peek at the next token it is supposed to predict.

![Masked LM trains on ~15% of positions; causal LM trains on essentially all of them](/images/inference/03-where-representation-lives/03-training-signal-density.webp)
_Two graded guesses against seven, from the same eight words._

When a pretraining run costs tens of millions of dollars, getting several times more learning from every token you pay to process decides the architecture.

**2. One format for everything.**

A decoder-only model has exactly one skill: given some text, predict what comes next. It turns out almost every task can be written that way:

```text
Translate to French: The cheese is good. →   Le fromage est bon.
Summarize: <long article> TL;DR:          →   <summary>
Q: What is the capital of Japan? A:       →   Tokyo
```

Chat is the same thing, with markers for who is speaking. A tool call is the model continuing the text with some JSON.

Compare that with BERT. To use it for, say, spam detection, you bolt a small extra layer (a **task-specific head**) onto the top and train it on labeled examples of spam and not-spam. Sentiment analysis needs a different head and different labeled data, and so on. One trained model per task.

With a decoder-only model, one model serves every task, and you pick the task by what you write in the prompt. The same property gives you **few-shot prompting** for free: put a few worked examples in the prompt, and the model continues the pattern without any retraining.

**3. Causal masking is what makes the KV cache safe to reuse.**

Each token can see only the previous tokens, never the next ones. So when a new token is generated, nothing about the previous tokens changes: their representations were *final* the moment they were computed, so they can be stored, and reusing them gives exactly the same result as recomputing them. In a bidirectional stack, every token also looks at the next tokens, so appending one new token changes the representation of every previous token, and you would have to recompute the entire sequence for every generated word.

**4. Simplicity at scale.**

One stack, one attention type, no cross-attention wiring, no encoder/decoder depth ratio to tune.

> **Reason 3 looks like a modeling choice, but the whole serving stack is built on it.** Because each token sees only the previous tokens, adding next tokens never changes what was already computed. The past is frozen. That is what makes the KV cache safe to reuse, and much of [Part 2](/Inference-Engineering-What-Actually-Runs-The-Model/) is built on top of that cache:
>
> - **Prefix caching.** Two requests that start with the same system prompt can share its cache. Whatever each request adds next cannot change it.
> - **Paged blocks.** The cache is written once, in small pages, as a conversation grows, and never has to be rewritten.
> - **Continuous batching.** Requests join and leave the batch between steps, each keeping its own cache, so no one's past is recomputed.
>
> Remove the triangular mask and every one of these either breaks or stops being worth doing.
{: .prompt-warning }

### What it genuinely gives up

While reading your prompt, each token sees only the previous tokens, never the next ones, even though the whole prompt is already there. A bidirectional model sees both sides, so it builds a richer representation of each token, and that is a real loss, not a rounding error.

Where it matters, encoders are still preferred: classification, named-entity recognition (NER), rerankers and text embeddings are still commonly done with BERT-family models. The workaround for getting embeddings out of an LLM is either the final token's hidden state, or stripping the causal mask off a pretrained decoder and continuing training, which is itself an admission that bidirectionality helps for understanding.

BERT's masked objective isn't a dead end either. Trained at every masking level instead of a fixed 15%, it becomes a generative model. That is masked diffusion, the subject of [Part 6](/Inference-Engineering-Diffusion-And-What-Ties-It-Together/).

> A note on terminology, since I got this wrong for months: it is **causal**, not *casual*. Causal as in cause-and-effect: information only flows forward in time. The word does the explaining.
{: .prompt-tip }

### Fill-in-the-middle: using the next tokens anyway

Generating left to right, a causal model can only add text at the end. But a lot of real work happens in the middle: inserting a missing sentence into a paragraph, or filling in the body of a function whose surrounding code already exists. Whatever goes into that gap has to fit the text after it too, not just the text before it, and a causal model never sees the text after it: it only sees the previous tokens.

The fix is to change the order of the text, not the model. During training, some documents are cut into three pieces and rearranged so the middle comes last:

```text
As written:   [....prefix....][..middle..][.......suffix.......]

As fed in:    <PRE> prefix <SUF> suffix <MID> middle
```

`<PRE>`, `<SUF>` and `<MID>` are special marker tokens. By the time the model reaches the middle, both the prefix and the suffix are already among its previous tokens, so it learns to write a middle that fits both. It is still ordinary next-token prediction, and the causal mask is untouched.

## Self-attention vs cross-attention

At the start of this post, we discussed that cross-attention was the second difference between an encoder block and a decoder block. It sounds like a separate mechanism, but it isn't: self-attention and cross-attention are the *same operation*, just fed from different places. To see why, start with what attention does.

### Attention from first principles

You have a sequence of vectors, one per token. Each needs updating using information from other tokens, but *which* ones depends on content, not position. In "the animal didn't cross the street because it was too tired," the word `it` needs `animal`; change `tired` to `wide` and it needs `street`.

So you need lookup by content. A Python dict does exact-match lookup; attention is the soft version, returning a weighted blend of every value rather than one.

Attention gives each token three vectors, each made by its own learned projection:

- **Query**: what am I looking for right now?
- **Key**: what do I advertise myself as, for others to find?
- **Value**: what do I actually hand over if selected?

**Why three projections rather than one?**

Because relationships between words run one way. In *red car*, `red` needs to look at `car` to know what it describes, but `car` barely needs `red`. If each token used the same vector for looking (query) and for being found (key), the score from `red` to `car` would always equal the score from `car` to `red`. Separate queries and keys let those two scores differ.

Value is kept separate for a similar reason: what makes a token easy to find is not the same as the information it should pass on.

### The one difference

![Self-attention takes Q, K and V from one sequence; cross-attention takes K and V from another](/images/inference/03-where-representation-lives/04-self-vs-cross-attention.webp)
_One line of code apart._

| | Self-attention | Cross-attention |
|---|---|---|
| Q comes from | the sequence itself | the target sequence |
| K, V come from | the sequence itself | a different source sequence |
| Matrix shape | N × N, square | N × M, rectangular |
| Causal mask | standard in decoders | not applicable: the source is complete |
| KV cache during decode | grows one row per token | computed once, never changes |
| Found in | everywhere | encoder-decoder models |

The KV cache row applies only to encoder-decoder models, since they are the ones that still use cross-attention. Their cross-attention keys and values come from the encoder output, which is computed once and never grows. Only the decoder's own self-attention cache grows as tokens are generated.

That sounds like an advantage decoder-only models give up, but they get almost the same thing. The prompt's part of their cache is also computed once, during prefill, and never changes, because the causal mask guarantees it. Only the newly generated tokens add to it. So the difference is small, and not enough to outweigh what the next section describes.

### Why decoder-only models threw cross-attention away

Cross-attention can be replaced with ordinary self-attention. Put the source and the target into one sequence, source first, and use a mask with two rules:

- each source token sees every other source token, previous and next;
- each target token sees the whole source, plus only the previous target tokens.

The target now reads the source just as cross-attention let it, with no second attention sublayer: only self-attention with a different mask. This setup is called **prefix LM**: both directions over the prompt, previous tokens only after it. It is not identical to an encoder-decoder, because both halves now share one set of weights, but it does the same job.

Decoder-only models go one step further and drop the special rule for the prompt: every token, prompt included, sees only the previous tokens. That costs some quality on the prompt, the loss described in the section "What it genuinely gives up" above. In return there is one attention pattern everywhere: one stack, no wiring between an encoder and a decoder, and one kind of KV cache. That is reason 4 from earlier, simplicity at scale.

Where cross-attention still lives: models that read one input and produce a separate output, especially when the input is a different kind of data. Examples are speech-to-text (Whisper), image-and-text models such as Flamingo, and translation and summarization models such as T5 and BART. Perceiver uses it for a different job, shrinking a very long input: a small, fixed set of vectors reads from the input through cross-attention, so the cost grows with the input's length instead of with its square.

## Encoders didn't die, they changed jobs

Open any modern multimodal model and there is an encoder sitting right there.

![A bidirectional vision encoder feeding a causal text decoder through a projector](/images/inference/03-where-representation-lives/05-encoders-changed-jobs.webp)
_Bidirectional for the thing that is already complete, causal for the thing being written._

The split is principled rather than historical. An image is finished when it arrives, so there is no reason to hobble the model with a mask. Text being generated is not finished, so causality is unavoidable.

## What this sets up

Three things carry forward.

**The representation is the KV cache**, so every memory-management trick in the serving stack is really representation management.

**Causality is why the cache is safe to reuse**, and prefix caching, paged blocks and continuous batching all build on that.

**Attention is one operation**, which is why a single kernel (FlashAttention) can serve self-attention, cross-attention, prefill and decode without knowing which it is being used for.

[Part 4](/Inference-Engineering-Memory-Bandwidth-All-The-Way-Down/) is the one the series is named after. It takes the `ops:byte` ratio I had been treating with suspicion, shows why dividing FLOPs by bytes is legitimate, and builds the roofline model out of nothing but milliseconds.

### References

1. Philip Kiely, [*Inference Engineering*](https://www.baseten.co/inference-engineering/): Baseten Books, 2026.
2. [*Attention Is All You Need*](https://arxiv.org/abs/1706.03762) (Vaswani et al.): still the cleanest statement of the encoder-decoder structure.
3. [*What Language Model Architecture and Pretraining Objective Work Best for Zero-Shot Generalization?*](https://arxiv.org/abs/2204.05832) (Wang et al.): compares architectures and objectives head-to-head; the causal decoder comes out best for zero-shot use after plain pretraining.
4. [*Efficient Training of Language Models to Fill in the Middle*](https://arxiv.org/abs/2207.14255) (Bavarian et al.): the fill-in-the-middle reordering.
5. [*Perceiver: General Perception with Iterative Attention*](https://arxiv.org/abs/2103.03206) (Jaegle et al.): cross-attention as a compressor.
