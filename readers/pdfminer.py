
import re
from io import StringIO
from collections import Counter
from xml.etree import ElementTree as ET

from .base import FrekiReader, Token, Page

max_char_dx = 0.05

class PdfMinerReader(FrekiReader):
    def __init__(self, xml_file):
        self.file = xml_file
        self._pages = {}
        self.init_pages()

    def init_pages(self):
        # PDFMiner can return XML with bad characters. First fix those:
        invalid_char_re = re.compile(
            '[^\x09\x0A\x0D\u0020-\uD7FF\uE000-\uFFFD'
            #'\U00010000-\U0010FFFF]'
            ']'
            , re.UNICODE
        )
        def replace_invalid_xml_chars(input, replacement_char='\uFFFD'):
            # \uFFFD is the unicode replacement character
            return invalid_char_re.sub(replacement_char, input)
        lines = []
        for line in open(self.file):
            lines.append(replace_invalid_xml_chars(line))
        instream = StringIO(''.join(lines))

        # iterparse to strip namespaces (is there a better way?)
        # thanks: https://bugs.python.org/msg216774
        xml_iter = ET.iterparse(instream)
        i = 0
        for event in xml_iter:
            _, elem = event
            elem.tag = elem.tag.split('}', 1)[-1]
            if elem.tag == 'page':
                i += 1
                llx, lly, urx, ury = map(float, elem.get('bbox').split(','))
                self._pages[i] = Page(
                    i,
                    urx - llx,
                    ury - lly,
                    tokens=self.init_tokens_for_page(elem)
                )
        #self.doc = xml_iter.root  # NOTE: non-documented attribute

    def init_tokens_for_page(self, page):
        tokens = []
        glyphs = []
        features = {}
        last_urx = last_lly = None
        last_fontspec = last_width = last_isalnum = None
        for glyph in page.findall('.//text'):
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
                (lly == last_lly
                    and fontspec == last_fontspec
                    and (dx / avg_width) <= max_char_dx
                    and last_isalnum == isalnum)):
                glyphs.append((text, fontspec, bbox, features))
            else:
                tokens.append((glyphs, features))
                glyphs = [(text, fontspec, bbox, features)]
                features = {}
            last_urx, last_lly = urx, lly
            last_fontspec, last_width, last_isalnum = fontspec, width, isalnum
        if glyphs:
            tokens.append((glyphs, features))
        return [
            Token(
                ''.join(g[0] for g in glyphs),  # text
                min(g[2][0] for g in glyphs),  # llx
                min(g[2][1] for g in glyphs),  # lly
                max(g[2][2] for g in glyphs),  # urx
                max(g[2][3] for g in glyphs),  # ury
                glyphs[0][1][0],  # font
                glyphs[0][1][1],  # size
                features
            )
            for glyphs, features in tokens
        ]

    def pages(self, *page_ids):
        if not page_ids:
            page_ids = sorted(self._pages)
        return [self._pages[pid] for pid in page_ids]

    def tokens(self, page):
        return self._pages[p].tokens
