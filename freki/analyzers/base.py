
class FrekiAnalyzer(object):
    def __init__(self, debug=False):
        self._debug = debug

    def analyze(self, reader, id=None):
        raise NotImplementedError()
