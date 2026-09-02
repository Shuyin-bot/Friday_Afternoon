"""Configuration for the IMAP email detection layer."""

from os import environ

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr


class EmailSettings(BaseModel):
    """Validated runtime settings used by the IMAP detector."""

    model_config = ConfigDict(frozen=True)

    imap_host: str = Field(min_length=1)
    imap_port: int = Field(default=993, gt=0, le=65535)
    imap_username: str = Field(min_length=1)
    imap_password: SecretStr
    mailbox: str = Field(default="INBOX", min_length=1)
    state_db_path: str = Field(default="data/email_state.db", min_length=1)
    data_dir: str = Field(default="data", min_length=1)
    ollama_base_url: str = Field(default="http://localhost:11434", min_length=1)
    ollama_model: str = Field(default="llama3.1:8b", min_length=1)

    @classmethod
    def from_env(cls) -> "EmailSettings":
        """Load `.env` if present and validate required environment variables."""
        load_dotenv()
        required = ("IMAP_HOST", "IMAP_USERNAME", "IMAP_PASSWORD")
        missing = [name for name in required if not environ.get(name)]
        if missing:
            names = ", ".join(missing)
            raise ValueError(f"Missing required environment variables: {names}")

        return cls(
            imap_host=environ["IMAP_HOST"],
            imap_port=int(environ.get("IMAP_PORT", "993")),
            imap_username=environ["IMAP_USERNAME"],
            imap_password=environ["IMAP_PASSWORD"],
            mailbox=environ.get("MAILBOX", "INBOX"),
            state_db_path=environ.get("STATE_DB_PATH", "data/email_state.db"),
            data_dir=environ.get("DATA_DIR", "data"),
            ollama_base_url=environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=environ.get("OLLAMA_MODEL", "llama3.1:8b"),
        )
