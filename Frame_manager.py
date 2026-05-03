class FrameManager:

    def __init__(self, num_frames):
        """
        Initialize frame manager with total number of physical frames.
        
        Args:
            num_frames: Total number of frames (from config.num_frames)
        """
        self.num_frames = num_frames
        # List of free frame numbers
        self.free_frames = list(range(num_frames))
        # Set of used frame numbers
        self.used_frames = set()

    def has_free_frames(self):
        """Return True if at least one free frame is available."""
        return len(self.free_frames) > 0

    def get_free_count(self):
        """Return number of free frames."""
        return len(self.free_frames)

    def get_used_count(self):
        """Return number of used frames."""
        return len(self.used_frames)

    def allocate_frame(self):
        """
        Allocate a free frame.
        
        Returns:
            frame number (int)
            
        Raises:
            Exception: If no free frames available (caller should check has_free_frames first)
        """
        if not self.free_frames:
            raise Exception("NO FREE FRAMES AVAILABLE! NEED EVICTION.")

        # Take the first free frame
        frame = self.free_frames.pop(0)
        self.used_frames.add(frame)
        return frame

    def free_frame(self, frame):
        """
        Free a used frame (return it to free pool).
        
        Args:
            frame: Frame number to free
            
        Returns:
            True if frame was freed, False if frame wasn't in used set
        """
        if frame in self.used_frames:
            self.used_frames.remove(frame)
            self.free_frames.append(frame)
            return True
        return False

    def is_frame_free(self, frame):
        """Check if a specific frame is free."""
        return frame in self.free_frames

    def is_frame_used(self, frame):
        """Check if a specific frame is used."""
        return frame in self.used_frames

    def print_status(self):
        """Print current frame manager status (for debugging)."""
        print(f"\n--- FRAME MANAGER STATUS ---")
        print(f"TOTAL FRAMES:   {self.num_frames}")
        print(f"FREE FRAMES:    {self.get_free_count()} {self.free_frames}")
        print(f"USED FRAMES:    {self.get_used_count()} {sorted(self.used_frames)}")
        print(f"----------------------------")


# TEST THE MODULE WHEN RUN DIRECTLY
if __name__ == "__main__":
    print("=" * 50)
    print("TESTING FRAME MANAGER")
    print("=" * 50)

    # CREATE FRAME MANAGER WITH 16 FRAMES (from config.num_frames)
    # In real usage, num_frames comes from config.num_frames = 16
    fm = FrameManager(16)

    print("\n--- INITIAL STATE ---")
    fm.print_status()

    print("\n--- ALLOCATING 5 FRAMES ---")
    for i in range(5):
        frame = fm.allocate_frame()
        print(f"ALLOCATED FRAME: {frame}")

    fm.print_status()

    print("\n--- FREEING FRAME 2 ---")
    fm.free_frame(2)
    fm.print_status()

    print("\n--- ALLOCATING ANOTHER FRAME ---")
    frame = fm.allocate_frame()
    print(f"ALLOCATED FRAME: {frame}")
    fm.print_status()

    print("\n--- CHECKING SPECIFIC FRAMES ---")
    print(f"IS FRAME 0 FREE? {fm.is_frame_free(0)}")
    print(f"IS FRAME 0 USED? {fm.is_frame_used(0)}")
    print(f"IS FRAME 2 FREE? {fm.is_frame_free(2)}")
    print(f"IS FRAME 15 FREE? {fm.is_frame_free(15)}")

    print("\n--- HAS FREE FRAMES? ---")
    print(f"FREE FRAMES AVAILABLE: {fm.has_free_frames()}")
    print(f"FREE COUNT: {fm.get_free_count()}")
    print(f"USED COUNT: {fm.get_used_count()}")

    print("\n" + "=" * 50)
    print("✅ FRAME MANAGER WORKS!")
    print("=" * 50)