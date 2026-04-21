import math
class SystemConfig:
    def __init__(self):
        # Input values (from file)
        self.ram_size_kb = 0
        self.page_size_bytes = 0
        self.tlb_size = 0
        self.tlb_latency_ns = 0
        self.ram_latency_ns = 0
        self.disk_latency_ms = 0

        # Calculated values
        self.ram_size_bytes = 0
        self.num_frames = 0
        self.offset_bits = 0  # This is the SHIFT value!
        self.offset_mask = 0

    def print_config(self):
        print("\n" + "=" * 50)
        print("SYSTEM CONFIGURATION")
        print("=" * 50)
        print(f"RAM Size: {self.ram_size_kb} KB ({self.ram_size_bytes} bytes)")
        print(f"Page Size: {self.page_size_bytes} bytes")
        print(f"Total Frames: {self.num_frames}")
        print(f"Offset Bits: {self.offset_bits}  ← SHIFT value")
        print(f"Offset Mask: 0x{self.offset_mask:X}")
        print(f"TLB Size: {self.tlb_size}")
        print(f"TLB Latency: {self.tlb_latency_ns} ns")
        print(f"RAM Latency: {self.ram_latency_ns} ns")
        print(f"Disk Latency: {self.disk_latency_ms} ms")
        print("=" * 50 + "\n")


def parse_config(filename):
    config = SystemConfig()

    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()

                 # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Split at equals sign
                if '=' not in line:
                    continue

                name, value = line.split('=')
                name = name.strip()

                try:
                    value = int(value.strip())
                except ValueError:
                    print(f"Warning: Could not parse '{value}' as integer")
                    continue

                # Assign values
                if name == 'RAM_SIZE_KB':
                    config.ram_size_kb = value
                elif name == 'PAGE_SIZE_BYTES':
                    config.page_size_bytes = value
                elif name == 'TLB_SIZE':
                    config.tlb_size = value
                elif name == 'TLB_LATENCY_NS':
                    config.tlb_latency_ns = value
                elif name == 'RAM_LATENCY_NS':
                    config.ram_latency_ns = value
                elif name == 'DISK_LATENCY_MS':
                    config.disk_latency_ms = value
                else:
                     print(f"Warning: Unknown config parameter '{name}'")
    except FileNotFoundError:
        print(f"Error: Config file '{filename}' not found!")
        raise

    return config


def calculate_derived_values(config):
    # Handle negative or zero RAM size
    if config.ram_size_kb <= 0:
        print(f"Warning: RAM size {config.ram_size_kb} KB is invalid, using default 1024 KB")
        config.ram_size_kb = 1024

    # Handle negative or zero page size
    if config.page_size_bytes <= 0:
        print(f"Warning: Page size {config.page_size_bytes} bytes is invalid, using default 4096 bytes")
        config.page_size_bytes = 4096

    # Convert KB to bytes
    config.ram_size_bytes = config.ram_size_kb * 1024

    # Calculate number of frames
    config.num_frames = config.ram_size_bytes // config.page_size_bytes

    # Calculate offset bits (SHIFT value) - log2(page_size)
    config.offset_bits = int(math.log2(config.page_size_bytes))

    # Verify page size is power of two (optional sanity check)
    if (1 << config.offset_bits) != config.page_size_bytes:
        print(f"Warning: Page size {config.page_size_bytes} is not a power of 2!")
        # Adjust to next power of two
        config.offset_bits = math.ceil(math.log2(config.page_size_bytes))

    # Calculate offset mask (page_size - 1)
    config.offset_mask = config.page_size_bytes - 1

    return config

if __name__ == "__main__":
    print("Testing Config Parser...")

    # Parse config
    config = parse_config("config.txt")
    config = calculate_derived_values(config)

    # Print results
    config.print_config()

    print("✅ Config Parser works!")