TEXFILE=dip
HITS=$(wildcard hits/*.tex)
FIGURES=$(wildcard figures/*.eps)
OTHER_FILES=$(wildcard *.sty) $(wildcard *.bst)

.phony: all clean view pdf
all: pdf view
pdf: $(TEXFILE).pdf

$(TEXFILE).pdf: $(TEXFILE).tex $(HITS) $(FIGURES) ref.bib $(OTHER_FILES)
	latexmk -bibtex -pdf $<
view: $(TEXFILE).pdf
	evince $^ 2>/dev/null
clean:
	latexmk -C
	rm -f *.log *.aux *.bbl *.blg
