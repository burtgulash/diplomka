#!/usr/bin/env python3

import dbm
import sys
import gzip

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: ./makedbm INPUT DBFILE", file=sys.stderr)
        sys.exit(1)

    with gzip.open(sys.argv[1], "r") as inputf, dbm.open(sys.argv[2], "n") as db:
        for i, line in enumerate(inputf):
            db[str(i)] = line.decode("utf8").strip()

