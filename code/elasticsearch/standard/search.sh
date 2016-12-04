#!/usr/bin/sh

QUERY="${@:--}"
curl -s -XGET localhost:9200/csfd_standard/filmy/_search -d"
{
    \"size\": 100,
    \"query\": {
        \"match\": {
            \"title\": {
                \"query\": \"$QUERY\",
                \"type\": \"phrase\",
                \"slop\": 30
            }
        }
    },
    \"highlight\": {
        \"pre_tags\": [\"HLSTART\"],
        \"post_tags\": [\"HLEND\"],
        \"fields\": {
            \"title\": {
                \"index_options\": \"offsets\"
            }
        }
    }
}" # | ./highlight.sh
