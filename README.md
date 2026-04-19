# Dennis Johan Loevlie — CV

LaTeX source for my academic CV.

- **Canonical academic CV**: [`main.tex`](./main.tex) → built to `dist/loevlie-cv-latest.pdf`
- **Industry CV**: [`industry.tex`](./industry.tex) — denser two-column variant
- **Variants**: [`variants/`](./variants/) — alternate font / layout experiments

## Build

```bash
make            # build canonical CV (main.tex)
make industry   # build industry CV
make academic   # build all academic variants
make watch      # latexmk -pvc continuous mode
make dist       # stage main.pdf into dist/ as loevlie-cv-YYYY-MM.pdf and -latest.pdf
make lint       # chktex pass on main.tex
make clean      # remove aux/log files
```

Requires TeX Live 2024+ (or MacTeX), with `biber`, `biblatex`, `biblatex-publist`,
`hyperxmp`, `bookmark`, `xurl`, `microtype`, and the IBM Plex font packages
(`plex-serif`, `plex-sans`, `plex-mono`).

## Add a publication

1. Append a `@article{...}` or `@inproceedings{...}` entry to [`publications.bib`](./publications.bib).
2. Set `author+an = {N=highlight}` so my surname renders in **bold** (where N is my position in the author list).
3. Tag with `keywords = {ml, ...}` or `keywords = {chem, ...}` to put the entry under the right subsection.
4. `make` — biber pulls the entry in automatically.

## Stack

- **Engine**: pdflatex (with `latexmk` driving the rerun for biber + lastpage)
- **Body**: IBM Plex Serif with old-style proportional figures
- **Headers / dates**: IBM Plex Sans (lining tabular figures)
- **URLs / code**: IBM Plex Mono
- **Bibliography**: `biblatex-publist` with `author+an` highlighting
- **PDF metadata**: `hyperxmp` (Adobe Bridge / Google Scholar / ATS pipelines)

## Variants

| File | Body font | Aesthetic move |
|------|-----------|----------------|
| `variants/main_v3_stanford_margins.tex` | Plex Serif | Bringhurst-correct measure (~75 chars/line, 0.85in side margins) |
| `variants/main_v4_lualatex.tex` | Plex Serif | LuaLaTeX engine; OTF + native Unicode |
| `variants/main_v5_1_cochineal.tex` | Cochineal | Real small caps (Caslon revival) |
| `variants/main_v5_2_libertinus.tex` | Libertinus Serif | Real small caps (Linux Libertine fork) |
| `variants/main_v5_3_ebgaramond.tex` | EB Garamond | Real small caps (classical Garamond) |
| `variants/main_v6_marginnote.tex` | Plex Serif | Tufte CV — dates in left margin |
| `variants/main_v7_michaillat.tex` | Plex Serif | Michaillat CV — section headers in left margin |

## CI

[`.github/workflows/build-cv.yml`](./.github/workflows/build-cv.yml) builds
`main.tex` on every push, uploads PDFs as artifacts, and (on `main`) deploys
to GitHub Pages. After enabling Pages, the latest CV lives at:

`https://loevlie.github.io/<repo-name>/loevlie-cv-latest.pdf`

## License

Source: MIT. CV content: All rights reserved.
