"""Pagination shared by every list endpoint."""

from pydantic import BaseModel

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


class PageRequest(BaseModel):
    limit: int = DEFAULT_LIMIT
    offset: int = 0

    def clamp(self) -> "PageRequest":
        return PageRequest(limit=max(1, min(self.limit, MAX_LIMIT)), offset=max(0, self.offset))


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int

    @classmethod
    def of(cls, items: list[T], request: PageRequest) -> "Page[T]":
        """Slices an already-filtered list (used where filtering happens in memory)."""
        r = request.clamp()
        return cls(
            items=items[r.offset : r.offset + r.limit],
            total=len(items),
            limit=r.limit,
            offset=r.offset,
        )
