"""Tests for FileManager tool."""

import pytest

from foundrai.tools.file_manager import FileManager, FileManagerInput


@pytest.mark.asyncio
async def test_write_and_read(tmp_path):
    fm = FileManager(tmp_path)
    result = await fm.execute(FileManagerInput(action="write", path="hello.txt", content="world"))
    assert result.success

    result = await fm.execute(FileManagerInput(action="read", path="hello.txt"))
    assert result.success
    assert result.output == "world"


@pytest.mark.asyncio
async def test_path_traversal_blocked(tmp_path):
    fm = FileManager(tmp_path)
    result = await fm.execute(FileManagerInput(action="read", path="../../../etc/passwd"))
    assert not result.success
    assert "outside project" in result.error


@pytest.mark.asyncio
async def test_read_nonexistent(tmp_path):
    fm = FileManager(tmp_path)
    result = await fm.execute(FileManagerInput(action="read", path="missing.txt"))
    assert not result.success
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_list_directory(tmp_path):
    fm = FileManager(tmp_path)
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    (tmp_path / "subdir").mkdir()

    result = await fm.execute(FileManagerInput(action="list", path="."))
    assert result.success
    assert "a.txt" in result.output
    assert "b.txt" in result.output
    assert "subdir/" in result.output


@pytest.mark.asyncio
async def test_exists(tmp_path):
    fm = FileManager(tmp_path)
    (tmp_path / "exists.txt").write_text("yes")

    result = await fm.execute(FileManagerInput(action="exists", path="exists.txt"))
    assert result.success
    assert result.output == "True"

    result = await fm.execute(FileManagerInput(action="exists", path="nope.txt"))
    assert result.success
    assert result.output == "False"


@pytest.mark.asyncio
async def test_write_creates_dirs(tmp_path):
    fm = FileManager(tmp_path)
    result = await fm.execute(
        FileManagerInput(action="write", path="deep/nested/file.txt", content="data")
    )
    assert result.success
    assert (tmp_path / "deep" / "nested" / "file.txt").exists()
