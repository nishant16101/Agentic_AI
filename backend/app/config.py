from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # Project Settings
    PROJECT_NAME: str = "Agentic Google Workspace"
    PROJECT_VERSION: str = "0.1.0"
    SECRET_KEY: str = ""
    API_V1_STR: str = "/api/v1"
    FRONTEND_URL: str = "http://localhost:5173"

    # LLM Settings
    LLM_PROVIDER: str = "openai" 
    OPENAI_API_KEY: str  # No default - must come from .env
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o" 
    
    # Google OAuth Settings
    GOOGLE_CLIENT_ID: str  # No default - must come from .env
    GOOGLE_CLIENT_SECRET: str  # No default - must come from .env
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/callback"
    GOOGLE_SCOPES: list[str] = [
        "openid",
        # CHANGED: Use full URL for basic scopes to avoid mismatch error
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        # END CHANGED
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/forms"
    ]
    CREDENTIALS_DIR: Path = BASE_DIR / "credentials"
    TOKEN_PATH: Path = CREDENTIALS_DIR / "token.json"

    # MCP Settings
    MCP_CONFIG_PATH: Path = BASE_DIR / "mcp_config" / "mcp_server_config.json"
    TOOL_DEFINITION_PATH: Path = BASE_DIR / "mcp_config" / "tool_definitions.json"
    MCP_PROTOCOL_VERSION: str = "0.9.1"

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./agentic_workspace.db"

    # JWT Settings
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8',
        extra="ignore"
    )


settings = Settings()

# Ensure credentials directory exists
settings.CREDENTIALS_DIR.mkdir(exist_ok=True)