#!/usr/bin/env python3

import os.path
import sys

def common_prefix_len(a, b):
    i = 0
    for x, y in zip(a, b):
        if x != y:
            break
        i += 1
    return i

def invert2(inv, seq):
    for i, x in enumerate(seq):
        inv[x] = i
    return inv

def invert(seq):
    return [x for _, x in sorted(zip(seq, range(len(seq))))]

class Node:

    def __init__(self, prefix_len, term_id, term, is_terminal, freq):
        self.prefix_len = prefix_len
        self.term_id = term_id
        self.term = term
        self.children = []
        self.ptr = 0
        self.is_terminal = is_terminal
        self.freq = freq

        self.not_yet_tagged = []

    def __repr__(self):
        return "N({},'{}',{},{})".format(self.prefix_len, self.term, self.ptr, len(self.children))

class SeqWriter:

    def __init__(self, outfile):
        self.outfile_name = outfile
        self.outfile = open(self.outfile_name, "w")

    def write(self, x):
        self.outfile.write(str(x))
        self.outfile.write("\n")

    def writemany(self, it):
        for x in it:
            self.write(x)

    def close(self):
        self.outfile.close()

class CumSeqWriter(SeqWriter):

    def __init__(self, outfile):
        super().__init__(outfile)
        self.cum = 0
        self.write(self.cum)

    def write(self, x):
        self.cum += x
        super().write(self.cum)


def outpath(directory, outfile):
    return os.path.join(directory, outfile)

