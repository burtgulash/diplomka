#!/usr/bin/env sh

OUT=${3}
while read -r query; do
    OUTFILE=$OUT/$(echo $query | tr ' ' '_').txt
    echo "$query > $OUTFILE"
    ./repeat.sh ${1} ${query} | ./search.sh ${2} 1 | grep '^TIMINGS' > $OUTFILE
    sleep .1
done
