#!/usr/bin/sh

INPUT=${1:--}
OUTDIR=${2:-/tmp}

tuples=$OUTDIR/tuples.idx
srcdb=$OUTDIR/srcdb.dbm
dict=$OUTDIR/dict.idx
stats=$OUTDIR/stats.idx
trie_dir=$OUTDIR/trie/
docs_dir=$OUTDIR/docs/
PYTHON=$(which python3)
echo "using python '$PYTHON'"

mkdir -p ${OUTDIR}

echo "indexing to $OUTDIR"
mkdir -p ${trie_dir} ${docs_dir}
$PYTHON ./index.py ${INPUT} ${tuples} ${dict} ${stats}

echo "creating srcdb ${srcdb}"
$PYTHON ./makedbm.py ${INPUT} ${srcdb}

echo "$(cat ${INPUT} | wc -l) docs total"

num_words=$(cut -f1 ${stats})
num_occurrences=$(cut -f2 ${stats})

echo "creating trie   words=${num_words}, occurrences=${num_occurrences}"
cat ${dict} | $PYTHON ./mktrie.py ${trie_dir} ${num_words} ${num_occurrences}

echo "reassigning term_ids + adding group_ids in tuples"
cat ${tuples} | $PYTHON ./retid.py ${trie_dir} > ${tuples}.ready

echo "sorting tuples"
cat ${tuples}.ready | sort -k1,1n -k2,2n -k3,3n -k4,4n > ${tuples}.sorted

echo "linearizing tuples"
cat ${tuples}.sorted | $PYTHON ./linearize.py ${docs_dir}
