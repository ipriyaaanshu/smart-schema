"""
Generated Pydantic model.
"""

from builtins import bool
from builtins import int
from builtins import str
from pydantic import BaseModel, Field, validator
from typing import Union, Optional, Any, List, Dict
import math

class ApiKeys(BaseModel):
    payment_gateway: str = None
    geocoding_service: str = None

class ServerSettings(BaseModel):
    host: str = None
    port: int = None
    timeout_seconds: int = None

class FeatureFlags(BaseModel):
    new_dashboard: bool = None
    beta_user_access: bool = None
    enable_analytics: bool = None

class Logging(BaseModel):
    level: str = None
    format: str = None
    file_path: str = None

class ConnectionOptions(BaseModel):
    ssl_mode: str = None
    max_connections: int = None

class DatabaseConnection(BaseModel):
    type: str = None
    host: str = None
    port: int = None
    username: str = None
    password_env_var: str = None
    database_name: str = None
    connection_options: ConnectionOptions = None

class AppConfig(BaseModel):
    application_name: str = None
    version: str = None
    debug_mode: bool = None
    server_settings: ServerSettings = None
    database_connection: DatabaseConnection = None
    feature_flags: FeatureFlags = None
    logging: Logging = None
    api_keys: ApiKeys = None


    @validator('*', pre=True)
    def handle_nan(cls, v: Any) -> Any:
        if isinstance(v, float) and math.isnan(v):
            return None
        return v
