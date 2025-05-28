"""
Generated Pydantic model.
"""

import math
from builtins import bool, int, str
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class FeatureFlags(BaseModel):
    new_dashboard: bool
    beta_user_access: bool
    enable_analytics: bool


class Logging(BaseModel):
    level: str
    format: str
    file_path: str


class ApiKeys(BaseModel):
    payment_gateway: str
    geocoding_service: str


class ServerSettings(BaseModel):
    host: str
    port: int
    timeout_seconds: int


class ConnectionOptions(BaseModel):
    ssl_mode: str
    max_connections: int


class DatabaseConnection(BaseModel):
    type: str
    host: str
    port: int
    username: str
    password_env_var: str
    database_name: str
    connection_options: ConnectionOptions


class AppConfig(BaseModel):
    application_name: str
    version: str
    debug_mode: bool
    server_settings: ServerSettings
    database_connection: DatabaseConnection
    feature_flags: FeatureFlags
    logging: Logging
    api_keys: ApiKeys

    @validator("*", pre=True)
    def handle_nan(cls, v: Any) -> Any:
        if isinstance(v, float) and math.isnan(v):
            return None
        return v
