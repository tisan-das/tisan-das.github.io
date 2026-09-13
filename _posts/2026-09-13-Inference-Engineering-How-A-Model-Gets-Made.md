---
layout: post
title: "Inference Engineering - Part 1: How a Model Gets Made"
image: /images/inference/01-how-a-model-gets-made/02-where-the-gradient-lands.webp
series: "Inference Engineering"
series_part: 1
categories: ["LLM", "Inference"]
tags: [llm, training, rlhf, rlvr, fine-tuning, alignment]
published: true
---

I kept running into large language model (LLM) systems and finding that I could *use* them without *understanding* them. That is an uncomfortable place to be: you end up accountable for behaviour you cannot explain, with no way to reason about it when something goes wrong.

So I started asking the awkward questions. Not "how do I deploy vLLM"; those have answers on the internet. *Why does vLLM need PyTorch at all? Is `ops:byte` even a legitimate unit? If decoder-only models threw away the encoder, where does the input representation live? What does `temperature` physically do to a number?*

What surprised me is how many of those answers converge on the same place: **moving bytes from memory is far slower than doing arithmetic on them.** Decoder-only architectures, the key-value (KV) cache, PagedAttention, continuous batching, FlashAttention, quantisation, speculative decoding. All of them are responses to that one constraint, wearing different clothes.

This series walks the path from training objectives down to IEEE 754 bit patterns and back. I have kept the confusions in, because the corrections turned out to be the most useful part.

{% include series-nav.html %}

> **Disclaimer.** This post is drafted with assistance from large language models (Claude Opus 5 and DeepSeek V4.1 Flash) based on conversations exploring LLM training and inference. All content has been reviewed, edited, and verified by a human author.
{: .prompt-info }

> **Where this started.** The series grew out of chapters 1 and 2 of Philip Kiely's [*Inference Engineering*](https://www.baseten.co/inference-engineering/) (Baseten Books, 2026), which is free to read online. This is not a chapter summary; it is the set of questions those chapters left me with, chased down to first principles.
{: .prompt-tip }

Part 1 is the groundwork: how a model gets built in the first place. Everything about serving assumes you know what artefact you are serving, and I had been hearing *pre-training*, *post-training*, *reinforcement learning (RL) training*, *safety training* and *fine-tuning* used interchangeably by people who clearly meant different things.

## Two eras: pre-training, then everything else

Here is the actual map, and the shorthand it uses: **SFT** is supervised fine-tuning; **RLHF** is reinforcement learning from human feedback; **RLVR** is reinforcement learning with verifiable rewards (an automated checker in place of the humans).

![The training pipeline from pre-training through to the aligned model](/images/inference/01-how-a-model-gets-made/01-training-pipeline.webp)

The same pipeline with the numbers attached:

| Stage | Objective | Scale | Share of compute |
|---|---|---|---|
| Pre-training | predict the next token | 10-30T tokens | ~90-98% |
| Mid-training | same, curated mix | 100B-2T tokens | a few % |
| SFT | same, masked to the answer | 10K-1M examples | well under 1% |
| Reward modelling | rank human preferences | 10K-1M pairs | under 1% |
| RLHF / RLVR | improve against a scorer | millions of rollouts | 1-20%, rising |

The data changes as much as the objective: web-scale text for pre-training, curated demonstrations for SFT, and pairwise comparisons for the reward model.

That compute split is worth sitting with. The stage that costs the most is the one that produces something you would never ship: a base model that continues documents rather than answering questions. The stages that produce the thing you actually talk to are a rounding error on the bill.

Percentages hide the thing that actually matters, though. Pre-training a frontier model is a capital project: tens to hundreds of millions of dollars of compute, run once, by a handful of organisations. An SFT or LoRA run on the same model is something one engineer can afford on a company card. **That gap, not the percentage split, is why fine-tuning is something everyone does and pre-training is something almost nobody does.**

