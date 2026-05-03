from collections import OrderedDict

class TLB:
    def __init__(self, size):
        self.size = size
        self.entries = OrderedDict()  # VPN -> Frame Number
        self.hits = 0
        self.misses = 0

    def lookup(self, vpn):
        """Checks for VPN in the TLB cache."""
        if vpn in self.entries:
            self.hits += 1
            # Move to end to mark as Most Recently Used
            self.entries.move_to_end(vpn)
            return self.entries[vpn]  # Return Frame Number
        
        self.misses += 1
        return None

    def update(self, vpn, frame_num):
        """Adds a new mapping to the TLB."""
        if vpn in self.entries:
            self.entries.move_to_end(vpn)
        self.entries[vpn] = frame_num
        
        # If TLB exceeds its fixed size, evict the oldest entry
        if len(self.entries) > self.size:
            self.entries.popitem(last=False)

    def invalidate(self, vpn):
        """
        CRITICAL: Removes a mapping if the page is evicted from RAM.
        This prevents the TLB from pointing to a frame that no longer holds that VPN.
        """
        if vpn in self.entries:
            self.entries.pop(vpn)