#!/usr/bin/env python3

regex = '^([\s\S]*)\(([\d{4}]*|\?*)(?:\/)?([\w]*)?\)(\s*{([\w!\s:;\/\.\-\'"?`_&@$%^*<>~+=\|\,\(\)]*)(\s*\(#([\d]*)\.([\d]*)\))?})?\s*([\d{4}]*)?(?:-)?([\d{4}]*)?'

import re
import sys
import gzip

def pr(x):
    if x:
        print(x)

with gzip.open(sys.argv[1]) as input:
    for line in input:
        m = re.match(regex, line.decode("iso-8859-2"))
        if m:
            name = m.group(1)
            year = m.group(2)
            c3 = m.group(3)
            c4 = m.group(4)
            c5 = m.group(5)
            c6 = m.group(6)
            c7 = m.group(7)
            c8 = m.group(8)
            c9 = m.group(9)
            c10 = m.group(10)
            #print(name.replace('"', ""), "\t", c5)
            print(c5)
