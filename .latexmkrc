# latexmk config — `latexmk` (no args) builds main.tex; `latexmk -pvc` watches
# Per CV typography KB: latexmk handles the rerun-detection for lastpage refs
# automatically, so a single `latexmk` call replaces `pdflatex && pdflatex`.

$pdf_mode  = 1;
$pdflatex  = 'pdflatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';
$lualatex  = 'lualatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';

# Use Skim on macOS — supports auto-refresh on file change
$pdf_previewer  = 'open -a Skim';
$preview_continuous_mode = 1;

# Default file when running `latexmk` with no argument
@default_files = ('main.tex');

# Cleanup ext list (latexmk -c)
$clean_ext = 'synctex.gz nav snm vrb run.xml bcf bbl';
