
from __future__ import absolute_import

from collections import Counter
from gzip import GzipFile
from xml.etree import ElementTree as ET

from .base import FrekiReader, Token, Page


class TetmlReader(FrekiReader):
    def __init__(self, tetml_file, debug=False):
        FrekiReader.__init__(self, debug=debug)
        if tetml_file.endswith('.gz'):
            f = GzipFile(tetml_file)
        else:
            f = tetml_file
        self.file = f
        self._pages = {}
        self.init_pages()

    def init_pages(self):
        # iterparse to strip namespaces (is there a better way?)
        # thanks: https://bugs.python.org/msg216774
        xml_iter = ET.iterparse(self.file)
        for event in xml_iter:
            _, elem = event
            elem.tag = elem.tag.split('}', 1)[-1]
            if elem.tag == 'Page':
                pagenum = int(elem.get('number'))
                self._pages[pagenum] = Page(
                    pagenum,
                    float(elem.get('width')),
                    float(elem.get('height')),
                    tokens=self.init_tokens_for_page(elem)
                )
        #self.doc = xml_iter.root  # NOTE: non-documented attribute

    def word_to_token(self, word_elem):
        text = word_elem.find('Text').text
        box = word_elem.find('Box')
        glyphs = word_elem.findall('.//Glyph')
        # token font face/size is most common pair

        font_info = Counter(
            (g.get('font'), g.get('size')) for g in glyphs
        ).most_common(1)[0][0]

        features = {}
        sub_sup = Counter(
            (g.get('sub', ''), g.get('sup', '')) for g in glyphs
        ).most_common(1)[0][0]
        if sub_sup[0]: features['sub'] = True
        if sub_sup[1]: features['sup'] = True

        text = ''
        last_size = None
        last_sub  = None
        for g in glyphs:
            size = float(g.get('size'))
            sub  = g.get('sub', False)

            if last_size is None:
                last_size = size

            if (sub and not last_sub) or size < last_size:
                text += '_{}'.format(g.text)
            else:
                text += g.text

            last_size = size
            last_sub  = sub

        token = Token(
            text,
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
        return token

    def init_tokens_for_page(self, page):
        tokens = []
        words = []
        
        for word in page.findall('.//Word'):
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
        return tokens

    def pages(self, *page_ids):
        if not page_ids:
            page_ids = sorted(self._pages)
        return [self._pages[pid] for pid in page_ids]
