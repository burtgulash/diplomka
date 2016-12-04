class Seq:
    def __iter__(self):
        return self
    def skip_n(self, n):
        for _ in range(n):
            next(self)

class ArraySeq(Seq):
    def __init__(self, slc):
        self.slc = slc
        self.i = 0
    def __next__(self):
        if self.i < len(self.slc):
            self.i += 1
            return self.slc[self.i - 1]
        else:
            raise StopIteration
    def subseq(self, start, end):
        return ArraySeq(self.slc[self.i + start : self.i + end])

class AscSeq(Seq):
    def __init__(self, start, seq):
        self.seq = seq
        self.i = start
    def __next__(self):
        n = next(self.seq)
        self.i += 1
        return n + self.i - 1
    def subseq(self, start, end):
        sub = AscSeq(start, self.seq.subseq(start, end))
        return sub

class CumSeq(Seq):
    def __init__(self, start, seq):
        self.seq = seq
        self.prev = start
    def __next__(self):
        prev = next(self.seq)
        cur = prev - self.prev
        self.prev = prev
        return cur
    def subseq(self, start, end):
        sub = self.seq.subseq(start - 1, end)
        return CumSeq(next(sub), sub)

class DeltaSeq(Seq):
    def __init__(self, start, seq):
        self.seq = seq
        self.cum = start
    def __next__(self):
        self.cum += next(self.seq)
        return self.cum
    def subseq(self, start, end):
        return self.seq.subseq(start - 1, end)
