from typing import Any, Literal, Optional

from pydantic import Field

from .base import BaseSchema


class PaginationMeta(BaseSchema):
    total_count: int = Field(
        ...,
        title="Total number of items",
    )
    page_size: int = Field(
        ...,
        title="Page size",
    )
    page_num: int = Field(
        ...,
        title="Page number",
    )
    total_pages: int = Field(
        ...,
        title="Total number of pages",
    )


class JSendResponse(BaseSchema):
    status: Literal["success", "fail", "error"]
    data: Optional[Any]
    pagination_meta: Optional[PaginationMeta] = None
    message: Optional[str] = None
