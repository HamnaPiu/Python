class AddressRead:

    def __init__(self, line_num, address, is_write, original_line):
        self.line_index = line_num      # Line number in trace file
        self.addr = address             # Virtual address (integer)
        self.write_flag = is_write      # True = write, False = read
        self.trace = original_line      # Raw line text

    

#Reads the trace file, validates each line, and returns a list of AddressRead objects.
def parse_trace(filename, max_address=0xFFFFFFFF):

    accesses = []
    errors = []
    line_count = 0
    read_count = 0
    write_count = 0

    try:
        with open(filename, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line_count = line_count + 1
                original_line = line
                line = line.strip()

                if not line:
                    continue

                is_write = False
                address_str = None

                parts = line.split() #["R", "0x1000"]

                if len(parts) == 2:
                    
                    first, second = parts

                    if first in ['R', 'W', 'READ', 'WRITE']:
                        is_write = (first in ['W', 'WRITE'])
                        address_str = second
                    else:
                        errors.append(f"LINE {line_num}: INVALID FORMAT - '{line}'")
                        continue
                else:
                    errors.append(f"LINE {line_num}: INVALID FORMAT - '{line}'")
                    continue

                try:
                    address = int(address_str, 16)
                except ValueError:
                    errors.append(f"LINE {line_num}: INVALID HEX - '{address_str}'")
                    continue

                if address > max_address:
                    errors.append(f"LINE {line_num}: OUT OF BOUNDS - {hex(address)} > {hex(max_address)}")
                    continue

                if is_write:
                    write_count += 1
                else:
                    read_count += 1

                accesses.append(AddressRead(line_num, address, is_write, original_line))

    except FileNotFoundError:
        print(f"ERROR: TRACE FILE '{filename}' NOT FOUND!")
        raise

    print("\n")
    print("TRACE FILE PARSING SUMMARY")
    print("\n")
    print(f"FILE:           {filename}")
    print(f"TOTAL LINES:    {line_count}")
    print(f"VALID ACCESSES: {len(accesses)}")
    print(f"  READS:        {read_count}")
    print(f"  WRITES:       {write_count}")
    print(f"ERRORS:         {len(errors)}")

    
    if errors:
        print(f"  (SHOWING FIRST FEW {len(errors)} ERRORS)")
        for err in errors[:5]:
            print(f"  {err}")

    print("\n")

    return accesses


def get_stats(accesses):

    if not accesses:
        return {'total': 0, 'reads': 0, 'writes': 0, 'write_percent': 0}

    reads = 0
    for a in accesses:
        if not a.write_flag:   # if it's a READ
            reads = reads + 1

    writes = len(accesses) - reads
    return {
        'total': len(accesses),
        'reads': reads,
        'writes': writes,
        'write_percent': (writes / len(accesses)) * 100
    }


print("TRACE PARSER MODULE LOADED")

if __name__ == "__main__":

    print("TESTING TRACE PARSER")
    print("\n")

    accesses = parse_trace("Trace_validator.txt")

    print("\nFIRST 5 ACCESSES:")
    print("\n")
    for acc in accesses[:5]:
        operation = "WRITE" if acc.write_flag else "READ"
        print(f"LINE {acc.line_index:4}: {operation} {hex(acc.addr)}")

    stats = get_stats(accesses)
    print("\nSTATISTICS:\n")
    
    print(f"TOTAL ACCESSES: {stats['total']}")
    print(f"READS:          {stats['reads']}")
    print(f"WRITES:         {stats['writes']}")
    print(f"WRITE %:        {stats['write_percent']:.1f}%")

    print("\n")
    print("TRACE PARSER WORKS!")
    print("\n")