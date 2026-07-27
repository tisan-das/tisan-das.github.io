---
layout: post
title: "Production RAG - Part 2: Extracting Trustworthy Text from PDFs"
image: /images/rag/02-pdf-extraction/01-two-reader-architecture.webp
series: "Production RAG"
categories: ["LLM", "RAG"]
tags: [rag, pdf, ocr, text-extraction, ingestion]
published: true
---

A PDF is not a document in any structured sense. Rooted in PostScript, it is a list of drawing instructions: place this glyph at these coordinates, fill this rectangle, draw this image. There is no paragraph, no table, no heading — those are things a human infers from spatial arrangement. Recovering a *word* means clustering individual characters by their 2D coordinates. Recovering a two-column layout means analysing the alignment of every character on the page. Every extraction problem in this post follows from that single fact.

{% include series-nav.html %}

> **Disclaimer.** This post was drafted with assistance from large language models (Claude Opus 4.8 and DeepSeek V4 Pro) based on conversations exploring production RAG concepts. All content has been reviewed, edited, and verified by a human author.
{: .prompt-info }

## The parser landscape

Four families of tooling exist, and the right policy is a cascade rather than a choice.

| Approach | Examples | Where it fits |
|---|---|---|
| Classical parsers | pypdf, PyMuPDF, pdfminer.six | Born-digital PDFs with an intact text layer |
| Commercial extractors | Adobe PDF Extract, Unstructured.io | Complex enterprise document types |
| OCR | Tesseract, hyperscaler OCR APIs | Scanned pages with no text layer |
| Vision-language models | Any modern multimodal LLM | Slides, forms, infographics — as a fallback |

VLM parsing is the newest and the most tempting. It handles complex layouts that defeat classical parsers. But it is generative: it can hallucinate text, it usually cannot reproduce embedded images, and it is slow and expensive at corpus scale. The sensible policy is **cheapest successful parser first** — classical parsers, then OCR, then a VLM only for difficult, high-value documents. The rest of this post is that policy made concrete, with a per-page decision that gates the expensive path.

## Two readers over the same bytes

The core architectural move is to run two independent PDF readers over the same file and let each do what only it can do. This is not redundancy — each reader can see something the other structurally cannot.

![Two-reader extraction architecture](/images/rag/02-pdf-extraction/01-two-reader-architecture.webp)
_Both readers converge on one per-page interface. The mode decision downstream needs a signal from each of them._

A layout-aware Python reader such as `pymupdf4llm` gives you the preferred text: headings recovered from font size and weight, and tables emitted as GitHub-flavoured markdown. What it does not give you is a reliable answer to *"is there a big raster image on this page?"* A Go PDF library walking `Resources → XObject` gives you exactly that, plus a flat-text fallback.

### The subprocess seam

Most of the practical engineering lives at the Go-to-Python boundary. Spawn the converter once per document, pipe the PDF bytes to stdin, and read back a JSON array of per-page strings so page indices line up with the Go reader's.

```python
# pymupdf_convert.py - the entire Python side
import sys, json, pymupdf4llm, pymupdf

doc   = pymupdf.open(stream=sys.stdin.buffer.read(), filetype='pdf')
pages = pymupdf4llm.to_markdown(doc, page_chunks=True, header=False, footer=False)
# Page numbers come from the Go side as '## Page N', never from the PDF footer -
# running headers and footers are stripped above.
json.dump([pg['text'] for pg in pages], sys.stdout)
```

Keeping the Python side this small is what makes the system degrade gracefully. If `python3` or the library is missing, the subprocess returns nothing and every page falls through to the Go reader's flat text. Nothing errors — you simply lose table structure for that run.

> Graceful degradation is the right default, but it fails *silently*. A broken deploy can quietly destroy table quality for weeks with nothing surfacing in the logs. Emit a warning and a metric whenever the fallback path activates, and wrap the spawn in a timeout so one pathological PDF cannot wedge ingestion.
{: .prompt-warning }

## When the text layer lies

Before indexing a page you have to answer one question: can this page's text layer be trusted? Getting this wrong is the most expensive silent failure in the pipeline, because unusable tokens enter the index and stay there.

### Why extracted text can be wrong

A PDF stores glyph identifiers — numbers indexing into an embedded, usually *subset* font — and recovers text through a translation table called the ToUnicode CMap. Subset fonts renumber glyphs in order of first appearance, so glyph 7 might mean `c` in one document and `q` in the next. When the CMap is missing or wrong, the extractor still produces output by guessing, and what comes out is typically an arbitrary but internally consistent permutation of the alphabet — a monoalphabetic substitution cipher whose key is unique per font per document.

