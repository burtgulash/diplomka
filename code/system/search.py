#!/usr/bin/env python3

import collections
import os.path
import math
import time

import seq
import cursor

class SeqReader:

    def __init__(self, seqfile):
        self.seqfile = seqfile
        with open(seqfile, "r") as f:
            self.seq = [int(x) for x in f.read().split("\n") if x]

    def __getitem__(self, key):
        return self.seq[key]

    def print(self):
        print(self.seqfile, self.seq)

class Trie:

    def __init__(self, children_ptrs, children_nodes, terms, tlens, firsts, breakpoints, breakpoints_long):
        self.children_ptrs = children_ptrs
        self.children_nodes = children_nodes
        self.terms = terms
        self.tlens = tlens
        self.firsts = firsts

        self.breakpoints = breakpoints
        self.breakpoints_long = breakpoints_long

    def find_k(self, breakpoints, word_len):
        for i, x in enumerate(breakpoints):
            if word_len <= x:
                return i
        return len(breakpoints)

    def _get_match(self, node):
        t0, t1 = self.tlens[node], self.tlens[node + 1]
        matched = bytes(self.terms[t0 : t1]).decode("utf8")
        assert(len(matched) > 0)
        return matched

    def _match_node(self, node, w_sofar, distance):
        #print("MATCHING", w_sofar)
        is_terminal = w_sofar[-1] == "\0"
        if is_terminal:
            yield self._result(w_sofar, distance, node)

    def _result(self, word, distance, node):
        # print("FOUND WORD", word, distance, node)
        return word[:-1], distance, node
        #return word[:-1], distance, node

    def _traverse(self, node, w_sofar, distance):
        # print("TRAVERSING", w_sofar)
        w_sofar += self._get_match(node)
        #yield from self._match_node(node, w_sofar, distance)
        for x in self._match_node(node, w_sofar, distance):
            yield x
        for x in self._traverse_children(node, w_sofar, distance):
            yield x

    def _traverse_children(self, node, w_sofar, distance):
        for child in self._children(node):
            for x in self._traverse(child, w_sofar, distance):
                yield x

    def _children(self, node):
        ch_ptr = self.children_ptrs[node]
        if ch_ptr == 0:
            # No more children to recurse to
            return ()

        return range(self.children_nodes[ch_ptr], self.children_nodes[ch_ptr + 1])

    def _distance_threshold(self, i):
        if i >= len(self.thresholds):
            return self.thresholds[-1]
        #print(self.thresholds[i])
        return self.thresholds[i]

    def search_dynamic(self, word, search_prefix=False, dynamic=True):
        if dynamic:
            breakpoints = self.breakpoints if len(word) < 5 else self.breakpoints_long
        else:
            breakpoints = [2, 5, 7]
            breakpoints = [1, 3, 5, 7]
        k = self.find_k(breakpoints, len(word))
        self.thresholds = [0] * 32

        last = 0
        for i, b in enumerate(breakpoints):
            for x in range(last, b):
                self.thresholds[x] = i
            last = b
        for x in range(last, len(self.thresholds)):
            self.thresholds[x] = len(breakpoints)

        for x in  self.search(word, k, search_prefix, dynamic=dynamic):
            yield x

    def search(self, word, k, search_prefix=False, dynamic=True):
        l = len(word)
        MAX_ROW = 64
        D = [[0 for _ in range(l + 1)] for _ in range(MAX_ROW)]
        for i in range(l + 1):
            D[0][i] = i

        word = word + "\0"
        n0, n1 = self.children_nodes[-2], self.children_nodes[-1]
        for child in range(n0, n1):
            for x in  self._search(word, k, "", child, D, 1, search_prefix=search_prefix, dynamic=dynamic):
                yield x

    def _search(self, word, k, w_sofar, n, D, lvl, search_prefix=False, dynamic=True):
        if dynamic:
            k = self._distance_threshold(min(len(w_sofar), len(word) - 1))

        matched = self._get_match(n)
        w_sofar += matched
        is_terminal = w_sofar[-1] == "\0"

        #maxrow = min(lvl + len(matched) - int(is_terminal), len(word) - 1 + 1)
        maxrow = lvl + len(matched) - int(is_terminal)
        for j in range(lvl, maxrow):
            minimum = 1337
            D[j][0] = j

            for i in range(1, len(D[j])):
                #sub_cost = 1
                sub_cost = 1 if j > 1 else 2

                substituted = 0 if word[i - 1] == w_sofar[j - 1] else sub_cost
                replaceCost = D[j - 1][i - 1] + substituted
                insertCost = D[j][i - 1] + 1 #1.125
                deleteCost = D[j - 1][i] + 1 #1.25
                cost = min(replaceCost, insertCost, deleteCost)

                D[j][i] = cost
                minimum = min(minimum, cost)

            if minimum > k:
                return

        distance = D[maxrow - 1][-1]

        # print(w_sofar, word, "DIST", distance)
        # for row in D[:maxrow + 1]:
        #     for col in row:
        #         print(col, end=", ")
        #     print()
        # print()

        # Optimization when searching prefixes: traverse the descendants
        # without fuzzy stuff once w_sofar is exhausted
        if search_prefix and len(w_sofar) + int(not is_terminal) >= len(word):
            if distance <= k:
                if is_terminal:
                    yield self._result(w_sofar, distance, n)
                for x in  self._traverse_children(n, w_sofar, distance):
                    yield x

        # Optimalization for < 1-character words: only look for children,
        # don't recurse
        elif not search_prefix and len(word) <= 1 + 1:
            for child in self._children(n):
                match = self._get_match(child)
                if match == "\0":
                    yield self._result(w_sofar + "\0", distance, child)

        # If the current node is terminal, it can't have any children. Avoid
        # recursion here
        elif is_terminal:
            # if not search_prefix:
            #     distance += max(0, len(w_sofar) - len(word)) / 1.6 # suffixes should not be penalized less
            if distance <= k:
                yield self._result(w_sofar, distance, n)

        # Handle descendants
        else:
            # Compute minimum if it hasn't been computed before
            # Caused by min(len(word) + 1) cutoff
            distance = min(D[maxrow - 1])

            # Recurse. Search fuzzily in descendants
            if distance <= k:
                for child in self._children(n):
                    for x in self._search(word, k, w_sofar, child, D,
                            maxrow, search_prefix, dynamic):
                        yield x

