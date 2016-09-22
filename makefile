sources = dip.tex

all: $(sources)
	pdflatex $^

.phony
clean:
	rm *.aux *.out *.log
