
from collections import namedtuple, defaultdict, Counter

min_line_overlap = 0.01

class Token(namedtuple('Token', ('text', 'llx', 'lly', 'urx', 'ury',
                                 'font', 'size', 'features'))):

    def __new__(cls, text, llx, lly, urx, ury,
                font=None, size=None, features=None):
        # round positions to tenths
        llx = round(llx, 1)
        lly = round(lly, 1)
        urx = round(urx, 1)
        ury = round(ury, 1)
        if size is None:
            size = ury - lly  # estimate size if unknown
        if features is None:
            features = {}
        return super(Token, cls).__new__(
            cls, text, llx, lly, urx, ury, font, size, features
        )

    @property
    def width(self):
        return self.urx - self.llx

    @property
    def height(self):
        return self.ury - self.lly

class TokContainer(object):
    def __init__(self, tokens=None):
        if tokens is None: tokens = []
        self.tokens = []
        self._llx = self._lly = self._urx = self._ury = None
        for token in tokens:
            self.append(token)

    def append(self, token):
        if not isinstance(token, Token):
            raise TypeError('Line objects can only contain Token objects.')
        self._llx = self._lly = self._urx = self._ury = None  # reset
        self.tokens.append(token)

    def extend(self, tokens):
        for token in tokens:
            self.append(token)


    @property
    def llx(self):
        if self._llx is None and self.tokens:
            self._llx = min(t.llx for t in self.tokens)
        return self._llx


    @property
    def lly(self):
        if self._lly is None and self.tokens:
            self._lly = min(t.lly for t in self.tokens)
        return self._lly


    @property
    def urx(self):
        if self._urx is None and self.tokens:
            self._urx = max(t.urx for t in self.tokens)
        return self._urx


    @property
    def ury(self):
        if self._ury is None and self.tokens:
            self._ury = max(t.ury for t in self.tokens)
        return self._ury


    @property
    def width(self):
        return self.urx - self.llx


    @property
    def height(self):
        return self.ury - self.lly

    def __iter__(self):
        return iter(self.tokens)

    def __repr__(self):
        return ' '.join([t.text for t in self.tokens])

class Line(TokContainer):

    def sort(self):
        self.tokens.sort(key=lambda tok: tok.llx)

    def overlap(self, other):
        a, b = self, other
        if a.ury <= b.lly or a.lly >= b.ury:
            return 0.0

        if a.ury == b.ury and a.lly == b.lly:
            return 1.0

        if a.height < b.height:
            a, b = b, a

        if b.height:
            return 0.0

        if a.ury < b.ury:
            return (a.ury - b.lly) / b.height
        else:
            return (b.ury - a.lly) / b.height




class Para(TokContainer):
    pass


class Page (namedtuple('Page', ('id', 'width', 'height', 'pgphs'))):

    @property
    def tokens(self):
        for p in self.pgphs:
            for t in p:
                yield t


class Block(namedtuple('Block', ('id', 'lines'))):
    def __new__(cls, lines=None, page=None, id=None):
        if lines is None:
            lines = []
        return super(Block, cls).__new__(cls, id, lines)

    @property
    def tabular(self):
        return len(self.tabular_lines()) > 0

    def tabular_lines(self):
        indices = set()
        for i, pair in enumerate(zip(self.lines[:-1], self.lines[1:])):
            a, b = pair
            a_locs = {t.llx: 1 for t in a.tokens}
            algns = sum(a_locs.get(t.llx, 0) for t in b.tokens)
            if algns / float(len(b.tokens)) >= 0.2:
                indices.add(i)
                indices.add(i+1)
        return indices

    @property
    def _llxs(self):
        return list((line.llx for line in self.lines))

    @property
    def _llys(self):
        return list((line.lly for line in self.lines))

    @property
    def _urxs(self):
        return list((line.urx for line in self.lines))

    @property
    def _urys(self):
        return list((line.ury for line in self.lines))

    @property
    def llx(self):
        return  0 if not len(self._llxs) else min(self._llxs)

    @property
    def lly(self):
        return 0 if not self._llys else min(self._llys)

    @property
    def urx(self):
        return 0 if not self._urxs else max(self._urxs)

    @property
    def ury(self):
        return 0 if not self._urys else max(self._urys)


