class FrameManager:

    def __init__(self, num_frames):
        self.num_frames = num_frames
        self.free_frames = list(range(num_frames))
        self.used_frames = set()

    def has_free_frames(self):
        return len(self.free_frames) > 0

    def get_free_count(self):
        return len(self.free_frames)

    def get_used_count(self):
        return len(self.used_frames)

    def allocate_frame(self):
        if not self.free_frames:
            raise Exception("NO FREE FRAMES AVAILABLE! NEED EVICTION.")

        frame = self.free_frames.pop(0)
        self.used_frames.add(frame)
        return frame

    def free_frame(self, frame):
        if frame in self.used_frames:
            self.used_frames.remove(frame)
            self.free_frames.append(frame)
            return True
        return False

    def is_frame_free(self, frame):
        return frame in self.free_frames

    def is_frame_used(self, frame):
        return frame in self.used_frames

    def print_status(self):
        print(f"\nFRAME MANAGER STATUS")
        print(f"TOTAL FRAMES:   {self.num_frames}")
        print(f"FREE FRAMES:    {self.get_free_count()} {self.free_frames}")
        print(f"USED FRAMES:    {self.get_used_count()} {sorted(self.used_frames)}")


if __name__ == "__main__":
    print("TESTING FRAME MANAGER")
    fm = FrameManager(16)

    print("\nINITIAL STATE")
    fm.print_status()

    print("\nALLOCATING 5 FRAMES")
    for i in range(5):
        frame = fm.allocate_frame()
        print(f"ALLOCATED FRAME: {frame}")

    fm.print_status()

    print("\nFREEING FRAME 2")
    fm.free_frame(2)
    fm.print_status()

    print("\nALLOCATING ANOTHER FRAME")
    frame = fm.allocate_frame()
    print(f"ALLOCATED FRAME: {frame}")
    fm.print_status()

    print("\nCHECKING SPECIFIC FRAMES")
    print(f"IS FRAME 0 FREE? {fm.is_frame_free(0)}")
    print(f"IS FRAME 0 USED? {fm.is_frame_used(0)}")
    print(f"IS FRAME 2 FREE? {fm.is_frame_free(2)}")
    print(f"IS FRAME 15 FREE? {fm.is_frame_free(15)}")

    print("\nHAS FREE FRAMES?")
    print(f"FREE FRAMES AVAILABLE: {fm.has_free_frames()}")
    print(f"FREE COUNT: {fm.get_free_count()}")
    print(f"USED COUNT: {fm.get_used_count()}")

    print("\nFRAME MANAGER WORKS!")