class GroupList:

    def __init__(self, group_id, start, end):
        self.group_id = group_id
        self.start = start
        self.end = end
        self.term_ids = []

class FullFilter:

    def __contains__(self, x):
        return True

def search(trie, query_term, trie_seqs, index_seqs, search_prefix, term_is, dynamic=True):
    gdocs, gtids, gpos, gchpos = index_seqs
    # TODO rename gtids. Is in both trie and index seqs

    term_ids, group_map, group_doc_lens, group_term_lens, group_term_ids = trie_seqs
    query_term = query_term.strip()

    tid_weight_map = {}
    groupped_groups = {}
    result = []
    for word, d, node in trie.search_dynamic(query_term, search_prefix=search_prefix, dynamic=dynamic):
        d += abs(len(query_term) - len(word)) / (1 + len(query_term) * 3)
        term_id = term_ids[node]
        group_id = group_map[term_id]

        if group_id not in groupped_groups:
            groupped_groups[group_id] = GroupList(group_id, group_doc_lens[group_id], group_doc_lens[group_id + 1])
        groupped_groups[group_id].term_ids.append(term_id)
        result.append([word, d, term_id, group_id])
        tid_weight_map[term_id] = d


    # TODO ENABLE TO PRINT FOUND TERMS
    # sorted by d
    #for x in sorted(result, key=lambda r: -r[1]):
    #    print(*x)
    #print()

    terms_sum = 0

    cursors = []
    for group_id, x in groupped_groups.items():
        group_terms = group_term_lens[group_id + 1] - group_term_lens[group_id]
        terms_sum += len(x.term_ids)

        docs = gdocs.subseq(x.start, x.end)
        tids = gtids.subseq(x.start, x.end)
        pos = gpos.subseq(x.start, x.end)
        chpos = gchpos.subseq(x.start, x.end)


        # print(set(x - min_group_tid for x in tid_filter))

        #print("FILTER", tid_filter)
        #print("MINGROUPTID", min_group_tid)
        size = x.end - x.start
        fill_factor = len(x.term_ids) / group_terms

        min_group_tid = group_term_ids[group_term_lens[group_id]]
        tid_filter = set(x.term_ids)

        cur = cursor.Cursor(docs, tids, pos, chpos, size)
        if fill_factor == 1.0:
            cur = cursor.FullCursor(cur, min_group_tid, term_is)
        else:
            cur = cursor.FilteredCursor(cur, min_group_tid, tid_filter, fill_factor, term_is)



        # print("LENSET", len(set(x.term_ids)))
        cursors += [cur]

        print("{},\t docs: {}\t({}-{}),\t terms: {}/{}".format(group_id, size, x.start, x.end, len(x.term_ids), group_terms))

    final_cursor = None
    if len(cursors) > 1:
        final_cursor = cursor.CursorUnion1(cursors)
        print("UNION CURSOR", final_cursor)
    elif len(cursors) == 1:
        final_cursor = cursors[0]
    else:
        final_cursor = None

    print("--- Groups", len(groupped_groups), terms_sum)
    return final_cursor, tid_weight_map

