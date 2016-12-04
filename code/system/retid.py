#!/usr/bin/env python3

import os.path
import search

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: ./retid TRIEDIR", file=sys.stderr)
        sys.exit(1)

    triedir = sys.argv[1]
    tidmap = search.SeqReader(os.path.join(triedir, "tidmap")).seq
    gidmap = search.SeqReader(os.path.join(triedir, "groupmap")).seq
    gtids = search.SeqReader(os.path.join(triedir, "gtids")).seq
    gtlens = search.SeqReader(os.path.join(triedir, "gtlens")).seq

    # Find minimum term_id of each group
    min_gtids = [gtids[g] for g in gtlens[:-1]]

    infile = sys.stdin
    outfile = sys.stdout
    for line in infile:
        tup = map(int, line.strip().split("\t"))
        term_id, doc_id, pos, chpos = tup

        # Remap term_id to lexicographic order set by tidmap
        term_id = tidmap[term_id]

        # Use group_id map to obtain group_id
        group_id = gidmap[term_id]

        # Remove common component of group tids - that is minimum tid of a group
        term_id = term_id - min_gtids[group_id]

        outfile.write("\t".join(map(str, (group_id, doc_id, term_id, pos, chpos))))
        outfile.write("\n")

    outfile.flush()