```text
original:   Unit consumption Rates
extracted:  Vojw dpotvnqujpo Sbuft
```

Two properties make this the worst kind of failure. Nothing errors — the extractor returns a string, and every layer reports success. And the output *looks* like text: no replacement characters, just letters. Skimming a log of extracted text, your eye slides right past it.

### Why the obvious statistics do not work

A letter swap preserves letter frequencies as a multiset, word lengths, spaces, punctuation and entropy. The classic index-of-coincidence test is *exactly invariant* under monoalphabetic substitution — permuted English scores like English — so it will confidently certify a corrupted page as clean.

The only property a letter swap destroys is whether the letters spell real words. A lexicon check or a character n-gram model are the only viable instruments. Everything else is permutation-invariant, and therefore blind.

### A cascade, not a single ratio

There are four distinct ways a text layer betrays you, and they have different symptoms:

| Failure | Cause | Symptom |
|---|---|---|
| Broken encoding | Subset font with no ToUnicode CMap | `U+FFFD`, control runes, private-use codepoints |
| CID passthrough | Extractor cannot map glyph IDs | Literal `(cid:142)` sequences |
| Shifted CMap | A wrong but valid mapping | Well-formed Latin letters that spell nothing |
| Scanned page | No text layer at all | Near-empty string |

A bad-rune ratio catches only the first. A scan has no runes at all, and a shifted CMap produces perfectly legal ASCII. So the detector is a cascade of cheap tests where any single one can condemn the page.

![The five-tier gibberish detection cascade](/images/rag/02-pdf-extraction/02-gibberish-cascade.webp)
_Tiers run cheapest first, and any one of them can route the page to full-page OCR._

```go
// Tier 1: runs on RAW text, before any normalization.
func badRuneRatio(s string) (ratio float64, counted int) {
    var bad int
    for _, r := range s {
        if unicode.IsSpace(r) { continue }   // evidence for neither side
        counted++
        switch {
        case r == utf8.RuneError:            // == '\uFFFD'; also invalid UTF-8
            bad++
        case unicode.IsControl(r):
            bad++
        case unicode.Is(unicode.Co, r):      // private use area
            bad++
        }
    }
    if counted == 0 { return 0, 0 }
    return float64(bad) / float64(counted), counted
}
```

> **Ordering gotcha.** Compute this ratio on the *raw* extracted text, before whitespace normalization runs. Normalization scrubs exactly the evidence this tier depends on. Normalize first and the ratio is permanently `0.0`, the OCR path never fires, and you index garbage forever with no error anywhere. This deserves an assertion in your test suite, not a comment.
{: .prompt-danger }

### The lexicon tier

This is the tier that catches the shifted-CMap case, and the one most likely to cry wolf on a technical corpus. The check itself is trivial — split into words, look each one up, count the fraction found. Everything difficult is in deciding which tokens are eligible to be judged.

| Why it cries wolf | The fix |
|---|---|
| The page is mostly a table | Score prose blocks only; cells are numbers and codes |
| Identifiers with digits | Reject any token containing a digit or path character |
| Short technical tokens | Ignore tokens under four runes (`vCPU`, `EKS`, `1x`) |
| Barely any text on the page | Insufficient evidence — assume clean and skip the tier |
| Domain jargon | Extend the lexicon from your own corpus |

**Length weighting is the single biggest accuracy win.** A four-letter permuted string lands on a real word by accident reasonably often; a nine-letter one essentially never does — the space is roughly 5.4 trillion strings against perhaps forty thousand real words. Weight each token by `len - 3` so long tokens carry the evidence, and fail open below a minimum evidence total.

> Splitting on `!unicode.IsLetter` is wrong for identifier-heavy text. Given `CEAMVCSRE3110002C` it yields `CEAMVCSRE` — a nine-letter token that misses the lexicon and, under length weighting, misses hard. Split on whitespace first, then reject the whole token if it contains digits.
{: .prompt-warning }

### Building the lexicon

Bigger is not better. Lexicon size trades sensitivity against specificity: a huge word list raises the accidental-hit rate on permuted garbage more than it helps clean pages, which already clear the threshold comfortably. A curated list of roughly twenty thousand common words beats a 300k-word list of inflections and archaisms.

The real gap is domain vocabulary, and the permutation's own properties give you a nearly perfect harvesting filter:

