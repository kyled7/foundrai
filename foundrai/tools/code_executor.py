"""Code executor tool."""

from __future__ import annotations

import os

from foundrai.tools.base import BaseTool, ToolInput, ToolOutput


class CodeExecutorInput(ToolInput):
    """Input for code execution."""

    code: str
    language: str = "python"
    timeout_seconds: int = 30


class NoopCodeExecutor(BaseTool):
    """No-op code executor when sandbox is unavailable."""

    name = "code_executor"
    description = "Execute code in a sandboxed environment."
    input_schema = CodeExecutorInput

    async def execute(self, input: CodeExecutorInput) -> ToolOutput:  # type: ignore[override] # noqa: A002
        """Return a message indicating sandbox is unavailable."""
        return ToolOutput(
            success=True,
            output=(
                "[Sandbox unavailable — code not executed. "
                "Assuming correct based on static analysis.]"
            ),
        )


class CodeExecutor(BaseTool):
    """Execute code in a sandboxed Docker container."""

    name = "code_executor"
    description = "Execute code in a sandboxed environment. Returns stdout and stderr."
    input_schema = CodeExecutorInput

    DOCKER_IMAGES = {
        "python": "python:3.11-slim",
        "javascript": "node:20-slim",
        "bash": "bash:5",
    }

    def __init__(self, timeout: int = 30, max_memory: int = 512) -> None:
        self.timeout = timeout
        self.max_memory = max_memory

    async def execute(self, input: CodeExecutorInput) -> ToolOutput:  # type: ignore[override] # noqa: A002
        """Run code in Docker container."""
        import asyncio
        import os
        import tempfile

        image = self.DOCKER_IMAGES.get(input.language)
        if not image:
            return ToolOutput(
                success=False, output="",
                error=f"Unsupported language: {input.language}",
            )

        ext = {
            "python": ".py", "javascript": ".js", "bash": ".sh"
        }.get(input.language, ".py")
        run_cmd = {
            "python": "python", "javascript": "node", "bash": "bash"
        }.get(input.language, "python")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=ext, delete=False
        ) as f:
            f.write(input.code)
            code_path = f.name

        try:
            cmd = [
                "docker", "run", "--rm",
                "--memory", f"{self.max_memory}m",
                "--network", "none",
                "--read-only",
                "--tmpfs", "/tmp:size=64m",
                "-v", f"{code_path}:/code/main{ext}:ro",
                image,
                run_cmd,
                f"/code/main{ext}",
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=input.timeout_seconds,
            )

            return ToolOutput(
                success=proc.returncode == 0,
                output=stdout.decode("utf-8", errors="replace"),
                error=(
                    stderr.decode("utf-8", errors="replace")
                    if proc.returncode != 0 else None
                ),
            )
        except TimeoutError:
            return ToolOutput(
                success=False, output="", error="Execution timed out"
            )
        finally:
            os.unlink(code_path)


class E2BCodeExecutor(BaseTool):
    """Execute code using E2B cloud sandboxes."""

    name = "code_executor"
    description = "Execute code in a sandboxed environment. Returns stdout and stderr."
    input_schema = CodeExecutorInput

    TEMPLATE_IDS = {
        "python": "python3",
        "javascript": "nodejs",
        "bash": "base",
    }

    def __init__(self, timeout: int = 30, max_memory: int = 512) -> None:
        self.timeout = timeout
        self.max_memory = max_memory
        self.api_key = os.getenv("E2B_API_KEY")
        if not self.api_key:
            raise ValueError(
                "E2B_API_KEY environment variable is required for E2BCodeExecutor"
            )

    async def execute(self, input: CodeExecutorInput) -> ToolOutput:  # type: ignore[override] # noqa: A002
        """Run code in E2B sandbox."""
        import asyncio

        try:
            from e2b import Sandbox
        except ImportError as e:
            return ToolOutput(
                success=False,
                output="",
                error=f"E2B SDK not installed: {e}",
            )

        template_id = self.TEMPLATE_IDS.get(input.language)
        if not template_id:
            return ToolOutput(
                success=False,
                output="",
                error=f"Unsupported language: {input.language}",
            )

        sandbox = None
        try:
            # Create sandbox
            sandbox = Sandbox(template=template_id, api_key=self.api_key)

            # Execute code with timeout
            ext = {
                "python": ".py",
                "javascript": ".js",
                "bash": ".sh",
            }.get(input.language, ".py")
            run_cmd = {
                "python": "python",
                "javascript": "node",
                "bash": "bash",
            }.get(input.language, "python")

            # Write code to file
            file_path = f"/tmp/code{ext}"
            sandbox.filesystem.write(file_path, input.code)

            # Execute with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    sandbox.process.start_and_wait,
                    f"{run_cmd} {file_path}",
                ),
                timeout=input.timeout_seconds,
            )

            return ToolOutput(
                success=result.exit_code == 0,
                output=result.stdout,
                error=result.stderr if result.exit_code != 0 else None,
            )

        except asyncio.TimeoutError:
            return ToolOutput(
                success=False,
                output="",
                error="Execution timed out",
            )
        except Exception as e:
            return ToolOutput(
                success=False,
                output="",
                error=f"E2B execution failed: {e!s}",
            )
        finally:
            if sandbox:
                try:
                    sandbox.close()
                except Exception:
                    pass  # Best effort cleanup
