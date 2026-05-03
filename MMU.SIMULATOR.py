#!/usr/bin/env python3

from config_parser import parse_config, calculate_derived_values
from Trace_validator import parse_trace
from Address_Splitter import address_splitter
from Page_Table import PageTable
from Tlb import TLB
from Frame_manager import FrameManager
from Performance_Metrics import PerformanceMetrics
from Algo_fifo import FIFOAlgorithm
from Algo_lru import LRUAlgorithm
from Algo_OPT import OPTAlgorithm
from collections import deque


class MMU:
    def __init__(self, config, frame_manager, algorithm="FIFO", trace_addresses=None):
        self.config = config
        self.frame_manager = frame_manager
        self.algorithm = algorithm
        
        self.page_table = PageTable()
        self.tlb = TLB(config.tlb_size)
        self.metrics = PerformanceMetrics(config)
        
        self.total_accesses = 0
        self.current_index = 0
        
        if algorithm == "FIFO":
            self.replacement = FIFOAlgorithm()
        elif algorithm == "LRU":
            self.replacement = LRUAlgorithm(capacity=config.num_frames)
        elif algorithm == "OPT":
            if trace_addresses is None:
                raise ValueError("OPT algorithm requires trace_addresses parameter")
            self.future_map = self._build_future_map(trace_addresses)
            self.replacement = OPTAlgorithm(self.future_map)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        print("=" * 70)
        print(f" MMU SIMULATOR INITIALIZED WITH {algorithm} ALGORITHM ")
        print("=" * 70)
        print(f" PHYSICAL FRAMES AVAILABLE: {config.num_frames}")
        print(f" TLB ENTRIES: {config.tlb_size}")
        print(f" PAGE SIZE: {config.page_bytes} BYTES")
        print(f" RAM SIZE: {config.ram_kb} KB")
        print("=" * 70 + "\n")
    
    def _build_future_map(self, trace_addresses):
        future_map = {}
        trace_vpns = []
        
        for addr in trace_addresses:
            vpn, _ = address_splitter(addr, self.config.offset_bits, self.config.offset_mask_value)
            trace_vpns.append(vpn)
        
        for idx, vpn in enumerate(trace_vpns):
            if vpn not in future_map:
                future_map[vpn] = deque()
            future_map[vpn].append(idx)
        
        return future_map
    
    def _handle_page_fault(self, vpn, is_write):
        self.metrics.log_access('PAGE_FAULT', is_dirty_eviction=False)
        dirty_evicted = False
        frame_num = None
        
        if self.frame_manager.has_free_frames():
            frame_num = self.frame_manager.allocate_frame()
            print(f"     PAGE FAULT: FREE FRAME {frame_num} ALLOCATED")
        else:
            victim_vpn = self.replacement.get_victim()
            victim_pte = self.page_table.get_entry(victim_vpn)
            frame_num = victim_pte.frame
            
            print(f"     PAGE FAULT: EVICTING VPN {victim_vpn} FROM FRAME {frame_num}")
            
            if victim_pte.dirty == 1:
                print(f"        DIRTY PAGE: WRITING BACK TO DISK")
                dirty_evicted = True
                self.metrics.log_access('PAGE_FAULT', is_dirty_eviction=True)
            
            self.page_table.invalidate(victim_vpn)
            self.tlb.invalidate(victim_vpn)
        
        self.page_table.add_entry(vpn, frame_num)
        
        if is_write:
            self.page_table.mark_dirty(vpn)
            print(f"        WRITE OPERATION: DIRTY BIT SET")
        
        self.tlb.update(vpn, frame_num)
        self.replacement.update_usage(vpn)
        
        return frame_num
    
    def translate(self, virtual_address, is_write):
        self.total_accesses += 1
        self.current_index += 1
        
        vpn, offset = address_splitter(virtual_address, self.config.offset_bits, self.config.offset_mask_value)
        
        frame_num = self.tlb.lookup(vpn)
        
        if frame_num is not None:
            self.metrics.log_access('TLB_HIT')
            self.replacement.update_usage(vpn)
            print(f"     [TLB HIT] VPN={vpn} -> FRAME={frame_num}")
            physical_address = (frame_num << self.config.offset_bits) | offset
            return physical_address, self.metrics.total_simulated_time_ns
        
        self.metrics.log_access('PT_HIT')
        pte = self.page_table.get_entry(vpn)
        
        if pte and pte.valid == 1:
            frame_num = pte.frame
            self.tlb.update(vpn, frame_num)
            self.replacement.update_usage(vpn)
            print(f"     [PAGE TABLE HIT] VPN={vpn} -> FRAME={frame_num}")
            physical_address = (frame_num << self.config.offset_bits) | offset
            return physical_address, self.metrics.total_simulated_time_ns
        else:
            print(f"     [PAGE FAULT] VPN={vpn} NOT IN RAM")
            frame_num = self._handle_page_fault(vpn, is_write)
            print(f"        LOADED VPN {vpn} INTO FRAME {frame_num}")
            physical_address = (frame_num << self.config.offset_bits) | offset
            return physical_address, self.metrics.total_simulated_time_ns
    
    def get_stats(self):
        total_tlb = self.tlb.hits + self.tlb.misses
        tlb_hit_rate = (self.tlb.hits / total_tlb * 100) if total_tlb > 0 else 0
        
        return {
            'algorithm': self.algorithm,
            'total_accesses': self.metrics.total_accesses,
            'tlb_hits': self.tlb.hits,
            'tlb_misses': self.tlb.misses,
            'tlb_hit_rate': tlb_hit_rate,
            'page_faults': self.metrics.page_faults,
            'page_fault_rate': (self.metrics.page_faults / self.metrics.total_accesses * 100) if self.metrics.total_accesses > 0 else 0,
            'disk_reads': self.metrics.page_faults,
            'disk_writes': self.metrics.dirty_writes,
            'total_latency_ns': self.metrics.total_simulated_time_ns,
            'avg_latency_ns': self.metrics.get_eat(),
            'eat_ns': self.metrics.get_eat()
        }
    
    def print_stats(self):
        stats = self.get_stats()
        
        print("\n" + "=" * 70)
        print(f" PERFORMANCE REPORT [{stats['algorithm']}] ")
        print("=" * 70)
        
        print("\n[ ACCESS SUMMARY ]")
        print(f"   TOTAL ACCESSES:     {stats['total_accesses']}")
        print(f"   TLB HITS:           {stats['tlb_hits']}")
        print(f"   TLB MISSES:         {stats['tlb_misses']}")
        print(f"   TLB HIT RATE:       {stats['tlb_hit_rate']:.2f}%")
        
        print("\n[ MEMORY STATISTICS ]")
        print(f"   PAGE FAULTS:        {stats['page_faults']}")
        print(f"   FAULT RATE:         {stats['page_fault_rate']:.2f}%")
        print(f"   DISK READS:         {stats['disk_reads']}")
        print(f"   DISK WRITES:        {stats['disk_writes']}")
        
        print("\n[ LATENCY ANALYSIS ]")
        print(f"   TOTAL TIME:         {stats['total_latency_ns']:,} NS")
        print(f"   AVERAGE TIME:       {stats['avg_latency_ns']:.2f} NS")
        print(f"   EFFECTIVE ACCESS TIME (EAT): {stats['eat_ns']:.2f} NS")
        
        print("\n" + "-" * 70)
        
        self.page_table.print_table()
        
        total_tlb = self.tlb.hits + self.tlb.misses
        tlb_rate = (self.tlb.hits / total_tlb * 100) if total_tlb > 0 else 0
        print(f"\n[ TLB CACHE STATUS ]")
        print(f"   HITS: {self.tlb.hits}  |  MISSES: {self.tlb.misses}  |  HIT RATE: {tlb_rate:.2f}%")
        
        self.frame_manager.print_status()
        print("=" * 70 + "\n")


