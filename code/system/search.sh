#!/usr/bin/env sh

INDIR=${1:-/tmp}
DYNAMIC=${2}
PYTHON=pypy3
#PYTHON=python3
>&2 echo "Searching in index '$INDIR' using '$PYTHON'"
$PYTHON ./search.py $INDIR/trie $INDIR/docs $INDIR/srcdb.dbm $DYNAMIC