> The substitution key is unique per font per document, so a garbled token such as `dpotvnqujpo` appears in exactly one document and nowhere else. Real domain vocabulary appears across many. Requiring a candidate to occur in **three or more distinct documents** filters garbled tokens out almost completely — without ever needing to know which pages were garbled in the first place.
{: .prompt-tip }

### Calibration

This tier earns its complexity because the two populations separate unusually well. Permuted text does not score somewhat lower than English; it scores near zero.

![Lexicon hit-rate score bands](/images/rag/02-pdf-extraction/03-lexicon-score-bands.webp)
_When the threshold sits in a wide empty valley, its exact value barely matters._

Expect clean *technical* prose to land lower than general English — roughly 0.50–0.80 with a 20k-word lexicon, against 0.80+ for a novel. That gap is domain vocabulary, which is why the harvest step matters. If your own measurements show the two bands overlapping, the preprocessing is wrong — usually tables leaking into the token stream — and no threshold will save you.

Do not guess thresholds. Dump per-page signals as JSONL during ingestion, histogram them over a few hundred real pages, and look for the valley. And you never need to *find* garbled PDFs to test with: manufacture perfectly labelled data by applying the same transformation the broken font applies. Shuffle the alphabet with a seeded RNG, leave digits, punctuation and whitespace untouched — that is faithful to the real failure. Garble a hundred clean pages with a few fixed seeds and assert in CI that every clean page scores above threshold and every garbled variant below.

## The per-page decision

Two signals — the gibberish verdict and the image area — classify each page into one of three modes.

![Per-page transcription mode decision](/images/rag/02-pdf-extraction/04-page-mode-decision.webp)
_The expensive vision path is gated behind this decision, so you pay vision rates only on pages that need them._

`FIGURES` mode is where the two readers combine on a single page, and it is the scenario the design was tuned for. On a pricing page, the Python reader extracts the surrounding prose cleanly, but the actual rate numbers are baked into a large raster image it cannot read. The Go reader reports the image, `FIGURES` fires, and the output carries both: clean prose under `## Page N`, plus a figures-only transcription appended under `## Page N (transcribed figures)`. `REPLACE` is the harsher relative — when the text layer itself is garbage, OCR replaces the whole page.

Three refinements are worth building in from the start:

- **Tier 0 is asymmetric.** No text *and* no image is a genuinely blank page, and OCR would spend a vision call to produce nothing. No text *with* a big image is a scan. Same ratio, opposite action — the second reader's image signal disambiguates.
- **Add a document-level prior.** If more than ~60% of a document's pages landed in `REPLACE`, it is a scan throughout; promote the borderline pages too. Documents are homogeneous, and a page-independent classifier throws that information away.
- **Persist the decision.** Store the mode, the signal values and an `extractor_version` per page. Re-ingestion becomes idempotent, decisions are auditable months later, and a threshold change tells you exactly which documents need re-extraction.

> The cost asymmetry should drive where you put the thresholds. A false positive — a clean page sent to OCR — costs one vision call and slightly worse text. Loud and bounded. A false negative — a garbled page indexed as clean — puts unsearchable tokens in the keyword index and a meaningless vector in the vector index. Silent, permanent, and degrading every query that should have hit that page.
{: .prompt-tip }

## Three table representations, deliberately

How a table gets extracted depends entirely on where it came from, and it is worth keeping three renderings rather than forcing one:

| Source | Extractor | Output shape |
|---|---|---|
| `.xlsx` / `.csv` file | Direct linearization | `Header: value \| Header: value` rows |
| Born-digital PDF | Layout-aware parser | GFM pipe table |
| Raster image or garbled font | Vision OCR | `Header: value` rows, by prompt design |

Normalising these into one schema means re-parsing structure you have either already lost or already have. Keeping extraction and chunking decoupled through plain text, rather than a shared typed schema, is precisely what lets the OCR path participate at all, since a vision model produces prose and nothing else.

## What comes next

The chunker in the [next post](/Production-RAG-Chunking/) does not care which of the three representations it receives — it recognises "this is a table" from the text itself.

## References

1. Ofer Mendelevitch and Forrest Sheng Bao, *Hands-On RAG for Production*, O'Reilly Media, 2026
2. [PyMuPDF and pymupdf4llm documentation](https://pymupdf.readthedocs.io/)
3. [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
4. [PDF 32000-1:2008 — Document management, Portable Document Format](https://www.pdfa.org/resource/pdf-specification-archive/)
