from Algo_base import ReplacementAlgorithm
from collections import OrderedDict

class LRUAlgorithm(ReplacementAlgorithm):
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = OrderedDict()

    def update_usage(self, vpn):
        if vpn in self.cache:
            self.cache.move_to_end(vpn)
        self.cache[vpn] = True

    def get_victim(self):
        victim, _ = self.cache.popitem(last=False)
        return victim
