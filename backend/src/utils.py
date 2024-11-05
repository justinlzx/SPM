from typing import List

from pydantic import BaseModel
from sqlalchemy.ext.declarative import DeclarativeMeta


def convert_model_to_pydantic_schema(model_data: List[DeclarativeMeta], schema: BaseModel):
    # Check if the model has a method to convert to dict (common in SQLAlchemy models)
    return [
        schema.model_validate(model.__dict__ if hasattr(model, "__dict__") else model)
        for model in model_data
    ]
