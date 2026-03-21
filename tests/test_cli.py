"""Tests for CLI commands."""

from __future__ import annotations

from typer.testing import CliRunner

from foundrai.cli import _print_summary, app

runner = CliRunner()


class TestInitCommand:
    def test_creates_project(self, tmp_path):
        result = runner.invoke(app, ["init", "test-project", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / "test-project" / "foundrai.yaml").exists()
        assert (tmp_path / "test-project" / ".foundrai").is_dir()
        assert (tmp_path / "test-project" / ".foundrai" / "logs").is_dir()
        assert (tmp_path / "test-project" / ".foundrai" / "artifacts").is_dir()
        assert (tmp_path / "test-project" / ".env.example").exists()
        assert (tmp_path / "test-project" / ".gitignore").exists()

    def test_config_has_project_name(self, tmp_path):
        runner.invoke(app, ["init", "my-app", "--path", str(tmp_path)])
        content = (tmp_path / "my-app" / "foundrai.yaml").read_text()
        assert 'name: "my-app"' in content

    def test_does_not_overwrite_existing_config(self, tmp_path):
        proj = tmp_path / "existing"
        proj.mkdir()
        (proj / "foundrai.yaml").write_text("existing content")
        result = runner.invoke(app, ["init", "existing", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "already exists" in result.stdout
        assert (proj / "foundrai.yaml").read_text() == "existing content"

    def test_does_not_overwrite_existing_env(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / ".env.example").write_text("existing")
        result = runner.invoke(app, ["init", "proj", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert (proj / ".env.example").read_text() == "existing"

    def test_does_not_overwrite_existing_gitignore(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / ".gitignore").write_text("existing")
        result = runner.invoke(app, ["init", "proj", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert (proj / ".gitignore").read_text() == "existing"

    def test_shows_next_steps(self, tmp_path):
        result = runner.invoke(app, ["init", "myproj", "--path", str(tmp_path)])
        assert "Next steps" in result.stdout
        assert "sprint start" in result.stdout


class TestStatusCommand:
    def test_no_project(self, tmp_path):
        result = runner.invoke(app, ["status", "--project", str(tmp_path / "nonexistent")])
        assert result.exit_code == 1

    def test_no_sprints(self, tmp_path):
        # Create a project first
        runner.invoke(app, ["init", "proj", "--path", str(tmp_path)])
        result = runner.invoke(app, ["status", "--project", str(tmp_path / "proj")])
        assert result.exit_code == 0
        assert "No sprints found" in result.stdout


class TestLogsCommand:
    def test_no_project(self, tmp_path):
        result = runner.invoke(app, ["logs", "--project", str(tmp_path / "nonexistent")])
        assert result.exit_code == 1

    def test_no_events(self, tmp_path):
        runner.invoke(app, ["init", "proj", "--path", str(tmp_path)])
        result = runner.invoke(app, ["logs", "--project", str(tmp_path / "proj")])
        assert result.exit_code == 0
        assert "No events found" in result.stdout


class TestSprintStartCommand:
    def test_no_project(self, tmp_path):
        result = runner.invoke(
            app, ["sprint", "start", "Build something", "--project", str(tmp_path / "nonexistent")]
        )
        assert result.exit_code == 1


class TestPrintSummary:
    def test_completed_sprint(self, capsys):
        from foundrai.models.sprint import SprintMetrics

        state = {
            "status": "completed",
            "sprint_number": 1,
            "tasks": [],
            "artifacts": [],
            "metrics": SprintMetrics(
                total_tasks=3, completed_tasks=2, failed_tasks=1, total_tokens=500
            ),
        }
        _print_summary(state)
        captured = capsys.readouterr()
        assert "3 total" in captured.out
        assert "2 passed" in captured.out
        assert "1 failed" in captured.out

    def test_failed_sprint(self, capsys):
        from foundrai.models.sprint import SprintMetrics

        state = {
            "status": "failed",
            "sprint_number": 2,
            "tasks": [],
            "artifacts": [],
            "metrics": SprintMetrics(),
        }
        _print_summary(state)
        captured = capsys.readouterr()
        assert "FAILED" in captured.out

    def test_with_enum_status(self, capsys):
        from foundrai.models.enums import SprintStatus
        from foundrai.models.sprint import SprintMetrics

        state = {
            "status": SprintStatus.COMPLETED,
            "sprint_number": 1,
            "tasks": [],
            "artifacts": [],
            "metrics": SprintMetrics(total_tasks=1, completed_tasks=1),
        }
        _print_summary(state)
        captured = capsys.readouterr()
        assert "COMPLETED" in captured.out

    def test_without_metrics_model(self, capsys):
        """When metrics is not a SprintMetrics object."""
        state = {
            "status": "completed",
            "sprint_number": 1,
            "tasks": [],
            "artifacts": [],
            "metrics": "not a metrics object",
        }
        _print_summary(state)
        captured = capsys.readouterr()
        assert "0 total" in captured.out
