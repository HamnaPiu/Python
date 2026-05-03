class PageTableEntry:
    def __init__(self, frame=-1, valid=0, dirty=0):
        self.frame = frame
        self.valid = valid
        self.dirty = dirty

    def __repr__(self):
        return f"PTE(frame={self.frame}, valid={self.valid}, dirty={self.dirty})"


class PageTable:
    def __init__(self):
        self.table = {}

    def add_entry(self, vpn, frame):
        self.table[vpn] = PageTableEntry(frame=frame, valid=1, dirty=0)

    def get_entry(self, vpn):
        return self.table.get(vpn)

    def get_frame(self, vpn):
        entry = self.table.get(vpn)
        if entry and entry.valid:
            return entry.frame
        return -1

    def is_valid(self, vpn):
        entry = self.table.get(vpn)
        return entry is not None and entry.valid == 1

    def mark_dirty(self, vpn):
        entry = self.table.get(vpn)
        if entry:
            entry.dirty = 1

    def is_dirty(self, vpn):
        entry = self.table.get(vpn)
        return entry is not None and entry.dirty == 1

    def invalidate(self, vpn):
        entry = self.table.get(vpn)
        if entry:
            entry.valid = 0
            entry.frame = -1

    def set_frame(self, vpn, frame):
        entry = self.table.get(vpn)
        if entry:
            entry.frame = frame
            entry.valid = 1
            entry.dirty = 0
        else:
            self.add_entry(vpn, frame)

    def contains(self, vpn):
        return vpn in self.table

    def print_table(self):
        print("\nPAGE TABLE CONTENTS")
        valid_entries = [(vpn, pte) for vpn, pte in self.table.items() if pte.valid == 1]
        if not valid_entries:
            print("(EMPTY)")
        else:
            print(f"{'VPN':<8} {'FRAME':<8} {'DIRTY':<8}")
            for vpn, pte in sorted(valid_entries):
                print(f"{vpn:<8} {pte.frame:<8} {pte.dirty:<8}")


if __name__ == "__main__":
    print("TESTING PAGE TABLE")

    pt = PageTable()
    pt.add_entry(1, 5)
    pt.add_entry(2, 3)
    print(f"get_entry(1): {pt.get_entry(1)}")
    print(f"get_frame(1): {pt.get_frame(1)}")
    print("PAGE TABLE READY")