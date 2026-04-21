class MemoryAccess:

    def __init__(self, line_num, address, is_write, original_line):
        self.line_num = line_num  # Line number in trace file
        self.address = address  # Virtual address (integer)
        self.is_write = is_write  # True = write, False = read
        self.original_line = original_line  # Raw line text

    def __repr__(self):
        op = "WRITE" if self.is_write else "READ"
        return f"{op} {hex(self.address)} (line {self.line_num})"


def parse_trace(filename, max_address=0xFFFFFFFF):

    accesses = []
    errors = []
    line_count = 0
    read_count = 0
    write_count = 0

    try:
        with open(filename, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line_count += 1
                original_line = line
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Parse the line
                is_write = False
                address_str = None

                # Split into parts
                parts = line.split()

                if len(parts) == 2:
                    # Format: "R 0x1234" or "0x1234 R"
                    first, second = parts

                    # Check if first part is R/W
                    if first.upper() in ['R', 'W', 'READ', 'WRITE']:
                        # Format: "R 0x1234"
                        is_write = (first.upper() in ['W', 'WRITE'])
                        address_str = second
                    elif second.upper() in ['R', 'W', 'READ', 'WRITE']:
                        # Format: "0x1234 R"
                        is_write = (second.upper() in ['W', 'WRITE'])
                        address_str = first
                    else:
                        errors.append(f"Line {line_num}: Invalid format - '{line}'")
                        continue

                elif len(parts) == 1:
                    # Format: "0x1234" only (no R/W info)
                    address_str = parts[0]
                    is_write = False  # Assume read
                    # Uncomment next line to show warning
                    # print(f"Warning: Line {line_num} has no R/W info. Assuming READ.")

                else:
                    errors.append(f"Line {line_num}: Invalid format - '{line}'")
                    continue

                # Clean address string
                address_str = address_str.strip()
                if address_str.startswith('0x') or address_str.startswith('0X'):
                    address_str = address_str[2:]

                # Convert hex to integer
                try:
                    address = int(address_str, 16)
                except ValueError:
                    errors.append(f"Line {line_num}: Invalid hex - '{address_str}'")
                    continue

                # Check out of bounds (32-bit)
                if address > max_address:
                    errors.append(f"Line {line_num}: Out of bounds - {hex(address)} > {hex(max_address)}")
                    continue

                # Valid access
                if is_write:
                    write_count += 1
                else:
                    read_count += 1

                accesses.append(MemoryAccess(line_num, address, is_write, original_line))

    except FileNotFoundError:
        print(f"Error: Trace file '{filename}' not found!")
        raise

    # Print summary
    print(f"\n{'=' * 50}")
    print(f"TRACE FILE PARSING SUMMARY")
    print(f"{'=' * 50}")
    print(f"File:           {filename}")
    print(f"Total lines:    {line_count}")
    print(f"Valid accesses: {len(accesses)}")
    print(f"  Reads:        {read_count}")
    print(f"  Writes:       {write_count}")
    print(f"Errors:         {len(errors)}")

    if errors and len(errors) <= 10:
        for err in errors:
            print(f"  {err}")
    elif errors:
        print(f"  (Showing first 5 of {len(errors)} errors)")
        for err in errors[:5]:
            print(f"  {err}")

    print(f"{'=' * 50}\n")

    return accesses


def get_stats(accesses):

    if not accesses:
        return {'total': 0, 'reads': 0, 'writes': 0, 'write_percent': 0}

    reads = sum(1 for a in accesses if not a.is_write)
    writes = sum(1 for a in accesses if a.is_write)

    return {
        'total': len(accesses),
        'reads': reads,
        'writes': writes,
        'write_percent': (writes / len(accesses)) * 100
    }


# Test the module when run directly
if __name__ == "__main__":
    print("=" * 50)
    print("TESTING TRACE PARSER")
    print("=" * 50)

    # Test with our small trace file
    accesses = parse_trace("codes.txt")

    # Print first 5 accesses
    print("\nFIRST 5 ACCESSES:")
    print("-" * 40)
    for acc in accesses[:5]:
        op = "WRITE" if acc.is_write else "READ"
        print(f"Line {acc.line_num:4}: {op} {hex(acc.address)}")

    # Print statistics
    stats = get_stats(accesses)
    print(f"\nSTATISTICS:")
    print("-" * 40)
    print(f"Total accesses: {stats['total']}")
    print(f"Reads:          {stats['reads']}")
    print(f"Writes:         {stats['writes']}")
    print(f"Write %:        {stats['write_percent']:.1f}%")

    print("\n" + "=" * 50)
    print("✅ Trace Parser works!")
    print("=" * 50)