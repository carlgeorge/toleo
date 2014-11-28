import sys


class ToleoException(Exception):
    '''
    Base exception class.
    '''
    def __init__(self, message, error=None):
        super().__init__(message)
        self.message = message
        self.error = error or 'ToleoException'

    def quit(self):
        sys.exit('{}: {}'.format(self.error, self.message))
