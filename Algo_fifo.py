from Algo_base import ReplacementAlgorithm
from collections import deque

class FIFOAlgorithm(ReplacementAlgorithm):
    def __init__(self):
        self.queue = deque()

    def update_usage(self, vpn):
        if vpn not in self.queue:
            self.queue.append(vpn)

    def get_victim(self):
        return self.queue.popleft()
