#!/usr/bin/env sh
jq -cr '{time: .took, total: .hits.total}'
