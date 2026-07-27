"""
ai_service.py — AI Service with Pydantic v2 validation + YAML/JSON config support.

HOW TO USE:
    # Option 1: Load from a config file (.yaml or .json — auto-detected)
    service = AIService.from_file("config.yaml")
    service = AIService.from_file("config.json")

    # Option 2: Load from environment variables only (no file needed)
    service = AIService.from_env()

    # Option 3: Build config manually in code (useful for tests)
    config = AIConfig(llm=LLMConfig(api_key="sk-..."))
    service = AIService(config)

    # Call the service
    response = service.chat("What is the capital of France?")
    print(response.content)

    embed = service.embed("Paris is the capital of France.")
    print(embed.dimensions)

CONFIG PRIORITY (highest → lowest):
    1. Environment variable  (e.g. LLM_API_KEY)
    2. Config file value     (config.yaml or config.json)
    3. Built-in default      (the `default=` on each field)

DEPENDENCIES:
    pip install pydantic pyyaml langchain-openai
"""

# ── Standard library ──────────────────────────────────────────────────────────
import json
import logging
import os
from functools import cached_property
from pathlib import Path
from typing import Any, Optional

# ── Third-party ───────────────────────────────────────────────────────────────
import yaml
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator

# Module-level logger. Messages appear as: "2024-01-01 [INFO] ai_service: ..."
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — HELPER FUNCTION
#
# A plain function that reads a config file and returns its contents as a dict.
# Keeping it as a standalone function (not a method) makes it easy to test
# and reuse without needing any class instance.
# ══════════════════════════════════════════════════════════════════════════════

def _load_config_file(path: Path) -> dict[str, Any]:
    """
    Read a .yaml, .yml, or .json config file and return its contents as a dict.

    Args:
        path: A Path object pointing to the config file.

    Returns:
        A dictionary with the file contents (empty dict if file is blank).

    Raises:
        FileNotFoundError: If the file doesn't exist at the given path.
        ValueError: If the file extension is not .yaml, .yml, or .json.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: '{path}'\n"
            f"  → Create the file, or use AIService.from_env() to skip it."
        )

    suffix = path.suffix.lower()  # e.g. ".yaml", ".json"

    if suffix in (".yaml", ".yml"):
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}  # safe_load returns None on empty file

    if suffix == ".json":
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    raise ValueError(
        f"Unsupported config file format: '{suffix}'\n"
        f"  → Supported formats: .yaml, .yml, .json"
    )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — CONFIGURATION MODELS
#
# These Pydantic models define what valid configuration looks like.
# Pydantic will automatically:
#   - Check that values have the right types (e.g. temperature must be a float)
#   - Enforce constraints (e.g. temperature must be between 0.0 and 2.0)
#   - Give you clear error messages if something is wrong
#
# Each model has a `apply_env_overrides` validator that checks environment
# variables first. If an env var is set, it wins over the config file value.
# ══════════════════════════════════════════════════════════════════════════════

class LLMConfig(BaseModel):
    """
    Settings for the language model (ChatGPT-compatible endpoint).

    Environment variable overrides:
        LLM_BASE_URL, LLM_API_KEY, LLM_MODEL,
        LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_TIMEOUT
    """

    base_url: str = Field(
        default="https://llmservice.air.id",
        description="API endpoint URL for the LLM.",
    )
    # SecretStr is a special Pydantic type that hides the value in logs and repr.
    # To get the actual string, call: api_key.get_secret_value()
    api_key: SecretStr = Field(
        default="",
        description="API key. Use the LLM_API_KEY env var — don't hardcode this.",
    )
    model: str = Field(
        default="qwen2-32B-Instruct-resolved",
        description="Model name to use for completions.",
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,  # ge = greater-than-or-equal — Pydantic rejects values below 0.0
        le=2.0,  # le = less-than-or-equal    — Pydantic rejects values above 2.0
        description="Output randomness. 0.0 = focused/deterministic, 2.0 = very random.",
    )
    max_tokens: int = Field(
        default=2048,
        gt=0,  # gt = greater-than — must be at least 1
        description="Maximum tokens the model can return per response.",
    )
    timeout: int = Field(
        default=30,
        gt=0,
        description="Seconds before an API request times out.",
    )

    # `model_validator(mode="before")` runs BEFORE individual fields are validated.
    # This is where we apply environment variable overrides so that by the time
    # Pydantic checks types, the env var values are already in place.
    @model_validator(mode="before")
    @classmethod
    def apply_env_overrides(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Check each environment variable and override the matching field if set.

        The `env_map` dict maps field names → (env var name, type to cast to).
        To add a new override, just add a line here.
        """
        env_map = {
            "base_url":    ("LLM_BASE_URL",    str),
            "api_key":     ("LLM_API_KEY",      str),
            "model":       ("LLM_MODEL",        str),
            "temperature": ("LLM_TEMPERATURE",  float),
            "max_tokens":  ("LLM_MAX_TOKENS",   int),
            "timeout":     ("LLM_TIMEOUT",      int),
        }
        for field_name, (env_var, cast_type) in env_map.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                values[field_name] = cast_type(env_value)
        return values

    # `model_validator(mode="after")` runs AFTER all fields are set and validated.
    # Use this for checks that need to look at the final, fully-resolved values.
    @model_validator(mode="after")
    def check_api_key(self) -> "LLMConfig":
        """Reject placeholder or empty API keys."""
        raw_key = self.api_key.get_secret_value()
        placeholders = {"", "your-llm-api-key", "change-me", "YOUR_KEY_HERE"}
        if raw_key in placeholders:
            raise ValueError(
                "LLM API key is missing or is a placeholder.\n"
                "  → Set the LLM_API_KEY environment variable, or\n"
                "  → Set llm.api_key in your config file."
            )
        return self


