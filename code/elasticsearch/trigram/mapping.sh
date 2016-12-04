#!/usr/bin/env sh

curl -XPUT localhost:9200/csfd_trigram/_mapping/filmy -d'
{
  "properties": {
    "title": {
        "type": "multi_field",
        "fields": {
            "title": {
                "type": "string",
                "analyzer": "my_standard",
                "term_vector": "with_positions_offsets"
            },
            "trigram": {
                "type": "string",
                "analyzer": "my_ngrams",
                "term_vector": "with_positions_offsets"
            },
            "shorts": {
                "type": "string",
                "analyzer": "my_short_words",
                "term_vector": "with_positions_offsets"
            }
        }
    }
  }
}'
