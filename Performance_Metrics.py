class PerformanceMetrics:
    def __init__(self):
        # Counters for Stats Engine
        self.total_accesses = 0
        self.tlb_hits = 0
        self.pt_hits = 0
        self.page_faults = 0
        self.dirty_writes = 0
        
        # Latency Constants (in ns)
        self.LATENCY_TLB = 1
        self.LATENCY_RAM = 100
        self.LATENCY_DISK = 10_000_000  # 10ms
        
        self.total_simulated_time_ns = 0

    def log_access(self, hit_type, is_dirty_eviction=False):
        """
        Calculates simulated time based on the access path.
        hit_type: 'TLB_HIT', 'PT_HIT', or 'PAGE_FAULT'
        """
        self.total_accesses += 1
        
        if hit_type == 'TLB_HIT':
            self.tlb_hits += 1
            self.total_simulated_time_ns += self.LATENCY_TLB
            
        elif hit_type == 'PT_HIT':
            self.pt_hits += 1
            # TLB Search (1ns) + RAM Access (100ns)[cite: 1]
            self.total_simulated_time_ns += (self.LATENCY_TLB + self.LATENCY_RAM)
            
        elif hit_type == 'PAGE_FAULT':
            self.page_faults += 1
            # Lookups (101ns) + Disk Read (10ms)[cite: 1]
            path_latency = self.LATENCY_TLB + self.LATENCY_RAM + self.LATENCY_DISK
            
            # If the evicted page was dirty, add another Disk Write penalty[cite: 1]
            if is_dirty_eviction:
                self.dirty_writes += 1
                path_latency += self.LATENCY_DISK
                
            self.total_simulated_time_ns += path_latency

    def get_eat(self):
        """Calculates Effective Access Time (EAT)[cite: 1]."""
        if self.total_accesses == 0: return 0
        return self.total_simulated_time_ns / self.total_accesses

    def print_report(self):
        print("\n--- PERFORMANCE REPORT ---")
        print(f"Total Accesses:    {self.total_accesses}")
        print(f"TLB Hit Ratio:     {(self.tlb_hits/self.total_accesses)*100:.2f}%")
        print(f"Page Fault Rate:   {(self.page_faults/self.total_accesses)*100:.2f}%")
        print(f"Total Disk Writes: {self.dirty_writes}")
        print(f"Simulated Time:    {self.total_simulated_time_ns} ns")
        print(f"Computed EAT:      {self.get_eat():.2f} ns")