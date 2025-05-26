"""
Data validation functionality for Smart Schema.
"""

from typing import Any, Dict, List, Tuple, Type

import pandas as pd
from pydantic import BaseModel, ValidationError


class ModelValidator:
    """Handles validation of data against Pydantic models."""

    def __init__(self, model: Type[BaseModel]):
        """Initialize the validator with a Pydantic model.

        Args:
            model: The Pydantic model class to validate against.
        """
        self.model = model

    def validate_dataframe(
        self, df: pd.DataFrame
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Validate a DataFrame against the model.

        Args:
            df: The DataFrame to validate.

        Returns:
            A tuple containing (valid_records, invalid_records).
        """
        valid_records = []
        invalid_records = []

        for _, row in df.iterrows():
            try:
                # Convert row to dict and validate
                record = row.to_dict()
                validated = self.model(**record)
                valid_records.append(validated.model_dump())
            except ValidationError as e:
                invalid_records.append({"record": record, "errors": e.errors()})

        return valid_records, invalid_records

    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """Validate a single record against the model.

        Args:
            record: The record to validate.

        Returns:
            A tuple containing (is_valid, errors).
        """
        try:
            self.model(**record)
            return True, []
        except ValidationError as e:
            return False, e.errors()
