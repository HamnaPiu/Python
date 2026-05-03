from collections import OrderedDict

class TLB:
    def __init__(self, size):
        self.size = size
        self.entries = OrderedDict()
        self.hits = 0
        self.misses = 0

    def lookup(self, vpn):
        if vpn in self.entries:
            self.hits += 1
            self.entries.move_to_end(vpn)
            return self.entries[vpn]
        
        self.misses += 1
        return None

    def update(self, vpn, frame_num):
        if vpn in self.entries:
            self.entries.move_to_end(vpn)
        self.entries[vpn] = frame_num
        
        if len(self.entries) > self.size:
            self.entries.popitem(last=False)

    def invalidate(self, vpn):
        if vpn in self.entries:
            self.entries.pop(vpn)