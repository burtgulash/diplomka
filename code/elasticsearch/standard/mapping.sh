#!/usr/bin/env sh

curl -XPUT localhost:9200/csfd_standard/_mapping/filmy -d'
{
  "properties": {
    "title": {
      "type": "string",
      "analyzer": "cestina"
    }
  }
}'