# Doesn't work 100%. Look for maximum bipartite matching problem
def exists_bipartite_match(group, size):
    positions = set(chpos for _, _, _, _, chpos, _ in group)
    return len(positions) >= size


def output_interval(qsize, lo, hi):
    start_penalty = lo[1] != 0
    end_penalty = hi[1] != qsize - 1

    cost = hi[0] + 1 - lo[0]
    cost += 3 * start_penalty + 1.5 * end_penalty
    return cost, lo[0], hi[0] + 1


def find_proximity_min_intervals(occs, qsize):
    freqs = [0] * qsize
    minpos = [0] * qsize

    for pos, x in occs[::-1]:
        minpos[x] = pos

    r_start = max(minpos)
    l, r = 0, len(occs) - 1
    for i, occ in enumerate(occs):
        pos, x = occ
        if pos > r_start:
            r = i - 1
            break
        freqs[x] += 1

    lmost = occs[l][1]
    while True:
        if freqs[lmost] == 1:
            yield output_interval(qsize, occs[l], occs[r])
            #print("MATCH", text[occs[l][0] : occs[r][0] + 1])
            break
        freqs[lmost] -= 1
        l += 1
        lmost = occs[l][1]

    r += 1
    while r < len(occs):
        rmost = occs[r][1]
        freqs[rmost] += 1

        if rmost != lmost:
            r += 1
            continue

        while True:
            if freqs[lmost] == 1:
                yield output_interval(qsize, occs[l], occs[r])
                #print("MATCH", text[occs[l][0] : occs[r][0] + 1], (occs[l][0], occs[r][0]))
                break
            freqs[lmost] -= 1
            l += 1
            lmost = occs[l][1]

        r += 1
            
def proximity_interval(match_group, qsize):
    occurrences = sorted((chpos, term_i) for _, _, _, _, chpos, term_i in match_group)
    cost, lo, hi = sorted(find_proximity_min_intervals(occurrences, qsize))[0]
    return cost, lo, hi
    #return math.log(1 + min_interval_sizes[0])

def edit_distance_rank(match_group, qsize):
    # edit_cost = sum(d for d, _, _, _, _, _ in match_group)
    min_dists = collections.defaultdict(list)
    for d, doc_id, term_id, pos, chpos, term_i in match_group:
        min_dists[term_i].append(d)
    #print(match_group)

    #print(min_dists, qsize)
    return sum(min(min_dists[term_i]) for term_i in range(qsize))


