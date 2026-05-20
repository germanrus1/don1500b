import time
from typing import Callable, Optional


class UnloadLogic:
    def __init__(self, config: dict):
        self._min_full_ms: float = config.get("min_full_duration_ms", 1000)
        self._min_empty_ms: float = config.get("min_empty_duration_ms", 500)

        self._full_since: Optional[float] = None
        self._empty_since: Optional[float] = None
        self._was_full_long_enough = False
        self._count = 0

        self.on_unload: Optional[Callable[[int], None]] = None

    def update(self, bin_full: bool) -> bool:
        now = time.monotonic()

        if bin_full:
            self._empty_since = None
            if self._full_since is None:
                self._full_since = now
            elif (now - self._full_since) * 1000 >= self._min_full_ms:
                self._was_full_long_enough = True
        else:
            self._full_since = None
            if self._was_full_long_enough:
                if self._empty_since is None:
                    self._empty_since = now
                elif (now - self._empty_since) * 1000 >= self._min_empty_ms:
                    self._count += 1
                    self._was_full_long_enough = False
                    self._empty_since = None
                    if self.on_unload:
                        self.on_unload(self._count)
                    return True
            else:
                self._empty_since = None

        return False

    @property
    def count(self) -> int:
        return self._count
