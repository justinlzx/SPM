from typing import Dict, List

from pydantic import BaseModel
from sqlalchemy.ext.declarative import DeclarativeMeta


# def convert_model_to_pydantic_schema(model_data: List[DeclarativeMeta], schema: BaseModel):
#     return [schema.model_validate(model) for model in model_data]


def convert_model_to_pydantic_schema(model_data: List[DeclarativeMeta], schema: BaseModel):
    # Check if the model has a method to convert to dict (common in SQLAlchemy models)
    return [
        schema.model_validate(model.__dict__ if hasattr(model, "__dict__") else model)
        for model in model_data
    ]


def fit_schema_to_model(
    schema_data: BaseModel,
    model_type: DeclarativeMeta,
    field_mapping: Dict[str, str] = None,
):
    """Transforms a Pydantic schema instance into a SQLAlchemy model instance.

    Args:
        schema_data (BaseModel): An instance of a Pydantic schema.
        model_type (DeclarativeMeta): The SQLAlchemy model class to transform the schema into.
        field_mapping (Dict[str, str], optional): A dictionary mapping schema field names to model
        field names. Defaults to None.

    Returns:
        model_type: An instance of the SQLAlchemy model populated with data from the schema.
    """
    if field_mapping is None:
        field_mapping = {}

    data_dict = schema_data.model_dump(by_alias=True)
    # Remove invalid fields
    valid_fields = {
        field_mapping.get(key, key): value
        for key, value in data_dict.items()
        if field_mapping.get(key, key) in model_type.__table__.columns
    }
    model_data = model_type(**valid_fields)
    return model_data


def fit_model_to_schema(
    model_data: DeclarativeMeta,
    schema_type: BaseModel,
    field_mapping: Dict[str, str] = None,
):
    """Transforms a SQLAlchemy model instance into a Pydantic schema instance.

    Args:
        model_data (DeclarativeMeta): An instance of a SQLAlchemy model.
        schema_type (BaseModel): The Pydantic schema class to transform the model into.
        field_mapping (Dict[str, str], optional): A dictionary mapping model field names to schema
        field names. Defaults to None.

    Returns:
        schema_type: An instance of the Pydantic schema populated with data from the model.
    """
    if field_mapping is None:
        field_mapping = {}

    # Remove invalid fields
    valid_fields = {
        field_mapping.get(key, key): value
        for key, value in model_data.items()
        if field_mapping.get(key, key) in schema_type.model_fields
    }

    schema_data = schema_type(**valid_fields)
    return schema_data
