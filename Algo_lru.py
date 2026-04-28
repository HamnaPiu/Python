from algo_base import ReplacementAlgorithm
from collections import OrderedDict

class LRUAlgorithm(ReplacementAlgorithm):
    """
    Least Recently Used (LRU) Page Replacement Algorithm.
    Evicts the page that has not been accessed for the longest time.
    """
    def __init__(self, capacity):
        # We use an OrderedDict because it maintains the order of keys
        # based on insertion and update times.
        self.capacity = capacity
        self.cache = OrderedDict()

    def update_usage(self, vpn):
        """
        Updates the usage state of a page.
        If the page is already in the cache, we move it to the end (Most Recently Used).
        If it's new, we just add it to the end.
        """
        if vpn in self.cache:
            # Move existing item to the end to mark it as 'Most Recently Used'
            self.cache.move_to_end(vpn)
        self.cache[vpn] = True

    def get_victim(self):
        """
        Removes and returns the 'Least Recently Used' page.
        In an OrderedDict, the oldest item is at the start (last=False).
        """
        # popitem(last=False) returns and removes the first (oldest) item
        victim, _ = self.cache.popitem(last=False)
        return victim
