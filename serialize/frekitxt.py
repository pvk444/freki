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
import unittest


# -------------------------------------------
# FrekiDoc
#
# Representation of a document, consisting of a collection
# of blocks.
# -------------------------------------------
class FrekiDoc(object):
    """
    Class to contain unified reading/writing of freki documents.
    """
    def __init__(self):
        self.blocks = []

    @classmethod
    def read(self, path):
        """
        Read in a Freki Document
        :param path:
        :return:
        """
        fd = FrekiDoc()
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
                        fd.blocks.append(cur_block)
                    cur_block = new_block

                elif line.startswith('line'):
                    l = FrekiLine.reads(line)
                    cur_block.append(l)

            # Add the last block in the queue at the document's end
            if cur_block:
                fd.blocks.append(cur_block)

        return fd

    def __str__(self):
        return '\n\n'.join([str(b) for b in self.blocks])

    def text_lines(self):
        for block in self.blocks:
            for line in block.lines:
                yield line.str_

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
        self.lines = [] if lines is None else lines
        self._attrs = kwargs

    @property
    def page(self): return self._attrs.get('page')

    @property
    def block_id(self): return self._attrs.get('block_id')

    @property
    def bbox(self): return self._attrs.get('bbox', '0,0,0,0')

    @property
    def doc_id(self): return self._attrs.get('doc_id')

    def __str__(self):
        start_line = self.lines[0].lineno if self.lines else 0  # Get the starting line number
        stop_line  = self.lines[-1].lineno if self.lines else 0 # Get the endling line number

        ret_str = 'doc_id={} page={} block_id={} bbox={} {} {}\n'.format(self.doc_id,
                                                                   self.page,
                                                                   self.block_id,
                                                                   self.bbox,
                                                                    start_line, stop_line)

        max_pre_len = max([len(l.preamble()) for l in self.lines]) if len(self.lines) else 0

        ret_str += '\n'.join(['{{:<{}}}:{{}}'.format(max_pre_len).format(line.preamble(), line.str_) for line in self.lines])

        return ret_str

    def append(self, l):
        self.lines.append(l)

# -------------------------------------------
# FrekiLine
# -------------------------------------------

class FrekiLine(object):
    """
    The "Line" class
    """
    def __init__(self, str_, **kwargs):
        self.str_ = str_

        self.attrs = kwargs

    @property
    def tag(self):
        return self.attrs.get('tag', 'O')

    @property
    def lineno(self):
        return self.attrs.get('line')

    @property
    def fonts(self):
        return self.attrs.get('fonts')

    def preamble(self):
        """
        Returns the preamble metadata

        :return:
        """
        pre_data = ['{}={}'.format(k, v) for k, v in sorted(self.attrs.items(), key=lambda x: linesort(x[0])) if
                    k != 'str_']
        return ' '.join(pre_data)

    def __str__(self):
        return '{}:{}'.format(' '.join(self.preamble()), self.str_)

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





# =============================================================================
# Unit test
# =============================================================================

class FrekiDocTest(unittest.TestCase):
    def runTest(self):

        fd = FrekiDoc.read('/Users/rgeorgi/Documents/code/igt-detect/4-match-fixed/3.txt')
        print(fd)