def main():
    print("\n" + "=" * 70)
    print("   WELCOME TO VIRTUAL MEMORY & TLB SIMULATOR")
    print("=" * 70 + "\n")
    
    trace_file = input(" ENTER TRACE FILE PATH (default: Trace_validator.txt): ").strip()
    if not trace_file:
        trace_file = "Trace_validator.txt"
    
    print("\n[1] LOADING CONFIGURATION...")
    config = parse_config("config.txt")
    config = calculate_derived_values(config)
    config.print_config()
    
    print("\n[2] LOADING TRACE FILE...")
    accesses = parse_trace(trace_file)
    
    if not accesses:
        print(" ERROR: NO VALID MEMORY ACCESSES FOUND!")
        return
    
    all_addresses = [acc.addr for acc in accesses]
    
    while True:
        print("\n" + "-" * 70)
        print("   REPLACEMENT ALGORITHM MENU")
        print("-" * 70)
        print("   1. FIFO (First-In-First-Out)")
        print("   2. LRU (Least Recently Used)")
        print("   3. OPT (Optimal - Clairvoyant)")
        print("   0. EXIT")
        print("-" * 70)
        
        try:
            choice = int(input("\n ENTER YOUR CHOICE (0-3): "))
        except ValueError:
            print(" ERROR: INVALID INPUT. PLEASE ENTER A NUMBER.")
            continue
        
        if choice == 0:
            print("\n EXITING SIMULATOR. GOODBYE!\n")
            break
        
        if choice == 1:
            algorithm = "FIFO"
        elif choice == 2:
            algorithm = "LRU"
        elif choice == 3:
            algorithm = "OPT"
        else:
            print(" ERROR: INVALID CHOICE. PLEASE ENTER 0-3.")
            continue
        
        print(f"\n[3] CREATING FRAME MANAGER...")
        fm = FrameManager(config.num_frames)
        fm.print_status()
        
        print(f"\n[4] INITIALIZING MMU WITH {algorithm} ALGORITHM...")
        
        if algorithm == "OPT":
            mmu = MMU(config, fm, algorithm=algorithm, trace_addresses=all_addresses)
        else:
            mmu = MMU(config, fm, algorithm=algorithm)
        
        print(f"\n[5] PROCESSING {len(accesses)} MEMORY ACCESSES WITH {algorithm}...")
        print("-" * 70 + "\n")
        
        for i, acc in enumerate(accesses):
            print(f" ACCESS [{i+1:03d}/{len(accesses)}] : {acc}")
            phys_addr, latency = mmu.translate(acc.addr, acc.write_flag)
            print(f"        PHYSICAL ADDRESS: {hex(phys_addr)}\n")
        
        mmu.print_stats()


if __name__ == "__main__":
    main()