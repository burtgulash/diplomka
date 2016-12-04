#!/usr/bin/env sh
INPUT="${@:-query}"
cat search.sql | psql -v query="'$INPUT'"
