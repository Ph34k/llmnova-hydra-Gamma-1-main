
import pytest
import os
from pathlib import Path
from gamma_engine.tools.editor import StrReplaceEditorTool

@pytest.fixture
def editor_tool(tmp_path):
    return StrReplaceEditorTool(base_path=str(tmp_path))

def test_create_file(editor_tool, tmp_path):
    file_path = "test_file.txt"
    content = "Hello\nWorld"
    result = editor_tool.execute(command="create", path=file_path, file_text=content)

    assert "File created successfully" in result
    assert (tmp_path / file_path).read_text(encoding="utf-8") == content

def test_create_existing_file_fails(editor_tool):
    file_path = "existing.txt"
    editor_tool.execute("create", path=file_path, file_text="initial")
    result = editor_tool.execute("create", path=file_path, file_text="overwrite")
    assert "Error: File already exists" in result

def test_view_file(editor_tool):
    file_path = "view_test.txt"
    content = "Line 1\nLine 2\nLine 3"
    editor_tool.execute("create", path=file_path, file_text=content)

    result = editor_tool.execute("view", path=file_path)
    assert "Line 1" in result
    assert "Line 3" in result
    assert "1" in result # Line numbers

def test_view_range(editor_tool):
    file_path = "range.txt"
    content = "1\n2\n3\n4\n5"
    editor_tool.execute("create", path=file_path, file_text=content)

    result = editor_tool.execute("view", path=file_path, view_range=[2, 4])
    assert "2" in result
    assert "3" in result
    assert "1" not in result # Should be excluded/hidden in snippet if strictly followed, or just check content
    # The output format is `cat -n`, so we check for the line content

def test_str_replace(editor_tool, tmp_path):
    file_path = "replace.txt"
    content = "Hello World"
    editor_tool.execute("create", path=file_path, file_text=content)

    result = editor_tool.execute("str_replace", path=file_path, old_str="World", new_str="Gamma")
    assert "Successfully replaced" in result
    assert (tmp_path / file_path).read_text(encoding="utf-8") == "Hello Gamma"

def test_str_replace_not_unique(editor_tool):
    file_path = "dup.txt"
    content = "Hello\nHello"
    editor_tool.execute("create", path=file_path, file_text=content)

    result = editor_tool.execute("str_replace", path=file_path, old_str="Hello", new_str="Hi")
    assert "Multiple occurrences" in result

def test_insert(editor_tool, tmp_path):
    file_path = "insert.txt"
    content = "Line 1\nLine 3"
    editor_tool.execute("create", path=file_path, file_text=content)

    result = editor_tool.execute("insert", path=file_path, insert_line=1, new_str="Line 2")
    assert "Successfully inserted" in result
    expected = "Line 1\nLine 2\nLine 3"
    assert (tmp_path / file_path).read_text(encoding="utf-8") == expected

def test_undo_edit(editor_tool, tmp_path):
    file_path = "undo.txt"
    editor_tool.execute("create", path=file_path, file_text="Version 1")
    editor_tool.execute("str_replace", path=file_path, old_str="Version 1", new_str="Version 2")

    assert (tmp_path / file_path).read_text(encoding="utf-8") == "Version 2"

    result = editor_tool.execute("undo_edit", path=file_path)
    assert "Undo successful" in result
    assert (tmp_path / file_path).read_text(encoding="utf-8") == "Version 1"
