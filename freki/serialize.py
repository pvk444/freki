"""
This module is included to have a standard
text-based serialization format for the output
of Freki, namely:

A :FrekiDoc: is a collection of lines, as well as
the :FrekiBlock: elements that group lines.

A :FrekiBlock: also contains metadata regarding page
number in the original PDF and x,y coordinate positions
within that page.

A "Line" is a line of text, that also contains metadata
concerning the label and span membership for IGT status,
the fonts contained on that line, and language ID information.
"""

import re


# -------------------------------------------
# FrekiDoc
#
# Representation of a document, consisting of a collection
# of blocks.
# -------------------------------------------
from collections import OrderedDict
from unittest import TestCase


class FrekiDoc(object):
    """
    Class to contain unified reading/writing of freki documents.
    """
    def __init__(self):
        self.blockmap = OrderedDict()
        self.linemap = OrderedDict()

    def __len__(self):
        return len(self.linemap)

    @classmethod
    def read(cls, path):
        """
        Read in a Freki Document from a file.

        :param path:
        :return:
        """
        # Create the blank document that will be returned.
        fd = cls()

        # Open the path for reading.
        with open(path, 'r', encoding='utf-8') as f:

            cur_block = None

            for line in f:

                # Skip blank lines
                if not line.strip():
                    continue

                # If the line in the document
                # is describing a new block,
                # create the new block...
                if line.startswith('doc_id'):
                    doc_preamble = {a.strip():b.strip() for a,b in [item.split('=') for item in line.split()[:-2]]}
                    cur_block = FrekiBlock(**doc_preamble)

                    # Make the containing doc accessible
                    # to the block.
                    cur_block.doc = fd

                    # Add this current block to the blockmap.
                    fd.blockmap[cur_block.block_id] = cur_block

                # Otherwise, if we are passing a new line
                # element..
                elif line.startswith('line'):
                    fl = FrekiLine.reads(line)  # Parse it..
                    cur_block.add_line(fl)
                    fd.add_line(fl)

        return fd

    def __str__(self):
        return '\n\n'.join([str(b) for b in self.blocks])

    def get_line(self, lineno):
        """:rtype: FrekiLine"""
        return self.linemap.get(lineno)

    def set_line(self, lineno, line):
        """:type line: FrekiLine """
        self.linemap[lineno] = line

    def lines(self):
        """
        Return all the lines in this document.
        :rtype: list[FrekiLine]
        """
        for line in self.linemap.values():
            yield line

    def spans(self):
        """
        Return an ordered dict of the spans in the document, with
        their IDs.
        """
        spans = OrderedDict()
        cur_span = None
        cur_span_id = None

        for line in self.lines():
            # If there's a labeled span:
            if line.span_id is not None:
                if (cur_span_id != line.span_id) or (cur_span is None):
                    if cur_span is not None:
                        spans[cur_span_id] = tuple(cur_span)
                    cur_span = [line.lineno, line.lineno]
                    cur_span_id = line.span_id

                elif cur_span_id == line.span_id:
                    cur_span[1] = line.lineno

            elif cur_span is not None:
                spans[cur_span_id] = tuple(cur_span)
                cur_span = None

        return spans


    @property
    def blocks(self):
        """:rtype: list[FrekiBlock]"""
        return list(self.blockmap.values())

    def llxs(self):
        return [b.llx for b in self.blocks]

    def fonts(self):
        fonts = []
        for block in self.blocks:
            for font in block.fonts:
                fonts.append(font)
        return fonts

    def add_line(self, fl):
        """:type fl: FrekiLine"""
        fl.doc = self
        self.linemap[fl.lineno] = fl


def linesort(a):
    """
    Define the order of attributes for the line.
    """
    order = ['line', 'tag', 'span_id', 'lang_name', 'lang_code', 'fonts']
    return order.index(a) if a in order else len(order)

