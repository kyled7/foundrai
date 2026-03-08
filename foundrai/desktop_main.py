"""Desktop entry point for FoundrAI — no CLI dependencies.

Designed to be frozen with PyInstaller and spawned as a Tauri sidecar.
Prints PORT:{port} to stdout so the Tauri shell can discover the server address.
"""

from __future__ import annotations

import logging
import os
import platform
import socket
import sys
from pathlib import Path

import yaml


def _find_free_port(preferred: int = 8420) -> int:
    """Return *preferred* if available, otherwise pick a random free port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def _default_project_dir() -> Path:
    """Platform-appropriate default project directory."""
    if platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home()
    return base / "FoundrAI"


def _ensure_project(project_dir: Path) -> None:
    """Create project directory, default config, and data directory if missing."""
    project_dir.mkdir(parents=True, exist_ok=True)

    # Data directory for logs, artifacts, DB
    data_dir = project_dir / ".foundrai"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "logs").mkdir(exist_ok=True)

    # Default config
    config_path = project_dir / "foundrai.yaml"
    if not config_path.exists():
        default_config = {
            "project": {
                "name": "my-project",
                "description": "FoundrAI Desktop Project",
            },
            "server": {
                "host": "127.0.0.1",
                "port": 8420,
            },
        }
        config_path.write_text(yaml.dump(default_config, default_flow_style=False))


def _load_env(project_dir: Path) -> None:
    """Load .env from project directory if it exists."""
    env_path = project_dir / ".foundrai" / ".env"
    if not env_path.exists():
        env_path = project_dir / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path, override=True)
        except ImportError:
            # python-dotenv not available — read manually
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ[key.strip()] = value.strip()


def main() -> None:
    """Start the FoundrAI server in desktop mode."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("foundrai.desktop")

    project_dir = _default_project_dir()
    logger.info("Project directory: %s", project_dir)

    _ensure_project(project_dir)
    _load_env(project_dir)

    # Change to project directory so relative paths in config resolve correctly
    os.chdir(project_dir)

    port = _find_free_port()

    # Print port for Tauri sidecar to capture
    print(f"PORT:{port}", flush=True)

    from foundrai.config import FoundrAIConfig, ServerConfig

    config = FoundrAIConfig(
        server=ServerConfig(host="127.0.0.1", port=port),
        desktop_mode=True,
    )

    from foundrai.api.app import create_app

    app = create_app(config)

    import uvicorn

    logger.info("Starting FoundrAI desktop server on 127.0.0.1:%d", port)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    sys.exit(main() or 0)
