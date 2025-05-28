"""
Utilities for generating and working with Pydantic models.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin, get_type_hints

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, create_model, validator, ValidationError

from ..utils.dataframe_utils import (
    align_dataframe_with_model,
    load_dataframe_with_model,
    validate_dataframe_with_model,
)


def _infer_type_from_value(value: Any) -> Type:
    """
    Infer Python type from a value.
    Handles basic types, lists, and dictionaries.
    """
    if value is None:
        return Any
    elif isinstance(value, bool):
        return bool
    elif isinstance(value, int):
        return int
    elif isinstance(value, float):
        return float
    elif isinstance(value, str):
        return str
    elif isinstance(value, list):
        if not value:
            return List[Any]
        # Get the most specific common type
        item_types = {_infer_type_from_value(item) for item in value}
        if len(item_types) == 1:
            return List[item_types.pop()]
        return List[Any]
    elif isinstance(value, dict):
        return Dict[str, Any]
    return Any


def _generate_schema_from_dict(
    data: Dict[str, Any], field_name: str = ""
) -> Dict[str, Dict[str, Any]]:
    """
    Generate a schema dictionary from a nested dictionary.
    """
    schema = {}
    for key, value in data.items():
        field_info = {
            "type": _infer_type_from_value(value),
            "is_nullable": value is None,
            "description": f"Field {key} from {field_name}" if field_name else f"Field {key}",
        }

        # Handle nested dictionaries
        if isinstance(value, dict):
            nested_schema = _generate_schema_from_dict(
                value, f"{field_name}.{key}" if field_name else key
            )
            field_info["nested_schema"] = nested_schema
            # Create a nested model type
            nested_model_name = f"{key.title()}Model"
            field_info["type"] = create_model(
                nested_model_name,
                **{
                    k: (v["type"], None if v["is_nullable"] else ...)
                    for k, v in nested_schema.items()
                },
            )

        # Handle lists of dictionaries
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            # Create a model for the list items
            item_schema = _generate_schema_from_dict(
                value[0], f"{field_name}.{key}[0]" if field_name else f"{key}[0]"
            )
            item_model_name = f"{key.title()}ItemModel"
            item_model = create_model(
                item_model_name,
                **{
                    k: (v["type"], None if v["is_nullable"] else ...)
                    for k, v in item_schema.items()
                },
            )
            field_info["type"] = List[item_model]

        schema[key] = field_info

    return schema


def generate_schema_from_json(
    json_data: Union[str, Dict[str, Any]],
    model_name: str = "JsonModel",
    description: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Generate a Pydantic schema from JSON data.

    Args:
        json_data: JSON string or dictionary
        model_name: Base name for the model
        description: Optional description for the model

    Returns:
        Dictionary containing the schema specification
    """
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data

    if not isinstance(data, dict):
        raise ValueError("JSON data must be an object/dictionary")

    return _generate_schema_from_dict(data)


