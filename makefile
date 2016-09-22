source = dip.tex
out = dip.pdf
.phony: clean view pdf

all: pdf view
pdf: clean $(out)
$(out): $(source)
	pdflatex $^
view: $(out)
	evince $(out) 2>/dev/null
clean:
	rm -f *.aux *.out *.log $(out)
