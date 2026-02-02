from unittest.mock import MagicMock, patch

import pytest

from gamma_engine.tools.web_dev import WebDevelopmentTool


def test_web_dev_tool_items():
    tool = WebDevelopmentTool()
    assert tool.name == "web_development_tool"

def test_web_dev_tool_start_server():
    tool = WebDevelopmentTool()
    
    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None # Running
        mock_proc.pid = 1234
        mock_popen.return_value = mock_proc
        
        result = tool.execute("start", command="echo 'server'", port=8000)
        
        assert "started successfully" in result
        assert 8000 in tool.active_servers
        assert tool.active_servers[8000] == mock_proc

def test_web_dev_tool_double_start():
    tool = WebDevelopmentTool()
    
    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc
        
        tool.execute("start", command="cmd1", port=8000)
        result = tool.execute("start", command="cmd2", port=8000)
        
        assert "already registered" in result

def test_web_dev_tool_stop_server():
    tool = WebDevelopmentTool()
    
    # Mock a running server
    mock_proc = MagicMock()
    mock_proc.pid = 1234
    tool.active_servers[8000] = mock_proc
    
    with patch("psutil.Process") as mock_psutil_proc:
        mock_parent = MagicMock()
        mock_parent.children.return_value = []
        mock_psutil_proc.return_value = mock_parent
        
        result = tool.execute("stop", port=8000)
        
        assert "stopped" in result
        assert 8000 not in tool.active_servers
        mock_parent.kill.assert_called()

def test_web_dev_tool_check_server():
    tool = WebDevelopmentTool()
    
    # Mock requests.get
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        result = tool.execute("check", port=8000)
        assert "Responding (Status: 200)" in result
