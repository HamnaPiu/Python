from Algo_base import ReplacementAlgorithm

class OPTAlgorithm(ReplacementAlgorithm):
    """
    Optimal (OPT) Page Replacement Algorithm.
    Evicts the page that will not be used for the longest period of time in the future.
    Note: Requires a pre-scanned 'future_map' of all memory accesses.
    """
    def __init__(self, future_map):
        # future_map is a dictionary where:
        # Key = VPN
        # Value = A deque of line numbers representing every time this page is accessed.
        self.future_map = future_map 
        self.current_pages = [] # Tracks which pages are currently in "physical memory"

    def update_usage(self, vpn):
        """
        Updates the future timeline for a page.
        When a page is accessed, we remove that specific timestamp from its future.
        """
        # Remove the 'current' access time because it is happening right now
        if vpn in self.future_map and self.future_map[vpn]:
            self.future_map[vpn].popleft()
        
        # Track that this page is now in RAM if it wasn't already
        if vpn not in self.current_pages:
            self.current_pages.append(vpn)

    def get_victim(self):
        """
        The 'Clairvoyant' logic: scans all pages in RAM and finds the one 
        whose next access is furthest away.
        """
        furthest_time = -1
        victim = -1
        victim_idx = -1

        for i, vpn in enumerate(self.current_pages):
            # STRATEGY 1: If a page is NEVER used again, it is the perfect victim.
            if not self.future_map[vpn]:
                victim = vpn
                victim_idx = i
                break
            
            # STRATEGY 2: Find the page with the highest next-use timestamp.
            next_use = self.future_map[vpn][0]
            if next_use > furthest_time:
                furthest_time = next_use
                victim = vpn
                victim_idx = i
        
        # Remove the victim from our tracking list before returning it
        self.current_pages.pop(victim_idx)
        return victim