def generate_schema_from_dataframe(
    df: pd.DataFrame,
    model_name: str = "DataFrameModel",
    description: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Generate a Pydantic schema from a pandas DataFrame.

    Args:
        df: Input pandas DataFrame
        model_name: Base name for the model
        description: Optional description for the model

    Returns:
        Dictionary containing the schema specification
    """
    schema = {}

    for column in df.columns:
        # Get sample of non-null values
        sample = df[column].dropna().head(1)
        if len(sample) == 0:
            # If all values are null, use string type
            field_type = str
        else:
            value = sample.iloc[0]
            field_type = _infer_type_from_value(value)

        # Check if column contains any null values
        is_nullable = df[column].isna().any()

        # Get column statistics for description
        stats = {
            "total_rows": len(df),
            "null_count": df[column].isna().sum(),
        }

        # Only count unique values if the type is hashable
        try:
            stats["unique_count"] = df[column].nunique()
        except TypeError:
            # For unhashable types like lists, estimate unique count
            stats["unique_count"] = "N/A (unhashable type)"

        schema[column] = {
            "type": field_type,
            "is_nullable": is_nullable,
            "description": (
                f"Column {column} from DataFrame\n"
                f"Total rows: {stats['total_rows']}\n"
                f"Null values: {stats['null_count']}\n"
                f"Unique values: {stats['unique_count']}"
            ),
        }

    return schema


def generate_pydantic_model(
    fields: Dict[str, Dict[str, Any]],
    model_name: str = "DataModel",
    description: Optional[str] = None,
) -> Type[BaseModel]:
    """
    Generate a Pydantic model from a field specification.

    Args:
        fields: Dictionary mapping field names to their specifications
               Each specification should have:
               - type: Python type or string representation of type
               - is_nullable: bool indicating if field is optional
               - default: Optional default value
               - description: Optional field description
        model_name: Name for the generated model class
        description: Optional description for the model

    Returns:
        Generated Pydantic model class
    """
    model_fields = {}
    for field_name, info in fields.items():
        field_type = info["type"]
        if info["is_nullable"]:
            field_type = Optional[field_type]
            default = info.get("default", None)
        else:
            default = ...

        # Add field with description if provided
        if "description" in info:
            model_fields[field_name] = (
                field_type,
                Field(default=default, description=info["description"]),
            )
        else:
            model_fields[field_name] = (field_type, default)

    # Create the base model
    model = create_model(
        model_name,
        **model_fields,
        __doc__=description or f"Model with fields: {', '.join(fields.keys())}",
    )

    # Add nan validator
    @validator("*", pre=True)
    def handle_nan(cls, v: Any) -> Any:
        if isinstance(v, float) and math.isnan(v):
            return None
        return v

    # Add the validator to the model
    setattr(model, "handle_nan", classmethod(handle_nan))

    return model


def save_model_to_file(
    model: Type[BaseModel],
    output_path: str,
    model_name: str = "DataModel",
) -> None:
    """
    Save a Pydantic model to a Python file.

    Args:
        model: Pydantic model class to save
        output_path: Path where the model file should be saved
        model_name: Name to use for the model class in the file
    """
    output_path = Path(output_path)

    # Collect all nested models and their dependencies
    nested_models = {}
    model_dependencies = {}
    required_imports = {
        "from typing import Union, Optional, Any, List, Dict",
        "from pydantic import BaseModel, Field, validator",
        "import math"
    }

    def get_type_module_and_name(type_hint: Any) -> tuple[Optional[str], str]:
        """Helper to get module and name for a type hint, handling complex types."""
        origin = get_origin(type_hint)
        args = get_args(type_hint)

        if origin is Union:
            actual_args = [arg for arg in args if arg is not type(None)]
            if actual_args:
                return get_type_module_and_name(actual_args[0])
            return None, "Any"
        if origin in (List, list, Dict, dict):
            for arg in args:
                module, _ = get_type_module_and_name(arg)
                if module and module not in ['typing', '__builtin__']:
                    required_imports.add(f"from {module} import {arg.__name__ if hasattr(arg, '__name__') else arg}")
            return None, type_hint.__name__ if hasattr(type_hint, '__name__') else str(type_hint)
        
        module = getattr(type_hint, '__module__', None)
        name = getattr(type_hint, '__name__', str(type_hint))
        return module, name

    def collect_nested_models(model_type: Type[BaseModel], model_name_param: str) -> None:
        if model_name_param in nested_models:
            return

        nested_models[model_name_param] = model_type
        model_dependencies[model_name_param] = set()

        for field in model_type.model_fields.values():
            field_type_annotation = field.annotation
            
            module, type_name = get_type_module_and_name(field_type_annotation)
            if module and module not in ['typing', '__builtin__']:
                actual_type_to_import = type_name
                if '.' in type_name:
                     actual_type_to_import = type_name.split('.')[-1]
                
                is_nested_model = False
                if module == model_type.__module__ :
                    if hasattr(field_type_annotation, 'model_fields'):
                         is_nested_model = True
                
                if not is_nested_model:
                     required_imports.add(f"from {module} import {actual_type_to_import}")

            origin = get_origin(field_type_annotation)
            args = get_args(field_type_annotation)

            if origin is list and args and hasattr(args[0], 'model_fields'):
                item_type = args[0]
                item_name = item_type.__name__
                model_dependencies[model_name_param].add(item_name)
                collect_nested_models(item_type, item_name)
            elif hasattr(field_type_annotation, 'model_fields'):
                type_name = field_type_annotation.__name__
                model_dependencies[model_name_param].add(type_name)
                collect_nested_models(field_type_annotation, type_name)

    collect_nested_models(model, model_name)

    sorted_models = []
    visited = set()

    def visit(model_name_to_visit: str) -> None:
        if model_name_to_visit in visited:
            return
        visited.add(model_name_to_visit)
        for dep in model_dependencies.get(model_name_to_visit, set()):
            visit(dep)
        sorted_models.append(model_name_to_visit)

    for name_to_visit in nested_models:
        visit(name_to_visit)

    model_code = f'"""\nGenerated Pydantic model.\n"""\n\n'
    model_code += "\n".join(sorted(list(required_imports))) + "\n\n"

    # Add model definitions in dependency order
    for model_name in sorted_models:
        model_type = nested_models[model_name]
        if hasattr(model_type, "model_fields"):
            model_code += f"class {model_name}(BaseModel):\n"
            for field_name, field in model_type.model_fields.items():
                field_type = field.annotation
                if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
                    # Handle Optional types
                    types = [t.__name__ for t in field_type.__args__ if t is not type(None)]
                    if len(types) == 1:
                        field_type = f"Optional[{types[0]}]"
                    else:
                        field_type = f"Union[{', '.join(types)}]"
                elif hasattr(field_type, "__origin__") and field_type.__origin__ is list:
                    # Handle list types
                    item_type = field_type.__args__[0]
                    if hasattr(item_type, "__name__"):
                        field_type = f"List[{item_type.__name__}]"
                    else:
                        field_type = "List[Any]"
                else:
                    field_type = field_type.__name__

                # Get field description if it exists
                field_info = field.json_schema_extra or {}
                description = field_info.get("description", "")

                if description:
                    model_code += (
                        f'    {field_name}: {field_type} = Field(description="""{description}""")\n'
                    )
                elif field.default is None:
                    model_code += f"    {field_name}: {field_type} = None\n"
                else:
                    model_code += f"    {field_name}: {field_type}\n"
            model_code += "\n"

    # Add nan validator
    model_code += """
    @validator('*', pre=True)
    def handle_nan(cls, v: Any) -> Any:
        if isinstance(v, float) and math.isnan(v):
            return None
        return v
"""

    output_path.write_text(model_code)


def generate_model_from_schema(
    schema: Dict[str, Dict[str, Any]],
    model_name: str = "DataModel",
    output_file: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """
    Generate a Pydantic model from a schema and save it to a file.

    Args:
        schema: Dictionary mapping field names to their specifications
        model_name: Name for the generated model class
        output_file: Optional path where the model file should be saved
        description: Optional description for the model

    Returns:
        Path to the generated model file
    """
    model = generate_pydantic_model(schema, model_name, description)
    if not output_file:
        output_file = f"{model_name.lower()}_model.py"
    save_model_to_file(model, output_file, model_name)
    return output_file


def load_and_validate_json_as_model(
    file_path: Union[str, Path], model_class: Type[BaseModel]
) -> Optional[BaseModel]:
    """
    Load a JSON file, validate its content against a Pydantic model, and return an instance.

    Args:
        file_path: Path to the JSON file.
        model_class: The Pydantic model class to validate against and instantiate.

    Returns:
        An instance of model_class if loading and validation are successful, None otherwise.
        Prints error messages to the console on failure.
    """
    try:
        file_path = Path(file_path) # Ensure it's a Path object
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        
        # Validate and instantiate the model
        validated_model = model_class(**config_data)
        # print(f"Successfully loaded and validated {file_path} as {model_class.__name__}") # Optional: success message
        return validated_model
            
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in configuration file at {file_path}")
        return None
    except ValidationError as e: # Pydantic's ValidationError
        print(f"Error: Configuration validation failed for {file_path}")
        # print(e.errors()) # The notebook already prints this if desired
        # For a library function, printing all errors might be too verbose by default.
        # Consider returning errors or having a verbose flag if more detail is needed here.
        return None
    except Exception as e: # Catch any other unexpected errors during loading/instantiation
        print(f"An unexpected error occurred while processing {file_path}: {e}")
        return None
