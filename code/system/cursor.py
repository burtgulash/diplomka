import math
import heapq

MAX_DOC = 2**32 - 1
MAX_TERM = 2**32 - 1

class Cursor:

    def __init__(self, docs, tids, pos, chpos, size):
        self.docs = docs
        self.tids = tids
        self.pos = pos
        self.chpos = chpos
        self.tid_ahead_by = 0
        self.pos_ahead_by = 0
        self.tid = -1
        self.size = size
        self.current_doc = -1
        self.position = -1
        self.chposition = -1

    def size_hint(self):
        return self.size

    def current(self):
        return self.current_doc

    def advance(self):
        try:
            self.current_doc = next(self.docs)
        except StopIteration:
            self.current_doc = MAX_DOC
        self.tid_ahead_by += 1
        self.pos_ahead_by += 1
        return self.current_doc

    def advance_to(self, doc_id):
        while True:
            x = self.advance()
            if x >= doc_id:
                return x

    def term_id(self):
        if self.current_doc == MAX_DOC:
            return None

        #print("AHEAD BY", self.tid_ahead_by)
        for _ in range(self.tid_ahead_by):
            self.tid = next(self.tids)
            #print("TERM_IDDD", self.tid)
        self.tid_ahead_by = 0
        assert self.tid is not None
        return self.tid

    def positions(self):
        for _ in range(self.pos_ahead_by):
            self.position = next(self.pos)
            self.chposition = next(self.chpos)
        self.pos_ahead_by = 0
        assert self.position is not None
        assert self.chposition is not None
        return self.position, self.chposition


class FilteredCursor:

    def __init__(self, cursor, min_group_tid, tid_filter, filter_fill_factor, term_is):
        self.cursor = cursor
        self.tid_filter = tid_filter
        # assert len(self.tid_filter) > 0
        self.min_group_tid = min_group_tid
        self.filter_fill_factor = filter_fill_factor
        self.current_doc = self.prime_up()
        self.term_is = term_is

    def size_hint(self):
        return self.cursor.size_hint() * math.sqrt(math.sqrt(self.filter_fill_factor))

    def term_id(self):
        return self.cursor.term_id()

    def collect_one(self, target):
        term_id = self.term_id() + self.min_group_tid
        pos, chpos = self.cursor.positions()
        for term_i in self.term_is:
            target.append( (self.cursor.current(), term_i, term_id, pos, chpos) )

    def advance(self, target):
        current_doc = self.cursor.current()
        if current_doc == MAX_DOC:
            return current_doc
        while True:
            if self.cursor.current() != MAX_DOC and self._validate_term_id():
                self.collect_one(target)
            x = self.cursor.advance()
            if x > current_doc:
                if self._validate_term_id():
                    return x
                return self.to_next()

    def _validate_term_id(self):
        if self.cursor.current() == MAX_DOC:
            return True
        term_id = self.term_id()
        term_id += self.min_group_tid
        return term_id in self.tid_filter
    
    def current(self):
        return self.cursor.current()

    def prime_up(self):
        while True:
            x = self.cursor.advance()
            if self._validate_term_id():
                return x

    def to_next(self):
        while True:
            x = self.cursor.advance()
            if self._validate_term_id():
                return x

    def advance_to(self, doc_id):
        x = self.cursor.advance_to(doc_id)
        if self._validate_term_id():
            return x
        return self.to_next()


class FullCursor:

    def __init__(self, cursor, min_group_tid, term_is):
        self.cursor = cursor
        self.min_group_tid = min_group_tid
        self.prime_up()
        self.term_is = term_is

    def size_hint(self):
        return self.cursor.size_hint()

    def term_id(self):
        return self.cursor.term_id()

    def current(self):
        return self.cursor.current()

    def prime_up(self):
        return self.cursor.advance()

    def collect_one(self, target):
        term_id = self.term_id() + self.min_group_tid
        pos, chpos = self.cursor.positions()
        for term_i in self.term_is:
            target.append( (self.cursor.current(), term_i, term_id, pos, chpos) )

    def advance(self, target):
        current_doc = self.cursor.current()
        if current_doc == MAX_DOC:
            return current_doc
        while True:
            self.collect_one(target)
            x = self.cursor.advance()
            if x > current_doc:
                return x

    def advance_to(self, doc_id):
        return self.cursor.advance_to(doc_id)


class CursorUnion1(Cursor):

    def __init__(self, cursors):
        self.size = sum(cur.size_hint() for cur in cursors) * math.sqrt(len(cursors))
        self.multiple = True
        self.cursors = list(sorted(cursors, key=lambda cur: cur.size_hint(), reverse=True))
        self.last_doc = self.prime_up()
        self.dead = []

    def size_hint(self):
        return self.size

    def current(self):
        return self.last_doc

    def prime_up(self):
        mincur, mindoc = None, 3333333333333
        for cur in self.cursors:
            x = cur.current()
            if x < mindoc:
                mincur, mindoc = cur, x
        assert mincur
        return mindoc

    def advance(self, target):
        mindoc = MAX_DOC
        for cur in self.cursors:
            if cur.current() < self.last_doc:
                x = cur.advance_to(self.last_doc)
                if x == MAX_DOC:
                    self.dead.append(cur)
                    continue
            if cur.current() > self.last_doc:
                if cur.current() < mindoc:
                    mindoc = cur.current()
                continue

            assert cur.current() == self.last_doc

            x = cur.advance(target)
            if x == MAX_DOC:
                self.dead.append(cur)
                continue
            if x < mindoc:
                mindoc = x

        if self.dead:
            for cur in self.dead:
                self.cursors.remove(cur)
            self.dead = []

        self.last_doc = mindoc
        return mindoc

    def advance_to(self, doc_id):
        if not self.cursors:
            return MAX_DOC

        mindoc = MAX_DOC
        for cur in self.cursors:
            if cur.current() < doc_id:
                x = cur.advance_to(doc_id)
                if x == MAX_DOC:
                    self.dead.append(cur)
                    continue
            if cur.current() < mindoc:
                mindoc = cur.current()
            if cur.current() == doc_id:
                break

        if self.dead:
            for cur in self.dead:
                self.cursors.remove(cur)
            self.dead = []

        self.last_doc = mindoc
        return mindoc


