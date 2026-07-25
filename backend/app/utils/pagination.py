"""Pagination helpers for SQLAlchemy queries."""

import math
from typing import Generic, List, Optional, Tuple, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Generic page wrapper returned by ``paginate_query``."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


def paginate(
    total: int,
    page: int,
    page_size: int,
) -> Tuple[int, int, Page]:
    """Compute pagination metadata and SQL offsets.

    Args:
        total: Total number of items available.
        page: Current page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        A tuple of ``(offset, limit, Page)``.
    """
    total_pages = max(1, math.ceil(total / page_size))
    page = max(1, min(page, total_pages))
    offset = (page - 1) * page_size

    page_info = Page(
        items=[],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )

    return offset, page_size, page_info