class TrieBuilder:

    def __init__(self, outdir, num_words, num_occurrences):
        self.outdir = outdir

        self.last_word = ""
        self.stack = [Node(0, -1, self.last_word, False, 0)]
        self.num_words = num_words
        self.threshold = max(200, num_occurrences // 200)
        print("GROUP DOCS THRESHOLD: %s" % self.threshold, file=sys.stderr)
        #self.freq_avg = num_occurrences / num_words

        self.group_id = 0
        self.term_id = 0
        self.prefix_term_id = num_words

        # Node pointer (ptr) starts at 1, because 0 is reserved for 'nil' node
        self.ptr = 1
        self.children_nodes = CumSeqWriter(outpath(outdir, "chnode"))
        self.children_nodes.write(0)

        self.children_ptrs = SeqWriter(outpath(outdir, "chptr"))
        #self.is_terminal = SeqWriter(outpath(outdir, "isterm"))

        self.term_id_map = []
        self.term_id_map_w = SeqWriter(outpath(outdir, "tidmap"))
        self.term_ids = SeqWriter(outpath(outdir, "tid"))
        self.firsts = SeqWriter(outpath(outdir, "fst"))
        self.termlens = CumSeqWriter(outpath(outdir, "tlen"))
        self.terms = SeqWriter(outpath(outdir, "term"))

        self.groups = []
        self.groups_w = SeqWriter(outpath(outdir, "group"))
        self.group_tids = SeqWriter(outpath(outdir, "gtids"))
        self.group_docs_lens = CumSeqWriter(outpath(outdir, "gdlens"))
        self.group_tids_lens = CumSeqWriter(outpath(outdir, "gtlens"))

        self.group_map = [0] * num_words
        self.group_map_w = SeqWriter(outpath(outdir, "groupmap"))

    def close_seqs(self):
        self.children_ptrs.close()

        self.children_nodes.close()
        #self.is_terminal.close()

        self.term_id_map_w.close()
        self.term_ids.close()
        self.firsts.close()
        self.terms.close()
        self.termlens.close()

        self.groups = []
        self.groups_w.close()
        self.group_tids.close()
        self.group_docs_lens.close()
        self.group_tids_lens.close()

        self.group_map_w.close()

    def flush_node(self, node, term):
        self.children_ptrs.write(node.ptr)
        #self.is_terminal.write(node.is_terminal)
        self.term_ids.write(node.term_id)
        self.firsts.write(ord(term[0]))

        term_bytes = term.encode("utf8")
        self.terms.writemany(term_bytes)
        self.termlens.write(len(term_bytes))

        assert node.is_terminal and term[-1] == "\0" \
        or not node.is_terminal and "\0" not in term

    def flush_children(self, node):
        self.children_nodes.write(len(node.children))
        # print("SETTING PTR", self.ptr)
        node.ptr = self.ptr
        self.ptr += 1

        for ch in node.children:
            ch_term = ch.term[node.prefix_len : ch.prefix_len]
            # print("flushing CHILD", node.term, ch.term, ch_term, ch.ptr)
            self.flush_node(ch, ch_term)

    def create_list_group(self, node):
        #group_id = node.term_id
        group_id = self.group_id
        self.group_id += 1

        self.groups.append(group_id)

        term_ids_of_this_group = node.not_yet_tagged
        if node.is_terminal:
            term_ids_of_this_group.append(node.term_id)

        self.group_docs_lens.write(node.freq)
        self.group_tids_lens.write(len(term_ids_of_this_group))
        self.group_tids.writemany(sorted(term_ids_of_this_group))

        for term_id in term_ids_of_this_group:
            self.group_map[term_id] = group_id

    def assign_list_group_to_children(self, node, list_size_threshold):
        unprocessed_lists_size = 0
        for ch in node.children:
            # Add this child node to either
            # 1. new list group
            if ch.freq > list_size_threshold:
                self.create_list_group(ch)

            # 2. to parent's buffer
            else:
                unprocessed_lists_size += ch.freq
                node.not_yet_tagged.extend(ch.not_yet_tagged)
                if ch.is_terminal:
                    node.not_yet_tagged += [ch.term_id]

        node.freq += unprocessed_lists_size

    def add(self, word, term_id, freq):
        word = word + "\0"

        prefix_len = common_prefix_len(word, self.last_word)
        # print("Adding", word, prefix_len)
        if prefix_len < len(self.last_word):
            flushed = self.stack.pop()
            while prefix_len < self.stack[-1].prefix_len:
                parent = self.stack.pop()
                parent.children.append(flushed)
                flushed = parent

                self.flush_children(flushed)
                self.assign_list_group_to_children(flushed, list_size_threshold=self.threshold)
                #self.assign_list_group_to_children(flushed, list_size_threshold=2048)

            if prefix_len > self.stack[-1].prefix_len:
                # print("NEW PREFIX", word[:prefix_len], self.term_id)
                # NOTE changed NOTE self.stack += [Node(prefix_len, self.prefix_term_id, word[:prefix_len], False, 0)]
                self.stack += [Node(prefix_len, -1, word[:prefix_len], False, 0)]
                self.prefix_term_id += 1

            #print("Adding child", [last[:flushed.prefix_len]])
            self.stack[-1].children += [flushed] # last[:flushed.prefix_len]]

        self.term_id_map.append(term_id)
        # print("NEW WORD", word, self.term_id)
        self.stack += [Node(len(word), self.term_id, word, True, freq)]
        self.term_id += 1

        # print("STACK", self.stack)
        self.last_word = word

    def finish(self):
        # Flush all terms resting on stack by providing phantom empty word ""
        self.add("", -1, -1)

        _ = self.stack.pop() # Now pop off this empty "" word
        self.term_id_map.pop()

        root = self.stack.pop()
        root.term_id = self.prefix_term_id

        self.flush_children(root)
        self.assign_list_group_to_children(root, list_size_threshold=max(32, self.threshold // 200))

        # Create last list group for all not yet groupped terms, which are
        # children of root
        self.create_list_group(root)

        # Already sorted
        for group_id in self.group_map:
            self.group_map_w.write(group_id)

        # Write mapping from old_term_id to new_term_id, which corresponds to
        # lexicographic sort of terms
        for new_term_id in invert(self.term_id_map):
            self.term_id_map_w.write(new_term_id)

        self.close_seqs()

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("usage: ./mktrie OUTDIR #WORDS #OCCURRENCES < words", file=sys.stderr)
        sys.exit(1)

    outdir = sys.argv[1]
    num_words = int(sys.argv[2])
    num_occurrences = int(sys.argv[3])
    t = TrieBuilder(outdir, num_words, num_occurrences)

    for line in sys.stdin:
        word, term_id, frequency = line.strip().split("\t")
        #print("Adding", word, term_id, frequency)
        t.add(word, int(term_id), int(frequency))

    t.finish()
