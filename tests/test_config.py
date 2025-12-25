"""Tests for the config module."""

import pytest
import tempfile
from pathlib import Path

from pro_mgr import config


class TestConfigLoading:
    """Tests for configuration loading."""
    
    def test_load_valid_config(self, tmp_path):
        """Test loading a valid config file."""
        config_content = """
[project]
name = "test-project"
version = "1.0.0"

[tasks.test]
command = "pytest"
description = "Run tests"

[tasks.build]
command = "python setup.py build"
depends_on = ["test"]
"""
        config_file = tmp_path / "pro-mgr.toml"
        config_file.write_text(config_content)
        
        cfg = config.load_config(str(tmp_path))
        
        assert cfg['project']['name'] == "test-project"
        assert 'test' in cfg['tasks']
        assert 'build' in cfg['tasks']
    
    def test_load_missing_config(self, tmp_path):
        """Test loading a missing config file raises error."""
        with pytest.raises(FileNotFoundError):
            config.load_config(str(tmp_path))
    
    def test_get_task(self, tmp_path):
        """Test getting a specific task."""
        config_content = """
[tasks.test]
command = "pytest"
description = "Run tests"
"""
        (tmp_path / "pro-mgr.toml").write_text(config_content)
        cfg = config.load_config(str(tmp_path))
        
        task = config.get_task(cfg, "test")
        assert task is not None
        assert task['command'] == "pytest"
    
    def test_get_nonexistent_task(self, tmp_path):
        """Test getting a task that doesn't exist."""
        config_content = "[tasks.test]\ncommand = 'pytest'"
        (tmp_path / "pro-mgr.toml").write_text(config_content)
        cfg = config.load_config(str(tmp_path))
        
        task = config.get_task(cfg, "nonexistent")
        assert task is None


class TestDependencyResolution:
    """Tests for task dependency resolution."""
    
    def test_resolve_simple_dependency(self, tmp_path):
        """Test resolving a simple dependency chain."""
        config_content = """
[tasks.install]
command = "pip install ."

[tasks.test]
command = "pytest"
depends_on = ["install"]
"""
        (tmp_path / "pro-mgr.toml").write_text(config_content)
        cfg = config.load_config(str(tmp_path))
        
        order = config.resolve_dependencies(cfg, "test")
        
        assert order == ["install", "test"]
    
    def test_resolve_complex_dependencies(self, tmp_path):
        """Test resolving complex dependency graph."""
        config_content = """
[tasks.install]
command = "pip install ."

[tasks.lint]
command = "flake8"

[tasks.test]
command = "pytest"
depends_on = ["install", "lint"]
"""
        (tmp_path / "pro-mgr.toml").write_text(config_content)
        cfg = config.load_config(str(tmp_path))
        
        order = config.resolve_dependencies(cfg, "test")
        
        # install and lint should come before test
        assert order.index("install") < order.index("test")
        assert order.index("lint") < order.index("test")
    
    def test_detect_cyclic_dependency(self, tmp_path):
        """Test detecting circular dependencies."""
        config_content = """
[tasks.a]
command = "echo a"
depends_on = ["b"]

[tasks.b]
command = "echo b"
depends_on = ["a"]
"""
        (tmp_path / "pro-mgr.toml").write_text(config_content)
        cfg = config.load_config(str(tmp_path))
        
        with pytest.raises(config.CyclicDependencyError):
            config.resolve_dependencies(cfg, "a")
    
    def test_task_not_found(self, tmp_path):
        """Test error when task doesn't exist."""
        config_content = "[tasks.test]\ncommand = 'pytest'"
        (tmp_path / "pro-mgr.toml").write_text(config_content)
        cfg = config.load_config(str(tmp_path))
        
        with pytest.raises(config.TaskNotFoundError):
            config.resolve_dependencies(cfg, "nonexistent")
