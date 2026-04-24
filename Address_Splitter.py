def address_splitter(virtual_addr, offset_bits, offset_mask):
    """
    Split address coming from trace_validator into VPN and offset.
    
    Argument :
        virtual_addr:  virtual address (from AddressRead.addr) as in frm trace_validator
        offset_bits and offset_mask from the config_parser
    Return:
        tuple: (vpn, offset) as integers
    """
    vpn = virtual_addr >> offset_bits
    offset = virtual_addr & offset_mask
    return vpn, offset


if __name__ == "__main__":
    print("\n")
    print("TESTING ADDRESS SPLITTER")
    print("\n")
    
    # Example values (would come from config normally)
    OFFSET_BITS = 11
    OFFSET_MASK = 0x7FF
    
    test_addr = 0x00001000
    
    vpn, offset = address_splitter(test_addr, OFFSET_BITS, OFFSET_MASK)
    
    print(f"VIRTUAL ADDRESS: {hex(test_addr)}")
    print(f"OFFSET BITS:     {OFFSET_BITS}")
    print(f"OFFSET MASK:     0x{OFFSET_MASK:X}")
    print(f"VPN:             {hex(vpn)}")
    print(f"OFFSET:          {hex(offset)}")
    print("\n✅ ADDRESS SPLITTER READY")
    print("=" * 50)