The order is not a convention either. The reward model is trained on comparisons between outputs of the *SFT* model, so SFT has to exist first, and RL from a raw base model is much harder, because the model cannot yet produce the kind of text the scorer was fitted to judge. Each stage hands the next one the thing it needs.

One step sits before all of them: the **tokenizer**. The vocabulary a model reads and writes in is *learned* from the corpus rather than chosen, and it is fixed before pre-training begins. It is also what fixes the 128,000-way output that [Part 5](/Inference-Engineering-Sampling-From-The-API-To-The-Bits/) spends its whole length dealing with.

> **Mid-training is the one nobody talks about.** It is a second, smaller pre-training run on a curated mix (often adding long documents and extending the context window), and it is where a raw base model picks up much of its usable quality. It costs a few percent of the compute and gets none of the attention.
{: .prompt-tip }

## The thing that actually distinguishes the stages

The architecture never changes across these stages, and the loss function mostly does not. What separates them is **which positions are allowed to produce a gradient**: the same model, the same optimiser, and three different answers to "which tokens are we allowed to learn from?"

![Where the gradient lands in pre-training, SFT and RL](/images/inference/01-how-a-model-gets-made/02-where-the-gradient-lands.webp)

SFT uses *literally the same cross-entropy loss* as pre-training, cross-entropy being the standard measure of how far the model's predicted distribution over the vocabulary sits from the token that actually came next. Three things change: the data becomes `(prompt, ideal response)` pairs in a chat template, the loss is masked so gradients only flow from assistant tokens, and the dataset is tiny with a low learning rate.

This is why a thousand examples can produce a competent assistant. The LIMA result (*Less Is More for Alignment*) is the evidence: roughly a thousand good examples, and the model becomes useful. The capabilities were already latent in the base model; SFT tells it which of its many personas to adopt.

Be careful with the popular version of that claim, which says SFT teaches *format, not knowledge*. That is really a statement about **sample efficiency**, not a limit on what fine-tuning can do. A thousand examples move style and format. Installing facts takes orders of magnitude more data. Domain fine-tuning genuinely does install knowledge; that is the entire point of it.

> **There is a trap in that.** If you fine-tune on facts the base model does not actually know, you teach it the *style* of confident answering without the underlying knowledge. That is a well-understood way to manufacture hallucinations, and it is the most common way a first fine-tuning project goes wrong.
{: .prompt-danger }

> **The other trap is what you lose.** Continued training does not only add; it can degrade what was already there, under the unglamorous name *catastrophic forgetting*. A model trained hard on one narrow task can get measurably worse at everything else. This is a large part of why LoRA exists: by freezing the base weights and training only a small number of added parameters, you constrain how far the model is able to drift from what it already knew.
{: .prompt-warning }

## Why go beyond SFT at all

SFT has three structural limits, and they are limits of the method rather than of the effort you put in:

- It can only imitate, so it caps out at the demonstrator's quality.
- Every training example is positive. There is no signal anywhere about what a *bad* answer looks like.
- Writing ideal answers is expensive. Judging which of two answers is better is cheap.

RLHF attacks all three by learning a scorer and optimising against it, though it is worth being precise about the first one. The imitation ceiling does not vanish; it *moves* to the fidelity of the reward model, which is bounded by the quality and coverage of the humans who trained it.

And the reason it is a *learned* scorer, rather than humans in the loop, is the part worth dwelling on.

You need millions of gradient updates to move a model this far. No human can sit in that loop. So you collect a few tens of thousands of comparisons, train the reward model once, and then query it at GPU speed for as long as you like. **It is a cache of human judgement**: an expensive signal, amortised behind a cheap proxy.

That framing is worth keeping, because it predicts the failure mode a few paragraphs down. Every cache of a judgement is lossy, and optimising hard against a lossy proxy is the definition of reward hacking.

![Steps two and three of RLHF: train a reward model, then improve the model against it](/images/inference/01-how-a-model-gets-made/03-rlhf-two-phases.webp)

