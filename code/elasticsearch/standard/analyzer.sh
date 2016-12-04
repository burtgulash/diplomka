#!/usr/bin/env sh

curl -XPUT localhost:9200/csfd_standard -d'{
  "settings": {
    "analysis": {
      "filter": {
        "czech_stemmer": {
          "type": "stemmer",
          "language": "czech"
        }
      },
      "analyzer": {
        "cestina": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "icu_folding",
            "asciifolding",
            "czech_stemmer"
          ]
        }
      }
    }
  }
}'
