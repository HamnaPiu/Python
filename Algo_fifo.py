from algo_base import ReplacementAlgorithm
from collections import deque

class FIFOAlgorithm(ReplacementAlgorithm):
    """
    First-In, First-Out (FIFO) Page Replacement Algorithm.
    Evicts the oldest page currently in memory based on its arrival order.
    """
    def __init__(self):
        # We use a deque (double-ended queue) to keep track of 
        # the order in which pages were brought into memory.
        self.queue = deque()

    def update_usage(self, vpn):
        """
        Adds the page to the queue if it hasn't been added yet.
        In FIFO, we only care about the first arrival time.
        """
        if vpn not in self.queue:
            self.queue.append(vpn)

    def get_victim(self):
        """
        Removes and returns the oldest page (the one that arrived first).
        """
        return self.queue.popleft()
