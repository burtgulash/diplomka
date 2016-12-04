#!/usr/bin/env sh

HLSTART=HLSTART
HLEND=HLEND

hls="\x1B[31m\x1B[1m"
hle="\x1B[0m"
hls='\\boldred{'
hle='}'

highlight_placeholders() {
    sed -e "s/$HLSTART/$hls/g" -e "s/$HLEND/$hle/g"
}

highlight() {
    jq -cr '.hits.hits[] | [((1/._score) * 100 | floor / 100), .highlight.title[]] | @tsv' \
    | highlight_placeholders
}

highlight
