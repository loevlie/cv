DATE := $(shell date +%Y-%m)

# Variants live under variants/; each compiles in place.
VARIANTS := main_v3_stanford_margins main_v4_lualatex \
            main_v5_1_cochineal main_v5_2_libertinus main_v5_3_ebgaramond \
            main_v6_marginnote main_v7_michaillat

.PHONY: all cv industry variants dist watch clean distclean lint

all: cv industry

# Canonical academic CV (Plex, biblatex+publist, hyperxmp). latexmk runs
# biber automatically when bib files change.
cv:
	latexmk -pdf main.tex

# Industry CV (two-column sidebar, denser)
industry:
	latexmk -pdf industry.tex

# Build every variant in place under variants/
variants:
	@for v in $(VARIANTS); do \
	  echo "→ $$v"; \
	  ( cd variants && latexmk -pdf $$v.tex ) || exit 1; \
	done

# Stage versioned + latest copies in dist/
dist: cv
	@mkdir -p dist
	cp main.pdf dist/loevlie-cv-$(DATE).pdf
	cp main.pdf dist/loevlie-cv-latest.pdf
	@echo "Wrote: dist/loevlie-cv-$(DATE).pdf and dist/loevlie-cv-latest.pdf"

# Continuous mode — Skim auto-refreshes on save
watch:
	latexmk -pdf -pvc main.tex

# Clean aux/log files (keeps PDFs)
clean:
	-latexmk -c
	rm -f *.aux *.log *.out *.toc *.fls *.fdb_latexmk *.synctex.gz *.bbl *.bcf *.blg *.run.xml
	rm -f variants/*.aux variants/*.log variants/*.out variants/*.fls variants/*.fdb_latexmk variants/*.synctex.gz

# Wipe everything including PDFs (use with care)
distclean: clean
	rm -f *.pdf variants/*.pdf
	rm -rf dist/

# chktex lint pass on the canonical CV
lint:
	chktex -q -n1 -n8 -n36 main.tex