class FrontierItem:

    def __init__(self, cursor):
        self.cursor = cursor

    def __lt__(self, other):
        return self.cursor.current() < other.cursor.current()


class CursorUnion2(Cursor):

    def __init__(self, cursors):
        self.size = sum(cur.size_hint() for cur in cursors) * math.sqrt(len(cursors))
        self.frontier = [FrontierItem(cursor) for cursor in cursors]
        heapq.heapify(self.frontier)

    def size_hint(self):
        return self.size

    def current(self):
        return self.frontier[0].cursor.current()

    def prime_up(self):
        return

    def advance(self, target):
        top = self.frontier[0]
        current_doc = top.cursor.current()
        while top.cursor.current() == current_doc:
            top.cursor.advance(target)
            heapq.heapreplace(self.frontier, top)
            top = self.frontier[0]
        return top.cursor.current()

    def advance_to(self, doc_id):
        top = self.frontier[0]
        while top.cursor.current() < doc_id:
            top.cursor.advance_to(doc_id)
            heapq.heapreplace(self.frontier, top)
            top = self.frontier[0]
        return top.cursor.current()


class CursorUnion3(Cursor):

    def __init__(self, cursors):
        self.size = sum(cur.size_hint() for cur in cursors) * math.sqrt(len(cursors))
        self.cursors = list(cursors)
        self.current_doc = self.prime_up()

    def size_hint(self):
        return self.size

    def current(self):
        return self.current_doc

    def prime_up(self):
        return min(cur.current() for cur in self.cursors)

    def advance(self, target):
        mindoc = MAX_DOC
        current_doc = self.current_doc
        for cur in self.cursors:
            x = cur.current()
            while x == current_doc:
                x = cur.advance(target)
            if x < mindoc:
                mindoc = x

        self.current_doc = mindoc
        return self.current_doc

    def advance_to(self, doc_id):
        mindoc = MAX_DOC
        for cur in self.cursors:
            x = cur.current()
            if x < doc_id:
                x = cur.advance_to(doc_id)
            if x < mindoc:
                mindoc = x

        self.current_doc = mindoc
        return self.current_doc


class CursorUnion4(Cursor):

    def __init__(self, cursors):
        self.size = sum(cur.size_hint() for cur in cursors) * math.sqrt(len(cursors))
        self.cursors = list(cursors)
        self.current_doc = self.prime_up()
        self.dead = []

    def size_hint(self):
        return self.size

    def current(self):
        return self.current_doc

    def prime_up(self):
        return min(cur.current() for cur in self.cursors)

    def advance(self, target):
        mindoc = MAX_DOC
        current_doc = self.current_doc
        for cur in self.cursors:
            x = cur.current()
            while x == current_doc:
                x = cur.advance(target)
            if x == MAX_DOC:
                self.dead.append(cur)
                continue
            if x < mindoc:
                mindoc = x
        
        if self.dead:
            for cur in self.dead:
                self.cursors.remove(cur)
            self.dead = []

        self.current_doc = mindoc
        return self.current_doc

    def advance_to(self, doc_id):
        mindoc = MAX_DOC
        for cur in self.cursors:
            x = cur.current()
            if x < doc_id:
                x = cur.advance_to(doc_id)
            if x == MAX_DOC:
                self.dead.append(cur)
                continue
            if x < mindoc:
                mindoc = x
        
        if self.dead:
            for cur in self.dead:
                self.cursors.remove(cur)
            self.dead = []

        self.current_doc = mindoc
        return self.current_doc


class CursorIntersection(Cursor):

    def __init__(self, cursors):
        assert cursors
        self.size = min(cur.size_hint() for cur in cursors)
        self.cursors = list(sorted(cursors, key=lambda cur: cur.size_hint()))
        self.align_to = self.prime_up()

    def size_hint(self):
        return self.size

    def prime_up(self):
        maxcur, maxdoc = None, -1
        for cur in self.cursors:
            x = cur.current()
            if x > maxdoc:
                maxcur, maxdoc = cur, x
        self.align_to = maxdoc
        assert maxcur
        return maxdoc

    def advance(self, target):
        while True:
            if self.align_to == MAX_DOC:
                return MAX_DOC

            aligned = True
            for cur in self.cursors:
                assert cur.current() <= self.align_to
                if cur.current() < self.align_to:
                    x = cur.advance_to(self.align_to)
                    if x > self.align_to:
                        self.align_to = x
                        aligned = False
                        break
                    assert x == self.align_to
                assert cur.current() == self.align_to
            if aligned:
                break


        maxdoc = -1
        for cur in self.cursors:
            # assert cur.current() == self.align_to
            x = cur.advance(target)
            if x > maxdoc:
                maxdoc = x

        prev = self.align_to
        self.align_to = maxdoc
        return prev
