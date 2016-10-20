TEXFILE=dip
HITS=$(wildcard hits/*.tex)

.phony: all clean view pdf
all: pdf view
pdf: $(TEXFILE).pdf

$(TEXFILE).pdf: $(TEXFILE).tex $(HITS)
	latexmk -pdf $<
view: $(TEXFILE).pdf
	evince $^ 2>/dev/null
clean:
	latexmk -C