# ─────────────────────────────────────────────────────────────────────────────

class EmbeddingConfig(BaseModel):
    """
    Settings for the text embedding model.

    Environment variable overrides:
        EMBEDDING_BASE_URL, EMBEDDING_API_KEY, EMBEDDING_MODEL, EMBEDDING_TIMEOUT
    """

    base_url: str = Field(
        default="",
        description="API endpoint URL for the embedding model.",
    )
    api_key: SecretStr = Field(
        default="",
        description="API key. Use the EMBEDDING_API_KEY env var — don't hardcode this.",
    )
    model: str = Field(
        default="Qwen3-Embedding-4B",
        description="Embedding model name.",
    )
    timeout: int = Field(
        default=30,
        gt=0,
        description="Seconds before an API request times out.",
    )

    @model_validator(mode="before")
    @classmethod
    def apply_env_overrides(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Check environment variables and override matching fields if set."""
        env_map = {
            "base_url": ("EMBEDDING_BASE_URL", str),
            "api_key":  ("EMBEDDING_API_KEY",  str),
            "model":    ("EMBEDDING_MODEL",    str),
            "timeout":  ("EMBEDDING_TIMEOUT",  int),
        }
        for field_name, (env_var, cast_type) in env_map.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                values[field_name] = cast_type(env_value)
        return values

    @model_validator(mode="after")
    def check_api_key(self) -> "EmbeddingConfig":
        """Reject placeholder or empty API keys."""
        raw_key = self.api_key.get_secret_value()
        placeholders = {"", "your-embedding-api-key", "change-me", "YOUR_KEY_HERE"}
        if raw_key in placeholders:
            raise ValueError(
                "Embedding API key is missing or is a placeholder.\n"
                "  → Set the EMBEDDING_API_KEY environment variable, or\n"
                "  → Set embedding.api_key in your config file."
            )
        return self


# ─────────────────────────────────────────────────────────────────────────────

# All accepted log level strings — used both for validation and the error message.
_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class ServiceConfig(BaseModel):
    """
    General behaviour flags for the AI service itself.

    Environment variable overrides:
        SERVICE_ENABLE_EMBEDDING, SERVICE_LOG_LEVEL
    """

    enable_embedding: bool = Field(
        default=True,
        description="Set to false to skip initialising the embedding client entirely.",
    )
    log_level: str = Field(
        default="INFO",
        description=f"Logging verbosity. One of: {', '.join(sorted(_VALID_LOG_LEVELS))}",
    )

    @model_validator(mode="before")
    @classmethod
    def apply_env_overrides(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Check environment variables and override matching fields if set."""
        if (v := os.getenv("SERVICE_ENABLE_EMBEDDING")) is not None:
            # Accept "true", "1", "yes" as True — anything else is False
            values["enable_embedding"] = v.lower() in ("1", "true", "yes")
        if (v := os.getenv("SERVICE_LOG_LEVEL")) is not None:
            values["log_level"] = v
        return values

    # `field_validator` targets a single named field (unlike `model_validator`).
    @field_validator("log_level")
    @classmethod
    def check_log_level(cls, value: str) -> str:
        """Normalise to uppercase and reject unknown log level strings."""
        upper = value.upper()
        if upper not in _VALID_LOG_LEVELS:
            raise ValueError(
                f"Invalid log_level '{value}'.\n"
                f"  → Must be one of: {', '.join(sorted(_VALID_LOG_LEVELS))}"
            )
        return upper  # store uppercase so logging.basicConfig accepts it


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — ROOT CONFIG (combines all three sub-configs above)
#
# This is the single object that represents the entire configuration.
# It holds LLMConfig, EmbeddingConfig, and ServiceConfig as nested fields.
# ══════════════════════════════════════════════════════════════════════════════

class AIConfig(BaseModel):
    """
    The top-level config object. Holds all sub-configs as nested fields.

    You usually don't create this directly — use one of the class methods:
        AIConfig.from_file("config.yaml")   # load from YAML or JSON
        AIConfig.from_env()                 # environment variables only
    """

    llm: LLMConfig = Field(
        default_factory=LLMConfig,  # create a fresh LLMConfig with defaults if not provided
        description="Language model settings.",
    )
    embedding: Optional[EmbeddingConfig] = Field(
        default=None,  # None means embedding is not configured
        description="Embedding model settings. Set to null/None to disable.",
    )
    service: ServiceConfig = Field(
        default_factory=ServiceConfig,
        description="Service-level flags (log level, feature toggles).",
    )

    # ── Class methods act as alternate constructors ───────────────────────────
    # Using `@classmethod` lets you call AIConfig.from_file(...) without
    # needing an existing instance first.

    @classmethod
    def from_file(cls, path: str | Path = "config.yaml") -> "AIConfig":
        """
        Load config from a YAML or JSON file.

        The format is detected automatically from the file extension:
            .yaml / .yml  →  parsed as YAML
            .json         →  parsed as JSON

        Args:
            path: Path to the config file. Defaults to "config.yaml".

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If validation fails (bad value, missing key, wrong type).
        """
        config_path = Path(path)
        raw = _load_config_file(config_path)           # returns a plain dict
        logger.debug("Loaded config from '%s': %s", config_path, raw)
        return cls.model_validate(raw)                 # Pydantic validates the dict

    @classmethod
    def from_env(cls) -> "AIConfig":
        """
        Build config from environment variables only — no file needed.

        Calls the default constructor, which triggers `apply_env_overrides`
        validators on each sub-config automatically.
        """
        return cls()

    def safe_summary(self) -> dict[str, Any]:
        """
        Return the full config as a plain dict with API keys replaced by "***".
        Safe to log or print without leaking secrets.

        Example:
            import json
            print(json.dumps(config.safe_summary(), indent=2))
        """
        return {
            "llm": {
                **self.llm.model_dump(exclude={"api_key"}),  # all fields except api_key
                "api_key": "***",
            },
            "embedding": (
                {**self.embedding.model_dump(exclude={"api_key"}), "api_key": "***"}
                if self.embedding else None
            ),
            "service": self.service.model_dump(),
        }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — RESPONSE MODELS
#
# Instead of returning raw strings or lists, each service method returns a
# typed Pydantic model. This means:
#   - You always know what fields are available (your editor can autocomplete)
#   - You can serialise to JSON easily with  response.model_dump()
#   - You can validate / pass responses between functions safely
# ══════════════════════════════════════════════════════════════════════════════

class ChatResponse(BaseModel):
    """
    Returned by AIService.chat().

    Fields:
        content       The text reply from the model.
        model         The model name that generated the reply.
        finish_reason Why the model stopped (e.g. "stop", "length"). May be None.
        usage         Token counts dict. May be None if the API doesn't return it.

    Example:
        response = service.chat("Hello!")
        print(response.content)            # "Hello! How can I help you?"
        print(response.usage)              # {"prompt_tokens": 5, "completion_tokens": 12, ...}
        print(response.model_dump())       # full dict — easy to log or store
    """

    content: str = Field(description="The text returned by the model.")
    model: str = Field(description="Model name that generated this response.")
    finish_reason: Optional[str] = Field(
        default=None,
        description="Why the model stopped. Common values: 'stop', 'length'.",
    )
    usage: Optional[dict[str, int]] = Field(
        default=None,
        description="Token usage: {'prompt_tokens': ..., 'completion_tokens': ..., 'total_tokens': ...}",
    )


class EmbedResponse(BaseModel):
    """
    Returned by AIService.embed().

    Fields:
        vector      The embedding as a list of floats.
        dimensions  Number of elements in the vector (same as len(vector)).
        model       The embedding model that produced this vector.

    Example:
        response = service.embed("Paris is the capital of France.")
        print(response.dimensions)     # e.g. 4096
        print(response.vector[:3])     # e.g. [0.023, -0.11, 0.004]
        print(response.model_dump())   # full dict
    """

    vector: list[float] = Field(description="The embedding vector.")
    dimensions: int = Field(description="Number of elements in the vector.")
    model: str = Field(description="Embedding model used.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — AI SERVICE
#
# The main class you interact with. It wraps LangChain's ChatOpenAI and
# OpenAIEmbeddings, using the config above to initialise them.
#
# The LLM and embedding clients are created lazily using @cached_property.
# "Lazy" means: they are only created the first time you actually call .chat()
# or .embed(), not when you create the AIService instance. After that, the same
# client object is reused every time (that's the "cached" part).
# ══════════════════════════════════════════════════════════════════════════════

class AIService:
    """
    High-level wrapper around LangChain's LLM and embedding clients.

    Create an instance with one of the class methods, then call .chat() or .embed().

    Examples:
        service = AIService.from_file("config.yaml")
        service = AIService.from_file("config.json")
        service = AIService.from_env()

        response = service.chat("Explain recursion simply.")
        print(response.content)

        embed = service.embed("some text")
        print(embed.dimensions)
    """

    def __init__(self, config: AIConfig) -> None:
        self.config = config
        # Configure the Python logging system as soon as we have a config.
        logging.basicConfig(
            level=config.service.log_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        logger.info("AIService ready. Config: %s", config.safe_summary())

    # ── Alternate constructors ────────────────────────────────────────────────

    @classmethod
    def from_file(cls, path: str | Path = "config.yaml") -> "AIService":
        """
        Create an AIService from a YAML or JSON config file.

        The format is auto-detected from the file extension (.yaml/.yml or .json).

        Args:
            path: Path to the config file. Defaults to "config.yaml".
        """
        config = AIConfig.from_file(path)
        return cls(config)

    @classmethod
    def from_env(cls) -> "AIService":
        """
        Create an AIService using only environment variables (no config file).

        Useful for Docker containers and CI pipelines where secrets are
        injected as environment variables.

        Required env vars:
            LLM_API_KEY
            EMBEDDING_API_KEY  (only needed if embedding is enabled)
        """
        config = AIConfig.from_env()
        return cls(config)

    # ── Internal: lazy client initialisation ─────────────────────────────────
    #
    # @cached_property works like @property, but the result is stored after
    # the first access. Every subsequent access returns the stored value
    # without running the function again.
    #
    # These are "private" by convention (prefixed with _). You don't call them
    # directly — use the public .chat() and .embed() methods instead.

    @cached_property
    def _llm(self) -> ChatOpenAI:
        """LangChain ChatOpenAI client — created once on first use."""
        cfg = self.config.llm
        logger.debug("Creating ChatOpenAI client (model=%s)", cfg.model)
        return ChatOpenAI(
            base_url=cfg.base_url,
            api_key=cfg.api_key.get_secret_value(),  # unwrap SecretStr to plain str
            model=cfg.model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            timeout=cfg.timeout,
        )

    @cached_property
    def _embedding_client(self) -> Optional[OpenAIEmbeddings]:
        """LangChain OpenAIEmbeddings client — created once on first use, or None if disabled."""
        # Short-circuit and return None if embedding is turned off or not configured.
        if not self.config.service.enable_embedding:
            logger.debug("Embedding disabled via service.enable_embedding=false.")
            return None
        if not self.config.embedding:
            logger.debug("No [embedding] section in config — client not created.")
            return None

        cfg = self.config.embedding
        logger.debug("Creating OpenAIEmbeddings client (model=%s)", cfg.model)
        return OpenAIEmbeddings(
            base_url=cfg.base_url,
            api_key=cfg.api_key.get_secret_value(),  # unwrap SecretStr to plain str
            model=cfg.model,
            timeout=cfg.timeout,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def chat(self, prompt: str) -> ChatResponse:
        """
        Send a text prompt to the LLM and get a structured response back.

        Args:
            prompt: The question or instruction to send to the model.

        Returns:
            ChatResponse with .content, .model, .finish_reason, .usage

        Raises:
            RuntimeError: If the API call fails for any reason.

        Example:
            response = service.chat("What is the capital of Indonesia?")
            print(response.content)   # "Jakarta"
        """
        logger.debug("chat() → prompt length=%d chars", len(prompt))
        try:
            raw = self._llm.invoke(prompt)
            return ChatResponse(
                content=raw.content,
                model=raw.response_metadata.get("model_name", self.config.llm.model),
                finish_reason=raw.response_metadata.get("finish_reason"),
                usage=raw.response_metadata.get("token_usage"),
            )
        except Exception as exc:
            logger.exception("chat() failed")
            raise RuntimeError(f"Chat request failed: {exc}") from exc

    def embed(self, text: str) -> EmbedResponse:
        """
        Generate an embedding vector for the given text.

        Args:
            text: The input text to convert into an embedding vector.

        Returns:
            EmbedResponse with .vector (list of floats), .dimensions, .model

        Raises:
            ValueError: If embedding is disabled or not configured.
            RuntimeError: If the API call fails.

        Example:
            response = service.embed("Hello world")
            print(response.dimensions)   # e.g. 4096
        """
        if self._embedding_client is None:
            raise ValueError(
                "Embedding is not available.\n"
                "  → Make sure service.enable_embedding is true in your config,\n"
                "  → and that the [embedding] section has a valid api_key."
            )
        logger.debug("embed() → text length=%d chars", len(text))
        try:
            vector = self._embedding_client.embed_query(text)
            return EmbedResponse(
                vector=vector,
                dimensions=len(vector),
                model=self.config.embedding.model,  # type: ignore[union-attr]
            )
        except Exception as exc:
            logger.exception("embed() failed")
            raise RuntimeError(f"Embedding request failed: {exc}") from exc

    def is_embedding_enabled(self) -> bool:
        """Return True if the embedding client is initialised and ready to use."""
        return self._embedding_client is not None