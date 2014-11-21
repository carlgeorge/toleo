import re
import pkg_resources


class Version():
    '''
    Version object that provides accurate comparison methods.  Comparison
    criteria will differ based on whether the version strings are in
    epoch:version-release format (EVR).

    If comparing two simple version strings, the result will be obvious.

    Examples:   4.2   < 5.0
                4.3.5 < 4.3.10

    If comparing a simple version string and an EVR version string, ignore the
    epoch and release.

    Examples:   4.2 == 4.2-3
              1:4.2 == 4.2

    If comparing two EVR version strings, evaluate the full EVR of both.

    Example:    4.2-7 < 1:4.1-4
              1:4.2-7 < 1:4.2-8
    '''
    def __init__(self, version_string):
        self.orig = version_string
        self.evr = version_string
        self.colons = self.orig.count(':')
        self.dashes = self.orig.count('-')
        if self.colons == 0:
            self.evr = ':' + self.evr
        elif self.colons > 1:
            raise ValueError('too many colons')
        if self.dashes == 0:
            self.evr = self.evr + '-'
        elif self.dashes > 1:
            raise ValueError('too many dashes')
        self.epoch, self.version, self.release = re.split('[:-]', self.evr)
        self.pure = not (bool(self.epoch) or bool(self.release))

    def __str__(self):
        return self.orig

    def parse(self, version_string):
        return pkg_resources.parse_version(version_string)

    def __eq__(self, other):
        if (self.epoch or self.release) and (other.epoch or other.release):
            return self.parse(self.evr) == self.parse(other.evr)
        else:
            return self.parse(self.version) == self.parse(other.version)

    def __ne__(self, other):
        if (self.epoch or self.release) and (other.epoch or other.release):
            return self.parse(self.evr) != self.parse(other.evr)
        else:
            return self.parse(self.version) != self.parse(other.version)

    def __lt__(self, other):
        if (self.epoch or self.release) and (other.epoch or other.release):
            return self.parse(self.evr) < self.parse(other.evr)
        else:
            return self.parse(self.version) < self.parse(other.version)

    def __gt__(self, other):
        if (self.epoch or self.release) and (other.epoch or other.release):
            return self.parse(self.evr) > self.parse(other.evr)
        else:
            return self.parse(self.version) > self.parse(other.version)

    def __le__(self, other):
        if (self.epoch or self.release) and (other.epoch or other.release):
            return self.parse(self.evr) <= self.parse(other.evr)
        else:
            return self.parse(self.version) <= self.parse(other.version)

    def __ge__(self, other):
        if (self.epoch or self.release) and (other.epoch or other.release):
            return self.parse(self.evr) >= self.parse(other.evr)
        else:
            return self.parse(self.version) >= self.parse(other.version)
