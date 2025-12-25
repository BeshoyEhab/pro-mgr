"""
Runner module for pro-mgr.
Handles task execution, virtual environment activation, and dependency running.
"""

import os
import subprocess
import platform
from pathlib import Path
from typing import Dict, Optional, Tuple

from git import Repo, InvalidGitRepositoryError

from . import db, config


class RunnerError(Exception):
    """Base exception for runner errors."""
    pass


class GitDirtyError(RunnerError):
    """Raised when git has uncommitted changes and task requires clean state."""
    pass


def get_shared_cache_dir() -> str:
    """Get the path to the shared pip cache directory."""
    cache_dir = Path.home() / ".pro-mgr" / "pip-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return str(cache_dir)


def activate_virtualenv(venv_path: str) -> Dict[str, str]:
    """
    Get environment variables for activating a virtual environment.
    
    Args:
        venv_path: Path to the virtual environment
    
    Returns:
        Dict of environment variables to set
    """
    venv = Path(venv_path)
    
    if platform.system() == "Windows":
        scripts_dir = venv / "Scripts"
        python_path = scripts_dir / "python.exe"
    else:
        scripts_dir = venv / "bin"
        python_path = scripts_dir / "python"
    
    # Build environment with activated venv
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = str(venv)
    env['PATH'] = str(scripts_dir) + os.pathsep + env.get('PATH', '')
    
    # Remove PYTHONHOME if set (can interfere with venv)
    env.pop('PYTHONHOME', None)
    
    # Use shared pip cache to avoid re-downloading packages
    env['PIP_CACHE_DIR'] = get_shared_cache_dir()
    
    return env


def check_git_dirty(project_path: str) -> bool:
    """
    Check if the git repository has uncommitted changes.
    
    Args:
        project_path: Path to the project
    
    Returns:
        True if there are uncommitted changes (dirty), False if clean
    """
    try:
        repo = Repo(project_path)
        return repo.is_dirty(untracked_files=True)
    except InvalidGitRepositoryError:
        # Not a git repo, consider it clean
        return False


def execute_command(cmd: str, cwd: str, env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
    """
    Execute a shell command.
    
    Args:
        cmd: Command to execute
        cwd: Working directory
        env: Environment variables (optional)
    
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    if env is None:
        env = os.environ.copy()
    
    # Use shell=True for complex commands with pipes, etc.
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        env=env,
        capture_output=False,  # Let output go to terminal
    )
    
    return result.returncode, "", ""


def execute_command_capture(cmd: str, cwd: str, env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
    """
    Execute a shell command and capture output.
    
    Args:
        cmd: Command to execute
        cwd: Working directory
        env: Environment variables (optional)
    
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    if env is None:
        env = os.environ.copy()
    
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )
    
    return result.returncode, result.stdout, result.stderr


def run_single_task(
    task_config: Dict,
    project_path: str,
    env: Optional[Dict[str, str]] = None
) -> int:
    """
    Run a single task.
    
    Args:
        task_config: Task configuration dict
        project_path: Path to the project
        env: Environment variables
    
    Returns:
        Exit code
    """
    command = task_config.get('command', '')
    
    # Expand snippets in the command
    command = config.expand_snippets(command)
    
    # Execute
    exit_code, _, _ = execute_command(command, project_path, env)
    
    return exit_code


def run_task(
    project_name: str,
    task_name: str,
    force: bool = False
) -> int:
    """
    Run a task for a project, including dependencies.
    
    Args:
        project_name: Name of the project
        task_name: Name of the task to run
        force: Whether to skip git dirty check
    
    Returns:
        Exit code (0 for success)
    
    Raises:
        RunnerError: If project or task not found
        GitDirtyError: If git is dirty and task requires clean state
    """
    # Get project info
    project = db.get_project(project_name)
    if not project:
        raise RunnerError(f"Project not found: {project_name}")
    
    project_path = project['root_path']
    venv_path = project.get('venv_path')
    
    # Load configuration
    try:
        proj_config = config.load_config(project_path)
    except FileNotFoundError:
        raise RunnerError(f"No pro-mgr.toml found in {project_path}")
    
    # Get task
    task_config = config.get_task(proj_config, task_name)
    if not task_config:
        raise RunnerError(f"Task not found: {task_name}")
    
    # Check git dirty state
    if task_config.get('fail_on_dirty_branch', False) and not force:
        if check_git_dirty(project_path):
            raise GitDirtyError(
                "Git has uncommitted changes. Commit first or use --force"
            )
    
    # Get environment with venv activated
    env = None
    if venv_path and Path(venv_path).exists():
        env = activate_virtualenv(venv_path)
    
    # Resolve and run dependencies
    try:
        execution_order = config.resolve_dependencies(proj_config, task_name)
    except config.CyclicDependencyError as e:
        raise RunnerError(str(e))
    
    # Run each task in order
    for current_task_name in execution_order:
        current_task = config.get_task(proj_config, current_task_name)
        if not current_task:
            continue
        
        print(f"\n▶ Running task: {current_task_name}")
        
        exit_code = run_single_task(current_task, project_path, env)
        
        if exit_code != 0:
            print(f"✗ Task '{current_task_name}' failed with exit code {exit_code}")
            return exit_code
        
        print(f"✓ Task '{current_task_name}' completed")
    
    return 0


def get_shell_activation_command(project_name: str) -> str:
    """
    Get the shell command to activate a project's environment.
    
    Args:
        project_name: Name of the project
    
    Returns:
        Shell command string for eval
    """
    project = db.get_project(project_name)
    if not project:
        raise RunnerError(f"Project not found: {project_name}")
    
    project_path = project['root_path']
    venv_path = project.get('venv_path')
    
    commands = []
    
    # Change to project directory
    commands.append(f'cd "{project_path}"')
    
    # Activate venv if exists
    if venv_path and Path(venv_path).exists():
        venv = Path(venv_path)
        if platform.system() == "Windows":
            activate_script = venv / "Scripts" / "activate"
        else:
            activate_script = venv / "bin" / "activate"
        
        if activate_script.exists():
            commands.append(f'source "{activate_script}"')
    
    return "; ".join(commands)
