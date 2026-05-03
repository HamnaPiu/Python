from Algo_base import ReplacementAlgorithm
from collections import deque

class OPTAlgorithm(ReplacementAlgorithm):
    def __init__(self, future_map, capacity):
        self.future_map = future_map
        self.capacity = capacity
        self.current_pages = []

    def update_usage(self, vpn):
        if vpn in self.future_map and self.future_map[vpn]:
            self.future_map[vpn].popleft()
        
        if vpn not in self.current_pages:
            if len(self.current_pages) >= self.capacity:
                raise Exception("OPT: No free frames! Call get_victim first.")
            self.current_pages.append(vpn)

    def get_victim(self):
        furthest_time = -1
        victim = None
        victim_idx = -1

        for i, vpn in enumerate(self.current_pages):
            if not self.future_map.get(vpn):
                victim = vpn
                victim_idx = i
                break
            
            next_use = self.future_map[vpn][0]
            if next_use > furthest_time:
                furthest_time = next_use
                victim = vpn
                victim_idx = i
        
        if victim_idx != -1:
            self.current_pages.pop(victim_idx)
        
        return victim


if __name__ == "__main__":
    print("TESTING OPT ALGORITHM")
    
    trace = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    print(f"TRACE: {trace}")
    future_map = {}
    for idx, vpn in enumerate(trace):
        future_map.setdefault(vpn, deque()).append(idx)
    
    print(f"FUTURE MAP: {[(vpn, list(dq)) for vpn, dq in future_map.items()]}")
    opt = OPTAlgorithm(future_map.copy(), capacity=3)
    for i in range(3):
        vpn = trace[i]
        opt.update_usage(vpn)
        print(f"LOADED VPN {vpn} → MEMORY: {opt.current_pages}")
    victim = opt.get_victim()
    print(f"\nVICTIM (FARTHEST FUTURE USE): {victim}")
    print("\nOPT ALGORITHM READY")