import os
import shutil
import unittest

from gamma_engine.tools.filesystem import ListFilesTool, ReadFileTool


class TestTools(unittest.TestCase):
    def setUp(self):
        # Setup workspace for testing
        self.workspace = os.path.abspath("workspace")
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

        # Create a dummy file for testing
        with open(os.path.join(self.workspace, "test_file.txt"), "w") as f:
            f.write("test content")

    def tearDown(self):
        # Clean up workspace after tests
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace)

    def test_list_files(self):
        tool = ListFilesTool()
        result = tool.execute(".")
        self.assertIn("test_file.txt", result)

    def test_read_file_error(self):
        tool = ReadFileTool()
        result = tool.execute("non_existent_file.txt")
        self.assertIn("Error", result)

if __name__ == '__main__':
    unittest.main()
