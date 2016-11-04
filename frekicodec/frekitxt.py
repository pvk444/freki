import re
import unittest


def linepresort(a):
    order = ['line', 'tag', 'lang_name', 'lang_code', 'span_id', 'fonts']
    return order.index(a) if a in order else len(order)

class FrekiLine(object):
    def __init__(self, str_, **kwargs):
        self.str_ = str_
        self.tag = kwargs.get('tag')
        self.fonts = kwargs.get('fonts')
        self.line = kwargs.get('line')

    def preamble(self):
        pre_data = ['{}={}'.format(k, v) for k, v in sorted(vars(self).items(), key=lambda x: linepresort(x[0])) if
                    k != 'str_']
        return ' '.join(pre_data)

    def __str__(self):
        return '{}:{}'.format(' '.join(self.preamble()), self.str_)

    @classmethod
    def reads(cls, line):
        """
        Create a line from a formatted freki line.

        :param line: string
        :rtype: FrekiLine
        """
        preamble, text = re.search('(line.*?):(.*)', line).groups()
        preamble_data = re.findall('\S+=[^=]+(?=(?:\s+\S+)|\s*$)', preamble)
        line_preamble = {k.strip():v for k, v in [item.split('=') for item in preamble_data]}
        return cls(text, **line_preamble)

# -------------------------------------------
# FrekiBlock
# -------------------------------------------
class FrekiBlock(object):
    def __init__(self, block_id=None, doc_id=None, page=None, lines=None, bbox=None):
        self.lines = [] if lines is None else lines
        self.block_id = block_id
        self.doc_id = doc_id
        self.page = page
        self.llx, self.lly, self.urx, self.ury = [None]*4 if not bbox else bbox

    def __str__(self):
        start_line = self.lines[0].line if self.lines else 0  # Get the starting line number
        stop_line  = self.lines[-1].line if self.lines else 0 # Get the endling line number

        ret_str = 'doc_id={} page={} block_id={} bbox={} {} {}\n'.format(self.doc_id,
                                                                   self.page,
                                                                   self.block_id,
                                                                   ','.join(['{:g}'.format(i) for i in [self.llx, self.lly, self.urx, self.ury]]),
                                                                    start_line, stop_line)

        max_pre_len = max([len(l.preamble()) for l in self.lines]) if len(self.lines) else 0

        ret_str += '\n'.join(['{{:<{}}}:{{}}'.format(max_pre_len).format(line.preamble(), line.str_) for line in self.lines])

        return ret_str

    def append(self, l):
        self.lines.append(l)

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


                    new_block = FrekiBlock(block_id=doc_preamble['block_id'],
                                           doc_id=doc_preamble['doc_id'],
                                           page=doc_preamble.get('page'),
                                           bbox=[float(i) for i in doc_preamble.get('bbox').split(',')])

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

# =============================================================================
# Unit test
# =============================================================================

class FrekiDocTest(unittest.TestCase):
    def runTest(self):

        fd = FrekiDoc.read('/Users/rgeorgi/Documents/code/igt-detect/4-match-fixed/3.txt')
        print(fd)