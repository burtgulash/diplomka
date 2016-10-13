TEXFILE=dip

.phony: all clean view pdf
all: pdf view
pdf: $(TEXFILE).pdf
$(TEXFILE).pdf: $(TEXFILE).tex
	latexmk -pdf $(TEXFILE)
view: $(TEXFILE).pdf
	evince $^ 2>/dev/null
clean:
	rm -f *.aux *.out *.log $(TEXFILE).pdf
