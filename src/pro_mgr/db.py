"""
Database module for {{name}}.
Handles SQLite operations for projects and snippets.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any


def get_db_path() -> Path:
    """Get the path to the database file."""
    db_dir = Path.home() / ".pro-mgr"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "pro-mgr.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(get_db_path(), timeout=10.0)  # 10 second timeout
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create projects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            name TEXT PRIMARY KEY,
            root_path TEXT NOT NULL,
            venv_path TEXT,
            description TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create snippets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snippets (
            name TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usage_count INTEGER DEFAULT 0
        )
    """)
    
    # Create config table for user preferences
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


# ============== Project Operations ==============

def add_project(name: str, root_path: str, venv_path: str = None, 
                description: str = None, tags: str = None) -> bool:
    """
    Add a new project to the database.
    
    Args:
        name: Unique project name
        root_path: Absolute path to project root
        venv_path: Path to virtual environment (optional)
        description: Project description (optional)
        tags: Comma-separated tags (optional)
    
    Returns:
        True if successful, False if project already exists
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO projects (name, root_path, venv_path, description, tags)
            VALUES (?, ?, ?, ?, ?)
        """, (name, root_path, venv_path, description, tags))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_project(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a project by name.
    
    Args:
        name: Project name
    
    Returns:
        Project dict or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()  # Close connection BEFORE calling update_project
    
    if row:
        result = dict(row)
        # Update last_accessed (connection is already closed)
        update_project(name, last_accessed=datetime.now().isoformat())
        return result
    return None


def get_all_projects() -> List[Dict[str, Any]]:
    """
    Get all registered projects.
    
    Returns:
        List of project dicts
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY last_accessed DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_project(name: str) -> bool:
    """
    Remove a project from the registry (does not delete files).
    
    Args:
        name: Project name
    
    Returns:
        True if deleted, False if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE name = ?", (name,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def update_project(name: str, **fields) -> bool:
    """
    Update project fields.
    
    Args:
        name: Project name
        **fields: Fields to update (description, tags, last_accessed, etc.)
    
    Returns:
        True if updated, False if not found
    """
    if not fields:
        return False
    
    # Build SET clause dynamically
    set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
    values = list(fields.values()) + [name]
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE projects SET {set_clause} WHERE name = ?", values)
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def project_exists(name: str) -> bool:
    """Check if a project with the given name exists."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM projects WHERE name = ?", (name,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


# ============== Snippet Operations ==============

def add_snippet(name: str, content: str, tags: str = None) -> bool:
    """
    Add a new code snippet.
    
    Args:
        name: Unique snippet name
        content: The snippet content/command
        tags: Comma-separated tags (optional)
    
    Returns:
        True if successful, False if snippet already exists
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO snippets (name, content, tags)
            VALUES (?, ?, ?)
        """, (name, content, tags))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_snippet(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a snippet by name.
    
    Args:
        name: Snippet name
    
    Returns:
        Snippet dict or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM snippets WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        # Increment usage count
        increment_snippet_usage(name)
        return dict(row)
    return None


def get_all_snippets(tag: str = None) -> List[Dict[str, Any]]:
    """
    Get all snippets, optionally filtered by tag.
    
    Args:
        tag: Optional tag to filter by
    
    Returns:
        List of snippet dicts
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if tag:
        cursor.execute(
            "SELECT * FROM snippets WHERE tags LIKE ? ORDER BY usage_count DESC",
            (f"%{tag}%",)
        )
    else:
        cursor.execute("SELECT * FROM snippets ORDER BY usage_count DESC")
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def search_snippets(query: str) -> List[Dict[str, Any]]:
    """
    Search snippets by name, content, or tags.
    
    Args:
        query: Search query
    
    Returns:
        List of matching snippet dicts
    """
    conn = get_connection()
    cursor = conn.cursor()
    pattern = f"%{query}%"
    cursor.execute("""
        SELECT * FROM snippets 
        WHERE name LIKE ? OR content LIKE ? OR tags LIKE ?
        ORDER BY usage_count DESC
    """, (pattern, pattern, pattern))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_snippet(name: str, content: str = None, tags: str = None) -> bool:
    """
    Update a snippet's content or tags.
    
    Args:
        name: Snippet name
        content: New content (optional)
        tags: New tags (optional)
    
    Returns:
        True if updated, False if not found
    """
    updates = {}
    if content is not None:
        updates['content'] = content
    if tags is not None:
        updates['tags'] = tags
    
    if not updates:
        return False
    
    set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [name]
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE snippets SET {set_clause} WHERE name = ?", values)
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def delete_snippet(name: str) -> bool:
    """
    Delete a snippet.
    
    Args:
        name: Snippet name
    
    Returns:
        True if deleted, False if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM snippets WHERE name = ?", (name,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def increment_snippet_usage(name: str) -> None:
    """Increment the usage count for a snippet."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE snippets SET usage_count = usage_count + 1 WHERE name = ?",
        (name,)
    )
    conn.commit()
    conn.close()


# ============== Config Operations ==============

def set_config(key: str, value: str) -> None:
    """
    Set a configuration value.
    
    Args:
        key: Configuration key (e.g., 'author', 'license', 'default_template')
        value: Value to set
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO config (key, value)
        VALUES (?, ?)
    """, (key, value))
    conn.commit()
    conn.close()


def get_config(key: str) -> Optional[str]:
    """
    Get a configuration value.
    
    Args:
        key: Configuration key
    
    Returns:
        Value or None if not set
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else None


def get_all_config() -> Dict[str, str]:
    """
    Get all configuration values.
    
    Returns:
        Dictionary of key-value pairs
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM config ORDER BY key")
    rows = cursor.fetchall()
    conn.close()
    return {row['key']: row['value'] for row in rows}


def delete_config(key: str) -> bool:
    """
    Delete a configuration value.
    
    Args:
        key: Configuration key
    
    Returns:
        True if deleted, False if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM config WHERE key = ?", (key,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# Initialize database on module import
init_db()
