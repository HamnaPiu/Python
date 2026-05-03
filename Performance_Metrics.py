class PerformanceMetrics:
    def __init__(self, config):
        # READ LATENCIES FROM CONFIG (matches your config_parser)
        self.LATENCY_TLB = config.tlb_latency_ns      # Now matches
        self.LATENCY_RAM = config.ram_latency_ns      # Now matches
        self.LATENCY_DISK = config.disk_latency_ns    # Now matches
        
        # COUNTERS
        self.total_accesses = 0
        self.tlb_hits = 0
        self.pt_hits = 0
        self.page_faults = 0
        self.dirty_writes = 0
        self.total_simulated_time_ns = 0

    def log_access(self, hit_type, is_dirty_eviction=False):
        self.total_accesses += 1
        
        if hit_type == 'TLB_HIT':
            self.tlb_hits += 1
            self.total_simulated_time_ns += self.LATENCY_TLB
            
        elif hit_type == 'PT_HIT':
            self.pt_hits += 1
            self.total_simulated_time_ns += (self.LATENCY_TLB + self.LATENCY_RAM)
            
        elif hit_type == 'PAGE_FAULT':
            self.page_faults += 1
            path_latency = self.LATENCY_TLB + self.LATENCY_RAM + self.LATENCY_DISK
            
            if is_dirty_eviction:
                self.dirty_writes += 1
                path_latency += self.LATENCY_DISK
                
            self.total_simulated_time_ns += path_latency

    def get_eat(self):
        if self.total_accesses == 0:
            return 0.0
        return self.total_simulated_time_ns / self.total_accesses

    def get_hit_rate(self):
        if self.total_accesses == 0:
            return 0.0
        return (self.tlb_hits / self.total_accesses) * 100

    def get_fault_rate(self):
        if self.total_accesses == 0:
            return 0.0
        return (self.page_faults / self.total_accesses) * 100

    def print_report(self):
        print("\n" + "=" * 50)
        print("PERFORMANCE REPORT")
        print("=" * 50)
        print(f"\n--- LATENCY CONFIGURATION ---")
        print(f"TLB LATENCY:   {self.LATENCY_TLB} NS")
        print(f"RAM LATENCY:   {self.LATENCY_RAM} NS")
        print(f"DISK LATENCY:  {self.LATENCY_DISK:,} NS")
        
        print(f"\n--- ACCESS STATISTICS ---")
        print(f"TOTAL ACCESSES:    {self.total_accesses}")
        print(f"TLB HITS:          {self.tlb_hits}")
        print(f"PAGE TABLE HITS:   {self.pt_hits}")
        print(f"PAGE FAULTS:       {self.page_faults}")
        print(f"DIRTY WRITES:      {self.dirty_writes}")
        
        print(f"\n--- RATIOS ---")
        print(f"TLB HIT RATIO:     {self.get_hit_rate():.2f}%")
        print(f"PAGE FAULT RATE:   {self.get_fault_rate():.2f}%")
        
        print(f"\n--- TIMING ---")
        print(f"TOTAL SIMULATED TIME: {self.total_simulated_time_ns:,} NS")
        print(f"EFFECTIVE ACCESS TIME (EAT): {self.get_eat():.2f} NS")
        print("\n" + "=" * 50)


# SELF TEST
if __name__ == "__main__":
    from config_parser import parse_config, calculate_derived_values
    
    print("=" * 50)
    print("TESTING PERFORMANCE METRICS")
    print("=" * 50)
    
    config = parse_config("config.txt")
    config = calculate_derived_values(config)
    metrics = PerformanceMetrics(config)
    
    print("\n--- SIMULATING ACCESSES ---")
    metrics.log_access('TLB_HIT')
    print(f"TLB HIT → TIME + {metrics.LATENCY_TLB} NS")
    
    metrics.log_access('PT_HIT')
    print(f"PT HIT → TIME + {metrics.LATENCY_TLB + metrics.LATENCY_RAM} NS")
    
    metrics.log_access('PAGE_FAULT', is_dirty_eviction=False)
    print(f"PAGE FAULT (CLEAN) → TIME + {metrics.LATENCY_TLB + metrics.LATENCY_RAM + metrics.LATENCY_DISK} NS")
    
    metrics.log_access('PAGE_FAULT', is_dirty_eviction=True)
    print(f"PAGE FAULT (DIRTY) → TIME + {metrics.LATENCY_TLB + metrics.LATENCY_RAM + metrics.LATENCY_DISK + metrics.LATENCY_DISK} NS")
    
    metrics.print_report()
    print("\n✅ PERFORMANCE METRICS WORKS!")
    print("=" * 50)