#!/usr/bin/env sh

curl -XPUT localhost:9200/csfd_trigram -d'{
  "settings": {
    "analysis": {
      "tokenizer": {
        "my_ngram_tokenizer": {
          "type": "nGram",
          "min_gram": 3,
          "max_gram": 3,
          "token_chars": ["letter", "digit"]
        }
      },
      "filter": {
        "my_ngram_filter": {
          "type": "ngram",
          "min_gram": 3,
          "max_gram": 3
        },
        "my_short_words_filter": {
            "type": "length",
            "max": 2
        }
      },
      "analyzer": {
        "my_ngrams": {
          "type": "custom",
          "tokenizer": "my_ngram_tokenizer",
          "filter": [
            "asciifolding",
            "lowercase"
          ]
        },
        "my_standard": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": [
                "asciifolding",
                "lowercase"
            ]
        },
        "my_short_words": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": [
                "asciifolding",
                "lowercase",
                "my_short_words_filter"
            ]
        }
      }
    }
  }
}'
