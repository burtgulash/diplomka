#!/usr/bin/env sh
COUNT=${1}
shift
yes ${@} | head -n ${COUNT}
