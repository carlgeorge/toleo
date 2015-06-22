import asyncio


class Relationship():
    '''
    Defines the relationship between an upstream and a downstream.  Provides a
    _load coroutine method that can be added to an event loop's task queue.
    '''
    def __init__(self, upstream, downstream):
        self.upstream = upstream
        self.downstream = downstream

    @asyncio.coroutine
    def _load(self):
        yield from self.upstream._load()
        yield from self.downstream._load()
