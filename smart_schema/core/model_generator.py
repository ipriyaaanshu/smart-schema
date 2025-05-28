"""
Model generator for smart_schema.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

import numpy as np
import pandas as pd
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, create_model

from ..utils.data_transformer import json_to_dataframe, normalize_datetime


def _convert_numpy_type(value: Any) -> Type:
    """
    Convert numpy types to Python types.

    Args:
        value: The value to convert

    Returns:
        The corresponding Python type
    """
    if isinstance(value, np.integer):
        return int
    elif isinstance(value, np.floating):
        return float
    elif isinstance(value, np.bool_):
        return bool
    elif isinstance(value, np.ndarray):
        if value.dtype.kind in "iuf":  # integer, unsigned integer, float
            return List[_convert_numpy_type(value[0])]
        return List[str]
    return type(value)


def _infer_schema_with_openai(
    data: Union[Dict[str, Any], pd.DataFrame],
    model_name: str,
    api_key: str,
    openai_model: str = "gpt-4o-mini",
) -> Dict[str, Dict[str, Any]]:
    """
    Infer schema using OpenAI's API.

    Args:
        data: The data to infer schema from (either a dictionary or DataFrame)
        model_name: Name of the model to generate
        api_key: OpenAI API key
        openai_model: OpenAI model to use for inference (default: "gpt-4o-mini")

    Returns:
        Dictionary containing the schema specification
    """
    # Convert DataFrame to dict if needed
    if isinstance(data, pd.DataFrame):
        data = data.to_dict(orient="records")[0]  # Get first row as example

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Prepare prompt for OpenAI
    prompt = f"""

            You are an expert Python developer.

            Given the following data sample, generate a JSON schema for Pydantic models using accurate Python data types.

            Model name: {model_name}

            For each field in the data:
            1. Identify the most appropriate Python type.
            2. Determine whether the field can be null or missing (use "is_nullable").
            3. Provide a concise and meaningful description.
            4. If the field is a nested object, generate a separate model and assign it a CamelCase model name. Use that model's name under the key "nested_model" for the corresponding field.

            Supported Python types:
            - str: strings, identifiers, free text
            - int: whole numbers
            - float: decimal values, measurements
            - bool: true/false values
            - datetime: ISO-format dates or timestamps
            - List[type]: for arrays
            - Dict[str, type]: for key-value maps

            Data example:
            {data}

            Output ONLY valid JSON in the following format — no explanations, comments, or markdown:

            {{
            "models": {{
                "main_model": {{
                    "name": "{model_name}",
                    "fields": {{
                        "field_name": {{
                            "type": "python_type",
                            "is_nullable": true_or_false,
                            "description": "field description",
                            "nested_model": "ModelName"  // optional; include only if field is a nested object
                        }}
                    }}
                }},
                "nested_models": {{
                    "ModelName": {{
                        "fields": {{
                            "field_name": {{
                                "type": "python_type",
                                "is_nullable": true_or_false,
                                "description": "field description"
                            }}
                        }}
                    }}
                }}
            }}
            }}
            """

    # Call OpenAI API
    response = client.chat.completions.create(
        model=openai_model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that generates accurate Pydantic model schemas. Always return valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    # Parse the response
    schema_str = response.choices[0].message.content
    try:
        schema = json.loads(schema_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse OpenAI response as JSON: {e}\nResponse: {schema_str}")

    # First pass: Create all nested models with placeholder types
    nested_models = {}
    for model_name, model_info in schema["models"]["nested_models"].items():
        fields = {}
        for field_name, field_info in model_info["fields"].items():
            if "nested_model" in field_info:
                # Use Any as a placeholder for now
                field_type = Any
            else:
                try:
                    field_type = eval(
                        field_info["type"],
                        {
                            "str": str,
                            "int": int,
                            "float": float,
                            "bool": bool,
                            "datetime": datetime,
                            "List": List,
                            "Dict": Dict,
                            "Optional": Optional,
                            "Any": Any,
                            "Union": Union,
                        },
                    )
                except NameError as e:
                    raise ValueError(
                        f"Invalid type '{field_info['type']}' for field '{field_name}': {e}"
                    )

            if field_info["is_nullable"]:
                field_type = Optional[field_type]
            fields[field_name] = (
                field_type,
                Field(description=field_info["description"]),
            )

        # Create nested model with configuration
        nested_models[model_name] = create_model(
            model_name,
            __config__=ConfigDict(arbitrary_types_allowed=True),
            **fields,
        )

    # Second pass: Update nested model references
    for model_name, model_info in schema["models"]["nested_models"].items():
        fields = {}
        for field_name, field_info in model_info["fields"].items():
            if "nested_model" in field_info:
                field_type = nested_models[field_info["nested_model"]]
            else:
                try:
                    field_type = eval(
                        field_info["type"],
                        {
                            "str": str,
                            "int": int,
                            "float": float,
                            "bool": bool,
                            "datetime": datetime,
                            "List": List,
                            "Dict": Dict,
                            "Optional": Optional,
                            "Any": Any,
                            "Union": Union,
                        },
                    )
                except NameError as e:
                    raise ValueError(
                        f"Invalid type '{field_info['type']}' for field '{field_name}': {e}"
                    )

            if field_info["is_nullable"]:
                field_type = Optional[field_type]
            fields[field_name] = (
                field_type,
                Field(description=field_info["description"]),
            )

        # Update nested model with correct types
        nested_models[model_name] = create_model(
            model_name,
            __config__=ConfigDict(arbitrary_types_allowed=True),
            **fields,
        )

    # Create main model
    main_model_info = schema["models"]["main_model"]
    fields = {}
    for field_name, field_info in main_model_info["fields"].items():
        if "nested_model" in field_info:
            field_type = nested_models[field_info["nested_model"]]
        else:
            try:
                field_type = eval(
                    field_info["type"],
                    {
                        "str": str,
                        "int": int,
                        "float": float,
                        "bool": bool,
                        "datetime": datetime,
                        "List": List,
                        "Dict": Dict,
                        "Optional": Optional,
                        "Any": Any,
                        "Union": Union,
                    },
                )
            except NameError as e:
                raise ValueError(
                    f"Invalid type '{field_info['type']}' for field '{field_name}': {e}"
                )

        if field_info["is_nullable"]:
            field_type = Optional[field_type]
        fields[field_name] = (
            field_type,
            Field(description=field_info["description"]),
        )

    # Create main model with configuration
    return create_model(
        main_model_info["name"],
        __config__=ConfigDict(arbitrary_types_allowed=True),
        **fields,
    )


class ModelGenerator:
    """Generator for Pydantic models from various data sources."""

    def __init__(
        self,
        name: str,
        smart_inference: bool = False,
        openai_model: str = "gpt-4o-mini",
    ):
        """
        Initialize the model generator.

        Args:
            name: The name of the model to generate
            smart_inference: Whether to use OpenAI for schema inference
            openai_model: OpenAI model to use for inference (default: "gpt-4o-mini")
        """
        self.name = name
        self.smart_inference = smart_inference
        self.openai_model = openai_model

    def _get_openai_api_key(self, api_key: Optional[str] = None) -> Optional[str]:
        """
        Get OpenAI API key from parameters or environment.

        Args:
            api_key: Optional API key passed to the method

        Returns:
            API key if available, None otherwise

        Raises:
            ValueError: If smart_inference is True but no API key is available
        """
        if not self.smart_inference:
            return None

        if api_key:
            return api_key

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return api_key

        raise ValueError(
            "OpenAI API key is required for smart inference. "
            "Either set OPENAI_API_KEY environment variable or pass api_key parameter."
        )

    def from_dataframe(
        self,
        df: pd.DataFrame,
        datetime_columns: Optional[List[str]] = None,
        api_key: Optional[str] = None,
        openai_model: Optional[str] = None,
    ) -> Type[BaseModel]:
        """
        Generate a Pydantic model from a pandas DataFrame.

        Args:
            df: The DataFrame to generate the model from
            datetime_columns: Optional list of column names containing datetime values
            api_key: Optional OpenAI API key for schema inference
            openai_model: Optional OpenAI model to use for inference

        Returns:
            A Pydantic model class
        """
        # Use OpenAI for schema inference if enabled
        if self.smart_inference:
            api_key = self._get_openai_api_key(api_key)
            if api_key:
                # _infer_schema_with_openai now returns the Pydantic model directly
                return _infer_schema_with_openai(
                    df, self.name, api_key, openai_model or self.openai_model
                )

        # Generate field definitions
        fields = {}
        for column in df.columns:
            # Get the first non-null value to determine type
            sample = df[column].dropna().iloc[0] if not df[column].empty else None

            if sample is None:
                # Default to string if no sample available
                fields[column] = (str, ...)
            elif pd.api.types.is_datetime64_any_dtype(df[column]):
                # Handle datetime fields properly
                fields[column] = (
                    datetime,
                    Field(description=f"Datetime field for {column}"),
                )
            elif isinstance(sample, (np.integer, np.floating, np.bool_, np.ndarray)):
                # Convert numpy types to Python types
                python_type = _convert_numpy_type(sample)
                fields[column] = (python_type, ...)
            elif isinstance(sample, (int, float)):
                fields[column] = (type(sample), ...)
            elif isinstance(sample, bool):
                fields[column] = (bool, ...)
            elif isinstance(sample, list):
                # For lists, use the type of the first element
                if sample and isinstance(sample[0], (int, float, np.integer, np.floating)):
                    element_type = _convert_numpy_type(sample[0])
                    fields[column] = (List[element_type], ...)
                else:
                    fields[column] = (List[str], ...)
            elif isinstance(sample, dict):
                fields[column] = (Dict[str, Any], ...)
            else:
                fields[column] = (str, ...)

        # Create model with configuration
        model_config = ConfigDict(arbitrary_types_allowed=True)
        return create_model(self.name, __config__=model_config, **fields)

    def from_json(
        self,
        data: Dict[str, Any],
        datetime_columns: Optional[List[str]] = None,
        api_key: Optional[str] = None,
        openai_model: Optional[str] = None,
    ) -> Type[BaseModel]:
        """
        Generate a Pydantic model from JSON data.

        Args:
            data: The JSON data to generate the model from
            datetime_columns: Optional list of column names containing datetime values
            api_key: Optional OpenAI API key for schema inference
            openai_model: Optional OpenAI model to use for inference

        Returns:
            A Pydantic model class
        """
        # Use OpenAI for schema inference if enabled
        if self.smart_inference:
            api_key = self._get_openai_api_key(api_key)
            if api_key:
                return _infer_schema_with_openai(
                    data, self.name, api_key, openai_model or self.openai_model
                )

        # Store all models for reference
        models = {}

        def process_value(value: Any, field_name: str) -> Type:
            """Process a value to determine its type."""
            if isinstance(value, dict):
                # Create a nested model for dictionaries
                nested_fields = {}
                for k, v in value.items():
                    nested_fields[k] = (process_value(v, k), ...)

                # Create a clean model name
                model_name = "".join(word.capitalize() for word in field_name.split("_"))
                if model_name not in models:
                    models[model_name] = create_model(
                        model_name,
                        __config__=ConfigDict(arbitrary_types_allowed=True),
                        **nested_fields,
                    )
                return models[model_name]

            elif isinstance(value, list):
                # Handle lists
                if value and isinstance(value[0], dict):
                    # List of objects - create a nested model
                    nested_fields = {}
                    for k, v in value[0].items():
                        nested_fields[k] = (process_value(v, k), ...)

                    # Create a clean model name for list items
                    model_name = (
                        "".join(word.capitalize() for word in field_name.split("_")) + "Item"
                    )
                    if model_name not in models:
                        models[model_name] = create_model(
                            model_name,
                            __config__=ConfigDict(arbitrary_types_allowed=True),
                            **nested_fields,
                        )
                    return List[models[model_name]]
                elif value:
                    # List of primitive types
                    return List[type(value[0])]
                return List[Any]
            elif isinstance(value, (int, float, str, bool)):
                return type(value)
            return Any

        # Process each field
        fields = {}
        for field_name, value in data.items():
            fields[field_name] = (process_value(value, field_name), ...)

        # Create main model
        main_model_name = "".join(word.capitalize() for word in self.name.split("_"))
        models[main_model_name] = create_model(
            main_model_name,
            __config__=ConfigDict(arbitrary_types_allowed=True),
            **fields,
        )

        return models[main_model_name]

    def from_description(
        self,
        fields: List[Dict[str, Any]],
        api_key: Optional[str] = None,
        openai_model: Optional[str] = None,
    ) -> Type[BaseModel]:
        """
        Generate a Pydantic model from a list of field descriptions.

        Args:
            fields: List of dictionaries containing field descriptions. Each dictionary should have:
                   - name: Field name
                   - description: Field description
                   - nullable: Whether the field can be null (optional)
            api_key: Optional OpenAI API key for schema inference
            openai_model: Optional OpenAI model to use for inference

        Returns:
            A Pydantic model class
        """
        api_key = self._get_openai_api_key(api_key)
        if not api_key:
            raise ValueError("OpenAI API key is required for schema inference from descriptions")

        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        # Prepare prompt for OpenAI
        prompt = f"""
                    You are a Python expert generating Pydantic model schemas.

                    Given the following field descriptions, generate a Pydantic-compatible JSON schema. Use the model name: {self.name}.

                    For each field:
                    1. Infer the most appropriate Python type using the field name and description.
                    2. Set "is_nullable" to true if the field can be null or missing.
                    3. Include the original field description.

                    Important type inference rules:
                    - Fields with 'id' in the name should be str type, not int
                    - Nested objects should be Dict[str, Any]
                    - Lists of objects should be List[Dict[str, Any]]
                    - Lists of primitive types (strings, numbers, etc.) should be List[type]
                    - Address fields should be Dict[str, Any]
                    - Price fields should be float
                    - Boolean fields should start with 'is_' or 'has_'

                    Use only these Python types:
                    - str: for names, identifiers, descriptions, and general text
                    - int: for counts or whole numbers
                    - float: for decimal values or measurements
                    - bool: for true/false values
                    - datetime: for dates and times
                    - List[str]: for lists of strings
                    - List[int]: for lists of integers
                    - List[float]: for lists of floats
                    - List[Dict[str, Any]]: for lists of objects
                    - Dict[str, Any]: for nested objects

                    Field descriptions:
                    {json.dumps(fields, indent=2)}

                    Output JSON ONLY in the following structure (no explanations, markdown, or text outside this JSON):

                    {{
                    "models": {{
                        "main_model": {{
                            "name": "{self.name}",
                            "fields": {{
                                "field_name": {{
                                    "type": "python_type",
                                    "is_nullable": true_or_false,
                                    "description": "field description"
                                }}
                            }}
                        }}
                    }}
                    }}
                    """

        # Call OpenAI API
        response = client.chat.completions.create(
            model=openai_model or self.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that generates accurate Pydantic model schemas. Always return valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        # Parse the response
        schema_str = response.choices[0].message.content
        try:
            schema = json.loads(schema_str)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse OpenAI response as JSON: {e}\nResponse: {schema_str}"
            )

        # Create model fields
        fields = {}
        type_globals = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "datetime": datetime,
            "List": List,
            "Dict": Dict,
            "Optional": Optional,
            "Any": Any,
            "Union": Union,
        }

        for field_name, field_info in schema["models"]["main_model"]["fields"].items():
            try:
                field_type = eval(field_info["type"], type_globals)
                if field_info["is_nullable"]:
                    field_type = Optional[field_type]
                fields[field_name] = (
                    field_type,
                    Field(description=field_info["description"]),
                )
            except NameError as e:
                raise ValueError(
                    f"Invalid type '{field_info['type']}' for field '{field_name}': {e}"
                )

        # Create model with configuration
        return create_model(
            self.name,
            __config__=ConfigDict(arbitrary_types_allowed=True),
            **fields,
        )
