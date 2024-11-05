import inspect
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class BaseClass:
    """Base class for dataclasses."""

    @classmethod
    def from_dict(cls, env):
        cls_signature = inspect.signature(cls)
        cls_parameters = cls_signature.parameters
        cls_type_hints = {k: v.annotation for k, v in cls_parameters.items()}

        parsed_env = {}
        for k, v in env.items():
            if k in cls_type_hints:
                if cls_type_hints[k] == datetime and isinstance(v, str):
                    try:
                        parsed_env[k] = datetime.fromisoformat(v)
                    except ValueError:
                        parsed_env[k] = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
                elif cls_type_hints[k] == date and isinstance(v, str):
                    try:
                        parsed_env[k] = date.fromisoformat(v)
                    except ValueError:
                        parsed_env[k] = datetime.strptime(v, "%Y-%m-%d %H:%M:%S").date()
                else:
                    parsed_env[k] = v

        return cls(**parsed_env)


@dataclass
class EmployeeFilters(BaseClass):
    department: Optional[str] = None
