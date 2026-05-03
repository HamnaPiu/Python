from Algo_base import ReplacementAlgorithm
from collections import deque

class OPTAlgorithm(ReplacementAlgorithm):
    """
    Optimal (OPT) Page Replacement Algorithm.
    Evicts the page that will not be used for the longest period in the future.
    Requires a pre-scanned 'future_map' of all memory accesses.
    """
    def __init__(self, future_map, capacity):
        """
        Args:
            future_map: dict {vpn: deque of future access indices}
            capacity: Number of physical frames available
        """
        self.future_map = future_map
        self.capacity = capacity
        self.current_pages = []  # VPNs currently in memory

    def update_usage(self, vpn):
        """
        Remove current access from future queue and track that page is in memory.
        """
        # Remove this access from future map
        if vpn in self.future_map and self.future_map[vpn]:
            self.future_map[vpn].popleft()
        
        # Track that this page is in memory (if not already)
        if vpn not in self.current_pages:
            if len(self.current_pages) >= self.capacity:
                # This should not happen if caller checks before calling
                raise Exception("OPT: No free frames! Call get_victim first.")
            self.current_pages.append(vpn)

    def get_victim(self):
        """
        Find the page whose next use is farthest in the future (or never used again).
        """
        furthest_time = -1
        victim = None
        victim_idx = -1

        for i, vpn in enumerate(self.current_pages):
            # If page is never used again → perfect victim
            if not self.future_map.get(vpn):
                victim = vpn
                victim_idx = i
                break
            
            # Find page with farthest next use
            next_use = self.future_map[vpn][0]
            if next_use > furthest_time:
                furthest_time = next_use
                victim = vpn
                victim_idx = i
        
        # Remove victim from tracking list
        if victim_idx != -1:
            self.current_pages.pop(victim_idx)
        
        return victim


# SELF TEST
if __name__ == "__main__":
    print("=" * 50)
    print("TESTING OPT ALGORITHM")
    print("=" * 50)
    
    # Create trace
    trace = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    print(f"TRACE: {trace}")
    
    # Build future map
    future_map = {}
    for idx, vpn in enumerate(trace):
        future_map.setdefault(vpn, deque()).append(idx)
    
    print(f"FUTURE MAP: {[(vpn, list(dq)) for vpn, dq in future_map.items()]}")
    
    # Test OPT with capacity 3
    opt = OPTAlgorithm(future_map.copy(), capacity=3)
    
    # Simulate first 3 accesses
    for i in range(3):
        vpn = trace[i]
        opt.update_usage(vpn)
        print(f"LOADED VPN {vpn} → MEMORY: {opt.current_pages}")
    
    # Next access (VPN 4 - not in memory, need to evict)
    victim = opt.get_victim()
    print(f"\nVICTIM (FARTHEST FUTURE USE): {victim}")
    
    print("\n" + "=" * 50)
    print("✅ OPT ALGORITHM READY")
    print("=" * 50)