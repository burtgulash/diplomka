#!/usr/bin/env sh

INDEX=${1:-INDEX/NAME}
INPUTFILE=${2:-bulk_req.jsonl}
curl -s -XPOST "localhost:9200/$INDEX/_bulk" --data-binary "@$INPUTFILE"
