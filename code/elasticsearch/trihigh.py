#!/usr/bin/env python3

import unicodedata

def word_split(text):
    delim = set(" \t\n.,-?!\"';:@#$%^&*()[]{}")

    wbuf = []
    for i, c in enumerate(text):
        if c in delim:
            if wbuf:
                yield (i - len(wbuf), "".join(wbuf))
            wbuf = []
        else:
            wbuf.append(c)
    if wbuf:
        yield (i - len(wbuf) + 1, "".join(wbuf))


def word_ngrams(n, s):
    for i, word in word_split(s):
        for j in range(len(word) - n + 1):
            yield (i + j, word[j: j + n])


def match_regions(n, matches):
    start, last = None, None
    for m in matches:
        if last is None:
            start = m
        elif last + n < m:
            yield (start, last + n)
            start = m
        last = m

    if last is not None:
        yield start, last + n

def find_regions(matches):
    last_start, last_end = None, None
    for start, end in sorted(matches):
        if last_end is None:
            last_start, last_end = start, end
        elif last_end < start:
            yield (last_start, last_end)
            last_start = start
        last_end = end

    if last_start is not None:
        yield (last_start, last_end)


def unaccent(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def highlight(record, query, pre, post, n):
    q = unaccent(query.lower())
    query_ngrams = set(gram for _, gram in word_ngrams(n, q))
    query_ngrams |= set(word for _, word in word_split(q))

    record_ngrams = list(word_ngrams(n, record))
    record_ngrams.extend(word_split(record))


    matches = []
    for i, gram in sorted(record_ngrams):
        transformed_gram = unaccent(gram.lower())
        if transformed_gram in query_ngrams:
            matches.append((i, i + len(gram)))

    # print(matches)
    regions = list(find_regions(matches))
    # print(regions)

    result = []
    last = 0
    for start, end in regions:
        result.append(record[last:start])
        result.append(pre)
        result.append(record[start:end])
        result.append(post)
        last = end
    result.append(record[last:])

    return "".join(result)


HLSTART="\x1B[1m\x1B[31m"
HLEND="\x1B[0m"

HLSTART=r"\boldred{"
HLEND=r"}"

def main():
    import sys
    if len(sys.argv) < 2:
        print("usage: trihigh.py QUERY < RECORDS", file=sys.stderr)
        sys.exit(1)

    query = unaccent(" ".join(sys.argv[1:]).lower())
    for line in sys.stdin:
        record = line.strip()
        hl = highlight(record, query, HLSTART, HLEND, 3)
        #print(record, "|||", hl)
        print(hl)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
