#!/usr/bin/sh

QUERY=${@:-srncu}
curl -s -XGET 'localhost:9200/csfd_trigram/_search' -d "$(echo '
{
    "min_score": 0.1,
    "size": 100,
    "query": {
        "multi_match": {
            "query": "QUERY",
            "minimum_should_match": "70%",
            "boost": 2,
            "type": "most_fields",
            "fields": [
                "title.shorts",
                "title.title^3.5",
                "title.trigram^2.5"
            ]
        }
    },
    "highlight": {
        "pre_tags": ["HLSTART"],
        "post_tags": ["HLEND"],
        "type": "fvh",
        "number_of_fragments": 0,
        "fields": {
            "title": {
                "matched_fields": [
                    "title.trigram",
                    "title.title",
                    "title.shorts"
                ]
            }
        }
    }
}' | sed "s/QUERY/$QUERY/g")" #\
#| jq -cr '.hits.hits[] | [((1/._score) * 100 | floor / 100), ._source.title] | @tsv' \
#| ./trihigh.py $QUERY
