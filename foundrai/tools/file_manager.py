"""File manager tool."""

from __future__ import annotations

from pathlib import Path

from foundrai.tools.base import BaseTool, ToolInput, ToolOutput


class FileManagerInput(ToolInput):
    """Input for file manager operations."""

    action: str
    path: str
    content: str | None = None


class FileManager(BaseTool):
    """Read, write, and list files within the project directory."""

    name = "file_manager"
    description = "Manage project files. Actions: read, write, list, exists."
    input_schema = FileManagerInput

    def __init__(self, project_path: Path | str) -> None:
        self.project_path = Path(project_path).resolve()

    async def execute(self, input: FileManagerInput) -> ToolOutput:  # type: ignore[override] # noqa: A002
        """Execute file operation."""
        target = (self.project_path / input.path).resolve()

        # Sandbox check
        if not str(target).startswith(str(self.project_path)):
            return ToolOutput(success=False, output="", error="Path outside project directory")

        match input.action:
            case "read":
                return await self._read(target)
            case "write":
                return await self._write(target, input.content or "")
            case "list":
                return await self._list(target)
            case "exists":
                return ToolOutput(success=True, output=str(target.exists()))
            case _:
                return ToolOutput(
                    success=False,
                    output="",
                    error=f"Unknown action: {input.action}",
                )

    async def _read(self, path: Path) -> ToolOutput:
        if not path.exists():
            return ToolOutput(
                success=False,
                output="",
                error=f"File not found: {path.name}",
            )
        content = path.read_text(encoding="utf-8")
        return ToolOutput(success=True, output=content)

    async def _write(self, path: Path, content: str) -> ToolOutput:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return ToolOutput(success=True, output=f"Written {len(content)} bytes to {path.name}")

    async def _list(self, path: Path) -> ToolOutput:
        if not path.exists():
            return ToolOutput(
                success=False,
                output="",
                error=f"Directory not found: {path.name}",
            )
        entries = sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir())
        return ToolOutput(success=True, output="\n".join(entries))
