class PageTableEntry:
    def __init__(self, frame_num):
        self.frame_num = frame_num
        self.valid = 1
        self.dirty = 0

    def mark_dirty(self):
        self.dirty = 1


class PageTable:
    def __init__(self):
        self.entries = {}   # vpn -> PageTableEntry

    def lookup(self, vpn):
        """Return PageTableEntry if valid, else None."""
        pte = self.entries.get(vpn)
        return pte if pte and pte.valid else None

    def add(self, vpn, frame_num):
        """Add a new mapping (after page fault)."""
        self.entries[vpn] = PageTableEntry(frame_num)

    def remove(self, vpn):
        """Remove mapping (on eviction)."""
        self.entries.pop(vpn, None)

    def mark_dirty(self, vpn):
        """Mark a page as dirty (on write operation)."""
        pte = self.lookup(vpn)
        if pte:
            pte.mark_dirty()


# Self test
if __name__ == "__main__":
    pt = PageTable()
    pt.add(0x123, 5)
    pte = pt.lookup(0x123)
    print(f"LOOKUP 0x123: FRAME={pte.frame_num} VALID={pte.valid} DIRTY={pte.dirty}")
    pt.mark_dirty(0x123)
    print(f"AFTER DIRTY: FRAME={pte.frame_num} DIRTY={pte.dirty}")
    pt.remove(0x123)
    print(f"AFTER REMOVE: {pt.lookup(0x123)}")
    print("✅ PAGE TABLE READY")  