def rank_and_sort(result, wmaps):
    qsize = len(wmaps)

    r = []
    last, grp = -1, []
    for x in result:
        doc_id, term_i, term_id, pos, chpos = x
        if doc_id != last:
            if grp and exists_bipartite_match(grp, qsize):
                r.append(grp)
            last, grp = doc_id, []

        d = wmaps[term_i][term_id]
        grp.append((d, doc_id, term_id, pos, chpos, term_i))
    if grp and exists_bipartite_match(grp, qsize):
        r.append(grp)

    ranked_r = []
    for match_group in r:
        cost, lo, hi = proximity_interval(match_group, qsize)
        d = edit_distance_rank(match_group, qsize)
        tf = len(match_group)
        interval_size = hi - lo

        score = d * 1.4
        score += .01 * lo

        score += math.log(cost)
        #score += .001 * math.log(cost)

        if interval_size > 1:
            score -= math.log(3)

        score += .4 / (1 + math.log(tf))
        #score -= 2 * (1 + math.log(tf))

        ranked_r.append((score, (lo, hi), match_group))

    return list(sorted(ranked_r, key=lambda x: x[0]))


def next_occurrence(text, chars, from_index):
    occurrences = []
    for c in chars:
        try:
            occurrences.append(text.index(c, from_index))
        except ValueError:
            pass
    if occurrences:
        return min(occurrences)
    else:
        return None


def highlight(result_grp, doc_id, typed_chars, docdb, proximity_interval):
    document = docdb[str(doc_id)].decode("utf8")
    matched_positions = list(sorted((chpos, term_i) for _, _, _, _, chpos, term_i in result_grp))




    bold = r"\textbf{"
    colored = r"\color{red}"

 #   hl_start = r"{\color{red}"
 #   bold = r"\textbf{"
 #   hl_end = r"}"

 #   hl_start = r"\boldred{"
 #   hl_end = r"}"

    bold = "\033[1m"
    colored = "\033[91m"
    highlight_end = "\033[0m"

    hl_start = bold + colored
    hl_end = highlight_end


    evidence = []
    last = 0
    previous_chpos = -1
    for chpos, term_i in matched_positions:
        if chpos == previous_chpos:
            previous_chpos = chpos
            continue
        previous_chpos = chpos

        match_len = typed_chars[term_i]

        # If deletions occur in the final word reduce the highlight size to
        # real word size
        word_end = next_occurrence(document, " _", chpos)
        if word_end:
            match_len = min(match_len, word_end - chpos)

        #highlight_start = colored
        highlight_start = hl_start
    #    if proximity_interval[0] <= chpos <= proximity_interval[1]:
    #        highlight_start += bold
    #        in_min_interval = True
    #    else:
    #        in_min_interval = False

        evidence += [
            document[last : chpos],
            highlight_start,
            document[chpos : chpos + match_len],
            #highlight_end,
            hl_end,
        ]
    #    if in_min_interval:
    #        evidence += [hl_end]

        last = chpos + match_len
    evidence += [document[last:]]

    return "".join(evidence)# + "   |   " + document + "   |   " + str(matched_positions)


