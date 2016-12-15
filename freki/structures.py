

class BBox(object):
    """
    Bounding boxes. For mixin methods for other classes, see Box.
    """
    def __init__(self, llx, lly, urx, ury):
        self.llx = llx
        self.lly = lly
        self.urx = urx
        self.ury = ury

    @property
    def width(self):
        return self.urx - self.llx

    @property
    def height(self):
        return self.ury - self.lly

    def merge(self, other):
        """
        Expand the box to contain itself and *other*.
        """
        if None in (self.llx, other.llx):
            self.llx = self.llx or other.llx
        else:
            self.llx = min(self.llx, other.llx)

        if None in (self.lly, other.lly):
            self.lly = self.lly or other.lly
        else:
            self.lly = min(self.lly, other.lly)

        if None in (self.urx, other.urx):
            self.urx = self.urx or other.urx
        else:
            self.urx = max(self.urx, other.urx)

        if None in (self.ury, other.ury):
            self.ury = self.ury or other.ury
        else:
            self.ury = max(self.ury, other.ury)


class Box(object):
    """
    Mixin class for things with bounding boxes.
    """

    @property
    def llx(self):
        return self.bbox.llx
        
    @property
    def lly(self):
        return self.bbox.lly
        
    @property
    def urx(self):
        return self.bbox.urx
        
    @property
    def ury(self):
        return self.bbox.ury
        
    @property
    def width(self):
        width = getattr(self, '_width', None)
        if width is None:
            self._width = self.bbox.width
        return self._width

    @width.setter
    def width(self, width):
        self._width = width

    @property
    def height(self):
        height = getattr(self, '_height', None)
        if height is None:
            self._height = self.bbox.height
        return self._height

    @height.setter
    def height(self, height):
        self._height = height


class BoxContainer(Box):
    contained_type = None

    def __init__(self, items):
        self.bbox = BBox(None, None, None, None)
        self._items = []
        if items is None:
            items = []
        for item in items:
            self.append(item)

    def append(self, item):
        if (self.contained_type is not None
                and not isinstance(item, self.contained_type)):
            raise TypeError(
                'Incompatible item type: {}'.format(item.__class__.__name__)
            )
        self.bbox.merge(item.bbox)
        self._width, self._height = None, None  # invalidate old values
        self._items.append(item)

    def extend(self, iterable):
        for item in iterable:
            self.append(item)

        
class Token(Box):

    def __init__(self, text, bbox, font=None, features=None):
        self.text = text
        self.bbox = BBox(*bbox)
        self.font = font
        self.features = {} if features is None else features


class Line(BoxContainer):
    contained_type = Token

    def __init__(self, tokens=None, id=None):
        self.id = id
        BoxContainer.__init__(self, tokens)

    @property
    def tokens(self):
        return self._items

    def __iter__(self):
        return iter(self.tokens)

    def __repr__(self):
        return ' '.join([t.text for t in self.tokens])

    def sort(self):
        self._items.sort(key=lambda tok: tok.llx)

    def overlap(self, other):
        a, b = self.bbox, other.bbox
        if a.ury <= b.lly or a.lly >= b.ury:
            return 0.0

        if a.ury == b.ury and a.lly == b.lly:
            return 1.0

        if a.height < b.height:
            a, b = b, a

        if not b.height:
            return 0.0

        if a.ury < b.ury:
            return (a.ury - b.lly) / b.height
        else:
            return (b.ury - a.lly) / b.height


class Block(BoxContainer):
    def __init__(self, lines=None, id=None, label=None):
        self.id = id
        self.label = label
        BoxContainer.__init__(self, lines)

    @property
    def lines(self):
        return self._items

    def sort(self):
        self._items.sort(key=lambda line: line.lly, reverse=True)


class Page(BoxContainer):
    def __init__(self, blocks=None, id=None, page_width=None, page_height=None):
        self.id = id
        self.page_width = page_width
        self.page_height = page_height
        BoxContainer.__init__(self, blocks)

    @property
    def blocks(self):
        return self._items

    @blocks.setter
    def blocks(self, blocks):
        self._items.clear()
        self.extend(blocks)

    @property
    def lines(self):
        return [line for block in self.blocks for line in block.lines]

    @property
    def tokens(self):
        return [token for line in self.lines for token in line.tokens]

class Document(object):
    def __init__(self, pages=None, id=None):
        if pages is None:
            pages = []
        self.pages = pages
        self.id = id

    # @property
    # def lines(self):
    #     pass
