import math
import tkinter as tk
from collections import OrderedDict, deque
from pathlib import Path
from tkinter import ttk


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.txt"
TRACE_FILE = BASE_DIR / "Trace_validator.txt"


class SystemConfig:
    def __init__(self):
        self.ram_kb = 32
        self.page_bytes = 2048
        self.tlb_size = 4
        self.tlb_latency_ns = 1
        self.ram_latency_ns = 100
        self.disk_latency_ns = 10_000_000
        self.ram_bytes = 0
        self.num_frames = 0
        self.offset_bits = 0
        self.offset_mask = 0


def parse_config(path):
    config = SystemConfig()
    if path.exists():
        for raw_line in path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            name, value = [part.strip() for part in line.split("=", 1)]
            try:
                value = int(value)
            except ValueError:
                continue

            if name == "RAM_KB":
                config.ram_kb = value
            elif name == "PAGE_BYTES":
                config.page_bytes = value
            elif name == "TLB_SIZE":
                config.tlb_size = value
            elif name == "TLB_LATENCY_PS":
                config.tlb_latency_ns = max(1, math.ceil(value / 1000))
            elif name == "RAM_LATENCY_NS":
                config.ram_latency_ns = value
            elif name == "DISK_LATENCY_MS":
                config.disk_latency_ns = value * 1_000_000

    config.ram_bytes = max(1, config.ram_kb) * 1024
    config.page_bytes = max(1, config.page_bytes)
    config.num_frames = max(1, config.ram_bytes // config.page_bytes)
    config.offset_bits = int(math.log2(config.page_bytes))
    config.offset_mask = config.page_bytes - 1
    return config


def parse_trace(path):
    accesses = []
    if not path.exists():
        return accesses

    for line_num, raw_line in enumerate(path.read_text().splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        if len(parts) != 2 or parts[0].upper() not in {"R", "W", "READ", "WRITE"}:
            continue

        try:
            address = int(parts[1], 16)
        except ValueError:
            continue

        accesses.append(
            {
                "line": line_num,
                "op": "W" if parts[0].upper() in {"W", "WRITE"} else "R",
                "addr": address,
                "raw": line,
            }
        )
    return accesses


def make_demo_trace(config):
    page = config.page_bytes
    # This sequence is intentionally larger than the default 16-frame config:
    # it shows warm-up faults, TLB hits, page-table hits, evictions, and dirty write-backs.
    pattern = [
        ("W", 0, 0x010),
        ("R", 1, 0x020),
        ("R", 2, 0x030),
        ("W", 0, 0x040),
        ("R", 3, 0x050),
        ("R", 1, 0x060),
        ("W", 4, 0x070),
        ("R", 5, 0x080),
        ("R", 6, 0x090),
        ("W", 7, 0x0A0),
        ("R", 8, 0x0B0),
        ("R", 9, 0x0C0),
        ("W", 10, 0x0D0),
        ("R", 11, 0x0E0),
        ("R", 12, 0x0F0),
        ("W", 13, 0x100),
        ("R", 14, 0x110),
        ("R", 15, 0x120),
        ("W", 16, 0x130),
        ("R", 0, 0x140),
        ("R", 1, 0x150),
        ("W", 17, 0x160),
        ("R", 2, 0x170),
        ("W", 18, 0x180),
        ("R", 4, 0x190),
        ("R", 19, 0x1A0),
        ("W", 5, 0x1B0),
        ("R", 20, 0x1C0),
        ("R", 0, 0x1D0),
        ("W", 21, 0x1E0),
    ]
    accesses = []
    for line, (op, vpn, offset) in enumerate(pattern, 1):
        address = vpn * page + (offset % page)
        accesses.append(
            {
                "line": line,
                "op": op,
                "addr": address,
                "raw": f"{op} 0x{address:08X}",
            }
        )
    return accesses


class PixelMMUGame:
    TILE = 32

    def __init__(self, root):
        self.root = root
        self.root.title("MMU Valley - Pixel Virtual Memory Simulator")
        self.root.geometry("1180x760")
        self.root.minsize(1040, 700)
        self.root.configure(bg="#171923")

        self.config = parse_config(CONFIG_FILE)
        self.file_trace = parse_trace(TRACE_FILE)
        self.demo_trace = make_demo_trace(self.config)
        self.trace = self.demo_trace if len(self.file_trace) < 12 else self.file_trace
        self.trace_source = "Demo values" if self.trace is self.demo_trace else TRACE_FILE.name

        self.algorithm_var = tk.StringVar(value="FIFO")
        self.speed_var = tk.IntVar(value=18)
        self.running = False
        self.animating = False
        self.hero_parts = []

        self.build_shell()
        self.reset_simulation()
        self.draw_world()
        self.render_state("Ready. Choose an algorithm and press Start.")

    def build_shell(self):
        self.canvas = tk.Canvas(
            self.root,
            width=1180,
            height=660,
            bg="#73d972",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        controls = tk.Frame(self.root, bg="#171923")
        controls.pack(fill="x", padx=12, pady=8)

        ttk.Label(controls, text="Algorithm").pack(side="left", padx=(0, 6))
        self.algorithm_menu = ttk.Combobox(
            controls,
            textvariable=self.algorithm_var,
            values=("FIFO", "LRU", "OPT"),
            state="readonly",
            width=8,
        )
        self.algorithm_menu.pack(side="left", padx=(0, 14))
        self.algorithm_menu.bind("<<ComboboxSelected>>", lambda _event: self.reset_and_redraw())

        ttk.Button(controls, text="Start", command=self.start).pack(side="left", padx=4)
        ttk.Button(controls, text="Step", command=self.step_once).pack(side="left", padx=4)
        ttk.Button(controls, text="Reset", command=self.reset_and_redraw).pack(side="left", padx=4)
        ttk.Button(controls, text="Demo Values", command=self.load_demo_values).pack(side="left", padx=4)
        ttk.Button(controls, text="File Trace", command=self.load_file_trace).pack(side="left", padx=4)

        ttk.Label(controls, text="Speed").pack(side="left", padx=(20, 6))
        ttk.Scale(
            controls,
            from_=8,
            to=34,
            variable=self.speed_var,
            orient="horizontal",
            length=160,
        ).pack(side="left")

        self.footer_var = tk.StringVar()
        ttk.Label(controls, textvariable=self.footer_var).pack(side="right")

    def reset_simulation(self):
        self.index = 0
        self.page_table = {}
        self.frames = [None for _ in range(self.config.num_frames)]
        self.free_frames = deque(range(self.config.num_frames))
        self.tlb = OrderedDict()
        self.fifo_queue = deque()
        self.lru_order = OrderedDict()
        self.stats = {
            "accesses": 0,
            "tlb_hits": 0,
            "pt_hits": 0,
            "faults": 0,
            "dirty_writes": 0,
            "time_ns": 0,
        }
        self.last_event = None
        self.future_map = self.build_future_map()

    def build_future_map(self):
        future = {}
        for idx, access in enumerate(self.trace):
            vpn = self.split_address(access["addr"])[0]
            future.setdefault(vpn, deque()).append(idx)
        return future

    def reset_and_redraw(self):
        self.running = False
        self.reset_simulation()
        self.draw_world()
        self.render_state("Simulation reset.")

    def load_demo_values(self):
        self.running = False
        self.trace = self.demo_trace
        self.trace_source = "Demo values"
        self.reset_simulation()
        self.draw_world()
        self.render_state("Loaded dummy demo values: hits, faults, evictions, and dirty writes are included.")

    def load_file_trace(self):
        self.running = False
        self.file_trace = parse_trace(TRACE_FILE)
        self.trace = self.file_trace if self.file_trace else self.demo_trace
        self.trace_source = TRACE_FILE.name if self.file_trace else "Demo values"
        self.reset_simulation()
        self.draw_world()
        self.render_state(f"Loaded {self.trace_source}.")

    def draw_world(self):
        self.canvas.delete("all")
        self.draw_pixel_background()
        self.draw_building(65, 255, 150, 120, "#b87935", "#734c2a", "CPU", "Request Hut")
        self.draw_gate(275, 245, "TLB Gate")
        self.draw_building(455, 210, 175, 150, "#d8a24d", "#8d4f24", "Page Table", "Archive")
        self.draw_building(760, 245, 190, 125, "#6f8fbd", "#344766", "RAM", "Frame Barn")
        self.draw_mine(535, 505, "Disk Mine")
        self.draw_frame_patch()
        self.draw_hud_frame()
        self.draw_legend()

    def draw_pixel_background(self):
        self.canvas.create_rectangle(0, 0, 1180, 660, fill="#78d76b", outline="")
        for x in range(0, 1180, self.TILE):
            for y in range(0, 660, self.TILE):
                color = "#89e46f" if (x // self.TILE + y // self.TILE) % 2 == 0 else "#70cf65"
                self.canvas.create_rectangle(x, y, x + self.TILE, y + self.TILE, fill=color, outline=color)

        self.draw_path([(120, 320), (300, 320), (540, 285), (855, 315), (1035, 315)])
        self.draw_path([(540, 285), (590, 390), (595, 535)])
        self.draw_water()

        for x, y in [(40, 80), (130, 95), (995, 160), (1085, 120), (1000, 520), (75, 535)]:
            self.draw_tree(x, y)

    def draw_path(self, points):
        for index in range(len(points) - 1):
            x1, y1 = points[index]
            x2, y2 = points[index + 1]
            self.canvas.create_line(x1, y1, x2, y2, fill="#d7a84d", width=54)
            self.canvas.create_line(x1, y1, x2, y2, fill="#f0c65f", width=38)
            for dot in range(0, 8):
                px = x1 + (x2 - x1) * dot / 7
                py = y1 + (y2 - y1) * dot / 7
                self.canvas.create_rectangle(px - 5, py + 14, px + 8, py + 21, fill="#b8843d", outline="")

    def draw_water(self):
        self.canvas.create_rectangle(0, 0, 1180, 58, fill="#3ed6df", outline="")
        for y in range(8, 56, 12):
            for x in range(0, 1180, 70):
                self.canvas.create_rectangle(x, y, x + 38, y + 4, fill="#9af5f2", outline="")

    def draw_tree(self, x, y):
        self.canvas.create_rectangle(x + 21, y + 44, x + 35, y + 82, fill="#6b3e1e", outline="#3e2515")
        colors = ["#0f7f5d", "#14966a", "#21b877"]
        for i, color in enumerate(colors):
            self.canvas.create_rectangle(x + 8 - i * 3, y + 18 + i * 9, x + 52 + i * 3, y + 54 + i * 8, fill=color, outline="")
        self.canvas.create_rectangle(x + 18, y + 8, x + 43, y + 28, fill="#31c981", outline="")

    def draw_building(self, x, y, w, h, wall, roof, title, subtitle):
        self.canvas.create_rectangle(x + 12, y + 30, x + w - 12, y + h, fill=wall, outline="#3b2517", width=3)
        self.canvas.create_polygon(x, y + 36, x + w / 2, y, x + w, y + 36, fill=roof, outline="#3b2517", width=3)
        self.canvas.create_rectangle(x + 24, y + h - 45, x + 54, y + h, fill="#75431f", outline="#3b2517", width=2)
        self.canvas.create_rectangle(x + w - 52, y + 55, x + w - 20, y + 83, fill="#a7dfff", outline="#3b2517", width=2)
        self.canvas.create_line(x + w - 36, y + 55, x + w - 36, y + 83, fill="#3b2517", width=2)
        self.canvas.create_line(x + w - 52, y + 69, x + w - 20, y + 69, fill="#3b2517", width=2)
        self.canvas.create_text(x + w / 2, y + h + 20, text=title, font=("Small Fonts", 16, "bold"), fill="#15202b")
        self.canvas.create_text(x + w / 2, y + h + 38, text=subtitle, font=("Small Fonts", 10, "bold"), fill="#29465b")

    def draw_gate(self, x, y, label):
        self.tlb_gate_parts = []
        for dx in (0, 95):
            post = self.canvas.create_rectangle(x + dx, y + 35, x + dx + 25, y + 138, fill="#58515f", outline="#2b2730", width=3)
            gem = self.canvas.create_rectangle(x + dx + 5, y + 14, x + dx + 20, y + 30, fill="#f6d26b", outline="#2b2730", width=2)
            self.tlb_gate_parts.extend([post, gem])
        arch = self.canvas.create_rectangle(x + 10, y + 35, x + 110, y + 62, fill="#393542", outline="#2b2730", width=3)
        self.tlb_gate_parts.append(arch)
        self.canvas.create_text(x + 58, y + 164, text=label, font=("Small Fonts", 15, "bold"), fill="#15202b")

    def draw_mine(self, x, y, label):
        self.disk_parts = []
        self.disk_parts.append(self.canvas.create_rectangle(x + 5, y + 56, x + 172, y + 125, fill="#5b4b42", outline="#2c211d", width=3))
        self.disk_parts.append(self.canvas.create_polygon(x + 0, y + 62, x + 88, y, x + 180, y + 62, fill="#403536", outline="#2c211d", width=3))
        self.canvas.create_rectangle(x + 64, y + 68, x + 116, y + 125, fill="#171923", outline="#2c211d", width=3)
        for px, py in [(x + 22, y + 83), (x + 138, y + 78), (x + 96, y + 30)]:
            self.canvas.create_rectangle(px, py, px + 16, py + 16, fill="#ffd166", outline="#8a5a1f")
        self.canvas.create_text(x + 90, y + 150, text=label, font=("Small Fonts", 15, "bold"), fill="#15202b")

    def draw_frame_patch(self):
        self.canvas.create_rectangle(760, 410, 1110, 620, fill="#9b6b36", outline="#5a391d", width=3)
        self.canvas.create_text(935, 393, text="Physical Frames", font=("Small Fonts", 15, "bold"), fill="#15202b")

    def draw_hud_frame(self):
        self.canvas.create_rectangle(16, 78, 360, 205, fill="#2a1f32", outline="#f0c65f", width=4)
        self.hud_text = self.canvas.create_text(
            32,
            93,
            text="",
            anchor="nw",
            font=("Consolas", 11, "bold"),
            fill="#fff6ca",
        )
        self.canvas.create_rectangle(382, 78, 720, 175, fill="#233145", outline="#8bd3ff", width=3)
        self.trace_text = self.canvas.create_text(
            397,
            93,
            text="",
            anchor="nw",
            font=("Consolas", 10, "bold"),
            fill="#d9f7ff",
        )
        self.canvas.create_rectangle(742, 78, 1148, 175, fill="#2b2938", outline="#d79cff", width=3)
        self.event_text = self.canvas.create_text(
            757,
            93,
            text="",
            anchor="nw",
            font=("Consolas", 10, "bold"),
            fill="#ffe8ff",
        )

    def draw_legend(self):
        items = [("TLB hit", "#54ef8b"), ("Page table hit", "#ffd166"), ("Fault / disk", "#ff6b6b"), ("Dirty write", "#f97316")]
        x = 28
        for label, color in items:
            self.canvas.create_rectangle(x, 635, x + 18, 653, fill=color, outline="#14213d")
            self.canvas.create_text(x + 26, 644, text=label, anchor="w", font=("Small Fonts", 10, "bold"), fill="#15202b")
            x += 150

    def render_state(self, message):
        eat = self.stats["time_ns"] / self.stats["accesses"] if self.stats["accesses"] else 0
        fault_rate = (self.stats["faults"] / self.stats["accesses"] * 100) if self.stats["accesses"] else 0
        hit_rate = (self.stats["tlb_hits"] / self.stats["accesses"] * 100) if self.stats["accesses"] else 0
        hud = (
            f"MMU VALLEY\n"
            f"Access {self.index}/{len(self.trace)} | {self.algorithm_var.get()}\n"
            f"Trace: {self.trace_source}\n"
            f"TLB hits: {self.stats['tlb_hits']} ({hit_rate:5.1f}%)\n"
            f"PT hits:  {self.stats['pt_hits']}\n"
            f"Faults:   {self.stats['faults']} ({fault_rate:5.1f}%)\n"
            f"Dirty writes: {self.stats['dirty_writes']}\n"
            f"EAT: {eat:,.1f} ns"
        )
        self.canvas.itemconfig(self.hud_text, text=hud)

        upcoming = []
        for access in self.trace[self.index : self.index + 4]:
            vpn, offset = self.split_address(access["addr"])
            upcoming.append(f"{access['op']} {access['addr']:#010x}  VPN={vpn:#x} OFF={offset:#x}")
        self.canvas.itemconfig(self.trace_text, text="Next trace lines\n" + "\n".join(upcoming))
        self.canvas.itemconfig(self.event_text, text=message)
        self.footer_var.set(
            f"Frames: {self.config.num_frames} | Page: {self.config.page_bytes} B | TLB: {self.config.tlb_size}"
        )
        self.draw_tlb_slots()
        self.draw_frame_slots()
        self.draw_page_table_slots()

    def draw_tlb_slots(self):
        self.canvas.delete("tlbslot")
        entries = list(self.tlb.items())
        for i in range(max(1, self.config.tlb_size)):
            x = 267 + (i % 4) * 38
            y = 405 + (i // 4) * 35
            label = "--"
            color = "#dee2e6"
            if i < len(entries):
                vpn, frame = entries[i]
                label = f"{vpn:X}->{frame}"
                color = "#f9dc5c"
            self.canvas.create_rectangle(x, y, x + 34, y + 27, fill=color, outline="#32323d", tags="tlbslot")
            self.canvas.create_text(x + 17, y + 14, text=label, font=("Small Fonts", 8, "bold"), tags="tlbslot")

    def draw_frame_slots(self):
        self.canvas.delete("frameslot")
        visible = min(self.config.num_frames, 32)
        for i in range(visible):
            row, col = divmod(i, 8)
            x = 785 + col * 39
            y = 430 + row * 42
            vpn = self.frames[i]
            fill = "#4cc9f0" if vpn is not None else "#c4f1be"
            self.canvas.create_rectangle(x, y, x + 33, y + 32, fill=fill, outline="#31572c", width=2, tags="frameslot")
            text = f"F{i}" if vpn is None else f"{vpn:X}"
            self.canvas.create_text(x + 17, y + 16, text=text, font=("Small Fonts", 8, "bold"), tags="frameslot")
            if vpn is not None and self.page_table.get(vpn, {}).get("dirty"):
                self.canvas.create_rectangle(x + 23, y + 3, x + 30, y + 10, fill="#f97316", outline="", tags="frameslot")

    def draw_page_table_slots(self):
        self.canvas.delete("ptslot")
        entries = list(self.page_table.items())[-6:]
        for i, (vpn, data) in enumerate(entries):
            x, y = 470, 390 + i * 28
            dirty = "D" if data["dirty"] else "-"
            self.canvas.create_rectangle(x, y, x + 130, y + 22, fill="#fff3bf", outline="#6c4f28", tags="ptslot")
            self.canvas.create_text(
                x + 65,
                y + 11,
                text=f"VPN {vpn:X} -> F{data['frame']} {dirty}",
                font=("Small Fonts", 9, "bold"),
                tags="ptslot",
            )

    def split_address(self, address):
        return address >> self.config.offset_bits, address & self.config.offset_mask

    def start(self):
        if self.running or self.animating:
            return
        self.running = True
        self.step_once()

    def step_once(self):
        if self.animating or self.index >= len(self.trace):
            self.running = False
            if self.index >= len(self.trace):
                self.render_state("Trace complete. Reset to replay the valley route.")
            return

        access = self.trace[self.index]
        self.animating = True
        event = self.process_access(access)
        self.draw_world()
        self.render_state(self.describe_event(event))
        self.spawn_sprite(access, event)

    def process_access(self, access):
        vpn, offset = self.split_address(access["addr"])
        event = {
            "access": access,
            "vpn": vpn,
            "offset": offset,
            "frame": None,
            "outcome": "",
            "victim": None,
            "dirty_eviction": False,
            "path": [(120, 320), (330, 320)],
        }

        self.consume_future(vpn)
        self.stats["accesses"] += 1

        if vpn in self.tlb:
            frame = self.tlb[vpn]
            self.tlb.move_to_end(vpn)
            self.mark_used(vpn)
            self.mark_write(vpn, access["op"])
            self.stats["tlb_hits"] += 1
            self.stats["time_ns"] += self.config.tlb_latency_ns
            event.update({"outcome": "TLB_HIT", "frame": frame, "path": [(120, 320), (330, 320), (1035, 315)]})
            return event

        self.stats["time_ns"] += self.config.tlb_latency_ns
        event["path"].append((540, 285))

        if vpn in self.page_table:
            frame = self.page_table[vpn]["frame"]
            self.stats["pt_hits"] += 1
            self.stats["time_ns"] += self.config.ram_latency_ns
            self.mark_used(vpn)
            self.mark_write(vpn, access["op"])
            self.add_tlb(vpn, frame)
            event.update({"outcome": "PT_HIT", "frame": frame, "path": [(120, 320), (330, 320), (540, 285), (855, 315), (1035, 315)]})
            return event

        self.stats["faults"] += 1
        self.stats["time_ns"] += self.config.ram_latency_ns + self.config.disk_latency_ns
        event["path"].extend([(595, 535), (855, 315), (1035, 315)])

        if self.free_frames:
            frame = self.free_frames.popleft()
        else:
            victim = self.select_victim()
            frame = self.page_table[victim]["frame"]
            event["victim"] = victim
            event["dirty_eviction"] = self.page_table[victim]["dirty"]
            if event["dirty_eviction"]:
                self.stats["dirty_writes"] += 1
                self.stats["time_ns"] += self.config.disk_latency_ns
            self.evict_page(victim)

        self.frames[frame] = vpn
        self.page_table[vpn] = {"frame": frame, "dirty": access["op"] == "W"}
        self.mark_used(vpn)
        self.add_tlb(vpn, frame)
        event.update({"outcome": "PAGE_FAULT", "frame": frame})
        return event

    def consume_future(self, vpn):
        if vpn in self.future_map and self.future_map[vpn]:
            self.future_map[vpn].popleft()

    def mark_used(self, vpn):
        algorithm = self.algorithm_var.get()
        if algorithm == "FIFO":
            if vpn not in self.fifo_queue:
                self.fifo_queue.append(vpn)
        elif algorithm == "LRU":
            self.lru_order[vpn] = True
            self.lru_order.move_to_end(vpn)

    def mark_write(self, vpn, op):
        if op == "W" and vpn in self.page_table:
            self.page_table[vpn]["dirty"] = True

    def add_tlb(self, vpn, frame):
        if vpn in self.tlb:
            self.tlb.move_to_end(vpn)
        self.tlb[vpn] = frame
        while len(self.tlb) > self.config.tlb_size:
            self.tlb.popitem(last=False)

    def select_victim(self):
        algorithm = self.algorithm_var.get()
        if algorithm == "LRU" and self.lru_order:
            victim, _ = self.lru_order.popitem(last=False)
            return victim

        if algorithm == "OPT":
            victim = None
            furthest = -1
            for vpn in self.page_table:
                future_uses = self.future_map.get(vpn, deque())
                if not future_uses:
                    return vpn
                if future_uses[0] > furthest:
                    furthest = future_uses[0]
                    victim = vpn
            return victim

        while self.fifo_queue:
            victim = self.fifo_queue.popleft()
            if victim in self.page_table:
                return victim
        return next(iter(self.page_table))

    def evict_page(self, victim):
        frame = self.page_table[victim]["frame"]
        self.frames[frame] = None
        self.page_table.pop(victim, None)
        self.tlb.pop(victim, None)
        self.lru_order.pop(victim, None)

    def describe_event(self, event):
        access = event["access"]
        lines = [
            f"Line {access['line']}: {access['op']} {access['addr']:#010x}",
            f"VPN {event['vpn']:#x}, offset {event['offset']:#x}",
            f"Result: {event['outcome'].replace('_', ' ')}",
            f"Frame: F{event['frame']}",
        ]
        if event["victim"] is not None:
            writeback = "yes" if event["dirty_eviction"] else "no"
            lines.append(f"Evicted VPN {event['victim']:#x}; dirty write: {writeback}")
        return "\n".join(lines)

    def spawn_sprite(self, access, event):
        self.hero_parts = []
        x, y = event["path"][0]
        color = "#ffb86b" if access["op"] == "R" else "#ff6b6b"
        self.hero_parts.append(self.canvas.create_rectangle(x - 11, y - 22, x + 11, y + 8, fill=color, outline="#3b2517", width=2))
        self.hero_parts.append(self.canvas.create_rectangle(x - 15, y - 32, x + 15, y - 20, fill="#75431f", outline="#3b2517", width=2))
        self.hero_parts.append(self.canvas.create_rectangle(x - 7, y - 43, x + 7, y - 31, fill="#ffd7a8", outline="#3b2517", width=2))
        self.hero_parts.append(
            self.canvas.create_text(
                x,
                y + 22,
                text=f"{access['op']} VPN {event['vpn']:X}",
                font=("Small Fonts", 10, "bold"),
                fill="#15202b",
            )
        )
        self.animate_path(event, 1)

    def animate_path(self, event, waypoint_index):
        if waypoint_index >= len(event["path"]):
            self.flash_event(event)
            self.index += 1
            self.animating = False
            self.canvas.delete(*self.hero_parts)
            self.render_state(self.describe_event(event))
            if self.running:
                self.root.after(280, self.step_once)
            return

        target = event["path"][waypoint_index]
        self.move_sprite_to(event, target, waypoint_index)

    def move_sprite_to(self, event, target, waypoint_index):
        current = self.sprite_center()
        dx = target[0] - current[0]
        dy = target[1] - current[1]
        distance = max(1, math.hypot(dx, dy))
        step = max(4, self.speed_var.get())
        if distance <= step:
            self.move_sprite(dx, dy)
            self.flash_checkpoint(event, waypoint_index)
            self.root.after(60, lambda: self.animate_path(event, waypoint_index + 1))
            return

        self.move_sprite(dx / distance * step, dy / distance * step)
        self.root.after(18, lambda: self.move_sprite_to(event, target, waypoint_index))

    def sprite_center(self):
        x1, y1, x2, y2 = self.canvas.coords(self.hero_parts[0])
        return (x1 + x2) / 2, y2 - 8

    def move_sprite(self, dx, dy):
        for part in self.hero_parts:
            self.canvas.move(part, dx, dy)

    def flash_checkpoint(self, event, waypoint_index):
        if waypoint_index == 1:
            self.flash_items(self.tlb_gate_parts, "#54ef8b" if event["outcome"] == "TLB_HIT" else "#ff6b6b")
        elif waypoint_index == 2 and event["outcome"] in {"PT_HIT", "PAGE_FAULT"}:
            self.flash_rect(455, 210, 630, 360, "#ffd166" if event["outcome"] == "PT_HIT" else "#ff6b6b")
        elif waypoint_index == 3 and event["outcome"] == "PAGE_FAULT":
            self.flash_items(self.disk_parts, "#ff8c42")

    def flash_event(self, event):
        if event["dirty_eviction"]:
            self.flash_items(self.disk_parts, "#f97316")
        if event["outcome"] == "TLB_HIT":
            self.flash_items(self.tlb_gate_parts, "#54ef8b")
        elif event["outcome"] == "PT_HIT":
            self.flash_rect(455, 210, 630, 360, "#ffd166")
        else:
            self.flash_items(self.disk_parts, "#ff6b6b")

    def flash_items(self, items, color):
        old = [(item, self.canvas.itemcget(item, "fill")) for item in items]
        for item, _old_color in old:
            self.canvas.itemconfig(item, fill=color)
        self.root.after(140, lambda: [self.canvas.itemconfig(item, fill=old_color) for item, old_color in old])

    def flash_rect(self, x1, y1, x2, y2, color):
        flash = self.canvas.create_rectangle(x1 - 6, y1 - 6, x2 + 6, y2 + 6, outline=color, width=6)
        self.root.after(180, lambda: self.canvas.delete(flash))


if __name__ == "__main__":
    root = tk.Tk()
    app = PixelMMUGame(root)
    root.mainloop()
