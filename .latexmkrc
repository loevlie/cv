# latexmk config — `latexmk` builds main.tex; `latexmk -pvc` watches.
# Per CV typography KB: latexmk handles the rerun-detection for lastpage
# refs and biber automatically, so a single `latexmk` call replaces the
# pdflatex → biber → pdflatex × 2 dance.

$pdf_mode  = 1;
$pdflatex  = 'pdflatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';
$lualatex  = 'lualatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';

# Skim previewer — only consulted when `latexmk -pv` or `-pvc` is passed
# explicitly. We do NOT set $preview_continuous_mode here: that would
# force every `latexmk` invocation (including CI runs) to enter watch
# mode and hang. Use `make watch` (which expands to `latexmk -pvc`) for
# the local continuous-mode workflow.
$pdf_previewer  = 'open -a Skim';

# Default file when running `latexmk` with no argument
@default_files = ('main.tex');

# Cleanup ext list (latexmk -c)
$clean_ext = 'synctex.gz nav snm vrb run.xml bcf bbl bpx';
