import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from config_parser import parse_config, calculate_derived_values
from Trace_validator import parse_trace
from Frame_manager import FrameManager
from Page_Table import PageTable
from Tlb import TLB
from Address_Splitter import address_splitter
from Performance_Metrics import PerformanceMetrics
from Algo_fifo import FIFOAlgorithm
from Algo_lru import LRUAlgorithm
from Algo_OPT import OPTAlgorithm
import threading
from collections import deque


class MMUGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VIRTUAL MEMORY & TLB SIMULATOR")
        self.root.geometry("1000x800")
        self.root.configure(bg='#2E1A47')  # Dark Purple

        # Variables
        self.trace_file = "Trace_validator.txt"
        self.algorithm = tk.StringVar(value="FIFO")
        self.config = None
        self.all_accesses = []
        self.all_vpns = []
        
        # Store latest metrics for live display
        self.current_metrics = None
        self.current_tlb = None

        self.setup_ui()

    def setup_ui(self):
        # ===== TOP FRAME (Title) =====
        title_frame = tk.Frame(self.root, bg='#2E1A47', height=50)
        title_frame.pack(fill=tk.X, pady=5)
        title_frame.pack_propagate(False)

        title = tk.Label(title_frame, text="VIRTUAL MEMORY & TLB SIMULATOR",
                         font=("Times New Roman", 18, "bold"), bg='#2E1A47', fg='#FFFFFF')
        title.pack(expand=True)

        # ===== MIDDLE FRAME (Algorithm + System Setup + Live Stats) =====
        middle_frame = tk.Frame(self.root, bg='#2E1A47')
        middle_frame.pack(fill=tk.X, padx=10, pady=2)  # Reduced pady from 5 to 2

        # Row 0: Algorithm Choice and System Setup (side by side) - MADE SHORTER
        top_row = tk.Frame(middle_frame, bg='#2E1A47')
        top_row.pack(fill=tk.X, pady=2)  # Reduced pady from 5 to 2
        
        top_row.grid_columnconfigure(0, weight=1)
        top_row.grid_columnconfigure(1, weight=1)

        # ALGORITHM CHOICE (Left side) - REDUCED HEIGHT
        algo_frame = tk.LabelFrame(top_row, text="ALGORITHM CHOICE",
                                    font=("Times New Roman", 12, "bold"),
                                    bg='#2E1A47', fg='#FFFFFF',
                                    bd=2, relief=tk.GROOVE)
        algo_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=2)  # Reduced pady

        algo_frame.grid_rowconfigure(0, weight=1)
        algo_frame.grid_rowconfigure(1, weight=1)
        algo_frame.grid_rowconfigure(2, weight=1)
        algo_frame.grid_columnconfigure(0, weight=1)

        # Reduced padding and font sizes to make box shorter
        algo_label = tk.Label(algo_frame, text="SELECT ALGORITHM:", font=("Times New Roman", 10, "bold"),
                              bg='#2E1A47', fg='#FFFFFF')
        algo_label.grid(row=0, column=0, pady=5)  # Reduced from 10 to 5

        # VERTICAL RADIO BUTTONS - Reduced spacing
        radio_frame = tk.Frame(algo_frame, bg='#2E1A47')
        radio_frame.grid(row=1, column=0, pady=5)  # Reduced from 10 to 5

        self.fifo_btn = tk.Radiobutton(radio_frame, text="FIFO", variable=self.algorithm,
                                       value="FIFO", bg='#2E1A47', fg='#FFFFFF',
                                       font=("Times New Roman", 11), selectcolor='#2E1A47')
        self.fifo_btn.pack(anchor=tk.CENTER, pady=2)  # Reduced from 5 to 2

        self.lru_btn = tk.Radiobutton(radio_frame, text="LRU", variable=self.algorithm,
                                      value="LRU", bg='#2E1A47', fg='#FFFFFF',
                                      font=("Times New Roman", 11), selectcolor='#2E1A47')
        self.lru_btn.pack(anchor=tk.CENTER, pady=2)

        self.opt_btn = tk.Radiobutton(radio_frame, text="OPT", variable=self.algorithm,
                                      value="OPT", bg='#2E1A47', fg='#FFFFFF',
                                      font=("Times New Roman", 11), selectcolor='#2E1A47')
        self.opt_btn.pack(anchor=tk.CENTER, pady=2)

        # Run button - Reduced padding and size
        run_btn = tk.Button(algo_frame, text="▶ RUN SIMULATION", command=self.run_simulation,
                           bg='#4CAF50', fg='white', font=("Times New Roman", 11, "bold"),
                           relief=tk.RAISED, bd=2, padx=12, pady=5, cursor="hand2")  # Reduced padding
        run_btn.grid(row=2, column=0, pady=8)  # Reduced from 15 to 8

        # SYSTEM SETUP (Right side) - REDUCED HEIGHT
        setup_frame = tk.LabelFrame(top_row, text="SYSTEM SETUP",
                                     font=("Times New Roman", 12, "bold"),
                                     bg='#2E1A47', fg='#FFFFFF',
                                     bd=2, relief=tk.GROOVE)
        setup_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=2)  # Reduced pady

        # Config display + Edit button
        config_controls = tk.Frame(setup_frame, bg='#2E1A47')
        config_controls.pack(fill=tk.X, pady=2)  # Reduced from 5 to 2
        
        edit_btn = tk.Button(config_controls, text="✏ EDIT CONFIG", command=self.edit_config,
                            bg='#FF9800', fg='white', font=("Times New Roman", 8, "bold"),  # Smaller font
                            relief=tk.RAISED, bd=1, padx=8, cursor="hand2")  # Reduced padding
        edit_btn.pack(side=tk.RIGHT, padx=5)

        # Reduced height from 10 to 7 lines
        self.config_text = tk.Text(setup_frame, width=35, height=7,
                                   font=("Times New Roman", 9), bg='#1a0a2e', fg='#FFFFFF',
                                   relief=tk.SUNKEN, bd=1, state=tk.DISABLED)
        self.config_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ===== ROW 1: LIVE STATISTICS PANEL (Compact - UNCHANGED) =====
        stats_frame = tk.LabelFrame(middle_frame, text="LIVE STATISTICS",
                                     font=("Times New Roman", 11, "bold"),
                                     bg='#2E1A47', fg='#FFD700',
                                     bd=2, relief=tk.GROOVE)
        stats_frame.pack(fill=tk.X, pady=5)

        # Create stats display grid - More compact layout
        self.stats_labels = {}
        stats_items = [
            ("TLB HITS:", "0", "#4CAF50"),
            ("TLB MISSES:", "0", "#F44336"),
            ("TOTAL ACCESSES:", "0", "#2196F3"),
            ("PAGE FAULTS:", "0", "#FF9800"),
            ("HIT RATE:", "0%", "#FFD700"),
            ("CURRENT EAT:", "0 NS", "#00BCD4")
        ]
        
        for i, (label, default, color) in enumerate(stats_items):
            row = i // 3
            col = (i % 3) * 2
            
            tk.Label(stats_frame, text=label, font=("Times New Roman", 9, "bold"),
                     bg='#2E1A47', fg='#FFFFFF').grid(row=row, column=col, padx=8, pady=3, sticky=tk.W)
            
            self.stats_labels[label] = tk.Label(stats_frame, text=default, 
                                                 font=("Times New Roman", 9, "bold"),
                                                 bg='#2E1A47', fg=color)
            self.stats_labels[label].grid(row=row, column=col+1, padx=8, pady=3, sticky=tk.W)

        # ===== BOTTOM FRAME (Simulation Output) - EXTENDED =====
        bottom_frame = tk.LabelFrame(self.root, text="SIMULATION OUTPUT",
                                      font=("Times New Roman", 12, "bold"),
                                      bg='#2E1A47', fg='#FFFFFF',
                                      bd=2, relief=tk.GROOVE)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Make output text area MUCH TALLER (expands to fill the saved space)
        self.output_text = scrolledtext.ScrolledText(bottom_frame, width=70,
                                                      font=("Times New Roman", 10),
                                                      bg='#000000', fg='#FFFFFF',
                                                      relief=tk.SUNKEN, bd=1)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Button frame for output controls
        output_controls = tk.Frame(bottom_frame, bg='#2E1A47')
        output_controls.pack(fill=tk.X, pady=5)

        clear_btn = tk.Button(output_controls, text="🗑 CLEAR OUTPUT", command=self.clear_output,
                             bg='#F44336', fg='white', font=("Times New Roman", 10),
                             relief=tk.RAISED, bd=1, padx=10, cursor="hand2")
        clear_btn.pack(side=tk.LEFT, padx=5)

        save_btn = tk.Button(output_controls, text="💾 SAVE RESULTS", command=self.save_results,
                            bg='#2196F3', fg='white', font=("Times New Roman", 10),
                            relief=tk.RAISED, bd=1, padx=10, cursor="hand2")
        save_btn.pack(side=tk.LEFT, padx=5)

        # Progress bar
        progress_frame = tk.Frame(bottom_frame, bg='#2E1A47')
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress.pack(side=tk.LEFT, padx=5)
        
        self.progress_label = tk.Label(progress_frame, text="0%", bg='#2E1A47', fg='#FFFFFF',
                                        font=("Times New Roman", 9))
        self.progress_label.pack(side=tk.LEFT, padx=5)

        # ===== STATUS BAR (Bottom) =====
        self.status_bar = tk.Label(self.root, text="READY", relief=tk.SUNKEN,
                                    anchor=tk.W, bg='#1a0a2e', fg='#FFFFFF',
                                    font=("Times New Roman", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Load initial config
        self.load_config()

    def update_live_stats(self, tlb_cache, metrics, total_accesses):
        """Update the live statistics display"""
        total = tlb_cache.hits + tlb_cache.misses
        hit_rate = (tlb_cache.hits / total * 100) if total > 0 else 0
        
        self.stats_labels["TLB HITS:"].config(text=str(tlb_cache.hits))
        self.stats_labels["TLB MISSES:"].config(text=str(tlb_cache.misses))
        self.stats_labels["TOTAL ACCESSES:"].config(text=str(total_accesses))
        self.stats_labels["PAGE FAULTS:"].config(text=str(metrics.page_faults))
        self.stats_labels["HIT RATE:"].config(text=f"{hit_rate:.1f}%")
        self.stats_labels["CURRENT EAT:"].config(text=f"{metrics.get_eat():.0f} NS")
        self.root.update_idletasks()

    def edit_config(self):
        """Open config editor dialog"""
        editor = tk.Toplevel(self.root)
        editor.title("EDIT CONFIGURATION")
        editor.geometry("500x550")
        editor.configure(bg='#2E1A47')
        editor.transient(self.root)
        editor.grab_set()
        
        tk.Label(editor, text="EDIT SYSTEM CONFIGURATION", font=("Times New Roman", 14, "bold"),
                 bg='#2E1A47', fg='#FFFFFF').pack(pady=10)
        
        tk.Label(editor, text="Edit values below. Click SAVE when done.", 
                 font=("Times New Roman", 10), bg='#2E1A47', fg='#FFD700').pack()
        
        # Read current config
        try:
            with open("config.txt", 'r') as f:
                config_content = f.read()
        except:
            config_content = "# CONFIG FILE NOT FOUND"
        
        text_area = scrolledtext.ScrolledText(editor, width=60, height=20,
                                               font=("Courier", 10), bg='#1a0a2e', fg='#FFFFFF')
        text_area.pack(padx=10, pady=10)
        text_area.insert(1.0, config_content)
        
        def save_config():
            new_content = text_area.get(1.0, tk.END)
            try:
                with open("config.txt", 'w') as f:
                    f.write(new_content)
                self.load_config()  # Reload config
                self.update_status("CONFIG UPDATED SUCCESSFULLY")
                messagebox.showinfo("SUCCESS", "Configuration saved and reloaded!")
                editor.destroy()
            except Exception as e:
                messagebox.showerror("ERROR", f"Failed to save config: {e}")
        
        button_frame = tk.Frame(editor, bg='#2E1A47')
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="💾 SAVE", command=save_config,
                  bg='#4CAF50', fg='white', font=("Times New Roman", 11, "bold"),
                  padx=20, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="❌ CANCEL", command=editor.destroy,
                  bg='#F44336', fg='white', font=("Times New Roman", 11, "bold"),
                  padx=20, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=10)

    def save_results(self):
        """Save simulation results to file"""
        from datetime import datetime
        content = self.output_text.get(1.0, tk.END)
        if content.strip():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_results_{timestamp}.txt"
            with open(filename, 'w') as f:
                f.write(content)
            self.update_status(f"RESULTS SAVED TO {filename}")
            messagebox.showinfo("SUCCESS", f"Results saved to {filename}")
        else:
            messagebox.showwarning("WARNING", "No simulation results to save!")

    def log(self, message):
        """Add message to output window"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()

    def clear_output(self):
        self.output_text.delete(1.0, tk.END)

    def update_status(self, message):
        self.status_bar.config(text=message)
        self.root.update_idletasks()

    def load_config(self):
        try:
            config = parse_config("config.txt")
            config = calculate_derived_values(config)
            self.config = config

            # Display config
            self.config_text.config(state=tk.NORMAL)
            self.config_text.delete(1.0, tk.END)
            self.config_text.insert(tk.END, f"RAM SIZE: {config.ram_kb} KB\n")
            self.config_text.insert(tk.END, f"RAM BYTES: {config.ram_bytes} B\n")
            self.config_text.insert(tk.END, f"PAGE SIZE: {config.page_bytes} B\n")
            self.config_text.insert(tk.END, f"TOTAL FRAMES: {config.num_frames}\n")
            self.config_text.insert(tk.END, f"TLB SIZE: {config.tlb_size}\n")
            self.config_text.insert(tk.END, f"TLB LATENCY: {config.tlb_latency_ns} NS\n")
            self.config_text.insert(tk.END, f"RAM LATENCY: {config.ram_latency_ns} NS\n")
            self.config_text.insert(tk.END, f"DISK LATENCY: {config.disk_latency_ns} NS\n")
            self.config_text.insert(tk.END, f"OFFSET BITS: {config.offset_bits}\n")
            self.config_text.insert(tk.END, f"OFFSET MASK: 0x{config.offset_mask_value:X}\n")
            self.config_text.config(state=tk.DISABLED)
            self.update_status("CONFIG LOADED SUCCESSFULLY")
        except Exception as e:
            messagebox.showerror("ERROR", f"FAILED TO LOAD CONFIG: {e}")
            self.update_status("ERROR LOADING CONFIG")

    def load_trace(self):
        try:
            accesses = parse_trace(self.trace_file)
            self.all_accesses = accesses
            
            # Extract VPNs for OPT algorithm
            self.all_vpns = []
            for acc in accesses:
                vpn, _ = address_splitter(acc.addr, self.config.offset_bits, self.config.offset_mask_value)
                self.all_vpns.append(vpn)
            
            self.update_status(f"LOADED {len(accesses)} MEMORY ACCESSES")
            return accesses
        except Exception as e:
            messagebox.showerror("ERROR", f"FAILED TO LOAD TRACE: {e}")
            self.update_status("ERROR LOADING TRACE")
            return None

    def _build_future_map(self):
        """Build future use map for OPT algorithm."""
        future = {}
        for idx, vpn in enumerate(self.all_vpns):
            if vpn not in future:
                future[vpn] = deque()
            future[vpn].append(idx)
        return future

    def _run_fifo_lru(self, accesses, frame_manager, page_table, tlb_cache, metrics, replacement_algo):
        """Run FIFO or LRU simulation."""
        total = len(accesses)
        for i, acc in enumerate(accesses):
            vpn, offset = address_splitter(acc.addr, self.config.offset_bits, self.config.offset_mask_value)
            
            self.log(f"\nACCESS {i+1}/{total}: {hex(acc.addr)} ({'WRITE' if acc.write_flag else 'READ'})")
            self.log(f"  VPN: {vpn}, OFFSET: {offset}")
            
            # Check TLB
            frame_num = tlb_cache.lookup(vpn)
            
            if frame_num is not None:
                # TLB HIT
                metrics.log_access('TLB_HIT')
                replacement_algo.update_usage(vpn)
                self.log(f"  ✓ TLB HIT → FRAME: {frame_num}")
                self.log(f"  LATENCY: {metrics.total_simulated_time_ns} NS")
                self.update_live_stats(tlb_cache, metrics, i+1)
                self._update_progress(i+1, total)
                continue
            
            # TLB MISS - Check Page Table
            pte = page_table.get_entry(vpn)
            
            if pte and pte.valid == 1:
                # PAGE TABLE HIT
                metrics.log_access('PT_HIT')
                frame_num = pte.frame
                tlb_cache.update(vpn, frame_num)
                replacement_algo.update_usage(vpn)
                self.log(f"  ✓ PAGE TABLE HIT → FRAME: {frame_num}")
                self.log(f"  LATENCY: {metrics.total_simulated_time_ns} NS")
                self.update_live_stats(tlb_cache, metrics, i+1)
                self._update_progress(i+1, total)
                continue
            
            # PAGE FAULT
            self.log(f"  ⚠ PAGE FAULT - PAGE NOT IN RAM")
            
            # Check free frames
            if frame_manager.has_free_frames():
                frame_num = frame_manager.allocate_frame()
                self.log(f"    → FREE FRAME AVAILABLE: {frame_num}")
                is_dirty_eviction = False
            else:
                # Evict victim
                victim_vpn = replacement_algo.get_victim()
                victim_pte = page_table.get_entry(victim_vpn)
                frame_num = victim_pte.frame
                is_dirty_eviction = (victim_pte.dirty == 1)
                self.log(f"    → EVICTED VPN {victim_vpn} FROM FRAME {frame_num}")
                if is_dirty_eviction:
                    self.log(f"      → DIRTY PAGE - WRITING BACK TO DISK")
                
                page_table.invalidate(victim_vpn)
                tlb_cache.invalidate(victim_vpn)
            
            # Load new page
            page_table.add_entry(vpn, frame_num)
            if acc.write_flag:
                page_table.mark_dirty(vpn)
                self.log(f"    → WRITE OPERATION - DIRTY BIT SET")
            
            tlb_cache.update(vpn, frame_num)
            replacement_algo.update_usage(vpn)
            metrics.log_access('PAGE_FAULT', is_dirty_eviction=is_dirty_eviction)
            
            self.log(f"    → LOADED VPN {vpn} INTO FRAME {frame_num}")
            self.log(f"  LATENCY: {metrics.total_simulated_time_ns} NS")
            self.update_live_stats(tlb_cache, metrics, i+1)
            self._update_progress(i+1, total)

    def _run_opt(self, accesses, frame_manager, page_table, tlb_cache, metrics, future_map):
        """Run OPT simulation."""
        current_pages = []
        total = len(accesses)
        
        for i, acc in enumerate(accesses):
            vpn, offset = address_splitter(acc.addr, self.config.offset_bits, self.config.offset_mask_value)
            
            self.log(f"\nACCESS {i+1}/{total}: {hex(acc.addr)} ({'WRITE' if acc.write_flag else 'READ'})")
            self.log(f"  VPN: {vpn}, OFFSET: {offset}")
            
            # Update future map (remove current access)
            if vpn in future_map and future_map[vpn]:
                future_map[vpn].popleft()
            
            # Check TLB
            frame_num = tlb_cache.lookup(vpn)
            
            if frame_num is not None:
                metrics.log_access('TLB_HIT')
                self.log(f"  ✓ TLB HIT → FRAME: {frame_num}")
                self.log(f"  LATENCY: {metrics.total_simulated_time_ns} NS")
                self.update_live_stats(tlb_cache, metrics, i+1)
                self._update_progress(i+1, total)
                if vpn not in current_pages:
                    current_pages.append(vpn)
                continue
            
            # Check if page in RAM
            pte = page_table.get_entry(vpn)
            
            if pte and pte.valid == 1:
                metrics.log_access('PT_HIT')
                frame_num = pte.frame
                tlb_cache.update(vpn, frame_num)
                self.log(f"  ✓ PAGE TABLE HIT → FRAME: {frame_num}")
                self.log(f"  LATENCY: {metrics.total_simulated_time_ns} NS")
                self.update_live_stats(tlb_cache, metrics, i+1)
                self._update_progress(i+1, total)
                if vpn not in current_pages:
                    current_pages.append(vpn)
                continue
            
            # PAGE FAULT
            self.log(f"  ⚠ PAGE FAULT - PAGE NOT IN RAM")
            
            if frame_manager.has_free_frames():
                frame_num = frame_manager.allocate_frame()
                self.log(f"    → FREE FRAME AVAILABLE: {frame_num}")
                is_dirty_eviction = False
            else:
                # Find optimal victim
                victim = None
                victim_idx = -1
                furthest = -1
                
                for idx, p in enumerate(current_pages):
                    next_use = future_map.get(p, deque())
                    if not next_use:
                        victim = p
                        victim_idx = idx
                        break
                    if next_use[0] > furthest:
                        furthest = next_use[0]
                        victim = p
                        victim_idx = idx
                
                victim_pte = page_table.get_entry(victim)
                frame_num = victim_pte.frame
                is_dirty_eviction = (victim_pte.dirty == 1)
                self.log(f"    → EVICTED VPN {victim} FROM FRAME {frame_num}")
                if is_dirty_eviction:
                    self.log(f"      → DIRTY PAGE - WRITING BACK TO DISK")
                
                page_table.invalidate(victim)
                tlb_cache.invalidate(victim)
                current_pages.pop(victim_idx)
            
            # Load new page
            page_table.add_entry(vpn, frame_num)
            if acc.write_flag:
                page_table.mark_dirty(vpn)
                self.log(f"    → WRITE OPERATION - DIRTY BIT SET")
            
            tlb_cache.update(vpn, frame_num)
            current_pages.append(vpn)
            metrics.log_access('PAGE_FAULT', is_dirty_eviction=is_dirty_eviction)
            
            self.log(f"    → LOADED VPN {vpn} INTO FRAME {frame_num}")
            self.log(f"  LATENCY: {metrics.total_simulated_time_ns} NS")
            self.update_live_stats(tlb_cache, metrics, i+1)
            self._update_progress(i+1, total)

    def _update_progress(self, current, total):
        """Update progress bar"""
        progress = (current / total) * 100
        self.progress['value'] = progress
        self.progress_label.config(text=f"{progress:.0f}%")
        self.root.update_idletasks()

    def run_simulation(self):
        if self.config is None:
            messagebox.showerror("ERROR", "CONFIG NOT LOADED!")
            return

        self.clear_output()
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.update_status("SIMULATION RUNNING...")

        # Reset live stats display
        for label in self.stats_labels:
            if label == "HIT RATE:":
                self.stats_labels[label].config(text="0%")
            elif label == "CURRENT EAT:":
                self.stats_labels[label].config(text="0 NS")
            else:
                self.stats_labels[label].config(text="0")

        # Run in separate thread
        thread = threading.Thread(target=self._run_simulation_thread)
        thread.daemon = True
        thread.start()

    def _run_simulation_thread(self):
        try:
            # Load trace
            self.log("LOADING TRACE FILE")
            accesses = self.load_trace()
            if not accesses:
                return

            self.log(f"LOADED {len(accesses)} MEMORY ACCESSES\n")

            # Create components
            frame_manager = FrameManager(self.config.num_frames)
            page_table = PageTable()
            tlb_cache = TLB(self.config.tlb_size)
            metrics = PerformanceMetrics(self.config)

            algo = self.algorithm.get()
            self.log(f"RUNNING {algo} ALGORITHM")

            if algo == "FIFO":
                replacement_algo = FIFOAlgorithm()
                self._run_fifo_lru(accesses, frame_manager, page_table, tlb_cache, metrics, replacement_algo)
            
            elif algo == "LRU":
                replacement_algo = LRUAlgorithm(capacity=self.config.num_frames)
                self._run_fifo_lru(accesses, frame_manager, page_table, tlb_cache, metrics, replacement_algo)
            
            elif algo == "OPT":
                future_map = self._build_future_map()
                self._run_opt(accesses, frame_manager, page_table, tlb_cache, metrics, future_map)

            # Print final statistics
            self.log("\n" + "=" * 60)
            self.log(f"FINAL STATISTICS ({algo})")
            self.log("=" * 60)
            self.log(f"TOTAL ACCESSES:     {metrics.total_accesses}")
            self.log("\nTLB STATISTICS:")
            self.log(f"  HITS:             {tlb_cache.hits}")
            self.log(f"  MISSES:           {tlb_cache.misses}")
            if (tlb_cache.hits + tlb_cache.misses) > 0:
                hit_rate = (tlb_cache.hits / (tlb_cache.hits + tlb_cache.misses)) * 100
                self.log(f"  HIT RATE:         {hit_rate:.2f}%")
            else:
                self.log(f"  HIT RATE:         N/A")
            self.log("\nPAGE FAULT STATISTICS:")
            self.log(f"  PAGE FAULTS:      {metrics.page_faults}")
            if metrics.total_accesses > 0:
                fault_rate = (metrics.page_faults / metrics.total_accesses) * 100
                self.log(f"  FAULT RATE:       {fault_rate:.2f}%")
            else:
                self.log(f"  FAULT RATE:       N/A")
            self.log("\nDISK I/O:")
            self.log(f"  DISK READS:       {metrics.page_faults}")
            self.log(f"  DISK WRITES:      {metrics.dirty_writes}")
            self.log("\nLATENCY:")
            self.log(f"  TOTAL TIME:       {metrics.total_simulated_time_ns:,} NS")
            self.log(f"  AVERAGE TIME:     {metrics.get_eat():.0f} NS")
            self.log("\nEFFECTIVE ACCESS TIME (EAT):")
            self.log(f"  EAT:              {metrics.get_eat():.2f} NS")

            self.log("\n✅ SIMULATION COMPLETE!")
            self.update_status(f"SIMULATION COMPLETE - {algo}")

        except Exception as e:
            self.log(f"\n❌ ERROR: {e}")
            import traceback
            self.log(traceback.format_exc())
            self.update_status(f"ERROR: {e}")
        finally:
            self.progress.stop()
            self.progress['value'] = 100
            self.progress_label.config(text="100%")


def main():
    root = tk.Tk()
    app = MMUGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()