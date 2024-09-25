from pydantic import BaseModel


class BaseSchema(BaseModel):
    class Config:
        from_attributes = (
            True  # Use this instead of orm_mode to support from_orm in Pydantic v2
        )
        populate_by_name = True  # Allow using the field name instead of the alias
