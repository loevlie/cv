// Slide template — IBM Plex on Touying. Brand-matches the CV.
//
// Per the v5 slides research: Touying chosen over Beamer for sub-second
// compile, math sweet spot, and easy Plex configuration. Anthropic-talk
// aesthetic: black on white, one idea per slide, single navy accent,
// generous whitespace.
//
// Build: `typst compile slides/talk.typ`
//        `typst watch slides/talk.typ`     (live preview)

#import "@preview/touying:0.5.5": *
#import themes.simple: *

// --- Brand tokens (mirror cv/main.tex palette) -----------------------------
#let navy   = rgb("#0A2540")
#let ink    = rgb("#1A1A1A")
#let mute   = rgb("#6B6B6B")
#let rule-c = rgb("#C8C8C8")

// --- Theme ----------------------------------------------------------------
#show: simple-theme.with(
  aspect-ratio: "16-9",
  config-info(
    title: [Multimodal Tabular Foundation Models],
    subtitle: [Pretraining strategies for heterogeneous schemas],
    author: [Dennis Johan Loevlie],
    date: datetime.today(),
    institution: [ELLIS PhD \@ CWI \& UvA],
  ),
  config-common(
    new-section-slide-fn: none,  // no section dividers — Anthropic-style
  ),
  footer: self => align(right, text(size: 9pt, fill: mute)[
    #self.info.author #h(0.4em) · #h(0.4em) #self.info.date.display() #h(0.4em) · #h(0.4em) slide #context counter(page).display()
  ]),
)

// --- Typography -----------------------------------------------------------
#set text(font: "IBM Plex Sans", size: 24pt, fill: ink, weight: "regular")
#show raw: set text(font: "IBM Plex Mono", size: 20pt)
#show math.equation: set text(font: "New Computer Modern Math")  // Plex Math is OTF-only
#show heading: set text(font: "IBM Plex Sans", weight: "semibold", fill: navy)
#show heading.where(level: 1): set text(size: 36pt)
#show heading.where(level: 2): set text(size: 30pt)
#show link: set text(fill: navy)

// --- Title slide ----------------------------------------------------------
#title-slide[
  #text(size: 36pt, fill: navy, weight: "bold")[Multimodal Tabular Foundation Models]
  #v(0.4em)
  #text(size: 22pt, fill: mute)[Pretraining strategies for heterogeneous schemas]
  #v(2em)
  #text(size: 18pt)[Dennis Johan Loevlie]
  #v(0.2em)
  #text(size: 14pt, fill: mute)[ELLIS PhD \@ CWI \& UvA #h(0.6em)·#h(0.6em) #datetime.today().display()]
]

// --- Content --------------------------------------------------------------

== One idea per slide

Tabular FMs treat *every column* as a token.

The hard part is not the model. It is the *schema*.

== Why now?

#v(0.5em)

- Cross-table pretraining: TabPFN, TabuLa-8B, CARTE, GTL
- Multimodal grounding: text/image columns alongside numerics
- Open data: NeurIPS Table Representation Learning workshop

== Math is fine

#v(1em)

$ p(y | x) = sum_(z) p(y | z) thin p(z | x) $

#v(1em)

#text(size: 18pt, fill: mute)[Standard latent-variable factorization. Pretraining
learns $p(z | x)$ across schemas; downstream supervised fine-tuning conditions
on schema-specific $p(y | z)$.]

== Code, sparingly

```python
def encode(row, schema):
    return [
      tokenizer(col_name, value, schema[col_name])
      for col_name, value in row.items()
    ]
```

== Architecture

#v(2em)

#align(center)[
  #rect(width: 80%, height: 4cm, stroke: rule-c)[
    #align(center + horizon)[
      #text(fill: mute)[hero figure here — replace with `#image("hero.svg")`]
    ]
  ]
]

== Results

- TabPFN-bench: \+6.1 avg accuracy
- 14/14 downstream benchmarks improved
- Zero per-task fine-tuning

== Where we go next

1. *Larger schemas* — 1k+ columns
2. *Image-column pretraining* at scale
3. *Probabilistic head* — Bayesian uncertainty over predictions

#focus-slide[
  Thank you.
  #v(1em)
  #text(size: 18pt, fill: mute)[
    Slides + paper:\ #link("https://loevlie.github.io/cv")
  ]
]
