#!/usr/bin/env sh
jq -cr '.hits.hits[] | [((1/._score) * 100 | floor / 100), ._source.title] | @tsv' | ./trihigh.py $@
