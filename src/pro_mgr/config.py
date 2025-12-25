"""
Configuration module for {{name}}.
Handles TOML parsing, task resolution, and dependency management.
"""

import toml
from pathlib import Path
from typing import Dict, Optional, List, Any, Set

from . import db


class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass


class CyclicDependencyError(ConfigError):
    """Raised when circular task dependencies are detected."""
    pass


class TaskNotFoundError(ConfigError):
    """Raised when a task is not found in the config."""
    pass


def load_config(project_path: str) -> Dict[str, Any]:
    """
    Load and parse the pro-mgr.toml configuration file.
    
    Args:
        project_path: Path to the project root directory
    
    Returns:
        Parsed configuration dictionary
    
    Raises:
        FileNotFoundError: If pro-mgr.toml doesn't exist
        ConfigError: If the TOML file is invalid
    """
    config_path = Path(project_path) / "pro-mgr.toml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = toml.load(f)
        return config
    except toml.TomlDecodeError as e:
        raise ConfigError(f"Invalid TOML syntax: {e}")


def get_task(config: Dict[str, Any], task_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a task definition from the configuration.
    
    Args:
        config: Parsed configuration dictionary
        task_name: Name of the task to retrieve
    
    Returns:
        Task definition dict or None if not found
    """
    tasks = config.get('tasks', {})
    return tasks.get(task_name)


def get_all_tasks(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Get all tasks from the configuration.
    
    Args:
        config: Parsed configuration dictionary
    
    Returns:
        Dictionary of all tasks
    """
    return config.get('tasks', {})


def resolve_dependencies(config: Dict[str, Any], task_name: str) -> List[str]:
    """
    Resolve task dependencies in execution order (topological sort).
    
    Args:
        config: Parsed configuration dictionary
        task_name: Name of the target task
    
    Returns:
        List of task names in execution order (dependencies first, target last)
    
    Raises:
        TaskNotFoundError: If a task doesn't exist
        CyclicDependencyError: If circular dependencies are detected
    """
    tasks = config.get('tasks', {})
    
    if task_name not in tasks:
        raise TaskNotFoundError(f"Task not found: {task_name}")
    
    # Track visited and currently being processed nodes
    visited: Set[str] = set()
    in_progress: Set[str] = set()
    result: List[str] = []
    
    def visit(name: str) -> None:
        """DFS visit for topological sort with cycle detection."""
        if name in visited:
            return
        
        if name in in_progress:
            raise CyclicDependencyError(
                f"Circular dependency detected involving task: {name}"
            )
        
        if name not in tasks:
            raise TaskNotFoundError(f"Task not found: {name}")
        
        in_progress.add(name)
        
        # Visit dependencies first
        task = tasks[name]
        for dep in task.get('depends_on', []):
            visit(dep)
        
        in_progress.remove(name)
        visited.add(name)
        result.append(name)
    
    visit(task_name)
    return result


def expand_snippets(command: str) -> str:
    """
    Replace snippet references with their content.
    
    Snippet references use the format: {snip:snippet_name}
    
    Args:
        command: Command string potentially containing snippet references
    
    Returns:
        Command with snippets expanded
    """
    import re
    
    pattern = r'\{snip:([^}]+)\}'
    
    def replace_snippet(match):
        snippet_name = match.group(1)
        snippet = db.get_snippet(snippet_name)
        if snippet:
            return snippet['content']
        # If snippet not found, leave the reference as-is
        return match.group(0)
    
    return re.sub(pattern, replace_snippet, command)


def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate a configuration file and return any warnings/errors.
    
    Args:
        config: Parsed configuration dictionary
    
    Returns:
        List of warning/error messages (empty if valid)
    """
    warnings = []
    
    # Check for project metadata
    if 'project' not in config:
        warnings.append("Missing [project] section")
    
    # Check for tasks
    tasks = config.get('tasks', {})
    if not tasks:
        warnings.append("No tasks defined")
    
    # Validate each task
    for name, task in tasks.items():
        if 'command' not in task:
            warnings.append(f"Task '{name}' is missing 'command' field")
        
        # Check for undefined dependencies
        for dep in task.get('depends_on', []):
            if dep not in tasks:
                warnings.append(f"Task '{name}' depends on undefined task '{dep}'")
    
    # Check for circular dependencies
    for name in tasks:
        try:
            resolve_dependencies(config, name)
        except CyclicDependencyError as e:
            warnings.append(str(e))
            break  # Only report first cycle
    
    return warnings


def get_project_metadata(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get project metadata from configuration.
    
    Args:
        config: Parsed configuration dictionary
    
    Returns:
        Project metadata dict with defaults
    """
    defaults = {
        'name': 'Unknown',
        'version': '0.0.0',
        'description': '',
    }
    project = config.get('project', {})
    return {**defaults, **project}
