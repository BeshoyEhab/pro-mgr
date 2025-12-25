"""Tests for the scaffold module."""

import pytest
import tempfile
from pathlib import Path

from pro_mgr import scaffold


class TestTemplates:
    """Tests for template operations."""
    
    def test_get_available_templates(self):
        """Test getting available templates."""
        templates = scaffold.get_available_templates()
        
        assert 'python-cli' in templates
        assert 'flask-api' in templates
        assert 'django-app' in templates
    
    def test_create_project_structure(self, tmp_path):
        """Test creating a project from template."""
        project_path = scaffold.create_project_structure(
            name="test-app",
            template="python-cli",
            path=str(tmp_path)
        )
        
        assert project_path.exists()
        assert (project_path / "pro-mgr.toml").exists()
        assert (project_path / "README.md").exists()
    
    def test_create_project_already_exists(self, tmp_path):
        """Test creating project in existing directory fails."""
        (tmp_path / "existing").mkdir()
        
        with pytest.raises(FileExistsError):
            scaffold.create_project_structure(
                name="existing",
                template="python-cli",
                path=str(tmp_path)
            )
    
    def test_invalid_template(self, tmp_path):
        """Test creating project with invalid template fails."""
        with pytest.raises(scaffold.TemplateNotFoundError):
            scaffold.create_project_structure(
                name="test",
                template="nonexistent-template",
                path=str(tmp_path)
            )


class TestGitVenv:
    """Tests for Git and venv operations."""
    
    def test_init_git(self, tmp_path):
        """Test initializing git repository."""
        result = scaffold.init_git(str(tmp_path))
        
        # May fail if git is not installed
        if result:
            assert (tmp_path / ".git").exists()
    
    def test_create_venv(self, tmp_path):
        """Test creating virtual environment."""
        venv_path = scaffold.create_venv(str(tmp_path))
        
        if venv_path:
            assert venv_path.exists()
    
    def test_detect_venv(self, tmp_path):
        """Test detecting existing venv."""
        # Create a fake venv structure
        venv_dir = tmp_path / ".venv" / "bin"
        venv_dir.mkdir(parents=True)
        (venv_dir / "python").touch()
        
        detected = scaffold.detect_venv(str(tmp_path))
        assert detected is not None
    
    def test_detect_no_venv(self, tmp_path):
        """Test detecting when no venv exists."""
        detected = scaffold.detect_venv(str(tmp_path))
        assert detected is None
