import pyalpm


class Version():
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text

    def __repr__(self):
        return '{}(\'{}\')'.format(self.__class__.__name__, self.__str__())

    def _check(self, other):
        if not isinstance(other, self.__class__):
            err = 'unorderable types: {}(), {}()'
            raise TypeError(err.format(self.__class__.__name__,
                                       other.__class__.__name__))

    def __eq__(self, other):
        self._check(other)
        return pyalpm.vercmp(self.text, other.text) == 0

    def __ne__(self, other):
        self._check(other)
        return pyalpm.vercmp(self.text, other.text) != 0

    def __lt__(self, other):
        self._check(other)
        return pyalpm.vercmp(self.text, other.text) < 0

    def __gt__(self, other):
        self._check(other)
        return pyalpm.vercmp(self.text, other.text) > 0

    def __le__(self, other):
        self._check(other)
        return pyalpm.vercmp(self.text, other.text) <= 0

    def __ge__(self, other):
        self._check(other)
        return pyalpm.vercmp(self.text, other.text) >= 0
