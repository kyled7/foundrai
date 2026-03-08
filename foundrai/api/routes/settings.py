"""API key management endpoints for desktop mode."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["settings"])
logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
}


def _env_path() -> Path:
    """Return the path to the desktop .env file."""
    return Path.home() / ".foundrai" / ".env"


def _read_env() -> dict[str, str]:
    """Read key=value pairs from the .env file."""
    path = _env_path()
    if not path.exists():
        return {}
    pairs: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            pairs[key.strip()] = value.strip()
    return pairs


def _write_env(pairs: dict[str, str]) -> None:
    """Write key=value pairs to the .env file."""
    path = _env_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{k}={v}" for k, v in sorted(pairs.items())]
    path.write_text("\n".join(lines) + "\n")


class KeyStatus(BaseModel):
    provider: str
    env_var: str
    configured: bool


class KeysResponse(BaseModel):
    keys: list[KeyStatus]


class SetKeyRequest(BaseModel):
    provider: str
    api_key: str


class ValidateResponse(BaseModel):
    provider: str
    valid: bool
    error: str | None = None


@router.get("/settings/keys", response_model=KeysResponse)
async def list_keys() -> KeysResponse:
    """List configured API key providers (values are never returned)."""
    env = _read_env()
    keys = []
    for provider, env_var in SUPPORTED_PROVIDERS.items():
        configured = bool(env.get(env_var) or os.environ.get(env_var))
        keys.append(KeyStatus(provider=provider, env_var=env_var, configured=configured))
    return KeysResponse(keys=keys)


@router.post("/settings/keys", response_model=KeyStatus)
async def set_key(req: SetKeyRequest) -> KeyStatus:
    """Save an API key for a provider."""
    if req.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {req.provider}. "
            f"Supported: {list(SUPPORTED_PROVIDERS.keys())}",
        )

    env_var = SUPPORTED_PROVIDERS[req.provider]

    # Persist to .env
    env = _read_env()
    env[env_var] = req.api_key
    _write_env(env)

    # Set in current process so LiteLLM picks it up immediately
    os.environ[env_var] = req.api_key

    logger.info("API key set for provider: %s", req.provider)
    return KeyStatus(provider=req.provider, env_var=env_var, configured=True)


@router.delete("/settings/keys/{provider}", response_model=KeyStatus)
async def delete_key(provider: str) -> KeyStatus:
    """Remove an API key for a provider."""
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    env_var = SUPPORTED_PROVIDERS[provider]

    # Remove from .env
    env = _read_env()
    env.pop(env_var, None)
    _write_env(env)

    # Remove from current process
    os.environ.pop(env_var, None)

    logger.info("API key removed for provider: %s", provider)
    return KeyStatus(provider=provider, env_var=env_var, configured=False)


@router.get("/settings/keys/validate", response_model=list[ValidateResponse])
async def validate_keys() -> list[ValidateResponse]:
    """Test configured API keys with a minimal LiteLLM call."""
    results = []
    for provider, env_var in SUPPORTED_PROVIDERS.items():
        key = os.environ.get(env_var)
        if not key:
            results.append(ValidateResponse(provider=provider, valid=False, error="Not configured"))
            continue
        try:
            import litellm

            model_map = {
                "anthropic": "anthropic/claude-haiku-4-5-20251001",
                "openai": "gpt-4o-mini",
                "google": "gemini/gemini-2.0-flash",
            }
            model = model_map.get(provider, "gpt-4o-mini")
            await litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
            )
            results.append(ValidateResponse(provider=provider, valid=True))
        except Exception as e:
            results.append(ValidateResponse(provider=provider, valid=False, error=str(e)))
    return results
