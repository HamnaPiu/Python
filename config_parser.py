import math

class Config:
    def __init__(self):
        self.ram_kb = 0
        self.page_bytes = 0
        self.tlb_size = 0
        self.tlb_latency_ns = 0
        self.ram_latency_ns = 0
        self.disk_latency_ns = 0
        self.ram_bytes = 0
        self.num_frames = 0
        self.offset_bits = 0
        self.offset_mask_value = 0

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
        print(f"TLB LATENCY: {self.tlb_latency_ns} NS")
        print(f"RAM LATENCY: {self.ram_latency_ns} NS")
        print(f"DISK LATENCY: {self.disk_latency_ns} NS")
        print("\n")


def parse_config(filename):
    config = Config()

    try:
        with open(filename, 'r') as file_read:
            for line in file_read:
                line = line.strip()

                if not line or line.startswith('#'):
                    continue

                if '=' not in line:
                    continue

                name, value = line.split('=')
                name = name.strip()

                try:
                    value = int(value.strip())
                except ValueError:
                    print(f"WARNING: COULD NOT PARSE '{value}' AS INTEGER")
                    continue

                if name == 'RAM_KB':
                    config.ram_kb = value
                elif name == 'PAGE_BYTES':
                    config.page_bytes = value
                elif name == 'TLB_SIZE':
                    config.tlb_size = value
                elif name == 'TLB_LATENCY_NS':
                    config.tlb_latency_ns = value
                elif name == 'RAM_LATENCY_NS':
                    config.ram_latency_ns = value
                elif name == 'DISK_LATENCY_NS':
                    config.disk_latency_ns = value
                else:
                    print(f"WARNING: UNKNOWN CONFIG PARAMETER '{name}'")

    except FileNotFoundError:
        print(f"ERROR: CONFIG FILE '{filename}' NOT FOUND")
        raise

    return config


def calculate_derived_values(config):
    if config.ram_kb <= 0:
        print("WARNING: RAM SIZE IS INVALID, USING DEFAULT 1024 KB")
        config.ram_kb = 1024

    if config.page_bytes <= 0:
        print("WARNING: PAGE SIZE IS INVALID, USING DEFAULT 4096 BYTES")
        config.page_bytes = 4096

    config.ram_bytes = config.ram_kb * 1024

    config.num_frames = config.ram_bytes // config.page_bytes

    config.offset_bits = int(math.log2(config.page_bytes))

    config.offset_mask_value = config.page_bytes - 1

    return config


if __name__ == "__main__":
    print("TESTING CONFIG PARSER...")
    config = parse_config("config.txt")
    config = calculate_derived_values(config)
    config.print_config()
    print("CONFIG PARSER WORKS!")