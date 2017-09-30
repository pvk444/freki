
from __future__ import absolute_import

from collections import Counter
from gzip import GzipFile
from xml.etree import ElementTree as ET

from freki.readers.base import FrekiReader
from freki.structures import Token, Line, Block, Page


class TetmlReader(FrekiReader):
    def __init__(self, tetml_file, debug=False):
        FrekiReader.__init__(self, debug=debug)
        if hasattr(tetml_file, 'read'):
            f = tetml_file
        else:
            if tetml_file.endswith('.gz'):
                f = GzipFile(tetml_file)
            else:
                f = open(tetml_file, 'r')

        self.file = f
        self._pages = {}
        self._init_pages()

    def _init_pages(self):
        # iterparse to strip namespaces (is there a better way?)
        # thanks: https://bugs.python.org/msg216774
        xml_iter = ET.iterparse(self.file)
        for event in xml_iter:
            _, elem = event
            elem.tag = elem.tag.split('}', 1)[-1]
            if elem.tag == 'Page':
                page = _read_page(elem)
                self._pages[page.id] = page

    def pages(self, *page_ids):
        if not page_ids:
            page_ids = sorted(self._pages)
        return [self._pages[pid] for pid in page_ids]


def _read_page(elem):
    blocks = []
    for i, para in enumerate(elem.findall('.//Para')):
        block = Block(id=i+1)
        tokens = []
        for word in para.findall('.//Word'):
            text = word.find('Text').text
            # dehyphenated words have 2+ boxes; we care more about layout,
            # so we will make separate tokens (this can also be done by
            # changing the TET extraction settings).
            for box in word.findall('Box'):
                glyphs = box.findall('Glyph')
                boxtext = ''.join(g.text for g in glyphs)
                features = {}

                if glyphs and glyphs[-1].get('dehyphenation') == 'pre':
                    boxtext += '-'
                    features['dehyphenation'] = 'pre'
                elif glyphs and glyphs[0].get('dehyphenation') == 'post':
                    features['dehyphenation'] = 'post'

                font_info = Counter(
                    (g.get('font'), g.get('size')) for g in glyphs
                ).most_common(1)[0][0]

                # TETML detects if a glyph is a super/subscript; again,
                # go with the most common for all glyphs in word
                sub_sup = Counter(
                    (g.get('sub', ''), g.get('sup', '')) for g in glyphs
                ).most_common(1)[0][0]
                if sub_sup[0]: features['sub'] = True
                if sub_sup[1]: features['sup'] = True
                token = Token(
                    boxtext,
                    (
                        float(box.get('llx')),
                        float(box.get('lly')),
                        float(box.get('urx')),
                        float(box.get('ury'))
                    ),
                    font=font_info[0],
                    # size=float(font_info[1]),
                    features=features
                )
                tokens.append(token)
        # for now all tokens in a Block go into a single Line because
        # it's not trivial to find lines by examining baselines, and
        # we don't (necessarily) have the line info from TET
        line = Line(tokens=tokens)
        block.append(line)
        blocks.append(block)
                
    page = Page(
        blocks=blocks,
        id=int(elem.get('number')),
        page_width=float(elem.get('width')),
        page_height=float(elem.get('height'))
    )
    return page