The reward model is usually the SFT model with its language-modelling head swapped for a scalar one, and it only ever learns a *relative* judgement: given two answers, which one a person would prefer. It never learns an absolute score, because nobody can produce one consistently, and preference is a far easier thing to collect than a rating.

The update that follows is usually **PPO** (Proximal Policy Optimization), and it carries one crucial constraint: the model is penalised for drifting too far from a frozen copy of itself.

> **That constraint is load-bearing.** Without it, the model sprints toward whatever degenerate text the reward model happens to rate highly, and you end up with something that has learned to please a scorer rather than a person.
>
> What this loop produces is a specific family of failure: the *personality* problems rather than the knowledge ones. Sycophancy, because raters prefer agreement. Verbosity bias, because raters prefer long answers. Collapsed output diversity, and a habit of hedging. Note what is *not* on that list: **hallucination is a pre-training and data problem**, and no amount of RLHF fixes it.
{: .prompt-warning }

**RLHF costs something even when it goes right.** Making a model more helpful measurably makes it worse at other things. The InstructGPT paper recorded exactly that, with regressions on particular tasks. The reason is simple: the training signal rewards what raters like, and raters are not measuring raw capability. The cost has a name: the **alignment tax**.

> **A shortcut worth knowing.** **DPO** (Direct Preference Optimization) skips the reward model entirely and optimises the model directly on the preference pairs. That removes the RL loop and much of its instability, at the cost of losing a reusable scorer you can point at many training runs. It is why the vocabulary diagram further down lists RLHF and DPO side by side.
{: .prompt-tip }

## RLVR: where reasoning models came from

The newer branch, and the reason "RL training" became a distinct term rather than a synonym for RLHF. The change is small to describe and enormous in consequence: **replace the learned scorer with a program.**

![RLHF scores with a learned reward model; RLVR scores with a program you can run](/images/inference/01-how-a-model-gets-made/04-rlhf-vs-rlvr.webp)

A learned scorer can be fooled. A unit test cannot be sweet-talked.

**RLHF** is reinforcement learning from human feedback; **RLVR** is reinforcement learning with verifiable rewards. The practical difference is where the reward comes from:

| | RLHF | RLVR |
|---|---|---|
| Reward comes from | a model fit to human rankings | a program you can run |
| Signal quality | soft, gameable | hard, checkable |
| Failure mode | sycophancy, verbosity | gaming the checker |
| Scales with | human labellers | compute |

**GRPO** (Group Relative Policy Optimization) is the algorithm most associated with it. Instead of training a separate value network to provide the baseline, it samples a *group* of completions for the same prompt and uses the group's mean reward as the baseline. That removes an entire model from the training loop, which matters enormously when you are doing millions of rollouts.

The empirical result is the interesting part. With only an outcome reward, and no supervision on the reasoning itself, models learn to produce long chains of thought, backtrack, and check their own work. Nobody demonstrated that behaviour to them; it fell out of being scored on whether the final answer was right. How much of that is genuine emergence versus the base model having already seen mountains of worked reasoning on the web is still argued, but the behaviour is real and reproducible.

Outcome-only reward has an obvious limitation: it tells you the final answer was wrong, and nothing about which step went wrong. That is what **process reward models** address, scoring each step rather than only the destination. It is a much denser signal, paid for by having to verify every step rather than just the endpoint. Outcome reward won the first round on cost; process reward is the current frontier.

## How you know any of it worked

None of these stages can be verified from the inside. A pre-training run reports a loss curve, and a falling loss does not tell you whether the model got better at anything you care about. So the pipeline is wrapped in evaluation: held-out benchmarks for capability, red-team suites for safety, and (for the RL stages) a close watch on whether the reward is rising because the model is improving or because it is learning to game the scorer.

The distinction that matters: **the training loss is what you optimise, and the eval is what you trust.** When the two diverge, the eval is right, and what you are watching is an optimisation pressure finding the gap in your proxy. Almost every failure mode described above shows up first as a gap between those two numbers, rather than as an obviously broken output.

