"""
Comprehensive test suite for Phase 2 Manus-inspired tools.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from gamma_engine.tools.filesystem import DiffFilesTool
from gamma_engine.tools.map_tool import (CodeStatsTool, MapDependenciesTool,
                                         MapDirectoryTool)
from gamma_engine.tools.search_tool import CodeSearchTool, FileSearchTool
# Import all new tools
from gamma_engine.tools.shell_tool import InteractiveShellTool, ShellTool


class TestShellTool(unittest.TestCase):
    """Test suite for ShellTool"""
    
    def setUp(self):
        self.tool = ShellTool()
    
    def test_simple_command(self):
        """Test executing a simple command"""
        # Platform-specific test
        import platform
        if platform.system() == "Windows":
            result = self.tool.execute("echo Hello")
        else:
            result = self.tool.execute("echo 'Hello'")
        
        self.assertIn("Hello", result)
    
    def test_command_history(self):
        """Test that command history is tracked"""
        self.tool.execute("echo test")
        history = self.tool.get_history()
        
        self.assertEqual(len(history), 1)
        self.assertIn("echo", history[0]['command'])
    
    def test_timeout(self):
        """Test command timeout"""
        import platform
        if platform.system() == "Windows":
            # PowerShell sleep
            result = self.tool.execute("Start-Sleep -Seconds 5", timeout=1)
        else:
            # Bash sleep
            result = self.tool.execute("sleep 5", timeout=1)
        
        self.assertIn("timed out", result.lower())


class TestSearchTools(unittest.TestCase):
    """Test suite for Search tools"""
    
    def setUp(self):
        self.code_search = CodeSearchTool()
        self.file_search = FileSearchTool()
        
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp()
        
        # Create test files
        test_file = Path(self.test_dir) / "test.py"
        test_file.write_text("""
def hello_world():
    print("Hello, World!")

class TestClass:
    def test_method(self):
        pass
""")
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_code_search_plain_text(self):
        """Test plain text code search"""
        result = self.code_search.execute(
            pattern="hello_world",
            path=self.test_dir
        )
        
        self.assertIn("test.py", result)
        self.assertIn("hello_world", result)
    
    def test_code_search_regex(self):
        """Test regex code search"""
        result = self.code_search.execute(
            pattern=r"def\s+\w+",
            path=self.test_dir,
            use_regex=True
        )
        
        self.assertIn("def", result)
    
    def test_file_search(self):
        """Test file name search"""
        result = self.file_search.execute(
            pattern="*.py",
            path=self.test_dir
        )
        
        self.assertIn("test.py", result)


class TestMapTools(unittest.TestCase):
    """Test suite for Map/Visualization tools"""
    
    def setUp(self):
        self.map_tool = MapDirectoryTool()
        self.stats_tool = CodeStatsTool()
        self.deps_tool = MapDependenciesTool()
        
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp()
        
        # Create test structure
        (Path(self.test_dir) / "src").mkdir()
        (Path(self.test_dir) / "src" / "main.py").write_text("import os\nimport sys\n")
        (Path(self.test_dir) / "README.md").write_text("# Test Project\n")
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_map_directory(self):
        """Test directory tree generation"""
        result = self.map_tool.execute(path=self.test_dir, max_depth=2)
        
        self.assertIn("src/", result)
        self.assertIn("README.md", result)
    
    def test_code_stats(self):
        """Test code statistics generation"""
        result = self.stats_tool.execute(path=self.test_dir)
        
        self.assertIn("Total Files", result)
        self.assertIn("Total Lines", result)
    
    def test_map_dependencies(self):
        """Test dependency analysis"""
        py_file = Path(self.test_dir) / "src" / "main.py"
        result = self.deps_tool.execute(file_path=str(py_file))
        
        self.assertIn("os", result)
        self.assertIn("sys", result)


class TestDiffTool(unittest.TestCase):
    """Test suite for DiffFilesTool"""
    
    def setUp(self):
        self.tool = DiffFilesTool()
        
        # Setup workspace
        self.workspace = os.path.abspath("workspace")
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)
        
        # Create test files
        self.file1 = os.path.join(self.workspace, "file1.txt")
        self.file2 = os.path.join(self.workspace, "file2.txt")
        
        with open(self.file1, 'w') as f:
            f.write("Line 1\nLine 2\nLine 3\n")
        
        with open(self.file2, 'w') as f:
            f.write("Line 1\nLine 2 Modified\nLine 3\n")
    
    def tearDown(self):
        if os.path.exists(self.file1):
            os.remove(self.file1)
        if os.path.exists(self.file2):
            os.remove(self.file2)
    
    def test_diff_files(self):
        """Test file diff generation"""
        result = self.tool.execute("file1.txt", "file2.txt")
        
        self.assertIn("Line 2", result)
        self.assertIn("Modified", result)
    
    def test_identical_files(self):
        """Test diff of identical files"""
        # Make file2 identical to file1
        with open(self.file2, 'w') as f:
            f.write("Line 1\nLine 2\nLine 3\n")
        
        result = self.tool.execute("file1.txt", "file2.txt")
        
        self.assertIn("identical", result.lower())


class TestToolIntegration(unittest.TestCase):
    """Test tool integration and schemas"""
    
    def setUp(self):
        os.environ["OPENAI_API_KEY"] = "sk-test-mock-key"
        
    def test_all_tools_have_schemas(self):
        """Verify all tools have valid schemas"""
        from gamma_engine.tools import get_all_tools
        
        tools = get_all_tools()
        
        for tool in tools:
            schema = tool.to_schema()
            
            self.assertIn("type", schema)
            self.assertEqual(schema["type"], "function")
            self.assertIn("function", schema)
            self.assertIn("name", schema["function"])
            self.assertIn("description", schema["function"])
            self.assertIn("parameters", schema["function"])
    
    def test_get_tool_schemas(self):
        """Test get_tool_schemas helper function"""
        from gamma_engine.tools import get_tool_schemas
        
        schemas = get_tool_schemas()
        
        # Should have all tools
        self.assertGreater(len(schemas), 10)
        
        # All should be valid
        for schema in schemas:
            self.assertIn("type", schema)


class TestFileWatchTool(unittest.TestCase):
    """Test suite for FileWatchTool"""
    
    def setUp(self):
        from gamma_engine.tools.filesystem import FileWatchTool
        self.tool = FileWatchTool()
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def test_watch_directory(self):
        """Test directory watching"""
        import threading
        import time

        # Create a file in a separate thread after a delay
        def create_file():
            time.sleep(1)
            with open(os.path.join(self.test_dir, "new_file.txt"), 'w') as f:
                f.write("content")
                
        t = threading.Thread(target=create_file)
        t.start()
        
        # Watch should pick up the event
        # use shorter timeout for test
        result = self.tool.execute(path=self.test_dir, timeout=3)
        
        t.join()
        
        self.assertIn("created", result.lower())
        self.assertIn("new_file.txt", result)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
