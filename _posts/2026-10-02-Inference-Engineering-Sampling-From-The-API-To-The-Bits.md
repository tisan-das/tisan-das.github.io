---
layout: post
title: "Inference Engineering - Part 5: Sampling, From the API Down to the Bits"
image: /images/inference/05-sampling/04-radix-select.webp
series: "Inference Engineering"
series_part: 5
categories: ["LLM", "Inference"]
tags: [llm, sampling, temperature, cuda, floating-point, gpu]
published: true
---

Three parameters sit between a trained model and its output: `temperature`, `top_k` and `top_p`. They are widely used and rarely defined precisely. All three act at the same instant and do the same job. The model has already run all of its layers and produced a score for every token in its vocabulary. These parameters act only on those final scores, after the model is done, to decide which token comes next. **They shape the choice, never the model.**

That makes them sound trivial. They are, arithmetically. But the **logit vector** (the model's raw, unnormalized scores) holds one entry per vocabulary token: about 128,000 numbers for a Llama-3-sized vocabulary, produced fresh for every sequence at every step. The last layer (the LM head) projects the final hidden state onto the whole vocabulary:

```
hidden state  [d_model, e.g. 4096]
      × LM head weight  [4096 × 128,256]
      = logits  [128,256]   → one raw score per possible next token
```

Per sequence, that is 512 KB in fp32 (a 32-bit float), and at batch 256 it is 128 MB that every pass has to drag out of high-bandwidth memory (HBM). So "find the largest k of 128,000 numbers" turns into a real engineering problem, and chasing it down leads all the way to how a float is laid out in memory.

{% include series-nav.html %}

> **Disclaimer.** This post is drafted with assistance from large language models (Claude Opus 5 and DeepSeek V4.1 Flash) based on conversations exploring LLM training and inference. All content has been reviewed, edited, and verified by a human author.
{: .prompt-info }

> **The short version.**
>
> - Temperature, top-k and top-p run after the model is done. They change which token gets picked, never the scores themselves.
> - Temperature raises every probability to the power 1/T. The dial is most sensitive below 1.0, and `T = 1` means different things on different models.
> - Top-k cuts by count, top-p by probability mass. Top-k runs first because it is cheaper, not because the order changes the result much.
> - On a GPU, top-k is a **radix select**: find one threshold by counting, never by comparing.
> - That works because a float's bit pattern, after one XOR, sorts exactly like the float itself.
{: .prompt-tip }

## Where the knobs actually sit

![The full path: tokens through every layer to logits, then temperature, softmax, top-k and top-p, and the draw](/images/inference/05-sampling/01-sampling-pipeline.webp)
_Everything expensive happens in the top row. Sampling only reads its final output._

- **Intermediate layers:** temperature, top-k and top-p never see their outputs (the hidden states).
- **The last layer:** sampling does not change it either. It only reads what that layer produces, which is the logit vector.
- **Weights:** these do not change at all. Changing the sampling settings never changes the logits: the same prompt produces the same scores for the first token at any temperature, top-k or top-p.

## Temperature, from first principles

Temperature is not a heuristic somebody invented for LLMs. The softmax **is** the Boltzmann distribution from statistical physics, borrowed wholesale:

| Physics | Language model |
|---|---|
| `P(state) ∝ exp(-E / kT)` | `P(token) ∝ exp(z / T)` |
| Energy of a state | Negative logit of a token |
| Temperature of the system | Sampling temperature |
| Low T: frozen in the ground state | Low T: locked onto the top token |
| High T: wanders over all states | High T: wanders over the vocabulary |

Divide every logit by `T`, then softmax. Take the ratio of any two tokens and the normalization cancels:

```
P_i / P_j  =  exp( (z_i - z_j) / T )
```

Halving the temperature doubles the exponent and **squares** the odds ratio. Doubling the temperature **square-roots** it. There is an even cleaner way to say it, since `exp(z_i/T) = (exp z_i)^(1/T)`:

```
P_i(T)  ∝  P_i(1) ^ (1/T)
```

Temperature raises every probability to the power 1/T, then renormalizes so they sum to 1 again.

![Temperature at 0.5, 1.0 and 2.0 on the same four logits](/images/inference/05-sampling/02-temperature.webp)
_At T = 0.5 the top token climbs from 0.64 to 0.86 and the tail nearly vanishes. At T = 2.0 it falls to 0.46 and the tail gains share._

| | 1st choice | 2nd | 3rd | 4th |
|---|---|---|---|---|
| T = 0.5 | 0.865 | 0.117 | 0.016 | 0.002 |
| T = 1.0 | 0.644 | 0.237 | 0.087 | 0.032 |
| T = 2.0 | 0.455 | 0.276 | 0.167 | 0.101 |

### The range, and what the ends mean

| Value | Effect |
|---|---|
| `T = 0` | Greedy: always the top token, no dice roll |
| `0 < T < 1` | Sharpened: same ranking, exaggerated gaps |
| `T = 1` | Exactly the distribution the model produced |
| `1 < T < 2` | Flattened: unlikely tokens get a real chance |
| `T > 2` | Approaches uniform over the whole vocabulary |

`T = 0` is a division by zero, so implementations special-case it to argmax. Negative temperatures are mathematically defined but would invert the ranking, so APIs reject them.

> **Temperature is not a calibrated, transferable number.** Anthropic's Messages API takes 0.0-1.0 with a default of 1.0; OpenAI's runs 0.0-2.0; open-source stacks generally leave it unbounded above. So `temperature=1.0` is the *maximum* on one API and the *midpoint* on another. Worse, `T = 1` leaves the model's distribution unchanged, and how spread out that distribution is depends on the model. A base model, trained only to predict internet text, spreads probability across many plausible continuations. RLHF (reinforcement learning from human feedback) concentrates it on the answers people preferred. So the same `T = 1` is far more random on a base model than on a chat model.
{: .prompt-warning }

An illustration, with made-up numbers for the next token after *"The capital of France is"*, both sampled at `T = 1`:

| | " Paris" | " a" | " located" | " the" | rest |
|---|---|---|---|---|---|
| Base model | 0.45 | 0.15 | 0.10 | 0.08 | 0.22 |
| Chat model | 0.97 | 0.01 | 0.01 | 0.00 | 0.01 |

The base model goes somewhere other than "Paris" more than half the time. The chat model almost never does.

### Diminishing returns

To see how the effect changes across the dial, take a toy vocabulary of eight tokens with logits 4, 3, 2, 1, 0, -1, -2 and -3, and compute the distribution at each temperature from 0.25 to 2.0:

| T | 0.25 | 0.5 | 0.75 | 1.0 | 1.25 | 1.5 | 1.75 | 2.0 |
|---|---|---|---|---|---|---|---|---|
| chance the top token wins | 0.98 | 0.86 | 0.74 | 0.63 | 0.55 | 0.49 | 0.44 | 0.40 |
| randomness (0 = always the top token, 1 = all eight equally likely) | 0.04 | 0.22 | 0.38 | 0.50 | 0.60 | 0.67 | 0.73 | 0.77 |

Compare two moves of the same size on the dial, 0.5 each. They are not the same size in behavior. Going from 0.25 to 0.75 drops the top token's chance from 98% to 74%: the model goes from almost never leaving its top choice to leaving it about one token in four. Going from 1.5 to 2.0 moves it only from 49% to 40%. The reason is that temperature divides the logits, so the real strength of the effect is 1/T, which falls from 4 to 1.33 in the first move but only from 0.67 to 0.5 in the second. **The dial is most sensitive below 1.0.**

### It does different things at different moments

Raising temperature will not make the model say Lyon instead of Paris: that gap is a logit difference of maybe 10, which even at `T = 2` leaves odds of about 150 to 1. What temperature affects are the thousands of moments in a paragraph where the model is genuinely torn between two reasonable phrasings.

> **"Temperature makes the model more creative" is misleading.** Raising it makes the model more willing to take its second-best option at every fork. Sometimes that reads as creativity. Sometimes it reads as a wrong fact, because factual recall also has second-best options.
{: .prompt-info }

### Small changes compound viciously

Every token is an independent draw. Chance of at least one off-track token in a response:

| tokens generated | 10 | 50 | 100 | 250 | 500 | 1000 |
|---|---|---|---|---|---|---|
| 1-in-1000 per token | 0.01 | 0.05 | 0.10 | 0.22 | 0.39 | 0.63 |
| 1-in-200 per token | 0.05 | 0.22 | 0.39 | 0.71 | 0.92 | 0.99 |
| 1-in-50 per token | 0.18 | 0.64 | 0.87 | 0.99 | 1.00 | 1.00 |

> **A 1-in-200 chance per token sounds safe. Over a 500-token answer it is a 92% chance of happening at least once.** And it is worse than independent, because once an odd token is emitted it enters the context and every subsequent token conditions on it. There is no undo. The right test for a temperature setting is a long generation, not a short one.
{: .prompt-danger }

### Settings that actually get used

| Task | Temperature | Why |
|---|---|---|
| Code, extraction, JSON, tool arguments, classification | 0 | There is one right answer, and every draw is a chance to be wrong. |
| Long reasoning chains | 0.5-0.7 | Fully greedy decoding over hundreds of tokens falls into repetition loops, where the highest-probability continuation is the phrase it just wrote. A little randomness is a *stability* feature here, not a creativity one. |
| Chat and explanation | 0.6-0.8 | Some variety in phrasing, without drifting far from the model's best guess. |
| Creative drafting | 0.9-1.0 | Prefer several samples at a moderate temperature over pushing the dial higher. |

> **One caveat for the infrastructure people: temperature 0 is not perfectly deterministic in a real serving stack.** GPU kernels sum floating-point numbers in an order that depends on how requests happened to be batched, and those tiny differences can occasionally flip which token wins. Reproducibility requires a fixed batch composition too.
{: .prompt-warning }

## Top-k and top-p

Both are scissors. They differ only in whether the cut is by **count** or by **mass**.

![Top-k keeps a fixed count; top-p keeps however many reach the mass threshold](/images/inference/05-sampling/03-topk-vs-topp.webp)
_Top-k ignores the shape of the distribution. That is its entire weakness._

**Top-k** keeps the `k` most likely tokens and discards the rest. With `k = 50`, the model always chooses among exactly 50 candidates, whether it is certain of the answer or torn between many.

**Top-p (nucleus)** sorts by probability, accumulates until the running total reaches `p`, and keeps exactly that set. The size is decided by the model's own confidence rather than by the caller: three candidates when it knows the answer, dozens when it does not. That adaptivity is why it became the default.

### Why is top-k applied before top-p?

The order looks backwards at first. Would it not be more natural to take the nucleus first and then trim it?

**For the surviving set, the order mostly does not matter.** Both filters sort descending and keep a *prefix* of the sorted list. The intersection of two prefixes is just the shorter prefix, so whichever cut lands earlier wins regardless of order.

The chosen order is an **engineering** decision. Top-p cannot run without a sorted cumulative distribution, and sorting 128,000 values every decode step per sequence is expensive. Top-k prunes the candidate list first with a cheaper *selection*, so the sort is over tens of items instead of six figures.

There *is* one real asymmetry. Most implementations apply top-k by setting rejected logits to negative infinity, and top-p then computes a softmax over what is left, which **renormalizes over the survivors**. So top-p sees inflated probabilities and reaches `p` sooner. Top-k-first is always at least as strict, never looser.

> **Practical advice: do not tune both.** Use top-p as the adaptive trim and leave top-k off, or set it generously (50+) purely as a hard ceiling against the very long tail. Two others worth knowing: `min_p` keeps any token whose probability is at least some fraction of the top token's, arguably a cleaner formulation of the same adaptive idea. Repetition and frequency penalties work differently, subtracting from scores of tokens that already appeared, *before* any of the above; they fight loops rather than tune randomness.
{: .prompt-tip }

## How does top-k actually run on a GPU?

The instinctive answer is a heap. `O(n log k)`. Both the complexity and the data structure are wrong, and a heap is close to the worst possible choice here.

| Approach | Work | Parallel depth | Used where |
|---|---|---|---|
| Full comparison sort | O(n log n) | O(log²n) as bitonic | rarely, as a fallback |
| Min-heap of size k | O(n log k) | **O(n log k), sequential** | CPU code |
| Quickselect | O(n) expected | O(n) | `std::nth_element` |
| Radix select | **O(n)** | **O(log n)** | GPU `topk` |

The heap's real problem is not its exponent: it is that its work is also its **depth**. Every sift-up depends on the previous one. On a chip whose entire premise is thousands of simultaneous threads, a strictly sequential algorithm uses one of them. A heap also does everything else a GPU dislikes: unpredictable branches inside a warp, scattered memory access, and a shared mutable structure needing coordination.

### What actually runs: radix select

The key reframe: **top-k does not need the sorted order. It needs the k-th largest value.** Once that number is known, "keep everything at or above it" is a single parallel comparison. So the problem becomes *find one threshold, by counting rather than comparing.*

![Radix select on sixteen values, finding the 5th largest in two passes](/images/inference/05-sampling/04-radix-select.webp)
_Two passes over sixteen numbers, and no two of them were ever compared._

Every step maps onto a primitive a GPU is built for: computing each value's bucket is a map, counting per bucket is a histogram (a reduce), finding the boundary bucket is a prefix sum over 256 counters, and keeping values above the threshold is another map.

At real scale (128,000 tokens, 32-bit keys, 8-bit digits, 256 buckets) the first pass examines all 128,000 values, the second about 500, the third about 2. The first pass is over 99% of the work: genuinely linear with a small constant. A comparison sort on the same data would be roughly 2.2 million comparisons, every one a data-dependent branch.

> **Modern kernels skip even that.** FlashInfer's sampling kernels avoid selection entirely: rather than finding the exact k-th largest, they **binary-search on the threshold value** (guess a cut, count in parallel how many clear it, adjust, repeat), then draw a token in the same kernel. Fewer passes over the logit vector, which is what the cost actually comes down to.
{: .prompt-tip }

### Why it matters at all

The logit tensor is 512 KB per sequence in fp32. At batch 256 that is 128 MB, and every pass costs a full HBM read.

And there is an asymmetry that makes this grow: **the weights are read once per decode step regardless of batch size, but the logit tensor scales linearly with batch.** Sampling is one of the few costs in decode that gets *relatively* more expensive as batch size grows, which, given everything in [Part 4](/Inference-Engineering-Memory-Bandwidth-All-The-Way-Down/), is exactly the direction everything else is being pushed.

## Detour: floating point from first principles

Understanding radix select requires understanding why floats can be bucketed by their leading bits at all. That turned into a detour worth writing down.

### The problem floats solve

Start with a fixed budget of bits. Spread uniformly, they give one spacing everywhere: with a step of 1, 0.5 cannot be written; with a step of 0.01, the largest number is 2.55.

The realization behind floating point: constant *absolute* precision is rarely what is needed; constant *relative* precision is. Measuring a planet, grams do not matter. Measuring a grain of sand, kilograms do not.

![The three fields of a float, and how exponent brackets divide into mantissa slots](/images/inference/05-sampling/05-float-anatomy.webp)
_Each exponent owns a bracket; the mantissa picks one of 16 evenly spaced slots inside it._

Two refinements explain the bits of the formula that look arbitrary.

**Why `1.mantissa`?** In proper scientific notation a number is normalized to one nonzero digit before the point. In binary the only nonzero digit is `1`, so the leading digit is *always* 1: storing it would waste a bit. It is implicit (the "hidden bit"), so four stored mantissa bits buy five bits of real precision.

**Why `exponent - 3`?** Negative exponents are needed for numbers below 1. Two's complement would work arithmetically but destroys integer ordering. Instead the exponent is stored **biased**: store `true exponent + 3`, so everything stored is non-negative and rises monotonically with the real exponent. The bias is always `2^(k-1) - 1` for a k-bit field: 3 for three bits, 127 for eight.

### The payoff: the bit pattern is a counter

Watch the transition at a bracket boundary. `0 011 1111` is 63 as an integer and 1.9375 as a float. Add one to the bit pattern: `0 100 0000` is 64, and 2.0, exactly one step of 1/16 further on. The mantissa rolled over and carried into the exponent, and the number sequence did not skip or jump.

Which gives the deep version of why the sorting trick works: **for non-negative floats, the bit pattern read as an integer is the *index* of that float in the sorted list of all representable floats.** Comparing bit patterns as integers is not a hack: it is comparing positions in an ordered enumeration. (Numerical code uses this directly: the ULP (unit in the last place) distance between two floats is just the difference of their integer bit patterns.)

### The bit trick, and why negatives flip everything

![Two problems with raw float bits, and the single operation that fixes both](/images/inference/05-sampling/06-float-sort-key.webp)
_Read the raw-int column top to bottom: it is out of order in two ways. The key column, after one operation per sign, is in order._

Adding a constant is strictly increasing, so positives keep their order and move to the top half. Subtraction from a constant is strictly *decreasing*, so negatives reverse their order (which is exactly the correction they needed) and land below all positives. **One operation, two problems.**

On a GPU an `if` is undesirable here, because a warp of 32 threads processing logits will contain a mix of signs and a branch means executing both sides serially. So real code computes both cases in one expression:

```c
uint32_t key(float f) {
    uint32_t bits = bit_cast<uint32_t>(f);
    uint32_t mask = (uint32_t)((int32_t)bits >> 31) | 0x80000000u;
    return bits ^ mask;
}
```

The function builds a mask, then XORs the bits with it. XOR flips a bit wherever the mask has a 1 and leaves it alone wherever the mask has a 0, so:

- a **positive** float needs the mask `0x80000000` (`1000…0000`): flip the sign bit only
- a **negative** float needs the mask `0xFFFFFFFF` (`1111…1111`): flip every bit

The mask is built from the sign bit in two steps, with no branch.

**Step 1: `(int32_t)bits >> 31` copies the sign bit into every position.** On a signed integer, `>>` is an **arithmetic** shift: each step moves every bit one place to the right, drops the rightmost bit, and fills the empty slot on the left with a copy of the sign bit. After 31 steps, every original bit except the sign bit has fallen off, and all 32 positions hold copies of it.

<details class="solution" markdown="1">
<summary>Step by step: the shift on the 8-bit toy</summary>

The same process on the 8-bit toy, shifting by 7 (sign bit in brackets):

```
negative: 1011 0000             positive: 0011 0000

start   [1]011 0000             start   [0]011 0000
>> 1    [1]101 1000             >> 1    [0]001 1000
>> 2    [1]110 1100             >> 2    [0]000 1100
>> 3    [1]111 0110             >> 3    [0]000 0110
>> 4    [1]111 1011             >> 4    [0]000 0011
>> 5    [1]111 1101             >> 5    [0]000 0001
>> 6    [1]111 1110             >> 6    [0]000 0000
>> 7    [1]111 1111  all ones   >> 7    [0]000 0000  all zeros
```

The hardware copies the sign bit because shifting a signed integer right divides it by 2, and a negative number has to stay negative: -8 is `1111 1000`, and `>> 1` gives `1111 1100`, which is -4.

</details>

The cast to `int32_t` is what selects this behavior. On an unsigned integer, `>>` is a **logical** shift that always fills with 0, so `1011 0000 >> 7` would give `0000 0001`, not all ones.

**Step 2: `| 0x80000000` forces the top bit on.** For a positive float, `0x00000000 | 0x80000000` is `0x80000000`. For a negative one, `0xFFFFFFFF` already has the top bit set, so it stays `0xFFFFFFFF`.

**Step 3: `bits ^ mask` applies whichever mask resulted.**

On real fp32 values:

| float | bits | `>> 31` | mask | key |
|---|---|---|---|---|
| -2.0 | `0xC0000000` | `0xFFFFFFFF` | `0xFFFFFFFF` | `0x3FFFFFFF` (1,073,741,823) |
| -1.0 | `0xBF800000` | `0xFFFFFFFF` | `0xFFFFFFFF` | `0x407FFFFF` (1,082,130,431) |
| 1.0 | `0x3F800000` | `0x00000000` | `0x80000000` | `0xBF800000` (3,212,836,864) |
| 2.0 | `0x40000000` | `0x00000000` | `0x80000000` | `0xC0000000` (3,221,225,472) |

Read top to bottom, the keys increase in the same order as the floats, so comparing them as plain unsigned integers sorts the floats correctly.

### Scaling up, and the edges

| Format | Sign | Exponent | Mantissa | Bias |
|---|---|---|---|---|
| Toy above | 1 | 3 | 4 | 3 |
| fp16 | 1 | 5 | 10 | 15 |
| bf16 | 1 | 8 | 7 | 127 |
| fp32 | 1 | 8 | 23 | 127 |

> **The bf16 row is worth a moment.** It has fp32's exponent field and a much shorter mantissa: same range, less precision. Converting fp32 to bf16 is just truncating the low 16 bits, and no value can overflow in the process. That property is most of why bf16 took over from fp16 in training. fp16's 5-bit exponent only covers about 6 × 10⁻⁸ to 65,504, so small gradients underflow to zero and large activations overflow to infinity, and fp16 training needs loss scaling to shift values into that window. bf16 has fp32's exponent and therefore fp32's range, and fp32 training never needed loss scaling: every value that fits in fp32 also fits in bf16. What bf16 gives up is precision, which training tolerates far better than values that vanish or explode.
{: .prompt-tip }

Two exponent patterns are reserved for special values: all zeros (`000`) and all ones (`111`). Both sit at the two ends of the bit-pattern range, which is what lets the "bits are a counter" property survive them. On the positive side of the toy format:

| bits | as integer | value | what it is |
|---|---|---|---|
| `0 000 0000` | 0 | 0 | zero |
| `0 000 0001` | 1 | 0.015625 | smallest denormal |
| `0 000 1111` | 15 | 0.234375 | largest denormal |
| `0 001 0000` | 16 | 0.25 | smallest normal number |
| `0 110 1111` | 111 | 15.5 | largest normal number |
| `0 111 0000` | 112 | infinity | |
| `0 111 0001` to `0 111 1111` | 113-127 | NaN | |

**Exponent all zeros: zero and denormals.** For this exponent the hidden leading 1 becomes a 0, so the value is `0.mantissa × 2^-2` instead of `1.mantissa × 2^(exponent - 3)`. Without this rule, the smallest positive number would be 0.25 and nothing would sit between 0 and 0.25, even though the values just above 0.25 are only 1/64 apart. **Denormals** fill that gap with 15 values spaced 1/64 apart: 0.015625, 0.03125, up to 0.234375. Zero is the case where the mantissa is zero too.

**Exponent all ones: infinity and NaN.** A zero mantissa means infinity. Any other mantissa means NaN ("not a number", the result of operations like 0/0 or infinity minus infinity).

**Why the counter still works.** Read the integer column top to bottom: zero gets the smallest pattern, the denormals run straight into the normal numbers (15, then 16), and infinity comes right after the largest finite value (111, then 112). Integer comparison still orders every one of them correctly.

**NaN is the exception.** NaN has no correct position, because it is not a number. Its patterns (113-127) are larger than infinity's, so integer comparison ranks a positive NaN above every real logit, and a top-k built on these keys would pick it as the most likely token. Plain float comparison does no better: every comparison involving NaN returns false. So sampling code checks for NaN separately instead of trusting the comparison.

## Quick reference

| Knob | What it does | Typical setting | Watch out for |
|---|---|---|---|
| `temperature` | Divides the logits by T: below 1 sharpens, above 1 flattens | 0 for exact tasks, 0.6-0.8 for chat | Not transferable across APIs or models |
| `top_k` | Keeps the k most likely tokens | Off, or 50+ as a ceiling | Ignores how confident the model is |
| `top_p` | Keeps the smallest set of tokens whose probabilities reach p | 0.9-0.95 | Runs after top-k, on renormalized probabilities |
| `min_p` | Keeps tokens with at least a set fraction of the top token's probability | 0.05-0.1 | Not offered by every API |

## What this sets up

Sampling is the cheapest step in decoding, and even here the cost comes down to bytes moved. The knobs themselves cost nothing: temperature, top-k and top-p are a little arithmetic on numbers that already exist. What costs time is reading those numbers out of HBM, 128 MB of logits at batch 256, once for every pass a kernel makes over them. So the engineering goes into touching the logits as few times as possible: radix select does nearly all its work in a single pass, and FlashInfer-style kernels filter and draw inside one kernel instead of writing intermediate results back to memory between steps.

[Part 6](/Inference-Engineering-Diffusion-And-What-Ties-It-Together/) closes the series with the live challenger to all of this (diffusion language models, which generate every position in parallel and bill per denoising step rather than per token) and then pulls the whole thread together.

### References

1. Philip Kiely, [*Inference Engineering*](https://www.baseten.co/inference-engineering/): Baseten Books, 2026.
2. [*The Curious Case of Neural Text Degeneration*](https://arxiv.org/abs/1904.09751) (Holtzman et al.): introduces nucleus (top-p) sampling.
3. [*Hierarchical Memory Layouts for GPU Radix Select*](https://arxiv.org/abs/1709.02520) and NVIDIA's CUB `DeviceRadixSort` documentation.
4. [FlashInfer](https://github.com/flashinfer-ai/flashinfer): the sorting-free sampling kernels.
5. [IEEE 754-2019](https://standards.ieee.org/ieee/754/6210/): the floating-point standard.
6. [*What Every Computer Scientist Should Know About Floating-Point Arithmetic*](https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html) (Goldberg).
