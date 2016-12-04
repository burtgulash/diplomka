#!/usr/bin/env python3

import json
import sys

for doc_id, line in enumerate(sys.stdin):
    record = {"title": line.strip()}
    # action = {"index": {
    #     "_index": "csfd1",
    #     "_type": "title",
    #     "_id": doc_id,
    # }}
    action = {"index": {"_id": doc_id}}
    sys.stdout.write(json.dumps(action))
    sys.stdout.write("\n")
    sys.stdout.write(json.dumps(record))
    sys.stdout.write("\n")