def run():
    import sys
    import dbm

    if len(sys.argv) != 5:
        print("usage: ./trie TRIEDIR DOCSDIR DOCDB DYNAMICSEARCH", file=sys.stderr)
        sys.exit(1)

    docdb = dbm.open(sys.argv[3], "r")

    print("Loading dict..")
    triedir = sys.argv[1]
    trie = Trie(
        SeqReader(os.path.join(triedir, "chptr")),
        SeqReader(os.path.join(triedir, "chnode")),
        SeqReader(os.path.join(triedir, "term")),
        SeqReader(os.path.join(triedir, "tlen")),
        SeqReader(os.path.join(triedir, "fst")),
        #breakpoints=[2, 6],
        breakpoints=[2, 4, 6, 8],
        breakpoints_long=[1, 3, 5, 7, 9, 11],
        #breakpoints=[1, 2, 3, 4, 5],
        #breakpoints_long=[1, 2, 3, 4, 5, 11],
        #breakpoints_long=[1, 2, 3, 4, 5, 6, 7],
    )

    term_ids = SeqReader(os.path.join(triedir, "tid"))
    group_map = SeqReader(os.path.join(triedir, "groupmap"))
    group_doc_lens = SeqReader(os.path.join(triedir, "gdlens"))
    group_term_lens = SeqReader(os.path.join(triedir, "gtlens"))
    group_term_ids = SeqReader(os.path.join(triedir, "gtids"))

    print("Loading docs..")
    docsdir = sys.argv[2]
    gdocs = seq.ArraySeq(SeqReader(os.path.join(docsdir, "gdocs")).seq)
    gtids = seq.ArraySeq(SeqReader(os.path.join(docsdir, "gtids")).seq)
    gpos = seq.ArraySeq(SeqReader(os.path.join(docsdir, "gpos")).seq)
    gchpos = seq.ArraySeq(SeqReader(os.path.join(docsdir, "gchpos")).seq)

    SEARCH_DYNAMIC = bool(int(sys.argv[4]))
    print("Searching.. dynamic=%s" % (SEARCH_DYNAMIC))
    try:
        while True:
            query = input("> ")
            if not query.strip():
                continue

            t_start = time.time()
            query_terms = [x.strip() for x in query.lower().split()]
            typed_chars = [len(x) for x in query_terms]

            last_incomplete = query[-1] != " "
            prefix_search = [False] * len(query_terms)
            #prefix_search = [True] * len(query_terms)

            #prefix_search[-1] = last_incomplete
            #if len(query_terms) == 1 and len(query_terms[-1]) == 1:
            #    prefix_search[-1] = False

            query_terms = [ (qt, term_i, prefix_search[term_i]) for term_i, qt in enumerate(query_terms) ]
            gqt = collections.defaultdict(list)
            for qt, term_i, search_prefix in query_terms:
                gqt[qt, search_prefix].append(term_i)

            cursors = []
            wmaps = {}
            for x, term_is in gqt.items():
                q, search_prefix = x
                cur, wmap = search(trie, q,
                                   (term_ids, group_map, group_doc_lens, group_term_lens, group_term_ids),
                                   (gdocs, gtids, gpos, gchpos),
                                   search_prefix, term_is,
                                   dynamic=SEARCH_DYNAMIC)
                cursors.append(cur)
                for term_i in term_is:
                    wmaps[term_i] = wmap


            if not all(cursors):
                print("NOT FOUND")
                continue

            if len(cursors) == 1:
                final_cursor = cursors[0]
            else:
                final_cursor = cursor.CursorIntersection(cursors)


            trie_end_time = time.time()
            trie_time = trie_end_time - t_start

            result = []
            while True:
                x = final_cursor.advance(result)
                if x == cursor.MAX_DOC:
                    break

            rank_t_start = time.time()
            invtime = rank_t_start - trie_end_time

            print()
            print()
            print("----------------------- -- RESULTS -- ------------------------------")
            groupped_result = rank_and_sort(result, wmaps)
            #for dist, proximity_interval, g in groupped_result[::-1]:
            for dist, proximity_interval, g in groupped_result[:50]:
                _, doc_id, _, _, _, _ = g[0]
                evidence = highlight(g, doc_id, typed_chars, docdb, proximity_interval)
                #print("{:<.2f} {:>10}  {:<}".format(dist, doc_id, evidence))
                print("{:<.2f} {:<}".format(dist, evidence))

            end_time = time.time()
            rank_time = end_time - rank_t_start
            total_time = end_time - t_start

            print("--------------------------------------------------------------------")
            print()
            print(final_cursor)
            print("Query [{}]".format(query.strip()))
            print("T [{:.3f}s] Trie [{:.3f}s] Inv [{:.3f}s] Rank [{:.3f}s]. {} hits, {} results".format(total_time, trie_time, invtime, rank_time, len(result), len(groupped_result)))

            print("TIMINGS|{}\t{}\t{:.4f}\t{:.4f}\t{:.4f}\t{:.4f}\n".format(
                query.strip(),
                len(groupped_result),
                total_time,
                trie_time,
                invtime,
                rank_time,
            ))
    except EOFError:
        pass

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        pass