# -------------------------------------------
# FrekiBlock
# -------------------------------------------
class FrekiBlock(object):
    """
    The "Block" class, consisting of:
    """
    def __init__(self, linenos=None, start_line=None, stop_line = None, **kwargs):
        self.linenos = [] if linenos is None else linenos
        self._attrs = kwargs
        self.doc = None

    @property
    def doc(self) -> FrekiDoc: return self._doc

    @doc.setter
    def doc(self, v): self._doc = v

    @property
    def lines(self):
        """
        :rtype: list[FrekiLine]
        """
        return [self.doc.get_line(ln) for ln in self.linenos]

    @property
    def page(self): return int(self._attrs.get('page'))

    @property
    def block_id(self): return self._attrs.get('block_id')

    @property
    def bbox(self): return [float(i) for i in self.bbox_str.split(',')]

    @property
    def bbox_str(self): return self._attrs.get('bbox', '0,0,0,0')

    @property
    def llx(self): return self.bbox[0]

    @property
    def lly(self): return self.bbox[1]

    @property
    def urx(self): return self.bbox[2]

    @property
    def ury(self): return self.bbox[3]

    @property
    def fonts(self):
        fonts = []
        for line in self.lines:
            for font in line.fonts:
                fonts.append(font)
        return fonts

    @property
    def doc_id(self): return self._attrs.get('doc_id')

    def __str__(self):
        start_line = self.lines[0].lineno if self.lines else 0  # Get the starting line number
        stop_line  = self.lines[-1].lineno if self.lines else 0 # Get the endling line number

        ret_str = 'doc_id={} page={} block_id={} bbox={} {} {}\n'.format(self.doc_id,
                                                                         self.page,
                                                                         self.block_id,
                                                                         self.bbox_str,
                                                                         start_line, stop_line)

        max_pre_len = max([len(l.preamble()) for l in self.lines]) if len(self.lines) else 0

        ret_str += '\n'.join(['{{:<{}}}:{{}}'.format(max_pre_len).format(line.preamble(), line) for line in self.lines])

        return ret_str

    def add_line(self, line):
        line.block = self
        self.linenos.append(line.lineno)


# -------------------------------------------
# FrekiLine
# -------------------------------------------
class FrekiLine(str):
    """
    The "Line" class
    """
    def __new__(cls, seq='', **kwargs):
        s = super().__new__(cls, seq)
        setattr(s, 'attrs', kwargs)
        s.block = kwargs.get('block')
        s.doc = kwargs.get('doc')
        return s

    @property
    def tag(self): return self.attrs.get('tag', 'O')

    @property
    def lineno(self): return int(self.attrs.get('line'))

    @property
    def span_id(self): return self.attrs.get('span_id')

    @span_id.setter
    def span_id(self, v): self.attrs['span_id'] = v

    @property
    def fonts(self):
        """
        :rtype: list[FrekiFont]
        """
        return [FrekiFont.reads(f) for f in self.attrs.get('fonts', '').split(',')]

    @fonts.setter
    def fonts(self, fonts):
        """:type fonts: list[FrekiFont]"""
        self.attrs['fonts'] = ','.join([str(f) for f in fonts])


    @property
    def block(self) -> FrekiBlock:
        return self._block

    @block.setter
    def block(self, v):
        self._block = v

    @property
    def doc(self) -> FrekiDoc: return self._doc

    @doc.setter
    def doc(self, d): self._doc = d

    def preamble(self):
        """
        Returns the preamble metadata

        :return:
        """
        pre_data = ['{}={}'.format(k, v) for k, v in sorted(self.attrs.items(), key=lambda x: linesort(x[0])) if
                    k != 'str_']
        return ' '.join(pre_data)


    @classmethod
    def reads(cls, line):
        """
        Create a line from a formatted freki line.

        :param line: The string, including preamble
        :rtype: FrekiLine
        """
        preamble, text = re.search('(line.*?):(.*)', line).groups()
        preamble_data = re.findall('\S+=[^=]+(?=(?:\s+\S+)|\s*$)', preamble)
        line_preamble = {k.strip():v.strip() for k, v in [item.split('=') for item in preamble_data]}
        return cls(text, **line_preamble)

    def search(self, regex, flags=0):
        return re.search(regex, self, flags=flags)



class FrekiFont(object):
    """
    Quick representation for a (font_type-font_size) pair.
    """
    def __init__(self, f_type, f_size):
        self.f_type = f_type
        self.f_size = f_size

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '{}-{}'.format(self.f_type, self.f_size)

    def __eq__(self, other):
        return all([hasattr(other, 'f_type'),
                   hasattr(other, 'f_size'),
                   self.f_type == other.f_type,
                   self.f_size == other.f_size])

    def __hash__(self):
        return hash(str(self))

    @classmethod
    def reads(cls, s):
        f_type, f_size = s.split('-')
        return cls(f_type, float(f_size))

class ReadTest(TestCase):
    def runTest(self):
        fd = FrekiDoc.read('/Users/rgeorgi/Documents/code/igt-detect/5-gold/2624.txt')
        print(fd)