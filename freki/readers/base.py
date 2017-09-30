
class FrekiReader(object):

    def __init__(self, debug=False):
        self._debug = debug

    def pages(self, *page_ids):
        '''
        Return the Page objects for the document.
        Zero or more *page_ids* may be specified, which are the page
        numbers (e.g. `1` is the first page). If zero *page_ids* are
        given, all pages are returned in order.
        '''
        raise NotImplementedError()