## Safety training is not a stage

This confused me for a while, because it is always listed alongside the others as though it were a box in the pipeline. It is not. It is a thread running through every box.

| Stage | Safety work that happens there |
|---|---|
| Pre-training | data filtering: drop hazardous and private text |
| SFT | refusals, plus over-refusal counterexamples |
| Preference / RL | harmless data, Constitutional AI, red-teaming |
| Deployment | runtime guardrails: classifiers, monitoring (**not training**) |

Constitutional AI is the notable technique here: instead of humans labelling harmfulness, the model critiques and revises its own outputs against a written set of principles, and those revision pairs become training data. What that buys you is auditability: the criteria become text you can read and argue with, rather than the implicit taste of a labelling workforce.

Note the last row. Runtime guardrails are not training at all, and conflating them with alignment work is how teams end up believing a model is safe because there is a classifier in front of it.

## The vocabulary, untangled

This is the map I wish I had been given at the start.

![Training, pre-training, post-training and everything that is not training](/images/inference/01-how-a-model-gets-made/05-training-vocabulary.webp)

Two of these terms are umbrellas, not techniques, and that is most of the confusion. The figure is the structure; the definitions below are where the ambiguity actually lives:

- **Post-training**: umbrella for everything after pre-training. Not a technique. When someone says "we did post-training", they have told you almost nothing.
- **Fine-tuning**: any continued training of a pretrained model. Often used loosely as a synonym for SFT specifically, which is exactly why it is ambiguous.
- **Instruction tuning**: the same thing as SFT. Two names, one method.
- **RL training**: the preference and verifiable-reward stages, the last row of the training pipeline table near the top of this post.
- **Alignment / safety training**: the subset of work aimed at values and harmlessness, spanning data filtering through post-training into runtime.
- **Distillation**: training a smaller model to imitate a larger one's outputs. Often filed under post-training, but it is a training method rather than a stage of its own.

> **And one axis that is orthogonal to all of it:** full fine-tuning vs LoRA/QLoRA (low-rank adapters, which train a small number of added parameters rather than all of them). That is about *which parameters receive gradients*, not which stage you are in. You can do LoRA at the SFT stage or the RL stage. When someone says "we fine-tuned it", you have to ask both questions (which stage, and which parameters) before you know what they did.
{: .prompt-tip }

## What this sets up

Two things from this post matter for everything that follows.

The first is that **the artefact you serve is a fixed set of weights.** All the interesting training-time machinery (masked losses, reward models, preference penalties) is gone by the time an inference server touches it. What arrives is a few hundred gigabytes of numbers and an architecture description.

The second is that **the architecture never changed across any of those stages.** Pre-training, SFT and RLHF all run the same decoder-only transformer. Which means every performance property of that architecture (including the one this series is named after) was fixed long before anybody thought about serving it.

[Part 2](/Inference-Engineering-What-Actually-Runs-The-Model/) picks up there: what actually executes those weights, why "running a model" and "serving a model" are different disciplines, and where the first hard wall shows up.

### References

1. Philip Kiely, [*Inference Engineering*](https://www.baseten.co/inference-engineering/): Baseten Books, 2026. Free to read online.
2. [*Training language models to follow instructions with human feedback*](https://arxiv.org/abs/2203.02155) (Ouyang et al.): the InstructGPT paper. Its three steps are SFT, then a reward model, then PPO; the RLHF figure near the top covers steps two and three.
3. [*LIMA: Less Is More for Alignment*](https://arxiv.org/abs/2305.11206) (Zhou et al.): the thousand-examples result.
4. [*Constitutional AI: Harmlessness from AI Feedback*](https://arxiv.org/abs/2212.08073) (Bai et al.).
5. [*DeepSeekMath*](https://arxiv.org/abs/2402.03300) (Shao et al.): introduces GRPO.
6. [*DeepSeek-R1*](https://arxiv.org/abs/2501.12948): reasoning behaviour emerging from outcome-only rewards.
