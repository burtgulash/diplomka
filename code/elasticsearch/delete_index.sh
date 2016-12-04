#!/usr/bin/sh

INDEX=${1:--}
curl -XDELETE "localhost:9200/$INDEX"
