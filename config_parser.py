import math

class Config:
    def __init__(self):
        # INPUT VALUES (from file)
        self.ram_kb = 0
        self.page_bytes = 0
        self.tlb_size = 0
        self.tlb_latency_ps = 0      # picoseconds
        self.ram_latency_ns = 0      # nanoseconds
        self.disk_latency_ms = 0     # milliseconds

        # CALCULATED VALUES
        self.ram_bytes = 0
        self.num_frames = 0
        self.offset_bits = 0          # SHIFT value
        self.offset_mask_value = 0          # page_bytes - 1

    def print_config(self):
        print("\n")
        print("SYSTEM SPECS")
        print("\n")
        print(f"RAM SIZE: {self.ram_kb} KB ({self.ram_bytes} BYTES)")
        print(f"PAGE SIZE: {self.page_bytes} BYTES")
        print(f"NUMBER OF FRAMES: {self.num_frames}")
        print(f"OFFSET BITS: {self.offset_bits}  ← SHIFT VALUE")
        print(f"OFFSET MASK: 0x{self.offset_mask_value:X}")
        print(f"TLB SIZE: {self.tlb_size}")
        print(f"TLB LATENCY: {self.tlb_latency_ps} PS")
        print(f"RAM LATENCY: {self.ram_latency_ns} NS")
        print(f"DISK LATENCY: {self.disk_latency_ms} MS")
        print("\n")


def parse_config(filename):
    config = Config()   # ← FIXED: Use Config, not SystemConfig

    try:
        with open(filename, 'r') as file_read:
            for line in file_read:
                line = line.strip()

                # SKIP EMPTY LINES AND COMMENTS
                if not line or line.startswith('#'):
                    continue

                # SPLIT AT EQUALS SIGN
                if '=' not in line:
                    continue

                name, value = line.split('=')
                name = name.strip()

                try:
                    value = int(value.strip())
                except ValueError:
                    print(f"WARNING: COULD NOT PARSE '{value}' AS INTEGER")
                    continue

                # ASSIGN VALUES (MATCH YOUR CONFIG.TXT NAMES)
                if name == 'RAM_KB':
                    config.ram_kb = value
                elif name == 'PAGE_BYTES':
                    config.page_bytes = value
                elif name == 'TLB_SIZE':
                    config.tlb_size = value
                elif name == 'TLB_LATENCY_PS':
                    config.tlb_latency_ps = value
                elif name == 'RAM_LATENCY_NS':
                    config.ram_latency_ns = value
                elif name == 'DISK_LATENCY_MS':
                    config.disk_latency_ms = value
                else:
                    print(f"WARNING: UNKNOWN CONFIG PARAMETER '{name}'")

    except FileNotFoundError:
        print(f"ERROR: CONFIG FILE '{filename}' NOT FOUND")
        raise

    return config


def calculate_derived_values(config):
    # HANDLE NEGATIVE OR ZERO RAM SIZE
    if config.ram_kb <= 0:
        print("WARNING: RAM SIZE IS INVALID, USING DEFAULT 1024 KB")
        config.ram_kb = 1024

    # HANDLE NEGATIVE OR ZERO PAGE SIZE
    if config.page_bytes <= 0:
        print("WARNING: PAGE SIZE IS INVALID, USING DEFAULT 4096 BYTES")
        config.page_bytes = 4096

    # CONVERT KB TO BYTES
    config.ram_bytes = config.ram_kb * 1024

    # CALCULATE NUMBER OF FRAMES
    config.num_frames = config.ram_bytes // config.page_bytes

    # CALCULATE OFFSET BITS (log2 OF PAGE SIZE)
    config.offset_bits = int(math.log2(config.page_bytes))

    # CALCULATE OFFSET MASK (PAGE_SIZE - 1)
    config.offset_mask_value = config.page_bytes - 1

    return config


if __name__ == "__main__":
    print("TESTING CONFIG PARSER...")

    # PARSE CONFIG
    config = parse_config("config.txt")
    config = calculate_derived_values(config)

    # PRINT RESULTS
    config.print_config()

    print("CONFIG PARSER WORKS!")