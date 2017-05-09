
from __future__ import absolute_import

import re
from io import StringIO
from xml.etree import ElementTree as ET

from freki.readers.base import FrekiReader
from freki.structures import Token, Line, Block, Page

max_char_dx = 0.05

class PdfMinerReader(FrekiReader):
    def __init__(self, xml_file, debug=False):
        FrekiReader.__init__(self, debug=debug)
        self.file = xml_file
        self._pages = {}
        self._init_pages()

    def _init_pages(self):
        # PDFMiner can return XML with bad characters. First fix those:
        lines = []
        f = open(self.file) if not hasattr(self.file, 'readline') else self.file
        for line in f:
            lines.append(replace_invalid_xml_chars(line))
        instream = StringIO(''.join(lines))

        # iterparse to strip namespaces (is there a better way?)
        # thanks: https://bugs.python.org/msg216774
        xml_iter = ET.iterparse(instream)
        for event in xml_iter:
            _, elem = event
            elem.tag = elem.tag.split('}', 1)[-1]
            if elem.tag == 'page':
                page = _read_page(elem)
                self._pages[page.id] = page

    def pages(self, *page_ids):
        if not page_ids:
            page_ids = sorted(self._pages)
        return [self._pages[pid] for pid in page_ids]


def _read_page(elem):
    blocks = []
    p_llx, p_lly, p_urx, p_ury = map(float, elem.get('bbox').split(','))
    for textbox in elem.findall('textbox'):
        lines = []
        for textline in textbox.findall('textline'):
            tokens, glyphs, features = [], [], {}
            last_urx = last_fontspec = last_width = last_isalnum = None
            for glyph in textline.findall('text'):
                text = glyph.text
                if text.isspace():
                    continue
                fontspec = (glyph.get('font'), float(glyph.get('size')))
                bbox = tuple(map(float, glyph.get('bbox').split(',')))
                llx, lly, urx, ury = bbox
                dx = 0 if last_urx is None else llx - last_urx
                width = urx - llx
                avg_width = width if not last_width else (last_width+width)/2
                isalnum = text.isalnum()
                if last_isalnum is None: last_isalnum = isalnum
                if (not glyphs or
                    (fontspec == last_fontspec
                        and (dx / avg_width) <= max_char_dx
                        and last_isalnum == isalnum)):
                    glyphs.append((text, fontspec, bbox, features))
                else:
                    tokens.append((glyphs, features))
                    glyphs = [(text, fontspec, bbox, features)]
                    features = {}
                last_urx, last_width = urx, width
                last_fontspec, last_isalnum = fontspec, isalnum
            if glyphs:
                tokens.append((glyphs, features))

            lines.append(
                Line(
                    [
                        Token(
                            ''.join(g[0] for g in glyphs),  # text
                            (
                                min(g[2][0] for g in glyphs),  # llx
                                min(g[2][1] for g in glyphs),  # lly
                                max(g[2][2] for g in glyphs),  # urx
                                max(g[2][3] for g in glyphs)   # ury
                            ),
                            glyphs[0][1][0],  # font
                            # glyphs[0][1][1],  # size
                            features
                        )
                        for glyphs, features in tokens
                    ]
                )
            )

        blocks.append(Block(lines, id=int(textbox.get('id'))))

    page = Page(
        blocks=blocks,
        id=int(elem.get('id')),
        page_width=p_urx - p_llx,
        page_height=p_ury - p_lly
    )
    return page


invalid_char_re = re.compile(
    '[^\x09\x0A\x0D\u0020-\uD7FF\uE000-\uFFFD'
    #'\U00010000-\U0010FFFF]'
    ']'
    , re.UNICODE
)


def replace_invalid_xml_chars(input, replacement_char='\uFFFD'):
    # \uFFFD is the unicode replacement character
    return invalid_char_re.sub(replacement_char, input)
