#!/usr/bin/env python3

import re
import unicodedata
import gzip
import sys

class TokenStats:
    def __init__(self, tid, count):
        self.tid = tid
        self.count = count

def transform(token):
    return unicodedata.normalize("NFKD", token).encode("ascii", "ignore").decode("ascii").lower()

def process(infile, outfile):
    d = {}
    tid = 0
    for did, line in enumerate(infile):
        line = line.decode("utf8").strip()
        line = line.replace("_", " ")
        pos, chpos = 0, 0
        for token in re.split("(\W+)", line):
            orig_token = token
            token = token.strip()
            if not token:
                chpos += len(orig_token) - orig_token.count("\t")
                continue

            skip = len(token)
            token = transform(token).strip()
            if not token:
                chpos += skip
                continue

            # print("TOK", orig_token, token)

            stats = d.get(token)
            if stats is None:
                stats = TokenStats(tid, 0)
                tid += 1
                d[token] = stats
            stats.count += 1

            tup = (stats.tid, did, pos, chpos)
            for i, x in enumerate(tup):
                outfile.write(str(x))
                delim = "\n" if i == len(tup) - 1 else "\t"
                outfile.write(delim)

            chpos += len(orig_token)
            pos += 1
    return d

def write_dict(dictionary, outfile):
    for token, stats in sorted(dictionary.items()):
        assert "\n" not in token
        assert token.strip()
        outfile.write(token)
        outfile.write("\t")
        outfile.write(str(stats.tid))
        outfile.write("\t")
        outfile.write(str(stats.count))
        outfile.write("\n")

def write_stats(dictionary, outfile):
    num_words = len(dictionary)
    num_occurrences = sum(stats.count for stats in dictionary.values())
    outfile.write(str(num_words))
    outfile.write("\t")
    outfile.write(str(num_occurrences))
    outfile.write("\n")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("usage: ./maketuples INPUT TUPLES DICT STATS", file=sys.stderr)
        sys.exit(1)

    inputfile, tup_outfile, dict_outfile, stats_outfile = sys.argv[1:5]
    try:
        with gzip.open(inputfile, "r") as inputf, open(tup_outfile, "w") as f:
            dictionary = process(inputf, f)
        with open(dict_outfile, "w") as f:
            write_dict(dictionary, f)
        with open(stats_outfile, "w") as f:
            write_stats(dictionary, f)
    except KeyboardInterrupt:
        pass
