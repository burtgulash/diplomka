#!/usr/bin/env python3

import os.path
from mktrie import SeqWriter

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: ./linearize DOCSDIR", file=sys.stderr)
        sys.exit(1)

    docsdir = sys.argv[1]
    groupped_docs = SeqWriter(os.path.join(docsdir, "gdocs"))
    groupped_tids = SeqWriter(os.path.join(docsdir, "gtids"))
    groupped_pos = SeqWriter(os.path.join(docsdir, "gpos"))
    groupped_chpos = SeqWriter(os.path.join(docsdir, "gchpos"))

    infile = sys.stdin
    for line in infile:
        tup = map(int, line.strip().split("\t"))
        group_id, doc_id, term_id, pos, chpos = tup

        groupped_docs.write(doc_id)
        groupped_tids.write(term_id)
        groupped_pos.write(pos)
        groupped_chpos.write(chpos)
