"""Type stubs for asyncinotify."""

from collections.abc import AsyncIterator
from enum import IntFlag
from pathlib import Path
from typing import Self

class Mask(IntFlag):
    CREATE = 0x100
    MOVED_TO = 0x80
    CLOSE_WRITE = 0x8

class Event:
    path: Path
    mask: Mask

class Inotify:
    def add_watch(self, path: str, mask: Mask) -> None: ...
    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None: ...
    def __aiter__(self) -> AsyncIterator[Event]: ...
    async def __anext__(self) -> Event: ...
