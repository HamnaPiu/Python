from abc import ABC, abstractmethod

class ReplacementAlgorithm(ABC):
    @abstractmethod
    def update_usage(self, vpn):
        """Update internal state when a page is accessed."""
        pass

    @abstractmethod
    def get_victim(self) -> int:
        """Return the VPN of the page to evict."""
        pass
