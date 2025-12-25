"""Tests for the database module."""

import pytest
import tempfile
import os
from pathlib import Path

# Set up test database before importing db module
test_db_dir = tempfile.mkdtemp()
os.environ['HOME'] = test_db_dir

from pro_mgr import db


class TestProjectOperations:
    """Tests for project database operations."""
    
    def setup_method(self):
        """Set up fresh database for each test."""
        # Initialize database first
        db.init_db()
        # Clear projects table
        conn = db.get_connection()
        conn.execute("DELETE FROM projects")
        conn.commit()
        conn.close()
    
    def test_add_project(self):
        """Test adding a project."""
        result = db.add_project(
            name="test-project",
            root_path="/test/path",
            venv_path="/test/path/.venv"
        )
        assert result is True
    
    def test_add_duplicate_project(self):
        """Test adding duplicate project fails."""
        db.add_project("test", "/path1")
        result = db.add_project("test", "/path2")
        assert result is False
    
    def test_get_project(self):
        """Test getting a project."""
        db.add_project("my-project", "/some/path", description="Test desc")
        project = db.get_project("my-project")
        
        assert project is not None
        assert project['name'] == "my-project"
        assert project['root_path'] == "/some/path"
        assert project['description'] == "Test desc"
    
    def test_get_nonexistent_project(self):
        """Test getting a project that doesn't exist."""
        project = db.get_project("nonexistent")
        assert project is None
    
    def test_get_all_projects(self):
        """Test getting all projects."""
        db.add_project("proj1", "/path1")
        db.add_project("proj2", "/path2")
        
        projects = db.get_all_projects()
        assert len(projects) == 2
    
    def test_delete_project(self):
        """Test deleting a project."""
        db.add_project("to-delete", "/path")
        result = db.delete_project("to-delete")
        
        assert result is True
        assert db.get_project("to-delete") is None
    
    def test_update_project(self):
        """Test updating a project."""
        db.add_project("updateable", "/path")
        db.update_project("updateable", description="New desc", tags="tag1,tag2")
        
        project = db.get_project("updateable")
        assert project['description'] == "New desc"
        assert project['tags'] == "tag1,tag2"


class TestSnippetOperations:
    """Tests for snippet database operations."""
    
    def setup_method(self):
        """Set up fresh database for each test."""
        db.init_db()
        conn = db.get_connection()
        conn.execute("DELETE FROM snippets")
        conn.commit()
        conn.close()
    
    def test_add_snippet(self):
        """Test adding a snippet."""
        result = db.add_snippet(
            name="docker-run",
            content="docker run -it ubuntu bash",
            tags="docker,container"
        )
        assert result is True
    
    def test_get_snippet(self):
        """Test getting a snippet."""
        db.add_snippet("my-snip", "echo hello")
        snippet = db.get_snippet("my-snip")
        
        assert snippet is not None
        assert snippet['name'] == "my-snip"
        assert snippet['content'] == "echo hello"
    
    def test_search_snippets(self):
        """Test searching snippets."""
        db.add_snippet("docker-build", "docker build .", tags="docker")
        db.add_snippet("docker-push", "docker push img", tags="docker")
        db.add_snippet("npm-install", "npm install", tags="node")
        
        results = db.search_snippets("docker")
        assert len(results) == 2
    
    def test_delete_snippet(self):
        """Test deleting a snippet."""
        db.add_snippet("temp", "temp content")
        result = db.delete_snippet("temp")
        
        assert result is True
        assert db.get_snippet("temp") is None
