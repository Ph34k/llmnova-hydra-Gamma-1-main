
import pytest
import os
import shutil
from gamma_engine.tools.filesystem import ListFilesTool, ReadFileTool, WriteFileTool, DiffFilesTool, FileWatchTool

@pytest.fixture
def workspace(tmp_path):
    """Create a temporary workspace for file tests."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    return str(ws)

def test_list_files(workspace):
    tool = ListFilesTool(base_path=workspace)

    # Create files
    (os.path.join(workspace, "file1.txt"))
    with open(os.path.join(workspace, "file1.txt"), "w") as f:
        f.write("content")
    os.mkdir(os.path.join(workspace, "dir1"))

    result = tool.execute(".")
    assert "file1.txt" in result
    assert "dir1/" in result

def test_read_file(workspace):
    tool = ReadFileTool(base_path=workspace)
    path = os.path.join(workspace, "test.txt")
    with open(path, "w") as f:
        f.write("Hello World")

    content = tool.execute("test.txt")
    assert content == "Hello World"

def test_read_file_not_found(workspace):
    tool = ReadFileTool(base_path=workspace)
    result = tool.execute("non_existent.txt")
    assert "Error" in result

def test_write_file(workspace):
    tool = WriteFileTool(base_path=workspace)
    result = tool.execute("new_file.txt", "New Content")

    assert "Successfully" in result
    with open(os.path.join(workspace, "new_file.txt"), "r") as f:
        assert f.read() == "New Content"

def test_write_file_nested(workspace):
    tool = WriteFileTool(base_path=workspace)
    result = tool.execute("nested/dir/file.txt", "Nested")

    assert "Successfully" in result
    assert os.path.exists(os.path.join(workspace, "nested/dir/file.txt"))

def test_diff_files(workspace):
    tool = DiffFilesTool(base_path=workspace)

    with open(os.path.join(workspace, "f1.txt"), "w") as f:
        f.write("Line 1\nLine 2")
    with open(os.path.join(workspace, "f2.txt"), "w") as f:
        f.write("Line 1\nLine 3")

    diff = tool.execute("f1.txt", "f2.txt")
    assert "Line 2" in diff
    assert "Line 3" in diff
    assert "--- f1.txt" in diff

def test_security_traversal(workspace):
    tool = ReadFileTool(base_path=workspace)
    # Attempt to read outside workspace
    result = tool.execute("../../../etc/passwd")
    assert "Access denied" in result