class FrekiReader(object):

    def _line_dy(self):
        all_line_diffs = []
        for page in self.pages():
            lines = self.lines(page)
            line_diffs = [a.lly - b.ury for a, b in zip(lines[:-1], lines[1:])]
            all_line_diffs.extend(line_diffs)

        if not all_line_diffs:
            line_dy = 0
        elif len(all_line_diffs) == 1:
            line_dy = all_line_diffs[0]
        else:
            # Get the average line diff.
            # line_dy = statistics.mean(line_diffs)
            line_dy = Counter(all_line_diffs).most_common(1)[0][0]
            # line_dy = max(line_diffs)
            # line_dy = statistics.variance(line_diffs) - statistics.stdev(line_diffs)

        return line_dy

    def pages(self, *page_ids):
        '''
        Return the Page objects for the document.
        Zero or more *page_ids* may be specified, which are the page
        numbers (e.g. `1` is the first page). If zero *page_ids* are
        given, all pages are returned in order.
        '''
        raise NotImplementedError()

    def blocks(self, page, coefficient=1.0):
        lines = self.lines(page)
        line_dy = coefficient * self._line_dy()
        i = 1

        block = Block(id='{}-{}'.format(page.id, i))
        last_y = lines[0].lly
        for line in lines:
            if last_y - line.ury > line_dy or last_y - line.ury < 0:
                yield block
                i += 1
                block = Block(id='{}-{}'.format(page.id, i))
            block.lines.append(line)
            last_y = line.lly

        # If we still have an unreturned block...
        yield block

    def page_xmin(self, page):
        tokens = list(page.tokens)
        if len(tokens) == 0:
            return 0
        else:
            return sorted(tokens, key=lambda x: x.llx)[0].llx

    def page_xmax(self, page):
        tokens = list(page.tokens)
        if len(tokens) == 0:
            return 0
        else:
            return sorted(tokens, key=lambda x: x.urx)[-1].urx

    def page_baselines(self, page):
        return sorted(set([t.lly for t in page.tokens]))

    def _baseline_dict(self, page):
        basedict = defaultdict(list)
        for token in page.tokens:
            basedict[token.lly].append(token)
        return basedict

    def page_xmiddle(self, page):
        """The point at the middle of the page"""
        return (self.page_xmin(page) + self.page_xmax(page)) / 2

    def page_width(self, page):
        return self.page_xmax(page) - self.page_xmin(page)

    def crossing_tokens(self, page, x):
        """A list of tokens on the page that cross over point x"""
        return [t for t in page.tokens if t.llx < x < t.urx]

    def is_dual_column(self, page):
        """
        Return whether there is a gap that no tokens cross for an unbroken 2/3
        of the page or more.

        :rtype: bool
        """
        basedict = self._baseline_dict(page)
        middle_x = self.page_xmiddle(page)

        longest_span = 0
        current_span = 0

        for lly in self.page_baselines(page):
            crossing_tokens = [t for t in basedict[lly] if t.llx < middle_x < t.urx]
            if not crossing_tokens:
                current_span += 1
                if current_span > longest_span:
                    longest_span = current_span
            else:
                current_span = 0

        # Return true if the longest span of "lines" that do not cross
        if len(self.page_baselines(page)) == 0:
            return False
        else:
            return (longest_span / len(self.page_baselines(page))) >= 0.9

    def lines_in_dual_column_order(self, page):
        """:type page: Page"""
        left_tokens  = [t for t in page.tokens if t.urx < self.page_xmiddle(page)]
        right_tokens = [t for t in page.tokens if t.llx > self.page_xmiddle(page)]

        left_lines  = tokens_to_lines(left_tokens)
        right_lines = tokens_to_lines(right_tokens)

        return merge_some_lines(left_lines) + merge_some_lines(right_lines)



    def lines_in_tet_order(self, page):
        """:type page: Page"""
        page_lines = []
        for para in page.pgphs:
            para_lines = tokens_to_lines(para.tokens)
            page_lines.extend(para_lines)

        page_lines = merge_lines(page_lines)

        return page_lines

    def lines(self, page):
        # lines = merge_lines(self.lines_in_tet_order(page))
        #
        # for line in lines:
        #     line.sort()
        if self.is_dual_column(page):
            return self.lines_in_dual_column_order(page)
        else:
            return self.lines_in_tet_order(page)

def tokens_to_lines(tokens):
    lines = []
    last_llx = None
    cur_line = Line()
    for token in tokens:
        if last_llx is None:
            last_llx = token.llx
            cur_line.append(token)
            continue
        if token.llx < last_llx:
            lines.append(cur_line)
            cur_line = Line(tokens=[token])
        else:
            cur_line.append(token)
        last_llx = token.llx

    lines.append(cur_line)

    for line in lines:
        line.sort()

    return lines

def merge_some_lines(lines):
    if not lines:
        return []

    new_lines = []
    cur_line = lines.pop(0)
    i = 1
    while lines:
        next_line = lines.pop(0)
        if cur_line.overlap(next_line) >= min_line_overlap:
            cur_line.extend(next_line)
        # elif next_line.overlap(cur_line) >= min_line_overlap:
        #     cur_line.extend(next_line)
        else:
            new_lines.append(cur_line)
            i+= 1
            cur_line = next_line

    new_lines.append(cur_line)

    return new_lines



def merge_lines(lines):
    # merge lines that overlap (e.g. super/subscripts)
    if not lines:  # no text content?
        return []


    merged_lines = [lines[0]]
    for line in lines[1:]:
        merged = False
        for line2 in merged_lines:
            if line.overlap(line2) >= min_line_overlap:
                line2.extend(line.tokens)
                merged = True
                break
        if not merged:
            merged_lines.append(line)
            # sort by page order and return
    return merged_lines