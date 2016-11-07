"""
This module is included to have a standard
text-based serialization format for the output
of Freki, namely:

A "Document" is a collection of "Blocks".

A "Block" is a collection of "Lines", that also have
metadata regarding page number in the original
PDF, and x,y coordinate positions within that page.

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


class FrekiDoc(object):
    """
    Class to contain unified reading/writing of freki documents.
    """
    def __init__(self):
        self.blockmap = OrderedDict()
        self.linemap = OrderedDict()

    @classmethod
    def read(cls, path):
        """
        Read in a Freki Document
        :param path:
        :return:
        """
        fd = cls()
        with open(path, 'r', encoding='utf-8') as f:

            # Keep track of the most recent data
            cur_block = None

            for line in f:

                # Skip blank lines
                if not line.strip():
                    continue

                # Parse the block preamble
                if line.startswith('doc_id'):
                    doc_preamble = {a:b for a,b in [item.split('=') for item in line.split()[:-2]]}


                    new_block = FrekiBlock(**doc_preamble)

                    # Dont add the first block
                    if cur_block is not None:
                        fd.blockmap[cur_block.block_id] = cur_block

                    cur_block = new_block

                elif line.startswith('line'):
                    l = FrekiLine.reads(line)
                    l.block = cur_block.block_id
                    fd.linemap[l.lineno] = l
                    cur_block.append(l)

            # Add the last block in the queue at the document's end
            if cur_block:
                fd.blockmap[cur_block.block_id] = cur_block

        return fd

    def __str__(self):
        return '\n\n'.join([str(b) for b in self.blocks])

    def get_line(self, lineno):
        return self.linemap.get(lineno)

    def lines(self):
        """
        Return all the lines in this document.
        :rtype: list[FrekiLine]
        """
        for line in self.linemap.values():
            yield line

    @property
    def blocks(self):
        return list(self.blockmap.values())


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
    def __init__(self, lines=None, start_line=None, stop_line = None, **kwargs):
        self.linedict = OrderedDict() if lines is None else lines
        self._attrs = kwargs

    @property
    def lines(self): return list(self.linedict.values())

    @property
    def page(self): return int(self._attrs.get('page'))

    @property
    def block_id(self): return self._attrs.get('block_id')

    @property
    def bbox(self): return [int(i) for i in self.bbox_str.split(',')]

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

    def append(self, l):
        self.linedict[l.lineno] = l

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
        return s

    @property
    def tag(self):
        return self.attrs.get('tag', 'O')

    @property
    def lineno(self):
        return int(self.attrs.get('line'))

    @property
    def fonts(self):
        """
        :rtype: list[FrekiFont]
        """
        return [FrekiFont.reads(f) for f in self.attrs.get('fonts', '').split(',')]

    @property
    def block(self):
        return self.attrs.get('block_id')

    @block.setter
    def block(self, v):
        self.attrs['block_id'] = v


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
        line_preamble = {k.strip():v for k, v in [item.split('=') for item in preamble_data]}
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
