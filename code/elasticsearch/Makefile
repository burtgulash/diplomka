.PHONY: all trigram standard clean
all: trigram standard
trigram:
	./$@/analyzer.sh
	./$@/mapping.sh
standard:
	./$@/analyzer.sh
	./$@/mapping.sh
clean:
	./delete_index.sh csfd_standard
	./delete_index.sh csfd_trigram
